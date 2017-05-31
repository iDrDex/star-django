import re

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.options import csrf_protect_m
from django.db import models, transaction
from django.shortcuts import render

from .models import Series


def platforms_list(obj):
    return ', '.join(obj.platforms)
platforms_list.short_description = 'Platforms'


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('pk', 'gse_name', platforms_list, 'samples_count')
    list_display_links = ('pk', 'gse_name')

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }

    def get_urls(self):
        from django.conf.urls import url

        info = self.model._meta.app_label, self.model._meta.model_name

        urls = super(SeriesAdmin, self).get_urls()
        my_urls = [
            url(r'^bulk/$', self.admin_site.admin_view(self.bulk_add), name='%s_%s_bulk' % info),
        ]
        return my_urls + urls

    @csrf_protect_m
    def bulk_add(self, request):
        if request.method == 'POST':
            gse_list = re.findall(r'GSE\d+', request.POST.get('gse_name', ''), re.I)
            gse_list = [s.upper() for s in gse_list]
            gses = set(gse_list)
            # Check for dups
            dups = len(gse_list) - len(gses)
            if dups:
                self.message_user(request, 'Skipped %d duplicate GSE(s)' % dups, messages.WARNING)

            with transaction.atomic():
                # Skip existing
                exist = Series.objects.filter(gse_name__in=gses).values_list('gse_name', flat=True)
                if exist:
                    self.message_user(request, 'Skipped %d known GSE(s)' % len(exist),
                                      messages.WARNING)
                    gses.difference_update(exist)

                # Create dummy series to be updated later
                if gses:
                    Series.objects.bulk_create(
                        Series(gse_name=name) for name in gses
                    )
                    self.message_user(request, 'Created %d new GSE(s)' % len(gses),
                                      messages.SUCCESS)
                else:
                    self.message_user(request, 'No new GSEs were created', messages.ERROR)

            return self.response_post_save_add(request, None)

        opts = self.model._meta
        context = dict(
            self.admin_site.each_context(request),
            opts=opts,
            title='Bulk add %s' % opts.verbose_name_plural,
        )
        return render(request, 'admin/legacy/series/bulk_add.html', context)
