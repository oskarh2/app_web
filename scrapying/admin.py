from django.contrib import admin
from .models import PageTracking

@admin.register(PageTracking)
class PageTrackingAdmin(admin.ModelAdmin):
    list_display = ['page', 'tracking_id', 'type', 'kind', 'status', 'user_id', 'created_at']
    list_filter = ['status', 'type', 'kind', 'created_at']
    search_fields = ['page', 'tracking_id', 'user_id']
    readonly_fields = ['tracking_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Información Principal', {
            'fields': ('page', 'type', 'kind', 'status')
        }),
        ('Datos Adicionales', {
            'fields': ('steps', 'metadata', 'user_id')
        }),
        ('Auditoría', {
            'fields': ('tracking_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )