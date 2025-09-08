from django.urls import path
from .api import (
    api_folders_list, api_files_list, api_create_folder, 
    api_upload_file, api_delete_file, api_delete_folder, api_user_stats
)

# API endpoints for integration
api_urlpatterns = [
    # Listing endpoints
    path('api/folders/', api_folders_list, name='api_folders_list'),
    path('api/files/', api_files_list, name='api_files_list'),
    path('api/user/<int:user_id>/stats/', api_user_stats, name='api_user_stats'),
    
    # CRUD operations
    path('api/folders/create/', api_create_folder, name='api_create_folder'),
    path('api/files/upload/', api_upload_file, name='api_upload_file'),
    path('api/files/<int:file_id>/delete/', api_delete_file, name='api_delete_file'),
    path('api/folders/<int:folder_id>/delete/', api_delete_folder, name='api_delete_folder'),
] 