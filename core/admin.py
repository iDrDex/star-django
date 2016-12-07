from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StatisticCache


class MyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_competent',)}),
    )
    list_display = UserAdmin.list_display + ('is_competent',)


class StatisticCacheAdmin(admin.ModelAdmin):
    readonly_fields = ('slug', 'count',)
    list_display = ('slug', 'count',)


admin.site.register(User, MyUserAdmin)
admin.site.register(StatisticCache, StatisticCacheAdmin)
