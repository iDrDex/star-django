# import os
# import os.path
# import sys
# import re
# import gzip
# import urllib2
# import shutil
# from functools import wraps

# from funcy import str_join, first, log_durations

# import pandas.rpy.common as com
# import rpy2.robjects as robjects

# r = robjects.r

import logging
logger = logging.getLogger("stargeo.analysis")
logger.setLevel(logging.DEBUG)

import numpy as np
import pandas as pd
from django.db import connections

from legacy.models import Tag, Sample, Series, Platform


def get_full_df():
    tags_qs = Tag.objects.values_list('tag_name', flat=True).order_by('tag_name').distinct()
    tags = [tag.lower() for tag in tags_qs]

    sample_tag_view_fields = ['id', 'series_id', 'platform_id', 'sample_id'] + tags
    fields = ['sample_tag_view.{0} as "sample_tag_view.{0}"'.format(f) for f in sample_tag_view_fields]
    for cls in (Sample, Series, Platform):
        fields += ['{0}.{1} as "{0}.{1}"'.format(cls._meta.db_table, field.column)
                    for field in cls._meta.fields]
    fields_sql = ','.join(fields)

    df = pd.read_sql_query('''
        select %s
            from sample_tag_view
            join sample on (sample_tag_view.sample_id = sample.id)
            join series on (sample_tag_view.series_id = series.id)
            join platform on (sample_tag_view.platform_id = platform.id)
    ''' % fields_sql, connections['legacy']).convert_objects(convert_numeric=True)

    clean_columns = []
    clean_series = []

    for col in df.columns:
        table, header = col.split(".")
        field = header.lower()
        if (field in tags) or \
                (field in ['gse_name', 'gpl_name', 'gsm_name', "series_id", "sample_id", "platform_id"]):
            toAdd = field
        else:
            toAdd = col
        if toAdd not in clean_columns:
            clean_columns.append(toAdd)
            clean_series.append(df[col])

    clean_df = pd.DataFrame(dict(zip(clean_columns, clean_series)))
    for col in clean_df.columns:
        if col in tags:
            if clean_df.dtypes[col] == object:
                clean_df[col] = clean_df[col].str.lower()

    return clean_df#.fillna(np.nan).replace('', np.nan)


def get_analysis_df(case_query, control_query, modifier_query):
    # NOTE: would be more efficient to select only required data
    df = get_full_df()
    # df = db(Sample_Tag_View).select(processor=pandas_processor)
    # print 'queries', case_query, control_query, modifier_query
    case_df = df.query(case_query.lower())
    # print 'case_df', len(case_df)
    control_df = df.query(control_query.lower())
    # print 'control_df', len(control_df)
    modifier_df = pd.DataFrame()
    # R: modify then select case and control, no need for this fancy intersections.
    if modifier_query:
        modifier_df = df.query(modifier_query.lower())
        case_df = df.ix[set(case_df.index).intersection(set(modifier_df.index))]
        control_df = df.ix[set(control_df.index).intersection(set(modifier_df.index))]

    # set 0 and 1 for analysis
    overlap_df = df.ix[set(case_df.index).intersection(set(control_df.index))]

    df['sample_class'] = None
    df['sample_class'].ix[case_df.index] = 1
    df['sample_class'].ix[control_df.index] = 0
    df['sample_class'].ix[overlap_df.index] = -1

    analysis_df = df.dropna(subset=["sample_class"])
    return analysis_df


class Gse:
    def __init__(self, name, samples, gpl2data, gpl2probes):
        self.name = name
        self.samples = samples
        self.gpl2data = gpl2data
        self.gpl2probes = gpl2probes

    def __str__(self):
        return '<Gse %r>' % self.name


def load_gse(df, series_id):
    gse_name = Series[series_id].gse_name
    logger.debug('Loading data for %s, id = %d', gse_name, series_id)
    gpl2data = {}
    gpl2probes = {}

    for platform_id in df.query("""series_id == %s""" % series_id).platform_id.unique():
        gpl_name = Platform[platform_id].gpl_name
        gpl2data[gpl_name] = get_data(series_id, platform_id)
        gpl2probes[gpl_name] = get_probes(platform_id)
    samples = df.query('series_id == %s' % series_id)
    return Gse(gse_name, samples, gpl2data, gpl2probes)


def __getMatrixNumHeaderLines(inStream):
    p = re.compile(r'^"ID_REF"')
    for i, line in enumerate(inStream):
        if p.search(line):
            return i


def matrix_filenames(series_id, platform_id):
    gse_name = Series[series_id].gse_name
    yield "%s/%s_series_matrix.txt.gz" % (gse_name, gse_name)

    gpl_name = Platform[platform_id].gpl_name
    yield "%s/%s-%s_series_matrix.txt.gz" % (gse_name, gse_name, gpl_name)


def get_matrix_filename(series_id, platform_id):
    filenames = list(matrix_filenames(series_id, platform_id))
    mirror_filenames = (os.path.join(conf.SERIES_MATRIX_MIRROR, filename) for filename in filenames)
    mirror_filename = first(filename for filename in mirror_filenames if os.path.isfile(filename))
    if mirror_filename:
        return mirror_filename

    for filename in filenames:
        print 'Loading URL', conf.SERIES_MATRIX_URL + filename, '...'
        try:
            res = urllib2.urlopen(conf.SERIES_MATRIX_URL + filename)
        except urllib2.URLError:
            pass
        else:
            mirror_filename = os.path.join(conf.SERIES_MATRIX_MIRROR, filename)
            print 'Cache to', mirror_filename

            directory = os.path.dirname(mirror_filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(mirror_filename, 'wb') as f:
                shutil.copyfileobj(res, f)

            return mirror_filename

    raise LookupError("Can't find matrix file for series %s, platform %s"
                      % (series_id, platform_id))


@log_durations(logger.debug)
def get_data(series_id, platform_id):
    matrixFilename = get_matrix_filename(series_id, platform_id)
    # setup data for specific platform
    for attempt in (0, 1):
        try:
            headerRows = __getMatrixNumHeaderLines(gzip.open(matrixFilename))
            na_values = ["null", "NA", "NaN", "N/A", "na", "n/a"]
            data = pd.io.parsers.read_table(gzip.open(matrixFilename),
                                            skiprows=headerRows,
                                            index_col=["ID_REF"],
                                            na_values=na_values,
                                            skipfooter=1,
                                            engine='python')
        except IOError as e:
            # In case we have cirrupt file
            print "Failed loading %s: %s" % (matrixFilename, e)
            os.remove(matrixFilename)
            if attempt:
                raise
            matrixFilename = get_matrix_filename(series_id, platform_id)

    data.index = data.index.astype(str)
    data.index.name = "probe"
    for column in data.columns:
        data[column] = data[column].astype(np.float64)
    # return data.head(100)
    return data


# @log_durations(logger.debug)
# def get_probes(platform_id):
#     df = db(Platform_Probe.platform_id == platform_id).select(processor=pandas_processor)
#     df.columns = [col.lower().replace("platform_probe.", "") for col in df.columns]
#     df.probe = df.probe.astype(str)  # must cast probes as str
#     df = df.set_index('probe')
#     # return df
#     return df


# def getFullMetaAnalysis(fcResults, debug=False):
#     import glob

#     debug and fcResults.to_csv("%s.fc.csv" % debug)
#     all = []
#     i = 0
#     allGeneEstimates = fcResults.sort('p') \
#         .drop_duplicates(['gse', 'gpl', 'mygene_sym', 'mygene_entrez', 'subset']) \
#         .dropna()
#     debug and allGeneEstimates.to_csv("%s.geneestimates.csv" % debug)
#     for group, geneEstimates in allGeneEstimates.groupby(['mygene_sym', 'mygene_entrez']):
#         mygene_sym, mygene_entrez = group
#         if debug:
#             print i, group
#         i += 1
#         geneEstimates.title = mygene_sym
#         # debug and geneEstimates.to_csv("%s.%s.fc.csv" % (debug, mygene_sym))
#         metaAnalysis = getMetaAnalysis(geneEstimates)
#         metaAnalysis['caseDataCount'] = geneEstimates['caseDataCount'].sum()
#         metaAnalysis['controlDataCount'] = geneEstimates['controlDataCount'].sum()
#         metaAnalysis['mygene_sym'] = mygene_sym
#         metaAnalysis['mygene_entrez'] = mygene_entrez
#         all.append(metaAnalysis)
#     allMetaAnalysis = pd.DataFrame(all).set_index(['mygene_sym', 'mygene_entrez'])
#     allMetaAnalysis['effect_size'] = allMetaAnalysis['TE.random']
#     allMetaAnalysis['direction'] = allMetaAnalysis['effect_size'].map(lambda x: "up" if x >= 0 else "down")
#     # allMetaAnalysis.to_csv(filename)

#     return allMetaAnalysis


# def getFullUnbalancedMetaAnalysis(rankedResults, filename=None):
#     import glob

#     if not glob.glob(filename):
#         sample_class2metaAnalysis = {}
#         # for sample_class in [0,1]:
#         all = []
#         # estimates = rankedResults[rankedResults.sample_class == sample_class]
#         i = 0
#         for group, geneEstimates in rankedResults.groupby(['mygene_sym', 'mygene_entrez', 'subset']):
#             # if i > 100:
#             # continue
#             # print i, group
#             i += 1
#             mygene_sym, mygene_entrez, subset = group
#             metaAnalysis = getUnbalancedMetaAnalysis(geneEstimates)
#             metaAnalysis['count'] = geneEstimates['count'].sum()
#             metaAnalysis['mygene_sym'] = mygene_sym
#             metaAnalysis['mygene_entrez'] = mygene_entrez
#             metaAnalysis['subset'] = subset
#             # meta = pd.DataFrame(metaAnalysis, index=pd.MultiIndex.from_tuples([group], names=['mygene_sym', 'mygene_entrez', 'subset'])).reset_index()
#             all.append(metaAnalysis)
#         allMetaAnalysis = pd.DataFrame(all)

#         controlMeta = allMetaAnalysis.query('subset == "control"').set_index(['mygene_sym', 'mygene_entrez'])
#         controlMeta.columns = ["control_%s" % col for col in controlMeta.columns]
#         caseMeta = allMetaAnalysis.query('subset == "case"').set_index(['mygene_sym', 'mygene_entrez'])
#         caseMeta.columns = ["case_%s" % col for col in caseMeta.columns]
#         jointMeta = caseMeta.join(controlMeta)
#         jointMeta['effect_size'] = jointMeta['case_TE.random'] - jointMeta['control_TE.random']
#         jointMeta['direction'] = jointMeta['effect_size'].map(lambda x: "up" if x >= 0 else "down")
#         jointMeta.to_csv(filename)
#     else:
#         jointMeta = pd.read_csv(filename) \
#             .set_index(['mygene_sym', 'mygene_entrez'])

#     return jointMeta


# class GseAnalyzer:
#     def __init__(self, gse):
#         self.gse = gse

#     # def getRnormalize_quantiles(self):
#     # r_data = com.convert_to_r_matrix(self.gse.data)
#     # r_normalData = r['normalize_quantiles'](r_data)
#     # r_normalData.colnames = r_data.colnames
#     # r_normalData.rownames = r_data.rownames
#     # return r_normalData

#     def getResults(self, gpls=None, subsets=None, numPerm=100, how='samr', name=None, debug=False):
#         gse = self.gse
#         samples = gse.samples

#         if 'subset' not in samples.columns:
#             samples['subset'] = "NA"

#         groups = samples.ix[samples.sample_class >= 0] \
#             .groupby(['subset', 'gpl_name'])

#         allResults = pd.DataFrame()

#         for group, df in groups:
#             subset, gpl = group
#             probes = gse.gpl2probes[gpl]
#             print subset, gpl
#             if subsets and subset not in subsets:
#                 print "skipping", subset
#                 continue
#             if gpls and gpl not in gpls:
#                 print "skipping", gpl
#                 continue
#             df = df.set_index("gsm_name")
#             data = gse.gpl2data[gpl][df.index]
#             # data = data.dropna(axis=1, thresh=data.shape[0] * .2)  #drop samples with > 80% missing samples

#             myCols = ['mygene_sym', 'mygene_entrez']
#             table = pd.DataFrame(columns=myCols).set_index(myCols)
#             if how == 'ranked':
#                 caseData = data[df.query('sample_class == 1').index]
#                 caseEstimates = getGeneEstimates(caseData, probes)
#                 caseEstimates['sample_class'] = 1
#                 caseEstimates['subset'] = 'case'
#                 if not caseEstimates.empty:
#                     table = pd.concat([table, caseEstimates])
#                 controlData = data[df.query('sample_class == 0').index]
#                 controlEstimates = getGeneEstimates(controlData, probes)
#                 controlEstimates['sample_class'] = 0
#                 controlEstimates['subset'] = 'control'
#                 if not controlEstimates.empty:
#                     table = pd.concat([table, controlEstimates])
#                 table['gse'] = gse.name
#                 table['gpl'] = gpl
#                 # table['subset'] = subset
#                 allResults = pd.concat([allResults, table.reset_index()])
#             # Studies with defined SAMPLE CLASS
#             else:
#                 # at least 2 samples required
#                 if len(df.sample_class) < 3:
#                     print "skipping for insufficient data", df.sample_class
#                     continue
#                 # at least 1 case and control required
#                 classes = df.sample_class.unique()
#                 if not (0 in classes and 1 in classes):
#                     print "skipping for insufficient data", df.sample_class
#                     continue
#                 # data.to_csv("data.test.csv")
#                 sample_class = df.ix[data.columns].sample_class

#                 if how == 'fc':
#                     debug = debug and debug + ".%s_%s_%s" % (self.gse.name, gpl, subset)
#                     table = getFoldChangeAnalysis(data, sample_class,
#                                                   debug=debug)
#                     debug and table.to_csv("%s.table.csv" % debug)
#                     # table['log2foldChange'] = table['fc'] if isLogged(data) else np.log2(table['fc'])
#                 else:
#                     if how == 'samr':
#                         results = getSamrAnalysis(data, sample_class, numPerm)
#                         if results:
#                             for table in results:
#                                 if not table.empty:
#                                     # SAMR returns raw fold changes but Numerator(r) contains the log2 transform
#                                     # table['log2foldChange'] = table['Numerator(r)'] if isLogged(data) else np.log2(table['Numerator(r)'])
#                                     table['log2foldChange'] = np.log2(table['Fold Change'])
#                                     # print table['log2foldChange']
#                     elif how == 'rp':
#                         results = getRpAnalysis(data, sample_class, numPerm)
#                         if results:
#                             for table in results:
#                                 if not table.empty:
#                                     # invert b/c RANKPROD does the goofy condition 1 / condition 2
#                                     # also force RP results in log2 with logged = False in RP call
#                                     table['log2foldChange'] = -1.0 * table['FC:(class1/class2)'] if isLogged(
#                                         data) else np.log2(-1.0 * table['FC:(class1/class2)'])
#                     if results:
#                         table1, table2 = results
#                         # table1['direction'] = 'up'
#                         # table2['direction'] = 'down'
#                         table = pd.concat([table1, table2])

#                 if not table.empty:
#                     table['direction'] = table.log2foldChange.map(lambda x: "up" if x > 0 else 'down')
#                     table['subset'] = subset
#                     table['gpl'] = gpl
#                     table['gse'] = self.gse.name
#                     probes = gse.gpl2probes[gpl]
#                     table = table \
#                         .join(probes[['mygene_entrez', 'mygene_sym']]) \
#                         .dropna(subset=['mygene_entrez', 'mygene_sym'])
#                     allResults = pd.concat([allResults, table.reset_index()])
#         # allResults.index.name = "probe"
#         self.results = allResults
#         return allResults


# class MetaAnalyzer():
#     def __init__(self, gses):
#         self.gses = gses
#         self.allFcResults = None
#         self.allRankedResults = None

#     def getFc(self, debug=False):
#         print "calculating fold changes"
#         allResults = [GseAnalyzer(gse).getResults(how='fc', debug=debug) for gse in self.gses]
#         self.allFcResults = pd.concat(allResults)
#         debug and self.allFcResults.to_csv("%s.allFcResults.csv" % debug)
#         return self.allFcResults

#     def getRanks(self):
#         print "calculating gene ranks"
#         self.allRankedResults = pd.concat([GseAnalyzer(gse).getResults(how='ranked') for gse in self.gses])
#         return self.allRankedResults

#     def getBalancedResults(self, debug=False):
#         if not type(self.allFcResults) == pd.DataFrame:
#             self.getFc(debug=debug)
#         return getFullMetaAnalysis(self.allFcResults, debug=debug)

#     def getUnbalancedResults(self, fileName):
#         if not type(self.allRankedResults) == pd.DataFrame:
#             self.getRanks()
#         return getFullUnbalancedMetaAnalysis(self.allRankedResults, fileName)


# def getFoldChangeAnalysis(data, sample_class, doPopSize=False, debug=False):
#     from scipy.stats import ttest_ind

#     data = getNormalize_quantiles(getLogged(data))

#     summary = pd.DataFrame(index=data.index)

#     # R: should we just transpose data matrix at the start?
#     summary['dataMu'] = data.mean(axis="columns")
#     summary['dataSigma'] = data.std(axis="columns")
#     summary['dataCount'] = data.count(axis="columns")

#     caseData = data.T[sample_class == 1].T
#     debug and caseData.to_csv("%s.case.data.csv" % debug)
#     summary['caseDataMu'] = caseData.mean(axis="columns")
#     summary['caseDataSigma'] = caseData.std(axis="columns") if len(caseData.columns) > 1 else 0
#     summary['caseDataCount'] = caseData.count(axis="columns")

#     controlData = data.T[sample_class == 0].T
#     debug and controlData.to_csv("%s.control.data.csv" % debug)

#     summary['controlDataMu'] = controlData.mean(axis="columns")
#     summary['controlDataSigma'] = controlData.std(axis="columns") if len(controlData.columns) > 1 else 0
#     summary['controlDataCount'] = controlData.count(axis="columns")

#     summary['fc'] = summary['caseDataMu'] - summary['controlDataMu']
#     summary['log2foldChange'] = summary['fc']
#     # else:
#     # summary['fc'] = np.log2(summary['caseDataMu']/summary['controlDataMu'])

#     summary['effect_size'] = summary['fc'] / summary['dataSigma']
#     ttest = pd.DataFrame([ttest_ind(caseData.ix[probe].dropna(),
#                                     controlData.ix[probe].dropna())
#                           for probe in data.index],
#                          columns=['ttest', 'p'],
#                          index=data.index)

#     debug and ttest.to_csv("%s.ttest.csv" % debug)

#     # mask to deal with missing data: http://stackoverflow.com/questions/23543431/treatment-of-nans
#     # ttest = ttest_ind(caseData[np.isfinite(caseData)],
#     # controlData[np.isfinite(controlData)],
#     # axis=1)
#     summary['ttest'] = ttest['ttest']
#     summary['p'] = ttest['p']
#     summary['direction'] = summary['effect_size'].map(lambda x: "up" if x >= 0 else "down")
#     if doPopSize:
#         summary['alpha'] = 0.05
#         summary['power'] = 0.75
#         summary['ratio'] = 2  # summary['controlDataCount']*1.0/summary['caseDataCount']
#         summary['alternative'] = summary['fc'].map(lambda x: "larger" if x >= 0 else "smaller")
#         summary['popsize'] = summary.apply(getPopsize, axis="columns")
#     # 1/0
#     return summary


# def getNormalize_quantiles(data):
#     rNormData = getRnormalize_quantiles(data)
#     normData = pd.DataFrame(np.asmatrix(rNormData))
#     normData.columns = data.columns
#     normData.index = data.index
#     return normData


# def getRnormalize_quantiles(data):
#     r.library("preprocessCore")
#     r_data = com.convert_to_r_matrix(data)
#     r_normalData = r['normalize.quantiles'](r_data)
#     r_normalData.colnames = r_data.colnames
#     r_normalData.rownames = r_data.rownames
#     return r_normalData


# def isLogged(data):
#     return True if (data.std() < 10).all() else False


# def getLogged(data):
#     # if (data.var() > 10).all():
#     if isLogged(data):
#         return data
#     return np.log2(translateNegativeCols(data))


# def translateNegativeCols(data):
#     """Translate the minimum value of each col to 1"""
#     transformed = data + np.abs(np.min(data)) + 1
#     return transformed


# def getMetaAnalysis(geneEstimates):
#     m = getMetaAnalysisFromR(geneEstimates)
#     # return _convertMetaAnslysisFromR(m)
#     return parseRListForSingleEntries(m)


# def getMetaAnalysisFromR(geneEstimates):
#     r.library("meta")
#     m = r.metacont(robjects.IntVector(geneEstimates.caseDataCount),
#                    robjects.FloatVector(geneEstimates.caseDataMu),
#                    robjects.FloatVector(geneEstimates.caseDataSigma),
#                    robjects.IntVector(geneEstimates.controlDataCount),
#                    robjects.FloatVector(geneEstimates.controlDataMu),
#                    robjects.FloatVector(geneEstimates.controlDataSigma),
#                    studlab=robjects.StrVector(geneEstimates.gse),
#                    byvar=robjects.StrVector(geneEstimates.subset),
#                    bylab="subset",
#                    title=geneEstimates.title
#     )
#     return m


# def parseRListForSingleEntries(rListVector):
#     return dict(zip(list(rListVector.names),
#                     [i[0] if i and len(i) == 1 else None for i in rListVector]))
