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
    url(r'^analysis/form/$', views.analysis_form),
    url(r'^analysis/(\d+)/$', views.analysis_detail),
]
