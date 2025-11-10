"""
Titan Server Storage Backend
Handles file storage on remote Titan server via SFTP
"""
import os
import io
import logging
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri
from django.core.files import File

logger = logging.getLogger(__name__)

@deconstructible
class TitanStorage(Storage):
    """
    Custom storage backend for Titan server
    Uses SFTP for file transfer when Titan server is accessible
    Falls back to local storage when Titan is not available
    """
    
    def __init__(self):
        self.titan_config = getattr(settings, 'TITAN_SERVER', {})
        self.use_titan = getattr(settings, 'USE_TITAN_STORAGE', False)
        self.local_root = settings.MEDIA_ROOT
        self.sftp_client = None
        self.ssh_client = None
        
    def _get_sftp_client(self):
        """
        Get or create SFTP client for Titan server connection
        """
        if not self.use_titan:
            return None
            
        if self.sftp_client is not None:
            return self.sftp_client
            
        try:
            import paramiko
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.titan_config.get('HOST'),
                port=self.titan_config.get('PORT', 22),
                username=self.titan_config.get('USERNAME'),
                password=self.titan_config.get('PASSWORD', ''),
                timeout=30
            )
            
            self.sftp_client = self.ssh_client.open_sftp()
            
            # Create base directory if it doesn't exist
            base_path = self.titan_config.get('BASE_PATH', '/storage/file-manager/')
            try:
                self.sftp_client.stat(base_path)
            except FileNotFoundError:
                self._makedirs_sftp(base_path)
                
            logger.info(f"Connected to Titan server at {self.titan_config.get('HOST')}")
            return self.sftp_client
            
        except Exception as e:
            logger.error(f"Failed to connect to Titan server: {e}")
            self.use_titan = False  # Fallback to local storage
            return None
    
    def _makedirs_sftp(self, path):
        """
        Create directories recursively on SFTP server
        """
        if not self.sftp_client:
            return
            
        dirs = []
        while path != '/':
            dirs.append(path)
            path = os.path.dirname(path)
        
        for d in reversed(dirs):
            try:
                self.sftp_client.stat(d)
            except FileNotFoundError:
                self.sftp_client.mkdir(d)
    
    def _get_titan_path(self, name):
        """
        Get full path on Titan server
        """
        base_path = self.titan_config.get('BASE_PATH', '/storage/file-manager/')
        return os.path.join(base_path, name)
    
    def _get_local_path(self, name):
        """
        Get local file path (fallback)
        """
        return os.path.join(self.local_root, name)
    
    def _save(self, name, content):
        """
        Save file to Titan server or local storage
        """
        sftp = self._get_sftp_client()
        
        if sftp:
            # Save to Titan server
            titan_path = self._get_titan_path(name)
            titan_dir = os.path.dirname(titan_path)
            
            try:
                # Ensure directory exists
                self._makedirs_sftp(titan_dir)
                
                # Upload file
                with sftp.open(titan_path, 'wb') as remote_file:
                    for chunk in content.chunks():
                        remote_file.write(chunk)
                
                logger.info(f"File saved to Titan server: {titan_path}")
                return name
                
            except Exception as e:
                logger.error(f"Failed to save to Titan, falling back to local: {e}")
                # Fall through to local save
        
        # Fallback to local storage
        local_path = self._get_local_path(name)
        local_dir = os.path.dirname(local_path)
        
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
        
        with open(local_path, 'wb') as local_file:
            for chunk in content.chunks():
                local_file.write(chunk)
        
        logger.info(f"File saved locally: {local_path}")
        return name
    
    def _open(self, name, mode='rb'):
        """
        Open file from Titan server or local storage
        """
        sftp = self._get_sftp_client()
        
        if sftp:
            titan_path = self._get_titan_path(name)
            try:
                # Download from Titan server
                remote_file = sftp.open(titan_path, mode)
                # Read content into memory (for small files)
                # For large files, consider implementing streaming
                content = remote_file.read()
                remote_file.close()
                return ContentFile(content, name=name)
                
            except Exception as e:
                logger.error(f"Failed to open from Titan, trying local: {e}")
                # Fall through to local open
        
        # Fallback to local storage
        local_path = self._get_local_path(name)
        return File(open(local_path, mode))
    
    def delete(self, name):
        """
        Delete file from Titan server and/or local storage
        """
        deleted = False
        
        sftp = self._get_sftp_client()
        if sftp:
            titan_path = self._get_titan_path(name)
            try:
                sftp.remove(titan_path)
                logger.info(f"File deleted from Titan server: {titan_path}")
                deleted = True
            except Exception as e:
                logger.error(f"Failed to delete from Titan: {e}")
        
        # Also try to delete from local storage
        local_path = self._get_local_path(name)
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"File deleted locally: {local_path}")
            deleted = True
        
        return deleted
    
    def exists(self, name):
        """
        Check if file exists on Titan server or local storage
        """
        sftp = self._get_sftp_client()
        
        if sftp:
            titan_path = self._get_titan_path(name)
            try:
                sftp.stat(titan_path)
                return True
            except FileNotFoundError:
                pass
        
        # Check local storage
        local_path = self._get_local_path(name)
        return os.path.exists(local_path)
    
    def size(self, name):
        """
        Get file size from Titan server or local storage
        """
        sftp = self._get_sftp_client()
        
        if sftp:
            titan_path = self._get_titan_path(name)
            try:
                stat = sftp.stat(titan_path)
                return stat.st_size
            except Exception as e:
                logger.error(f"Failed to get size from Titan: {e}")
        
        # Fallback to local storage
        local_path = self._get_local_path(name)
        if os.path.exists(local_path):
            return os.path.getsize(local_path)
        return 0
    
    def url(self, name):
        """
        Return URL for accessing the file
        Since Titan server might not be web-accessible, 
        we'll use local media URLs
        """
        return filepath_to_uri(name)
    
    def listdir(self, path):
        """
        List directory contents from Titan server or local storage
        """
        dirs = []
        files = []
        
        sftp = self._get_sftp_client()
        
        if sftp:
            titan_path = self._get_titan_path(path)
            try:
                for item in sftp.listdir_attr(titan_path):
                    if item.st_mode & 0o40000:  # Is directory
                        dirs.append(item.filename)
                    else:
                        files.append(item.filename)
                return dirs, files
            except Exception as e:
                logger.error(f"Failed to list from Titan: {e}")
        
        # Fallback to local storage
        local_path = self._get_local_path(path)
        if os.path.exists(local_path):
            for item in os.listdir(local_path):
                item_path = os.path.join(local_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
        
        return dirs, files
    
    def get_created_time(self, name):
        """
        Get file creation time
        """
        # Not easily available via SFTP, use modification time
        return self.get_modified_time(name)
    
    def get_modified_time(self, name):
        """
        Get file modification time
        """
        from datetime import datetime
        
        sftp = self._get_sftp_client()
        
        if sftp:
            titan_path = self._get_titan_path(name)
            try:
                stat = sftp.stat(titan_path)
                return datetime.fromtimestamp(stat.st_mtime)
            except Exception as e:
                logger.error(f"Failed to get mtime from Titan: {e}")
        
        # Fallback to local storage
        local_path = self._get_local_path(name)
        if os.path.exists(local_path):
            return datetime.fromtimestamp(os.path.getmtime(local_path))
        
        return None
    
    def close(self):
        """
        Close SFTP and SSH connections
        """
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

# Function to get the appropriate storage backend
def get_storage_backend():
    """
    Returns TitanStorage if configured to use Titan server,
    otherwise returns default storage
    """
    if getattr(settings, 'USE_TITAN_STORAGE', False):
        return TitanStorage()
    else:
        from django.core.files.storage import default_storage
        return default_storage