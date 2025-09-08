from django import forms
from .models import UploadedFile, Folder

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file', 'folder']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent', 'allowed_type']
