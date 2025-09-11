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
        fields = ['file', 'folder', 'description', 'is_public']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 3})
        self.fields['description'].required = False

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent', 'allowed_type', 'description', 'is_public']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 3})
        self.fields['description'].required = False

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
