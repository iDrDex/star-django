import os
import re
import gzip
import urllib.request, urllib.error
import shutil

from easydict import EasyDict
from funcy import log_durations, memoize, cat, re_all
import numpy as np
import pandas as pd
import scipy.stats as stats
from django.db import transaction

from legacy.models import PlatformProbe, MetaAnalysis
from tags.models import Tag, SampleAnnotation

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SERIES_MATRIX_URL = 'ftp://ftp.ncbi.nih.gov/pub/geo/DATA/SeriesMatrix/'
SERIES_MATRIX_MIRROR = os.environ['SERIES_MATRIX_MIRROR']


@log_durations(logger.debug)
def perform_analysis(analysis, debug=False):
    logger.info('Started %s analysis', analysis.analysis_name)
    df = get_analysis_df(analysis)
    debug and df.to_csv("%s.analysis_df.csv" % analysis.analysis_name)

    logger.info('Matching sources: %d' % df.groupby(['series_id', 'platform_id']).ngroups)

    # Remove single-class sources
    query = df.groupby(['series_id', 'platform_id']).sample_class.agg(lambda x: set(x)) >= {0, 1}
    df = filter_sources(df, query, 'as single-class')

    # Check for minimum number of samples
    if not df.empty and analysis.min_samples:
        counts = df.groupby(['series_id', 'platform_id']).sample_class.value_counts().unstack()
        query = (counts[0] >= analysis.min_samples) & (counts[1] >= analysis.min_samples)
        df = filter_sources(df, query, 'by min samples')

    # Check number of sources
    sources = df.groupby(['series_id', 'platform_id']).ngroups
    if sources <= 1:
        logger.error("FAIL Can't perform meta-analysis on %s"
                     % ('single source' if sources else 'no data'))
        return

    # Save analysis df
    analysis.upload_df(df)
    analysis.save(update_fields=['df'])

    # Calculating stats
    analysis.series_count = len(df.series_id.unique())
    analysis.platform_count = len(df.platform_id.unique())
    analysis.sample_count = len(df.sample_id.unique())
    analysis.series_ids = df.series_id.unique().tolist()
    analysis.platform_ids = df.platform_id.unique().tolist()
    analysis.sample_ids = df.sample_id.unique().tolist()
    analysis.save(update_fields=['series_count', 'platform_count', 'sample_count',
                                 'series_ids', 'platform_ids', 'sample_ids'])
    logger.info('Stats: %d sources, %d series, %d platforms, %d samples'
                % (sources, analysis.series_count, analysis.platform_count, analysis.sample_count))

    # Load GSE data, make and concat all fold change analyses results.
    # NOTE: we are doing load_gse() lazily here to avoid loading all matrices at once.
    logger.info('Loading data and calculating fold changes for %s', analysis.analysis_name)
    with log_durations(logger.debug, 'Load/fold for %s' % analysis.analysis_name):
        gses = (load_gse(df, gse_name) for gse_name in sorted(df.gse_name.unique()))
        fold_changes = pd.concat(map(get_fold_change_analysis, gses))
        if fold_changes.empty:
            logger.error("FAIL Got empty fold changes")
            return
        debug and fold_changes.to_csv("%s.fc.csv" % debug)

    logger.info('Saving fold changes to S3')
    analysis.upload_fold_changes(fold_changes, lazy=True)
    analysis.save(update_fields=['fold_changes'])

    logger.info('Meta-Analyzing %s', analysis.analysis_name)
    with log_durations(logger.debug, 'Meta analysis for %s' % analysis.analysis_name):
        balanced = getFullMetaAnalysis(fold_changes, debug=debug).reset_index()
        if balanced.empty:
            logger.error("FAIL Got empty meta-analysis")
            return
        debug and balanced.to_csv("%s.meta.csv" % debug)

    logger.info('Inserting %s analysis results', analysis.analysis_name)
    with log_durations(logger.debug, 'Saving results of %s' % analysis.analysis_name), \
            transaction.atomic():
        balanced['analysis'] = analysis
        balanced.columns = balanced.columns.map(lambda x: x.replace(".", "_").lower())
        field_names = [f.name for f in MetaAnalysis._meta.fields if f.name != 'id']
        rows = balanced[field_names].T.to_dict().values()
        # Delete old values in case we recalculating analysis
        MetaAnalysis.objects.filter(analysis=analysis).delete()
        MetaAnalysis.objects.bulk_create(MetaAnalysis(**row) for row in rows)
        # Mark as successful
        analysis.success = True
        analysis.save(update_fields=['success'])

    logger.info('DONE %s analysis', analysis.analysis_name)


def filter_sources(df, query, reason):
    start_sources = df.groupby(['series_id', 'platform_id']).ngroups
    new_df = df.set_index(['series_id', 'platform_id']).loc[query].reset_index()
    sources = new_df.groupby(['series_id', 'platform_id']).ngroups
    excluded = start_sources - sources
    if excluded:
        logger.info('Excluded %d source%s %s' % (excluded, 's' if excluded > 1 else '', reason))
    return new_df


# from debug_cache import DebugCache
# dcache_new = DebugCache('/home/suor/projects/health/debug_cache_new')
# dcache_tmp = DebugCache('/home/suor/projects/health/debug_cache_tmp')


# @dcache.checked
# @dcache_new.cached
@log_durations(logger.debug)
def get_fold_change_analysis(gse):
    # TODO: get rid of unneeded OOP interface
    return GseAnalyzer(gse).getResults(debug=False)


COLUMNS = {
    'sample__id': 'sample_id',
    'sample__gsm_name': 'gsm_name',
    'annotation': 'annotation',
    'series_annotation__series__id': 'series_id',
    'series_annotation__series__gse_name': 'gse_name',
    'series_annotation__platform__id': 'platform_id',
    'series_annotation__platform__gpl_name': 'gpl_name',
    'series_annotation__tag__tag_name': 'tag_name',
}

@log_durations(logger.debug)
def get_analysis_df(analysis):
    # Fetch all relevant data
    queries = [analysis.case_query, analysis.control_query, analysis.modifier_query]
    tokens = set(cat(re_all(r'[a-zA-Z]\w*', query) for query in queries))

    tags = Tag.objects.filter(tag_name__iregex='^(%s)$' % '|'.join(map(re.escape, tokens)))
    qs = SampleAnnotation.objects.filter(series_annotation__tag__in=tags)
    if analysis.specie:
        qs = qs.filter(series_annotation__series__specie=analysis.specie)
    df = qs.to_dataframe(list(COLUMNS.keys())).rename(columns=COLUMNS)

    # Make tag columns
    df.tag_name = df.tag_name.str.lower()
    df.annotation = df.annotation.str.lower()
    for tag in tags:
        tag_name = tag.tag_name.lower()
        df[tag_name] = df[df.tag_name == tag_name].annotation

    # Select only cells with filled annotations
    df = df.drop(['tag_name', 'annotation'], axis=1)
    df = df.groupby(['sample_id', 'series_id', 'platform_id', 'gsm_name', 'gse_name', 'gpl_name'],
                    as_index=False).first().fillna('')

    df = df.apply(pd.to_numeric, errors='ignore')

    # Apply case/control/modifier
    if analysis.modifier_query:
        df = df.query(analysis.modifier_query.lower())
    case_df = df.query(analysis.case_query.lower())
    control_df = df.query(analysis.control_query.lower())

    # Set 0 and 1 for analysis
    overlap_df = df.ix[set(case_df.index).intersection(set(control_df.index))]

    df['sample_class'] = None
    df.loc[case_df.index, 'sample_class'] = 1
    df.loc[control_df.index, 'sample_class'] = 0
    df.loc[overlap_df.index, 'sample_class'] = -1

    return df.dropna(subset=["sample_class"])


@log_durations(logger.debug)
def load_gse(df, gse_name):
    logger.debug('Loading data for %s', gse_name)
    gpl2data = {}
    gpl2probes = {}

    samples = df[df.gse_name == gse_name].copy()
    for gpl_name in samples.gpl_name.unique():
        gpl2data[gpl_name] = get_data(gse_name, gpl_name)
        gpl2probes[gpl_name] = get_probes(gpl_name)
    return Gse(gse_name, samples, gpl2data, gpl2probes)


def get_matrix_nondata_lines(inStream):
    p = re.compile(br'^"ID_REF"')
    for i, line in enumerate(inStream):
        if p.search(line):
            return i


def get_matrix_filename(gse_name, gpl_name):
    filenames = [
        "%s/%s_series_matrix.txt.gz" % (gse_name, gse_name),
        "%s/%s-%s_series_matrix.txt.gz" % (gse_name, gse_name, gpl_name),
    ]

    for filename in filenames:
        mirror_filename = os.path.join(SERIES_MATRIX_MIRROR, filename)
        if os.path.isfile(mirror_filename):
            return mirror_filename

    for filename in filenames:
        logger.info('Loading URL %s...' % (SERIES_MATRIX_URL + filename))
        try:
            res = urllib.request.urlopen(SERIES_MATRIX_URL + filename)
        except urllib.error.URLError:
            pass
        else:
            mirror_filename = os.path.join(SERIES_MATRIX_MIRROR, filename)
            logger.info('Cache to %s' % mirror_filename)

            directory = os.path.dirname(mirror_filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(mirror_filename, 'wb') as f:
                shutil.copyfileobj(res, f)

            return mirror_filename

    logger.error('Failed loading matrix for serie %s, platform %s', gse_name, gpl_name)


@log_durations(logger.debug)
def get_data(gse_name, gpl_name):
    for attempt in (0, 1):
        matrix_filename = get_matrix_filename(gse_name, gpl_name)
        if not matrix_filename:
            return pd.DataFrame()

        try:
            headerRows = get_matrix_nondata_lines(gzip.open(matrix_filename))
            data = pd.io.parsers.read_table(
                matrix_filename,
                engine='c',
                compression='gzip',
                lineterminator='\n',
                skiprows=headerRows,
                index_col=["ID_REF"],
                na_values=["null", "NA", "NaN", "N/A", "na", "n/a"],
            )
            # Drop last line
            data = data.drop(data.index[-1]).dropna()
            break
        except (IOError, pd.parser.CParserError) as e:
            # In case we have corrupt file
            logger.error("Broken series matrix %s: %s" % (matrix_filename, e))
            os.remove(matrix_filename)
            if attempt:
                raise

    data.index = data.index.astype(str)
    data.index.name = "probe"
    for column in data.columns:
        data[column] = data[column].astype(np.float64)
    return data


@log_durations(logger.debug)
def get_probes(gpl_name):
    df = PlatformProbe.objects.filter(platform__gpl_name=gpl_name).to_dataframe()
    df.columns = [col.lower().replace("platform_probe.", "") for col in df.columns]
    df.probe = df.probe.astype(str)  # must cast probes as str
    df = df.set_index('probe')
    return df


class Gse:
    def __init__(self, name, samples, gpl2data, gpl2probes):
        self.name = name
        self.samples = samples
        self.gpl2data = gpl2data
        self.gpl2probes = gpl2probes

    def __str__(self):
        return '<Gse %s>' % self.name


def getFullMetaAnalysis(fcResults, debug=False):
    debug and fcResults.to_csv("%s.fc.csv" % debug)
    all = []
    # i = 0
    allGeneEstimates = fcResults.sort_values('p') \
        .drop_duplicates(['gse', 'gpl', 'mygene_sym', 'mygene_entrez', 'subset']) \
        .dropna()
    debug and allGeneEstimates.to_csv("%s.geneestimates.csv" % debug)
    for group, geneEstimates in allGeneEstimates.groupby(['mygene_sym', 'mygene_entrez']):
        mygene_sym, mygene_entrez = group
        if len(geneEstimates) == 1:
            continue

        metaAnalysis = getMetaAnalysis(geneEstimates)
        metaAnalysis['caseDataCount'] = geneEstimates['caseDataCount'].sum()
        metaAnalysis['controlDataCount'] = geneEstimates['controlDataCount'].sum()
        metaAnalysis['mygene_sym'] = mygene_sym
        metaAnalysis['mygene_entrez'] = mygene_entrez
        all.append(metaAnalysis)

    if not all:
        return pd.DataFrame()

    allMetaAnalysis = pd.DataFrame(all).set_index(['mygene_sym', 'mygene_entrez'])
    debug and allMetaAnalysis.to_csv('allMetaAnalysis.csv')
    allMetaAnalysis['direction'] = allMetaAnalysis['random_TE'].map(
        lambda x: "up" if x >= 0 else "down")

    return allMetaAnalysis


# @dcache_new.cached
def getMetaAnalysis(geneEstimates):
    return MetaAnalyser(geneEstimates).get_results()


class GseAnalyzer:
    def __init__(self, gse):
        self.gse = gse

    def getResults(self, debug=False):
        gse = self.gse
        samples = gse.samples

        if 'subset' not in samples.columns:
            samples['subset'] = "NA"

        groups = samples[samples.sample_class >= 0].groupby(['subset', 'gpl_name'])

        allResults = pd.DataFrame()

        for group, df in groups:
            subset, gpl = group

            # NOTE: if data has changed then sample ids could be different
            if not set(df["gsm_name"]) <= set(gse.gpl2data[gpl].columns):
                logger.info("skipping %s: sample ids mismatch" % gpl)
                continue

            df = df.set_index("gsm_name")
            data = gse.gpl2data[gpl][df.index]
            # Drop samples with > 80% missing samples
            # data = data.dropna(axis=1, thresh=data.shape[0] * .2)

            sample_class = df.ix[data.columns].sample_class

            debug = debug and debug + ".%s_%s_%s" % (self.gse.name, gpl, subset)
            table = getFoldChangeAnalysis(data, sample_class, debug=debug)
            debug and table.to_csv("%s.table.csv" % debug)

            if not table.empty:
                table['direction'] = table.log2foldChange.map(
                    lambda x: "up" if x > 0 else 'down')
                table['subset'] = subset
                table['gpl'] = gpl
                table['gse'] = self.gse.name
                probes = gse.gpl2probes[gpl]
                table = table \
                    .join(probes[['mygene_entrez', 'mygene_sym']]) \
                    .dropna(subset=['mygene_entrez', 'mygene_sym'])
                allResults = pd.concat([allResults, table.reset_index()])
        # allResults.index.name = "probe"
        self.results = allResults
        return allResults


class MetaAnalyser:
    def isquared(self, H):
        """
        Calculate I-Squared.
        Higgins & Thompson (2002), Statistics in Medicine, 21, 1539-58.
        """
        if H.TE:
            t = lambda x: (x ** 2 - 1) / x ** 2
            return EasyDict(TE=t(H.TE), lower=t(H.lower), upper=t(H.upper))
        else:
            return EasyDict(TE=None, lower=None, upper=None)

    def calcH(self, Q, df, level):
        """
        Calculate H.
        Higgins & Thompson (2002), Statistics in Medicine, 21, 1539-58.
        """
        k = df + 1
        H = np.sqrt(Q / (k - 1))

        result = EasyDict(TE=None, lower=None, upper=None)
        if k > 2:
            if Q <= k:
                selogH = np.sqrt(1 / (2 * (k - 2)) * (1 - 1 / (3 * (k - 2) ** 2)))
            else:
                selogH = 0.5 * (np.log(Q) - np.log(k - 1)) / (np.sqrt(2 * Q) - np.sqrt(2 * k - 3))

            tres = self.getConfidenceIntervals(np.log(H), selogH, level)
            result = EasyDict(TE=1 if np.exp(tres.TE) < 1 else np.exp(tres.TE),
                              lower=1 if np.exp(tres.lower) < 1 else np.exp(tres.lower),
                              upper=1 if np.exp(tres.upper) < 1 else np.exp(tres.upper))
        return result

    norm_ppf = staticmethod(memoize(stats.norm.ppf))
    t_ppf = staticmethod(memoize(stats.t.ppf))

    def getConfidenceIntervals(self, TE, TE_se, level=.95, df=None):
        alpha = 1 - level
        zscore = TE / TE_se
        if not df:
            delta = self.norm_ppf(1 - alpha / 2) * TE_se
            lower = TE - delta
            upper = TE + delta
            pval = 2 * (1 - stats.norm.cdf(abs(zscore)))
        else:
            delta = self.t_ppf(1 - alpha / 2, df=df) * TE_se
            lower = TE - delta
            upper = TE + delta
            pval = 2 * (1 - stats.t.cdf(abs(zscore), df=df))

        result = EasyDict(TE=TE,
                          se=TE_se,
                          level=level,
                          df=df,
                          pval=pval,
                          zscore=zscore,
                          upper=upper,
                          lower=lower)

        return result

    @staticmethod
    def get_TE_se(gene_stats):
        # Convert to numpy arrays for speed
        caseSigma = gene_stats['caseDataSigma'].values
        caseCount = gene_stats['caseDataCount'].values
        controlSigma = gene_stats['controlDataSigma'].values
        controlCount = gene_stats['controlDataCount'].values

        # MD method
        na = np.sqrt(caseSigma ** 2 / caseCount + controlSigma ** 2 / controlCount)

        # Studies with non-positive variance get zero weight in meta-analysis
        for i in range(len(na)):
            if caseSigma[i] <= 0 or controlSigma[i] <= 0:
                na[i] = float('nan')

        return pd.Series(na, index=gene_stats.index)

    def __init__(self, gene_stats):
        TE = gene_stats.caseDataMu.values - gene_stats.controlDataMu.values

        # (7) Calculate results for individual studies
        TE_se = self.get_TE_se(gene_stats)
        w_fixed = (1 / TE_se ** 2).fillna(0)

        TE_fixed = np.average(TE, weights=w_fixed)
        TE_fixed_se = np.sqrt(1 / sum(w_fixed))
        self.fixed = self.getConfidenceIntervals(TE_fixed, TE_fixed_se)

        self.Q = sum(w_fixed * (TE - TE_fixed) ** 2)
        self.Q_df = TE_se.dropna().count() - 1

        self.cVal = sum(w_fixed) - sum(w_fixed ** 2) / sum(w_fixed)
        if self.Q <= self.Q_df:
            self.tau2 = 0
        else:
            self.tau2 = (self.Q - self.Q_df) / self.cVal
        self.tau = np.sqrt(self.tau2)
        self.tau2_se = None
        w_random = (1 / (TE_se ** 2 + self.tau2)).fillna(0)
        TE_random = np.average(TE, weights=w_random)
        TE_random_se = np.sqrt(1 / sum(w_random))
        self.random = self.getConfidenceIntervals(TE_random, TE_random_se)

        # Prediction interval
        self.level_predict = 0.95
        self.k = TE_se.count()
        self.predict = EasyDict(TE=None,
                                se=None,
                                level=None,
                                df=None,
                                pval=None,
                                zscore=None,
                                upper=None,
                                lower=None)
        if self.k >= 3:
            TE_predict_se = np.sqrt(TE_random_se ** 2 + self.tau2)
            self.predict = self.getConfidenceIntervals(TE_random, TE_predict_se, self.level_predict,
                                                       self.k - 2)

        # Calculate H and I-Squared
        self.level_comb = 0.95
        self.H = self.calcH(self.Q, self.Q_df, self.level_comb)
        self.I2 = self.isquared(self.H)

    def get_results(self):
        return dict(
            k=self.k,
            fixed_TE=self.fixed.TE,
            fixed_se=self.fixed.se,
            fixed_lower=self.fixed.lower,
            fixed_upper=self.fixed.upper,
            fixed_pval=self.fixed.pval,
            fixed_zscore=self.fixed.zscore,

            random_TE=self.random.TE,
            random_se=self.random.se,
            random_lower=self.random.lower,
            random_upper=self.random.upper,
            random_pval=self.random.pval,
            random_zscore=self.random.zscore,


            predict_TE=self.predict.TE,
            predict_se=self.predict.se,
            predict_lower=self.predict.lower,
            predict_upper=self.predict.upper,
            predict_pval=self.predict.pval,
            predict_zscore=self.predict.zscore,

            tau2=self.tau2,
            tau2_se=self.tau2_se,

            C=self.cVal,

            H=self.H.TE,
            H_lower=self.H.lower,
            H_upper=self.H.upper,

            I2=self.I2.TE,
            I2_lower=self.I2.lower,
            I2_upper=self.I2.upper,

            Q=self.Q,
            Q_df=self.Q_df,
        )


def getFoldChangeAnalysis(data, sample_class, debug=False):
    from scipy.stats import ttest_ind

    data = normalize_quantiles(get_logged(data))

    summary = pd.DataFrame(index=data.index)

    summary['dataMu'] = data.mean(axis="columns")
    summary['dataSigma'] = data.std(axis="columns")
    summary['dataCount'] = data.count(axis="columns")

    caseData = data.T[sample_class == 1].T
    debug and caseData.to_csv("%s.case.data.csv" % debug)
    summary['caseDataMu'] = caseData.mean(axis="columns")
    summary['caseDataSigma'] = caseData.std(axis="columns") if len(caseData.columns) > 1 else 0
    summary['caseDataCount'] = caseData.count(axis="columns")

    controlData = data.T[sample_class == 0].T
    debug and controlData.to_csv("%s.control.data.csv" % debug)

    summary['controlDataMu'] = controlData.mean(axis="columns")
    summary['controlDataSigma'] = controlData.std(axis="columns") \
        if len(controlData.columns) > 1 else 0
    summary['controlDataCount'] = controlData.count(axis="columns")

    summary['fc'] = summary['caseDataMu'] - summary['controlDataMu']
    summary['log2foldChange'] = summary['fc']
    # else:
    # summary['fc'] = np.log2(summary['caseDataMu']/summary['controlDataMu'])

    summary['effect_size'] = summary['fc'] / summary['dataSigma']

    ttest, prob = ttest_ind(caseData, controlData, axis=1)
    summary['ttest'] = ttest
    summary['p'] = prob
    summary['direction'] = summary['effect_size'].map(lambda x: "up" if x >= 0 else "down")

    return summary


def normalize_quantiles(df):
    """
    df with samples in the columns and probes across the rows
    """
    # http://biopython.org/pipermail/biopython/2010-March/006319.html
    A = df.values
    AA = np.empty_like(A)
    I = np.argsort(A, axis=0)
    AA[I, np.arange(A.shape[1])] = np.mean(A[I, np.arange(A.shape[1])], axis=1)[:, np.newaxis]
    return pd.DataFrame(AA, index=df.index, columns=df.columns)


import numexpr as ne

def get_logged(df):
    if df.empty or is_logged(df):
        return df

    data = df.values
    floor = np.abs(np.min(data, axis=0))  # noqa
    res = ne.evaluate('log(data + floor + 1) / log(2)')
    return pd.DataFrame(res, index=df.index, columns=df.columns)

def is_logged(df):
    return np.max(df.values) < 10
