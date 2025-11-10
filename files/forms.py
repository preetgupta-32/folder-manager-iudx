from django import forms
from .models import UploadedFile, Folder

class FileUploadForm(forms.ModelForm):
    process_file = forms.BooleanField(
        required=False, 
        initial=False,
        help_text="Process file into chunks for analysis"
    )
    
    class Meta:
        model = UploadedFile
        fields = ['file', 'folder', 'description']  # Removed is_public

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 3})
        self.fields['description'].required = False
        
        # Filter folders to show user's own folders and public folders (or all for admin)
        if user:
            if user.is_staff or user.is_superuser:
                self.fields['folder'].queryset = Folder.objects.all()
            else:
                from django.db import models
                self.fields['folder'].queryset = Folder.objects.filter(
                    models.Q(created_by=user) | models.Q(is_public=True)
                )

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent', 'allowed_type', 'is_public']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Make allowed_type not required and set default
        self.fields['allowed_type'].required = False
        self.fields['allowed_type'].initial = 'csv'
        
        # Add help text and styling for is_public field
        self.fields['is_public'].help_text = "Check this to make the folder visible to all users"
        self.fields['is_public'].label = "Make Public"
        
        # Filter parent folders to show user's own folders and public folders (or all for admin)
        if user:
            if user.is_staff or user.is_superuser:
                self.fields['parent'].queryset = Folder.objects.all()
            else:
                from django.db import models
                self.fields['parent'].queryset = Folder.objects.filter(
                    models.Q(created_by=user) | models.Q(is_public=True)
                )

class ConfigUploadForm(forms.Form):
    config_file = forms.FileField(
        required=False,
        help_text="Upload configuration JSON file"
    )
    config_data = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10}),
        required=False,
        help_text="Or paste JSON configuration directly"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        config_file = cleaned_data.get('config_file')
        config_data = cleaned_data.get('config_data')
        
        if not config_file and not config_data:
            raise forms.ValidationError("Please provide either a config file or config data")
        
        return cleaned_data
