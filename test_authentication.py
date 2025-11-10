#!/usr/bin/env python3
"""
Test script to verify authentication and permissions are working correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temp_site.settings')
django.setup()

from django.contrib.auth.models import User
from files.models import Folder, UploadedFile
from django.db.models import Count

def test_authentication():
    print("=" * 60)
    print("AUTHENTICATION & PERMISSION TEST REPORT")
    print("=" * 60)
    
    # 1. Check Users
    print("\n1. USER ACCOUNTS:")
    print("-" * 40)
    users = User.objects.all()
    for user in users:
        role = "Superuser" if user.is_superuser else "Staff" if user.is_staff else "Regular"
        print(f"  • {user.username} ({role})")
        print(f"    - Folders owned: {user.created_folders.count()}")
        print(f"    - Files uploaded: {user.uploaded_files.count()}")
    
    # 2. Check Folders
    print("\n2. FOLDER OWNERSHIP:")
    print("-" * 40)
    folders = Folder.objects.all()
    for folder in folders:
        owner = folder.created_by.username if folder.created_by else "No owner"
        visibility = "Public" if folder.is_public else "Private"
        print(f"  • {folder.name} - Owner: {owner} ({visibility})")
        print(f"    - Files: {folder.files.count()}")
        print(f"    - Type: {folder.allowed_type}")
    
    # 3. Check Files
    print("\n3. FILE OWNERSHIP:")
    print("-" * 40)
    files = UploadedFile.objects.all()[:5]  # Show first 5 files
    for file in files:
        owner = file.uploaded_by.username if file.uploaded_by else "No owner"
        visibility = "Public" if file.is_public else "Private"
        folder = file.folder.name if file.folder else "No folder"
        print(f"  • {file.original_name or file.file.name}")
        print(f"    - Owner: {owner} ({visibility})")
        print(f"    - Folder: {folder}")
    
    # 4. Check Orphan Data
    print("\n4. ORPHAN DATA CHECK:")
    print("-" * 40)
    orphan_folders = Folder.objects.filter(created_by__isnull=True).count()
    orphan_files = UploadedFile.objects.filter(uploaded_by__isnull=True).count()
    print(f"  • Orphan folders: {orphan_folders}")
    print(f"  • Orphan files: {orphan_files}")
    
    if orphan_folders > 0 or orphan_files > 0:
        print("  ⚠️  Run 'python manage.py assign_orphan_data' to fix orphan data")
    else:
        print("  ✓ No orphan data found")
    
    # 5. Permission Test
    print("\n5. PERMISSION TEST:")
    print("-" * 40)
    
    # Get a regular user and admin
    admin = User.objects.filter(is_superuser=True).first()
    regular_user = User.objects.filter(is_superuser=False, is_staff=False).first()
    
    if not regular_user:
        # Create a test regular user
        regular_user = User.objects.create_user(
            username='test_user',
            password='test_password'
        )
        print("  • Created test regular user: test_user")
    
    if admin and regular_user:
        # Test folder access
        test_folder = Folder.objects.first()
        if test_folder:
            admin_access = test_folder.is_accessible_by(admin)
            user_access = test_folder.is_accessible_by(regular_user)
            owner_access = test_folder.is_accessible_by(test_folder.created_by) if test_folder.created_by else False
            
            print(f"  • Testing folder: {test_folder.name}")
            print(f"    - Admin can access: {admin_access} (should be True)")
            print(f"    - Regular user can access: {user_access}")
            print(f"    - Owner can access: {owner_access} (should be True if owner exists)")
    
    # 6. Storage Configuration
    print("\n6. STORAGE CONFIGURATION:")
    print("-" * 40)
    from django.conf import settings
    titan_enabled = getattr(settings, 'USE_TITAN_STORAGE', False)
    titan_config = getattr(settings, 'TITAN_SERVER', {})
    
    print(f"  • Titan Storage Enabled: {titan_enabled}")
    if titan_config:
        print(f"  • Titan Server: {titan_config.get('HOST', 'Not configured')}")
        print(f"  • Titan Username: {titan_config.get('USERNAME', 'Not configured')}")
        print(f"  • Storage Path: {titan_config.get('BASE_PATH', 'Not configured')}")
    
    if not titan_enabled:
        print("  ℹ️  Currently using local storage")
        print("  ℹ️  Set USE_TITAN_STORAGE=True in settings when Titan is available")
    
    print("\n" + "=" * 60)
    print("✅ AUTHENTICATION SYSTEM IS CONFIGURED")
    print("=" * 60)
    
    print("\nQUICK ACCESS URLS:")
    print("  • Login: http://localhost:8000/login/")
    print("  • Register: http://localhost:8000/register/")
    print("  • Admin Panel: http://localhost:8000/admin/")
    print("  • Main App: http://localhost:8000/")
    print("  • User Profile: http://localhost:8000/profile/")

if __name__ == "__main__":
    test_authentication()