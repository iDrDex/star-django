from django.conf.urls import url

import djapi as api
from . import views


urlpatterns = [
    url(r'^series/$', views.series),
    url(r'^series/(\w+)/$', views.series_detail),
    url(r'^series/(\w+)/samples/$', views.series_samples),

    url(r'^platforms/$', views.platforms),
    url(r'^platforms/(\w+)/$', views.platform_detail),
    url(r'^platforms/(\w+)/probes/$', views.platform_probes),

    url(r'^tags/$', api.get_post(views.tags, views.tag_create)),
    # url(r'^tags/form/$', views.tag_create),
    url(r'^tags/(\d+)/$', views.tag_detail),

    url(r'^analysis/$', api.get_post(views.analysis_list, views.analysis_create), name='analysis'),
    url(r'^analysis/form/$', api.show_form(form=views.AnalysisForm, view='analysis')),
    url(r'^analysis/(\d+)/$', views.analysis_detail),

    url(r'^annotations/$', api.get_post(views.annotations, views.annotate),
        name='annotations'),
    url(r'^annotations/form/$', api.show_form(form=views.AnnotateForm, view='annotations')),
    url(r'^annotations/(\d+)/$', views.annotation_detail),
    url(r'^annotations/(\d+)/samples/$', views.annotation_samples),
]
