# type: ignore
import json, zipfile, os
from io import BytesIO
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Folder, UploadedFile
from .forms import FolderForm, FileUploadForm
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models


@login_required
def upload_page(request):
    # Filter folders based on user permissions
    if request.user.is_staff or request.user.is_superuser:
        # Admin sees all folders
        folders = Folder.objects.filter(parent=None).prefetch_related('subfolders', 'files')  # type: ignore
    else:
        # Regular users see their own folders AND public folders
        folders = Folder.objects.filter(
            parent=None
        ).filter(
            models.Q(created_by=request.user) | models.Q(is_public=True)
        ).prefetch_related('subfolders', 'files')  # type: ignore
    
    file_form = FileUploadForm(user=request.user)
    folder_form = FolderForm(user=request.user)
    message = None

    if request.method == 'POST':
        print(f"DEBUG: POST request received to upload_page")
        print(f"DEBUG: POST keys: {list(request.POST.keys())}")
        print(f"DEBUG: Files: {list(request.FILES.keys())}")
        print(f"DEBUG: create_folder value = '{request.POST.get('create_folder')}'")
        print(f"DEBUG: file in FILES = {request.FILES.get('file')}")
        print(f"DEBUG: folder_upload in FILES = {request.FILES.getlist('folder_upload')}")
        
        # If folder_upload is present and has files, handle folder upload only
        if request.FILES.getlist('folder_upload'):
            files = request.FILES.getlist('folder_upload')
            # Try to extract the top-level folder name from the first file's relative path
            first_file = files[0]
            rel_path = first_file.name
            top_folder_name = rel_path.split('/')[0] if '/' in rel_path else rel_path
            # Get the allowed type from the form
            allowed_type = request.POST.get('folder_allowed_type', 'csv')
            # Check if a root folder with this name exists
            folder_obj, created = Folder.objects.get_or_create(
                name=top_folder_name, 
                parent=None,
                defaults={'created_by': request.user}
            )  # type: ignore
            # Always update allowed_type to the selected value
            folder_obj.allowed_type = allowed_type
            if created:
                folder_obj.created_by = request.user
            folder_obj.save()
            for f in files:
                ext = f.name.split('.')[-1].lower()
                if allowed_type and ext != allowed_type:
                    continue  # skip files with wrong extension
                # Remove the top folder from the file name for storage
                f.name = '/'.join(f.name.split('/')[1:]) if '/' in f.name else f.name
                UploadedFile.objects.create(
                    file=f, 
                    folder=folder_obj,
                    uploaded_by=request.user
                )  # type: ignore
            return redirect('upload_page')
        # If a file is uploaded (and not a folder), handle single file upload
        elif request.FILES.get('file'):
            file_form = FileUploadForm(request.POST, request.FILES, user=request.user)
            if file_form.is_valid():
                f = file_form.save(commit=False)
                allowed = f.folder.allowed_type if f.folder else None
                ext = f.file.name.split('.')[-1].lower()
                if allowed and ext != allowed:
                    message = f"Cannot upload .{ext} to folder '{f.folder.name}' (allowed: .{allowed})"
                else:
                    f.uploaded_by = request.user
                    f.save()
                    return redirect('upload_page')
        # If folder form is submitted for creating a new folder
        elif request.POST.get('create_folder'):
            print(f"DEBUG: =================== FOLDER FORM SUBMISSION ===================")
            print(f"DEBUG: Raw POST data: {dict(request.POST)}")
            print(f"DEBUG: create_folder value: {request.POST.get('create_folder')}")
            
            folder_form = FolderForm(request.POST, user=request.user)
            print(f"DEBUG: Form is valid: {folder_form.is_valid()}")
            
            if folder_form.is_valid():
                print(f"DEBUG: Form validation passed, saving folder...")
                folder = folder_form.save(commit=False)
                folder.created_by = request.user
                folder.save()
                print(f"DEBUG: SUCCESS - Folder created: {folder.name} (ID: {folder.id})")
                messages.success(request, f"Folder '{folder.name}' created successfully!")
                return redirect('upload_page')
            else:
                print(f"DEBUG: VALIDATION FAILED - Form errors: {folder_form.errors}")
                for field, errors in folder_form.errors.items():
                    print(f"DEBUG:   - {field}: {errors}")
                message = f"Folder creation failed: {folder_form.errors}"

    return render(request, 'upload.html', {
        'folders': folders,
        'file_form': file_form,
        'folder_form': folder_form,
        'message': message
    })


@csrf_exempt
@login_required
def move_file(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_id = data.get('file_id')
        folder_id = data.get('folder_id')

        try:
            file = UploadedFile.objects.get(id=file_id)  # type: ignore
            folder = Folder.objects.get(id=folder_id)  # type: ignore
            # Check permissions: user can move their own files to their own folders OR public folders
            if not (request.user.is_staff or request.user.is_superuser):
                if file.uploaded_by != request.user:
                    return JsonResponse({'status': 'error', 'message': 'You can only move your own files'})
                if not (folder.created_by == request.user or folder.is_public):
                    return JsonResponse({'status': 'error', 'message': 'You can only move files to your own folders or public folders'})
            # Only allow move if file extension matches folder.allowed_type
            ext = file.file.name.split('.')[-1].lower()
            if folder.allowed_type and ext != folder.allowed_type:
                return JsonResponse({'status': 'error', 'message': f'Cannot move .{ext} file to folder (allowed: .{folder.allowed_type})'})
            file.folder = folder
            file.save()
            return JsonResponse({'status': 'success'})
        except (UploadedFile.DoesNotExist, Folder.DoesNotExist):  # type: ignore
            return JsonResponse({'status': 'error', 'message': 'File or folder not found'})


@csrf_exempt
@login_required
def rename_folder(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        folder_id = data.get('folder_id')
        new_name = data.get('name')

        try:
            folder = Folder.objects.get(id=folder_id)  # type: ignore
            # Check permissions: user can only rename their own folders
            if not (request.user.is_staff or request.user.is_superuser or folder.created_by == request.user):
                return JsonResponse({'status': 'error', 'message': 'Permission denied'})
            folder.name = new_name
            folder.save()
            return JsonResponse({'status': 'success'})
        except Folder.DoesNotExist:  # type: ignore
            return JsonResponse({'status': 'error', 'message': 'Folder not found'})


@csrf_exempt
@login_required
def delete_folder(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        folder_id = data.get('folder_id')

        try:
            folder = Folder.objects.get(id=folder_id)  # type: ignore
            # Check permissions: user can only delete their own folders
            if not (request.user.is_staff or request.user.is_superuser or folder.created_by == request.user):
                return JsonResponse({'status': 'error', 'message': 'Permission denied'})
            
            # First delete all physical files in this folder
            for file_obj in folder.files.all():
                if file_obj.file and os.path.exists(file_obj.file.path):
                    os.remove(file_obj.file.path)
                    print(f"DEBUG: Deleted physical file: {file_obj.file.path}")
            
            # Delete the folder (this will cascade delete all file records)
            folder.delete()
            return JsonResponse({'status': 'success'})
        except Folder.DoesNotExist:  # type: ignore
            return JsonResponse({'status': 'error', 'message': 'Folder not found'})


@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id)  # type: ignore
    # Check permissions
    if not file_obj.is_accessible_by(request.user):
        messages.error(request, "You don't have permission to access this file.")
        return redirect('upload_page')
    file_path = file_obj.file.path
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response


@login_required
def download_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    # Check permissions
    if not folder.is_accessible_by(request.user):
        messages.error(request, "You don't have permission to access this folder.")
        return redirect('upload_page')
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        for uf in folder.files.all():
            zf.write(uf.file.path, arcname=os.path.basename(uf.file.name))
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{folder.name}.zip"'
    return response
# views.py
@csrf_exempt
@login_required
def delete_file(request):
    if request.method=='POST':
        data = json.loads(request.body)
        file_id = data.get('file_id')
        
        # Get the file object before deleting to access the file path
        try:
            file_obj = UploadedFile.objects.get(id=file_id)
            # Check if user has permission to delete this file
            if not (request.user.is_staff or request.user.is_superuser or file_obj.uploaded_by == request.user):
                return JsonResponse({'status':'error', 'message': 'Permission denied'})
            # Delete the physical file from storage
            if file_obj.file and os.path.exists(file_obj.file.path):
                os.remove(file_obj.file.path)
                print(f"DEBUG: Deleted physical file: {file_obj.file.path}")
            # Now delete the database record
            file_obj.delete()
            return JsonResponse({'status':'ok'})
        except UploadedFile.DoesNotExist:
            return JsonResponse({'status':'error', 'message': 'File not found'})

@csrf_exempt
@login_required
def copy_file(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_id = data.get('file_id')
        folder_id = data.get('folder_id')
        try:
            file = UploadedFile.objects.get(id=file_id)
            folder = Folder.objects.get(id=folder_id)
            # Check permissions: user can copy their own files to their own folders OR public folders
            if not (request.user.is_staff or request.user.is_superuser):
                if file.uploaded_by != request.user:
                    return JsonResponse({'status': 'error', 'message': 'You can only copy your own files'})
                if not (folder.created_by == request.user or folder.is_public):
                    return JsonResponse({'status': 'error', 'message': 'You can only copy files to your own folders or public folders'})
            ext = file.file.name.split('.')[-1].lower()
            if folder.allowed_type and ext != folder.allowed_type:
                return JsonResponse({'status': 'error', 'message': f'Cannot copy .{ext} file to folder (allowed: .{folder.allowed_type})'})
            new_file = UploadedFile.objects.get(id=file.id)
            new_file.pk = None
            new_file.folder = folder
            new_file.uploaded_by = request.user  # Set the current user as uploader of the copy
            new_file.file.name = f"copies/{os.path.basename(file.file.name)}"
            new_file.save()
            return JsonResponse({'status': 'success'})
        except (UploadedFile.DoesNotExist, Folder.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'File or folder not found'})


@csrf_exempt
def delete_multiple_files(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
        
        # Get all file objects and delete physical files first
        files_to_delete = UploadedFile.objects.filter(id__in=file_ids)
        for file_obj in files_to_delete:
            if file_obj.file and os.path.exists(file_obj.file.path):
                os.remove(file_obj.file.path)
                print(f"DEBUG: Deleted physical file: {file_obj.file.path}")
        
        # Now delete the database records
        files_to_delete.delete()
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def move_multiple_files(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
        folder_id = data.get('folder_id')
        try:
            folder = Folder.objects.get(id=folder_id)
            files = UploadedFile.objects.filter(id__in=file_ids)
            for file in files:
                ext = file.file.name.split('.')[-1].lower()
                if folder.allowed_type and ext != folder.allowed_type:
                    continue  # skip files with wrong extension
                file.folder = folder
                file.save()
            return JsonResponse({'status': 'success'})
        except Folder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Folder not found'})

@csrf_exempt
def copy_multiple_files(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
        folder_id = data.get('folder_id')
        try:
            folder = Folder.objects.get(id=folder_id)
            files = UploadedFile.objects.filter(id__in=file_ids)
            for file in files:
                ext = file.file.name.split('.')[-1].lower()
                if folder.allowed_type and ext != folder.allowed_type:
                    continue  # skip files with wrong extension
                new_file = UploadedFile.objects.get(id=file.id)
                new_file.pk = None
                new_file.folder = folder
                new_file.file.name = f"copies/{os.path.basename(file.file.name)}"
                new_file.save()
            return JsonResponse({'status': 'success'})
        except Folder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Folder not found'})


def folder_detail(request, folder_id):
    folder = Folder.objects.prefetch_related('files').get(id=folder_id)
    html = render_to_string('folder_detail_panel.html', {'folder': folder})
    return HttpResponse(html)


def folder_list_json(request):
    folders = Folder.objects.all().values('id', 'name')
    return JsonResponse(list(folders), safe=False)


@csrf_exempt
def upload_to_folder(request, folder_id):
    if request.method == 'POST':
        folder = Folder.objects.get(id=folder_id)
        files = request.FILES.getlist('files')
        for f in files:
            ext = f.name.split('.')[-1].lower()
            if folder.allowed_type and ext != folder.allowed_type:
                continue  # skip files with wrong extension
            UploadedFile.objects.create(file=f, folder=folder)
        return HttpResponse('OK')
