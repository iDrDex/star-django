from django.conf.urls import patterns, include, url
from django.contrib import admin

from core.forms import PasswordResetForm


urlpatterns = patterns('',  # noqa
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'}),
    url(r'^accounts/password_reset/$', 'django.contrib.auth.views.password_reset',
        {'password_reset_form': PasswordResetForm}),
    url('^accounts/', include('django.contrib.auth.urls')),

    url(r'^$', 'core.views.dashboard', name='dashboard'),

    url(r'^search/$', 'tags.views.search', name='search'),
    url(r'^tags/$', 'tags.views.tag_control', name='tag_control'),
    url(r'^tags/create/$', 'tags.views.create_tag', name='tag_create'),
    url(r'^tags/(\d+)/$', 'tags.views.tag', name='tag'),

    url(r'^annotate/$', 'tags.annotate_views.annotate', name='annotate'),
    url(r'^validate/$', 'tags.annotate_views.validate', name='validate'),
    url(r'^on_demand_validate/$', 'tags.annotate_views.on_demand_validate',
        name='on_demand_validate'),
    url(r'^on_demand_result/(\d+)/$', 'tags.annotate_views.on_demand_result',
        name='on_demand_result'),

    url(r'^annotations/$', 'tags.review_views.series_annotations',
        name='series_annotations'),
    url(r'^annotations/(\d+)/samples/$', 'tags.review_views.sample_annotations',
        name='sample_annotations'),

    url(r'^analysis/$', 'analysis.views.index', name='analysis'),
    url(r'^analysis/create/$', 'analysis.views.create', name='analysis_create'),
    url(r'^analysis/(\d+)/$', 'analysis.views.detail', name='analysis_results'),
    url(r'^analysis/(\d+)/export/$', 'analysis.views.export', name='analysis_export'),
    url(r'^analysis/(\d+)/log/$', 'analysis.views.log', name='analysis_log'),
    url(r'^analysis/(\d+)/rerun/$', 'analysis.views.rerun', name='analysis_rerun'),
    url(r'^analysis/(\d+)/delete/$', 'analysis.views.delete', name='analysis_delete'),

    url(r'^stats/$', 'tags.user_views.stats', name='stats'),
    url(r'^accounting/$', 'tags.user_views.accounting', name='accounting'),
    url(r'^account_info/$', 'tags.user_views.account_info', name='account_info'),
    url(r'^redeem/$', 'tags.user_views.redeem', name='redeem'),
    url(r'^pay/$', 'tags.user_views.pay', name='pay'),

    url(r'^admin/', include(admin.site.urls)),
)
