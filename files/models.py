from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    allowed_type = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('json', 'JSON')],
        default='csv'
    )
    # Integration fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_folders')
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)  # For sharing permissions  # type: ignore

    def __str__(self):
        return self.name

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    # Integration fields
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # Size in bytes
    original_name = models.CharField(max_length=255, blank=True)  # Original filename
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)  # For sharing permissions  # type: ignore
    config_added = models.BooleanField(default=False)  # type: ignore

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, 'size'):  # type: ignore
            self.file_size = self.file.size  # type: ignore
            if not self.original_name:
                self.original_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or self.file.name
