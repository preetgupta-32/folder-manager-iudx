# File Manager with Authentication and Titan Server Support

## Features

- **User Authentication**: Login, registration, and user profiles
- **Admin Panel**: Admins can access all files and folders
- **User Privacy**: Users can only access their own files (unless marked public)
- **Titan Server Storage**: Ready for remote storage on titan@192.168.1.250
- **File Organization**: Folder-based file management with type restrictions

## Setup Instructions

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install django djangorestframework django-cors-headers werkzeug cryptography pyjwt paramiko
```

### 2. Database Setup

Since we're adding authentication, you'll need to handle existing data carefully:

#### Option A: Fresh Database (Recommended for new setup)
```bash
# Remove old database
rm db.sqlite3

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

#### Option B: Keep Existing Data
```bash
# First, create a default user for existing data
python manage.py shell
```
```python
from django.contrib.auth.models import User
from files.models import Folder, UploadedFile

# Create a default user for existing files
default_user = User.objects.create_user(username='legacy_user', password='change_this_password')

# Assign existing folders to default user
Folder.objects.filter(created_by__isnull=True).update(created_by=default_user)

# Assign existing files to default user
UploadedFile.objects.filter(uploaded_by__isnull=True).update(uploaded_by=default_user)
```

Then run migrations:
```bash
python manage.py migrate
```

### 3. Create User Accounts

#### Create Admin Account
```bash
python manage.py createsuperuser
# Follow prompts to set username and password
```

#### Create Regular Users
- Navigate to http://localhost:8000/register/ to create user accounts
- Or use the admin panel at http://localhost:8000/admin/

### 4. Configure Titan Server (When Available)

Edit `temp_site/settings.py` when you have access to the Titan server:

```python
TITAN_SERVER = {
    'HOST': '192.168.1.250',
    'USERNAME': 'titan',
    'PASSWORD': 'your_password_here',  # Add the password when provided
    'BASE_PATH': '/storage/file-manager/',
    'USE_SFTP': True,
    'PORT': 22,
}

# Enable Titan storage
USE_TITAN_STORAGE = True  # Change to True when Titan is accessible
```

### 5. Run the Server

```bash
python manage.py runserver
# Access at http://localhost:8000/
```

## Usage

### For Regular Users
1. Register at `/register/` or login at `/login/`
2. Upload files and create folders at `/`
3. View profile and stats at `/profile/`
4. Files are private by default (only you can see them)

### For Admins
1. Login with superuser credentials
2. Access admin panel at `/admin/`
3. Can view and manage ALL files and folders
4. Can make files/folders public or private
5. Can manage user accounts

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Get API token
- `POST /api/auth/register/` - Register via API

### Files & Folders
All endpoints now require authentication:
- `GET /api/folders/` - List folders (filtered by user)
- `POST /api/folders/create/` - Create folder
- `GET /api/files/` - List files (filtered by user)
- `POST /api/files/upload/` - Upload file

Example with authentication:
```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in requests
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://localhost:8000/api/folders/
```

## Titan Server Integration

The system is prepared for Titan server storage at `titan@192.168.1.250`:

- **Current Status**: Using local storage (Titan not accessible)
- **When Ready**: Set `USE_TITAN_STORAGE = True` in settings
- **Automatic Fallback**: If Titan fails, files are stored locally
- **Dual Storage**: Files can exist both locally and on Titan

### Required for Titan Setup:
1. SSH access credentials
2. Network connectivity to 192.168.1.250
3. Write permissions on Titan server
4. Install `paramiko` for SFTP support

## Troubleshooting

### Migration Issues
If you encounter migration errors with required fields:
1. Delete the database: `rm db.sqlite3`
2. Remove migration files: `rm files/migrations/0*.py`
3. Recreate migrations: `python manage.py makemigrations`
4. Apply migrations: `python manage.py migrate`

### Permission Denied Errors
- Ensure you're logged in
- Check if the file/folder belongs to you
- Admins can access everything

### Titan Connection Issues
- Check network connectivity: `ping 192.168.1.250`
- Verify SSH credentials
- Check `USE_TITAN_STORAGE` setting
- Review logs for connection errors

## Security Notes

- All files are private by default
- Users can only access their own files
- Admins have full access
- API requires authentication tokens
- Passwords are hashed using Django's security
- CSRF protection on web forms

## Next Steps

1. Get Titan server credentials from your mentor
2. Test Titan connectivity
3. Enable Titan storage in settings
4. Consider adding email verification
5. Implement file sharing between users
6. Add file preview capabilities