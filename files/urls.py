from django.urls import path, include
from .views import (
    upload_page, move_file, rename_folder, delete_folder, delete_file, copy_file,
    download_file, download_folder, delete_multiple_files, move_multiple_files, 
    copy_multiple_files, folder_detail, folder_list_json, upload_to_folder
)
from .api_urls import api_urlpatterns

urlpatterns = [
    # Web interface URLs
    path('', upload_page, name='upload_page'),
    path('move-file/', move_file),
    path('rename-folder/', rename_folder),
    path('delete-folder/', delete_folder),
    path('delete-file/', delete_file, name='delete_file'),
    path('copy-file/', copy_file, name='copy_file'),
    path('download/file/<int:file_id>/', download_file, name='download_file'),
    path('download-folder/<int:folder_id>/', download_folder, name='download_folder'),
    path('delete-multiple-files/', delete_multiple_files, name='delete_multiple_files'),
    path('move-multiple-files/', move_multiple_files, name='move_multiple_files'),
    path('copy-multiple-files/', copy_multiple_files, name='copy_multiple_files'),
    path('folder-detail/<int:folder_id>/', folder_detail, name='folder_detail'),
    path('folder-list-json/', folder_list_json, name='folder_list_json'),
    path('upload-to-folder/<int:folder_id>/', upload_to_folder, name='upload_to_folder'),
] + api_urlpatterns  # Include API endpoints
