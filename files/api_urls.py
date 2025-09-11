from django.urls import path

from .api import (
    # Existing endpoints
    api_folders_list, api_files_list, api_create_folder,
    api_upload_file, api_delete_file, api_delete_folder, api_user_stats,
    
    # Only include API endpoints that exist in api.py
    api_file_processing_status, api_file_chunks, api_file_inference,
    api_upload_config, api_file_preview, api_available_inferences,
    api_folder_contents
)

# API endpoints for integration
api_urlpatterns = [
    # Basic listing endpoints
    path('api/folders/', api_folders_list, name='api_folders_list'),
    path('api/files/', api_files_list, name='api_files_list'),
    path('api/user/<int:user_id>/stats/', api_user_stats, name='api_user_stats'),
    
    # CRUD operations
    path('api/folders/create/', api_create_folder, name='api_create_folder'),
    path('api/files/upload/', api_upload_file, name='api_upload_file'),
    path('api/files/<int:file_id>/delete/', api_delete_file, name='api_delete_file'),
    path('api/folders/<int:folder_id>/delete/', api_delete_folder, name='api_delete_folder'),
    
    # Enhanced processing endpoints
    path('api/files/<int:file_id>/processing-status/', api_file_processing_status, name='api_file_processing_status'),
    path('api/files/<int:file_id>/chunks/<int:chunk_number>/', api_file_chunks, name='api_file_chunks'),
    path('api/files/<int:file_id>/inference/', api_file_inference, name='api_file_inference'),
    path('api/files/<int:file_id>/config/', api_upload_config, name='api_upload_config'),
    path('api/files/<int:file_id>/preview/', api_file_preview, name='api_file_preview'),
    path('api/files/<int:file_id>/inferences/', api_available_inferences, name='api_available_inferences'),
    path('api/folders/<int:folder_id>/contents/', api_folder_contents, name='api_folder_contents'),
]
