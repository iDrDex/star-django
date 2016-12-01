import os
import math
from funcy import suppress

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
r = robjects.r
r.options(digits=2)

from django.conf import settings


PLOTS_DIR = os.path.join(os.path.dirname(settings.BASE_DIR), 'forest_plots')


def prepare_gene_plot(analysis, mygene_sym):
    filename = '%s/%s/%s.png' % (PLOTS_DIR, analysis.id, mygene_sym)
    if not os.path.exists(filename):
        with suppress(OSError):
            os.makedirs(os.path.dirname(filename))
        write_gene_plot(filename, mygene_sym, analysis.fold_changes.frame)
    return filename


def write_gene_plot(filename, mygene_sym, fc):
    meta_gene = fc[fc.mygene_sym == mygene_sym].drop_duplicates(['gpl', 'gse'])
    meta_gene.title = mygene_sym
    m = get_meta_analysis_from_r(meta_gene)

    grdevices = importr('grDevices')
    grdevices.png(filename, width=950, height=400)

    r.forest(m, pred=True)

    grdevices.dev_off()


def get_meta_analysis_from_r(gene_estimates):
    r.library("meta")
    m = r.metacont(
        robjects.IntVector(gene_estimates.caseDataCount),
        robjects.FloatVector(gene_estimates.caseDataMu),
        robjects.FloatVector(gene_estimates.caseDataSigma),
        robjects.IntVector(gene_estimates.controlDataCount),
        robjects.FloatVector(gene_estimates.controlDataMu),
        robjects.FloatVector(gene_estimates.controlDataSigma),
        studlab=robjects.StrVector(gene_estimates.gse),
        byvar=robjects.StrVector(gene_estimates.subset),
        bylab="subset",
        title=gene_estimates.title
    )
    return m


def get_gene_analysis(analysis, mygene_sym):
    fc = analysis.fold_changes.frame
    meta_gene = fc[fc.mygene_sym == mygene_sym].drop_duplicates(['gpl', 'gse'])
    meta_gene.title = mygene_sym
    m = get_meta_analysis_from_r(meta_gene)
    return r2py(m)


def r2py(obj):
    if isinstance(obj, float):
        return None if math.isnan(obj) else obj
    elif isinstance(obj, (int, str, bool)):
        return obj
    elif obj is robjects.NULL or obj is robjects.NA_Logical:
        return None
    elif isinstance(obj, robjects.ListVector):
        return {k: r2py(v) for k, v in obj.items()}
    elif isinstance(obj, robjects.Vector):
        return r2py(obj[0]) if len(obj) == 1 else map(r2py, obj)
    elif isinstance(obj, robjects.SignatureTranslatedFunction):
        return '<function>'
    else:
        return obj
