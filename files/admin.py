from django.contrib import admin
from django.contrib.auth.models import User
from .models import Folder, UploadedFile
from django.utils.html import format_html
from django.utils.safestring import mark_safe

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'allowed_type', 'file_count', 'is_public', 'created_at']
    list_filter = ['allowed_type', 'is_public', 'created_at', 'created_by']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = 'Files'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admins can see all folders
        if request.user.is_superuser:
            return qs
        # Staff can see all folders but with limited editing
        return qs
    
    def has_change_permission(self, request, obj=None):
        # Superusers can change any folder
        if request.user.is_superuser:
            return True
        # Staff can only change their own folders
        if obj and request.user.is_staff:
            return obj.created_by == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        # Similar logic for delete permissions
        if request.user.is_superuser:
            return True
        if obj and request.user.is_staff:
            return obj.created_by == request.user
        return super().has_delete_permission(request, obj)

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'uploaded_by', 'folder', 'file_size_formatted', 'processing_status', 'is_public', 'uploaded_at']
    list_filter = ['processing_status', 'is_public', 'uploaded_at', 'uploaded_by', 'folder']
    search_fields = ['original_name', 'uploaded_by__username', 'folder__name', 'description']
    readonly_fields = ['uploaded_at', 'file_size', 'processing_hash', 'file_link']
    ordering = ['-uploaded_at']
    
    def file_size_formatted(self, obj):
        if obj.file_size:
            size = obj.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"
        return "N/A"
    file_size_formatted.short_description = 'Size'
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download File</a>', obj.file.url)
        return "No file"
    file_link.short_description = 'File'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Admins can see all files
        if request.user.is_superuser:
            return qs
        # Staff can see all files but with limited editing
        return qs
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and request.user.is_staff:
            return obj.uploaded_by == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and request.user.is_staff:
            return obj.uploaded_by == request.user
        return super().has_delete_permission(request, obj)
    
    actions = ['make_public', 'make_private', 'process_files']
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f"{queryset.count()} files made public.")
    make_public.short_description = "Make selected files public"
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f"{queryset.count()} files made private.")
    make_private.short_description = "Make selected files private"
    
    def process_files(self, request, queryset):
        for file in queryset:
            file.update_processing_status()
        self.message_user(request, f"{queryset.count()} files processing status updated.")
    process_files.short_description = "Update processing status"

# Customize the admin site header and title
admin.site.site_header = "File Manager Admin"
admin.site.site_title = "File Manager Admin Portal"
admin.site.index_title = "Welcome to File Manager Administration"
