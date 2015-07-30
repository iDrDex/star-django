from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',  # noqa
    url(r'^$', 'core.views.dashboard', name='dashboard'),

    url(r'^search/$', 'tags.views.search', name='search'),
    url(r'^annotate/$', 'tags.views.annotate', name='annotate'),
    url(r'^validate/$', 'tags.views.validate', name='validate'),
    url(r'^on_demand_validate/$', 'tags.views.on_demand_validate', name='on_demand_validate'),
    url(r'^on_demand_result/(\d+)/$', 'tags.views.on_demand_result', name='on_demand_result'),

    url(r'^stats/$', 'tags.user_views.stats', name='stats'),
    url(r'^accounting/$', 'tags.user_views.accounting', name='accounting'),
    url(r'^account_info/$', 'tags.user_views.account_info', name='account_info'),
    url(r'^redeem/$', 'tags.user_views.redeem', name='redeem'),
    url(r'^pay/$', 'tags.user_views.pay', name='pay'),

    url(r'^admin/', include(admin.site.urls)),
)
