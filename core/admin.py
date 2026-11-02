from django.contrib import admin
from .models import SiteSetting, SystemErrorLog


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_phone', 'contact_email', 'updated_at')


@admin.register(SystemErrorLog)
class SystemErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'error_type', 'method', 'path', 'user', 'ip_address', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'error_type', 'method', 'created_at')
    search_fields = ('error_type', 'message', 'path', 'ip_address')
    readonly_fields = ('created_at', 'updated_at', 'traceback')
