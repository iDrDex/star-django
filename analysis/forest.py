import os
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
    grdevices.png(filename, width=800, height=400)

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
