from django.contrib import admin
from django.utils.html import format_html
from .models import DataFile

# Personnalisation de l'interface d'administration
admin.site.site_header = "Data Processing Admin"
admin.site.site_title = "Data Admin"
admin.site.index_title = "Bienvenue dans le tableau de bord"

@admin.register(DataFile)
class DataFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'file_type', 'upload_date', 'processed', 'status_badge')
    list_filter = ('processed', 'file_type', 'upload_date', 'user')
    search_fields = ('original_filename', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('upload_date', 'row_count', 'column_count', 'processing_summary')
    ordering = ('-upload_date',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'file', 'original_filename', 'upload_date')
        }),
        ('Type de fichier', {
            'fields': ('original_file_type', 'file_type')
        }),
        ('Statistiques', {
            'fields': ('row_count', 'column_count')
        }),
        ('Traitement', {
            'fields': ('processed', 'missing_values', 'outliers', 'processing_summary')
        })
    )
    
    def status_badge(self, obj):
        if obj.processed:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 10px;">Traité</span>')
        return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 10px;">Non traité</span>')
    
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'processed'
