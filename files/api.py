"""
API endpoints for file management system integration
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
import os
from .models import Folder, UploadedFile
from .forms import FolderForm, FileUploadForm


@csrf_exempt
@require_http_methods(["GET"])
def api_folders_list(request):
    """List all folders with their metadata"""
    user_id = request.GET.get('user_id')
    folders = Folder.objects.all()  # type: ignore
    
    if user_id:
        folders = folders.filter(created_by_id=user_id)
    
    folder_data = []
    for folder in folders:
        folder_data.append({
            'id': folder.id,
            'name': folder.name,
            'allowed_type': folder.allowed_type,
            'created_by': folder.created_by.username if folder.created_by else None,
            'created_at': folder.created_at.isoformat() if folder.created_at else None,
            'file_count': folder.files.count(),
            'is_public': folder.is_public,
            'description': folder.description,
            'parent_id': folder.parent_id
        })
    
    return JsonResponse({'folders': folder_data})


@csrf_exempt
@require_http_methods(["GET"])
def api_files_list(request):
    """List all files with their metadata"""
    folder_id = request.GET.get('folder_id')
    user_id = request.GET.get('user_id')
    
    files = UploadedFile.objects.all()  # type: ignore
    
    if folder_id:
        files = files.filter(folder_id=folder_id)
    if user_id:
        files = files.filter(uploaded_by_id=user_id)
    
    file_data = []
    for file in files:
        file_data.append({
            'id': file.id,
            'original_name': file.original_name,
            'file_path': file.file.url if file.file else None,
            'file_size': file.file_size,
            'uploaded_by': file.uploaded_by.username if file.uploaded_by else None,
            'uploaded_at': file.uploaded_at.isoformat() if file.uploaded_at else None,
            'folder_id': file.folder_id,
            'folder_name': file.folder.name if file.folder else None,
            'is_public': file.is_public,
            'description': file.description
        })
    
    return JsonResponse({'files': file_data})


@csrf_exempt
@require_http_methods(["POST"])
def api_create_folder(request):
    """Create a new folder via API"""
    try:
        data = json.loads(request.body)
        
        folder = Folder.objects.create(  # type: ignore
            name=data['name'],
            allowed_type=data.get('allowed_type', 'csv'),
            parent_id=data.get('parent_id'),
            created_by_id=data.get('user_id'),
            description=data.get('description', ''),
            is_public=data.get('is_public', False)
        )
        
        return JsonResponse({
            'status': 'success',
            'folder': {
                'id': folder.id,
                'name': folder.name,
                'allowed_type': folder.allowed_type
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def api_upload_file(request):
    """Upload a file via API"""
    try:
        folder_id = request.POST.get('folder_id')
        user_id = request.POST.get('user_id')
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public', 'false').lower() == 'true'
        
        if 'file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'No file provided'})
        
        uploaded_file = request.FILES['file']
        
        # Validate file type if folder is specified
        if folder_id:
            folder = Folder.objects.get(id=folder_id)  # type: ignore
            ext = uploaded_file.name.split('.')[-1].lower()
            if folder.allowed_type and ext != folder.allowed_type:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'File type .{ext} not allowed in this folder (allowed: .{folder.allowed_type})'
                })
        
        file_obj = UploadedFile.objects.create(  # type: ignore
            file=uploaded_file,
            folder_id=folder_id,
            uploaded_by_id=user_id,
            description=description,
            is_public=is_public,
            original_name=uploaded_file.name
        )
        
        return JsonResponse({
            'status': 'success',
            'file': {
                'id': file_obj.id,
                'name': file_obj.original_name,
                'size': file_obj.file_size,
                'url': file_obj.file.url
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_file(request, file_id):
    """Delete a file via API"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)  # type: ignore
        file_obj.delete()
        return JsonResponse({'status': 'success'})
    except UploadedFile.DoesNotExist:  # type: ignore
        return JsonResponse({'status': 'error', 'message': 'File not found'})


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_folder(request, folder_id):
    """Delete a folder via API"""
    try:
        folder = Folder.objects.get(id=folder_id)  # type: ignore
        folder.delete()
        return JsonResponse({'status': 'success'})
    except Folder.DoesNotExist:  # type: ignore
        return JsonResponse({'status': 'error', 'message': 'Folder not found'})


@csrf_exempt
@require_http_methods(["GET"])
def api_user_stats(request, user_id):
    """Get user's file management statistics"""
    try:
        user = User.objects.get(id=user_id)  # type: ignore
        
        folder_count = Folder.objects.filter(created_by=user).count()  # type: ignore
        file_count = UploadedFile.objects.filter(uploaded_by=user).count()  # type: ignore
        total_size = sum(f.file_size or 0 for f in UploadedFile.objects.filter(uploaded_by=user))  # type: ignore
        
        return JsonResponse({
            'user': user.username,
            'folders_created': folder_count,
            'files_uploaded': file_count,
            'total_storage_bytes': total_size,
            'total_storage_mb': round(total_size / (1024 * 1024), 2)
        })
    except User.DoesNotExist:  # type: ignore
        return JsonResponse({'status': 'error', 'message': 'User not found'}) 