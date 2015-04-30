from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',  # noqa
    url(r'^$', 'core.views.dashboard', name='dashboard'),

    url(r'^search/$', 'tags.views.search', name='search'),
    url(r'^annotate/$', 'tags.views.annotate', name='annotate'),
    url(r'^validate/$', 'tags.views.validate', name='validate'),
    url(r'^stats/$', 'tags.views.stats', name='stats'),

    url(r'^admin/', include(admin.site.urls)),
)
