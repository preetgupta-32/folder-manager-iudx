from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from files.models import Folder, UploadedFile

class Command(BaseCommand):
    help = 'Assigns folders and files without owners to a specified user or creates a default user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username to assign orphan files/folders to (default: admin)'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            # Try to get the user
            user = User.objects.get(username=username)
            self.stdout.write(f"Using existing user: {username}")
        except User.DoesNotExist:
            # If user doesn't exist, use the first superuser or admin user
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            
            if not user:
                self.stdout.write(self.style.ERROR("No users found. Please create a user first."))
                return
            
            self.stdout.write(f"Using user: {user.username}")
        
        # Find orphan folders
        orphan_folders = Folder.objects.filter(created_by__isnull=True)
        folder_count = orphan_folders.count()
        
        if folder_count > 0:
            orphan_folders.update(created_by=user)
            self.stdout.write(self.style.SUCCESS(f"✓ Assigned {folder_count} orphan folders to {user.username}"))
        else:
            self.stdout.write("No orphan folders found.")
        
        # Find orphan files
        orphan_files = UploadedFile.objects.filter(uploaded_by__isnull=True)
        file_count = orphan_files.count()
        
        if file_count > 0:
            orphan_files.update(uploaded_by=user)
            self.stdout.write(self.style.SUCCESS(f"✓ Assigned {file_count} orphan files to {user.username}"))
        else:
            self.stdout.write("No orphan files found.")
        
        # Report summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  Total folders assigned: {folder_count}")
        self.stdout.write(f"  Total files assigned: {file_count}")
        self.stdout.write(f"  Assigned to user: {user.username}")
        
        if user.is_superuser:
            self.stdout.write(f"  User type: Superuser (Admin)")
        elif user.is_staff:
            self.stdout.write(f"  User type: Staff")
        else:
            self.stdout.write(f"  User type: Regular User")
        
        self.stdout.write("="*50)