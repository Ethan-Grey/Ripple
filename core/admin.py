from django.contrib import admin
from .models import Report, UserWarning

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reporter', 'get_reported_content', 'reason', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status', 'reason', 'created_at', 'action_taken']
    search_fields = ['reporter__username', 'description', 'admin_notes']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'content_type', 'object_id', 'reason', 'description')
        }),
        ('Review Status', {
            'fields': ('status', 'action_taken', 'admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_reported_content(self, obj):
        return obj.get_reported_object_display()
    get_reported_content.short_description = 'Reported Content'
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete reports
        return request.user.is_superuser


@admin.register(UserWarning)
class UserWarningAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reason', 'issued_by', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'reason', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Warning Information', {
            'fields': ('user', 'issued_by', 'related_report', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete warnings
        return request.user.is_superuser