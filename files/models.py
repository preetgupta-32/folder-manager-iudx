from django.db import models
from django.contrib.auth.models import User
import os
import hashlib
from django.conf import settings
from werkzeug.utils import secure_filename

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    allowed_type = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('json', 'JSON'), ('parquet', 'PARQUET')],
        default='csv'
    )

    # Integration fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_folders')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    
    # Integration fields
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    original_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    config_added = models.BooleanField(default=False)
    
    # Enhanced processing fields (Flask reference pattern)
    processing_hash = models.CharField(max_length=128, blank=True, null=True)
    has_chunks = models.BooleanField(default=False)
    has_inference = models.BooleanField(default=False)
    has_config = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('raw', 'Raw'),
            ('processing', 'Processing'),
            ('processed', 'Processed'),
            ('error', 'Error')
        ],
        default='raw'
    )
    chunk_count = models.IntegerField(default=0)

    def get_processing_hash(self):
        """Generate hash-based directory like Flask reference"""
        if not self.processing_hash and self.file:
            filename = os.path.basename(self.file.name)
            sec_filename = secure_filename(filename)
            m = hashlib.sha512()
            m.update(bytes(sec_filename, "utf-8"))
            self.processing_hash = m.hexdigest()
            self.save()
        return self.processing_hash

    def get_processing_dir(self):
        """Get processing directory path"""
        if self.get_processing_hash():
            return os.path.join(settings.MEDIA_ROOT, self.processing_hash)
        return None

    def update_processing_status(self):
        """Update processing status based on directory contents"""
        processing_dir = self.get_processing_dir()
        if processing_dir and os.path.exists(processing_dir):
            # Check for chunks
            chunk_files = [f for f in os.listdir(processing_dir) if f.endswith('.json.gz')]
            self.has_chunks = len(chunk_files) > 0
            self.chunk_count = len(chunk_files)
            
            # Check for inference
            inference_dir = os.path.join(processing_dir, "inference")
            self.has_inference = os.path.exists(inference_dir)
            
            # Check for config
            config_file = os.path.join(processing_dir, "config.json")
            self.has_config = os.path.exists(config_file)
            self.config_added = self.has_config
            
            # Update status
            if self.has_chunks:
                self.processing_status = 'processed'
            else:
                self.processing_status = 'raw'
            
            self.save()

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        if not self.original_name and self.file:
            self.original_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or str(self.file.name) if self.file else f"File {self.id}"
