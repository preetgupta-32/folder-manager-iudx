"""
Enhanced API endpoints for file management system integration
Includes advanced processing capabilities from Flask reference
"""
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
import json
import os
import gzip
import hashlib
import mimetypes
import jwt
import pickle
import base64
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from .models import Folder, UploadedFile
from .forms import FolderForm, FileUploadForm

# ==================== UTILITY FUNCTIONS ====================

def get_file_processing_hash(filename):
    """Generate hash-based directory like Flask reference"""
    sec_filename = secure_filename(filename)
    m = hashlib.sha512()
    m.update(bytes(sec_filename, "utf-8"))
    return m.hexdigest()

def get_file_processing_info(file_obj):
    """Get file processing information"""
    if not file_obj.file:
        return {}
    
    filename = os.path.basename(file_obj.file.name)
    processing_hash = get_file_processing_hash(filename)
    processing_dir = os.path.join(settings.MEDIA_ROOT, processing_hash)
    chunks_dir = processing_dir
    inference_dir = os.path.join(processing_dir, "inference")
    config_file = os.path.join(processing_dir, "config.json")
    
    # Count chunks
    chunk_count = 0
    if os.path.exists(chunks_dir):
        chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.json.gz')]
        chunk_count = len(chunk_files)
    
    return {
        'processing_hash': processing_hash,
        'processing_dir': processing_dir,
        'has_chunks': chunk_count > 0,
        'has_inference': os.path.exists(inference_dir),
        'has_config': os.path.exists(config_file),
        'chunk_count': chunk_count,
        'status': 'processed' if chunk_count > 0 else 'raw'
    }

def initialize_file_processing(file_obj):
    """Initialize file processing directory structure"""
    processing_info = get_file_processing_info(file_obj)
    processing_dir = processing_info['processing_dir']
    
    # Create processing directory
    os.makedirs(processing_dir, exist_ok=True)
    os.makedirs(os.path.join(processing_dir, "inference"), exist_ok=True)
    
    # Update model fields
    file_obj.processing_hash = processing_info['processing_hash']
    file_obj.save()
    
    return processing_info

# ==================== EXISTING API ENDPOINTS ====================

@csrf_exempt
@require_http_methods(["GET"])
def api_folders_list(request):
    """List all folders with their metadata"""
    user_id = request.GET.get('user_id')
    folders = Folder.objects.all()
    
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
    """List all files with their metadata and processing status"""
    folder_id = request.GET.get('folder_id')
    user_id = request.GET.get('user_id')
    
    files = UploadedFile.objects.all()
    
    if folder_id:
        files = files.filter(folder_id=folder_id)
    if user_id:
        files = files.filter(uploaded_by_id=user_id)
    
    file_data = []
    for file in files:
        processing_info = get_file_processing_info(file)
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
            'description': file.description,
            # Enhanced with processing status
            'processing_hash': processing_info.get('processing_hash'),
            'has_chunks': processing_info.get('has_chunks', False),
            'has_inference': processing_info.get('has_inference', False),
            'has_config': processing_info.get('has_config', False),
            'processing_status': processing_info.get('status', 'raw'),
            'chunk_count': processing_info.get('chunk_count', 0)
        })
    
    return JsonResponse({'files': file_data})

@csrf_exempt
@require_http_methods(["POST"])
def api_create_folder(request):
    """Create a new folder via API"""
    try:
        data = json.loads(request.body)
        
        folder = Folder.objects.create(
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
    """Upload a file via API with processing initialization"""
    try:
        folder_id = request.POST.get('folder_id')
        user_id = request.POST.get('user_id')
        description = request.POST.get('description', '')
        is_public = request.POST.get('is_public', 'false').lower() == 'true'
        process_file = request.POST.get('process', 'false').lower() == 'true'
        
        if 'file' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'No file provided'})
        
        uploaded_file = request.FILES['file']
        
        # Validate file type if folder is specified
        if folder_id:
            folder = Folder.objects.get(id=folder_id)
            ext = uploaded_file.name.split('.')[-1].lower()
            if folder.allowed_type and ext != folder.allowed_type:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'File type .{ext} not allowed in this folder (allowed: .{folder.allowed_type})'
                })
        
        file_obj = UploadedFile.objects.create(
            file=uploaded_file,
            folder_id=folder_id,
            uploaded_by_id=user_id,
            description=description,
            is_public=is_public,
            original_name=uploaded_file.name
        )
        
        # Initialize processing if requested
        processing_info = {}
        if process_file:
            processing_info = initialize_file_processing(file_obj)
        
        return JsonResponse({
            'status': 'success',
            'file': {
                'id': file_obj.id,
                'name': file_obj.original_name,
                'size': file_obj.file_size,
                'url': file_obj.file.url,
                'processing_info': processing_info
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_file(request, file_id):
    """Delete a file via API with cleanup of processed data"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        
        # Clean up processing directory
        processing_info = get_file_processing_info(file_obj)
        if processing_info.get('processing_dir') and os.path.exists(processing_info['processing_dir']):
            shutil.rmtree(processing_info['processing_dir'])
        
        file_obj.delete()
        return JsonResponse({'status': 'success'})
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_folder(request, folder_id):
    """Delete a folder via API"""
    try:
        folder = Folder.objects.get(id=folder_id)
        folder.delete()
        return JsonResponse({'status': 'success'})
    except Folder.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Folder not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_user_stats(request, user_id):
    """Get user's enhanced file management statistics"""
    try:
        user = User.objects.get(id=user_id)
        
        folder_count = Folder.objects.filter(created_by=user).count()
        file_count = UploadedFile.objects.filter(uploaded_by=user).count()
        total_size = sum(f.file_size or 0 for f in UploadedFile.objects.filter(uploaded_by=user))
        
        # Enhanced stats with processing info
        processed_files = 0
        files_with_inference = 0
        files_with_config = 0
        total_chunks = 0
        
        for file in UploadedFile.objects.filter(uploaded_by=user):
            processing_info = get_file_processing_info(file)
            if processing_info.get('has_chunks'):
                processed_files += 1
                total_chunks += processing_info.get('chunk_count', 0)
            if processing_info.get('has_inference'):
                files_with_inference += 1
            if processing_info.get('has_config'):
                files_with_config += 1
        
        return JsonResponse({
            'user': user.username,
            'folders_created': folder_count,
            'files_uploaded': file_count,
            'files_processed': processed_files,
            'files_with_inference': files_with_inference,
            'files_with_config': files_with_config,
            'total_chunks': total_chunks,
            'total_storage_bytes': total_size,
            'total_storage_mb': round(total_size / (1024 * 1024), 2)
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'})

# ==================== ENHANCED API ENDPOINTS (Flask Reference Pattern) ====================

@csrf_exempt
@require_http_methods(["GET"])
def api_file_processing_status(request, file_id):
    """Get detailed processing status for a file"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        # Update model with current status
        file_obj.has_chunks = processing_info.get('has_chunks', False)
        file_obj.has_inference = processing_info.get('has_inference', False)
        file_obj.has_config = processing_info.get('has_config', False)
        file_obj.chunk_count = processing_info.get('chunk_count', 0)
        file_obj.processing_status = processing_info.get('status', 'raw')
        file_obj.processing_hash = processing_info.get('processing_hash')
        file_obj.save()
        
        return JsonResponse({
            'file_id': file_obj.id,
            'processing_hash': processing_info.get('processing_hash'),
            'status': processing_info.get('status'),
            'has_chunks': processing_info.get('has_chunks', False),
            'has_inference': processing_info.get('has_inference', False),
            'has_config': processing_info.get('has_config', False),
            'chunk_count': processing_info.get('chunk_count', 0),
            'processing_date': file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None
        })
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_file_chunks(request, file_id, chunk_number):
    """Get chunk data (Flask reference pattern)"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        if not processing_info.get('has_chunks'):
            return JsonResponse({'status': 'error', 'message': 'File not processed into chunks'})
        
        chunk_path = os.path.join(processing_info['processing_dir'], f"{chunk_number}.json.gz")
        
        if not os.path.exists(chunk_path):
            return JsonResponse({'status': 'error', 'message': 'Chunk not found'}, status=410)
        
        try:
            with gzip.open(chunk_path, "rb") as f:
                data = json.load(f)
                return JsonResponse({
                    'chunk_number': chunk_number,
                    'chunk_data': data,
                    'record_count': len(data) if isinstance(data, list) else 1
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error reading chunk: {str(e)}'})
            
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_file_inference(request, file_id):
    """Get inference results for a file"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        if not processing_info.get('has_inference'):
            return JsonResponse({'status': 'error', 'message': 'No inference available for this file'})
        
        inference_file = os.path.join(processing_info['processing_dir'], "inference", "inference.json")
        
        if not os.path.exists(inference_file):
            return JsonResponse({'status': 'error', 'message': 'Inference file not found'})
        
        try:
            with open(inference_file, 'r') as f:
                inference_data = json.load(f)
                return JsonResponse({
                    'file_id': file_id,
                    'inference': inference_data,
                    'generated_at': inference_data.get('timestamp', 'unknown')
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error reading inference: {str(e)}'})
            
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["POST"])
def api_upload_config(request, file_id):
    """Upload configuration file for processing"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        # Initialize processing if not already done
        if not os.path.exists(processing_info['processing_dir']):
            processing_info = initialize_file_processing(file_obj)
        
        config_path = os.path.join(processing_info['processing_dir'], "config.json")
        
        if 'file' in request.FILES:
            # Upload config file
            uploaded_config = request.FILES['file']
            with open(config_path, 'wb') as f:
                for chunk in uploaded_config.chunks():
                    f.write(chunk)
        else:
            # Upload config as JSON
            config_data = json.loads(request.body)
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        # Update model
        file_obj.has_config = True
        file_obj.config_added = True
        file_obj.save()
        
        return JsonResponse({'status': 'success', 'message': 'Config uploaded successfully'})
        
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@require_http_methods(["GET"])
def api_get_config(request, file_id):
    """Get configuration file for a file"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        config_path = os.path.join(processing_info['processing_dir'], "config.json")
        
        if not os.path.exists(config_path):
            return JsonResponse({'status': 'error', 'message': 'Config file not found'})
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return JsonResponse({
                    'file_id': file_id,
                    'config': config_data
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error reading config: {str(e)}'})
            
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_file_preview(request, file_id):
    """Preview file content (first 10 records like Flask reference)"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        # Try to get preview from processed chunks first
        if processing_info.get('has_chunks'):
            first_chunk_path = os.path.join(processing_info['processing_dir'], "1.json.gz")
            if os.path.exists(first_chunk_path):
                try:
                    with gzip.open(first_chunk_path, "rb") as f:
                        data = json.load(f)
                        preview_data = data[1:11] if isinstance(data, list) and len(data) > 1 else data[:10]
                        return JsonResponse({
                            'file_id': file_id,
                            'preview_type': 'processed',
                            'data': preview_data,
                            'total_records': len(data) if isinstance(data, list) else 1
                        })
                except Exception:
                    pass
        
        # Fallback to raw file preview
        if not file_obj.file:
            return JsonResponse({'status': 'error', 'message': 'File not found'})
        
        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            return JsonResponse({'status': 'error', 'message': 'File not accessible'})
        
        mimetype = mimetypes.guess_type(file_path)[0]
        
        if mimetype and (mimetype.startswith('text/') or mimetype == 'application/json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:5000]  # First 5KB
                    return JsonResponse({
                        'file_id': file_id,
                        'preview_type': 'text',
                        'content': content,
                        'mimetype': mimetype,
                        'file_size': os.path.getsize(file_path)
                    })
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Cannot read file: {str(e)}'})
        
        return JsonResponse({
            'file_id': file_id,
            'preview_type': 'binary',
            'message': 'Binary file preview not supported',
            'mimetype': mimetype,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        })
        
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_available_inferences(request, file_id):
    """Get list of available inference files with timestamps"""
    try:
        file_obj = UploadedFile.objects.get(id=file_id)
        processing_info = get_file_processing_info(file_obj)
        
        if not processing_info.get('has_inference'):
            return JsonResponse({'inferences': []})
        
        inference_dir = os.path.join(processing_info['processing_dir'], "inference")
        
        if not os.path.exists(inference_dir):
            return JsonResponse({'inferences': []})
        
        inference_files = []
        for filename in os.listdir(inference_dir):
            if filename.startswith('conf_and_inf_') and filename.endswith('.json'):
                file_path = os.path.join(inference_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        inference_files.append({
                            'filename': filename,
                            'timestamp': data.get('timestamp'),
                            'has_config': 'config' in data,
                            'has_inference': 'inference' in data,
                            'file_size': os.path.getsize(file_path)
                        })
                except Exception:
                    continue
        
        # Sort by timestamp (newest first)
        inference_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return JsonResponse({
            'file_id': file_id,
            'inferences': inference_files,
            'count': len(inference_files)
        })
        
    except UploadedFile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'File not found'})

@csrf_exempt
@require_http_methods(["GET"])
def api_folder_contents(request, folder_id):
    """Get detailed folder contents with processing status"""
    try:
        folder = Folder.objects.get(id=folder_id)
        
        files_data = []
        for file in folder.files.all():
            processing_info = get_file_processing_info(file)
            files_data.append({
                'id': file.id,
                'name': os.path.basename(file.file.name) if file.file else file.original_name,
                'original_name': file.original_name,
                'size': file.file_size,
                'uploaded_at': file.uploaded_at.isoformat() if file.uploaded_at else None,
                'uploaded_by': file.uploaded_by.username if file.uploaded_by else None,
                'description': file.description,
                'is_public': file.is_public,
                'processed': processing_info.get('has_chunks', False),
                'has_inference': processing_info.get('has_inference', False),
                'has_config': processing_info.get('has_config', False),
                'processing_status': processing_info.get('status', 'raw'),
                'chunk_count': processing_info.get('chunk_count', 0)
            })
        
        # Get subfolders
        subfolders_data = []
        for subfolder in folder.subfolders.all():
            subfolders_data.append({
                'id': subfolder.id,
                'name': subfolder.name,
                'allowed_type': subfolder.allowed_type,
                'file_count': subfolder.files.count(),
                'description': subfolder.description,
                'is_public': subfolder.is_public
            })
        
        return JsonResponse({
            'folder': {
                'id': folder.id,
                'name': folder.name,
                'allowed_type': folder.allowed_type,
                'description': folder.description,
                'is_public': folder.is_public,
                'created_at': folder.created_at.isoformat() if folder.created_at else None
            },
            'files': files_data,
            'subfolders': subfolders_data,
            'total_files': len(files_data),
            'total_subfolders': len(subfolders_data)
        })
        
    except Folder.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Folder not found'})
