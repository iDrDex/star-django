from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class MyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_competent',)}),
    )
    list_display = UserAdmin.list_display + ('is_competent',)


admin.site.register(User, MyUserAdmin)
