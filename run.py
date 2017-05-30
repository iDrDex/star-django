import starapi.main as api
from starapi import conf
conf.configure('./')
import starapi.analysis as analysis
from easydict import EasyDict

paramaters = EasyDict(
    analysis_name="primary vs nevus (cutaneous only)",
    case_query="""primary_cancer=='primary_cancer'""",
    control_query="""nevus=='nevus'""",
    modifier_query="""primary_uveal_melanoma!='primary_uveal_melanoma'""",
    min_samples=3
)

paramaters = EasyDict(
    analysis_name="Dengue",
    case_query="""DHF=='DHF' or DSS=='DSS'""",
    control_query="""DF=='DF'""",
    modifier_query="""Dengue_Acute=="Dengue_Acute" or Dengue_Early_Acute=='Dengue_Early_Acute' or Dengue_Late_Acute == 'Dengue_Late_Acute' or Dengue_DOF <= 7""",
    min_samples=3
)

# sample_class = api.get_annotations(paramaters.case_query, paramaters.control_query, paramaters.modifier_query)
# sample_class.to_csv('sc.csv')
# 1/0


samples, fc, results, permutations = analysis.perform_analysis(paramaters, nperm=0, debug=paramaters.analysis_name)
results.to_csv(paramaters.analysis_name+".csv")

1/0



sample_class = api.get_annotations("""MB_SHH=='MB_SHH' or  MB_Group3=='MB_Group3' or  MB_Group4=='MB_Group4' """,
                    """MB_Cerebellum_Control=='MB_Cerebellum_Control'""")#\

# sample_class = api.get_annotations("""asthma=='Asthma'""",
#                     """asthma_control=='asthma_control'""")#\
#                   .query("""gse_name == 'GSE4302'""")
sample_class['code'] = sample_class.gsm_name + "_" + sample_class.gpl_name + "_" + sample_class.gse_name
sample_class = sample_class.set_index('code')

combat=analysis.combat(sample_class.head(100))
