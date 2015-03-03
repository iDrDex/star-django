from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
    url(r'^$', 'tags.views.search', name='search'),
    url(r'^tag/$', 'tags.views.annotate', name='annotate'),

    url(r'^admin/', include(admin.site.urls)),
)
