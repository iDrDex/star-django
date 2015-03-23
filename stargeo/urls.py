from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView


urlpatterns = patterns('',  # noqa
    url(r'^$', TemplateView.as_view(template_name='dashboard.j2'), name='search'),
    url(r'^search/$', 'tags.views.search', name='search'),
    url(r'^annotate/$', 'tags.views.annotate', name='annotate'),
    url(r'^validate/$', 'tags.views.validate', name='validate'),

    url(r'^admin/', include(admin.site.urls)),
)
