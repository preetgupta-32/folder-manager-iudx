# Folder Manager IUDX - File Management System with Authentication

A comprehensive Django-based web application for managing folders and files with user authentication, permissions, and optional Titan server storage integration.

---

## 🌟 Features

### Core Features
- **User Authentication**: Login, registration, and user profiles
- **Admin Panel**: Admins can access and manage all files and folders
- **User Privacy**: Users can only access their own files (unless marked public)
- **Public Folders**: Share folders with all users
- **File Organization**: Folder-based file management with type restrictions
- **REST API**: Full API support for programmatic access
- **Titan Server Storage**: Ready for remote storage integration

### Security Features
- All files are private by default
- Users can only access their own files
- Admins have full access
- API requires authentication tokens
- Passwords are hashed using Django's security
- CSRF protection on web forms

---

## 📋 Requirements

- Python 3.10+
- pip (Python package manager)
- Git
- (macOS) Xcode Command Line Tools (for building some packages)
- (optional) Homebrew for installing dependencies like Rust

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/preetgupta-32/folder-manager-iudx.git
cd folder-manager-iudx
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# .\venv\Scripts\Activate.ps1   # Windows PowerShell
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install django djangorestframework django-cors-headers werkzeug cryptography pyjwt paramiko
```

### 4. Database Setup

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
# Run migrations
python manage.py migrate

# Use management command to assign orphan data
python manage.py assign_orphan_data
```

### 5. Run the Server

```bash
python manage.py runserver
# Access at http://localhost:8000/
```

---

## 📁 Project Structure

```
folder-manager-iudx/
├── files/                 # Main app with models, views, APIs
│   ├── models.py          # Folder and File models
│   ├── views.py           # Template-based views
│   ├── api.py             # REST API views (return JSON)
│   ├── auth_views.py      # Authentication views
│   ├── titan_storage.py   # Titan server integration
│   ├── urls.py            # URLs for views
│   ├── api_urls.py        # URLs for API endpoints
│   ├── templates/         # HTML templates
│   │   ├── base.html      # Base template with navbar
│   │   ├── upload.html    # Main dashboard
│   │   └── auth/          # Login, register, profile pages
│   └── static/            # CSS, JS files
├── temp_site/             # Django project settings & URLs
├── manage.py              # Django entry point
└── ...
```

---

## 💻 Usage

### For Regular Users
1. Register at `/register/` or login at `/login/`
2. Upload files and create folders at `/dashboard/`
3. View profile and stats at `/profile/`
4. Create public folders to share with other users
5. Files are private by default (only you can see them)

### For Admins
1. Login with superuser credentials
2. Access admin panel at `/admin/`
3. Can view and manage ALL files and folders
4. Can manage user accounts
5. See ADMIN badge in navbar

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login/` - Get API token
- `POST /api/auth/register/` - Register via API

### Files & Folders
All endpoints require authentication:
- `GET /api/folders/` - List folders (filtered by user)
- `POST /api/folders/create/` - Create folder
- `GET /api/files/` - List files (filtered by user)
- `POST /api/files/upload/` - Upload file
- `DELETE /api/files/<id>/delete/` - Delete file
- `GET /api/files/<id>/processing-status/` - Check processing status

### Example API Usage

```bash
# Login and get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in requests
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://localhost:8000/api/folders/
```

### JavaScript Example

```javascript
fetch('/api/folders/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrftoken,
    'Authorization': `Token ${token}`
  },
  body: JSON.stringify({ 
    name: "New Folder", 
    parent: 1, 
    allowed_type: "csv",
    is_public: false
  })
})
.then(res => res.json())
.then(data => console.log("Created folder:", data));
```

---

## 🖥️ Titan Server Integration

The system is prepared for Titan server storage at `titan@192.168.1.250`:

### Configuration

Edit `temp_site/settings.py`:

```python
TITAN_SERVER = {
    'HOST': '192.168.1.250',
    'USERNAME': 'titan',
    'PASSWORD': 'your_password_here',
    'BASE_PATH': '/storage/file-manager/',
    'USE_SFTP': True,
    'PORT': 22,
}

# Enable Titan storage
USE_TITAN_STORAGE = True  # Change to True when Titan is accessible
```

### Features
- **Current Status**: Using local storage (Titan not accessible)
- **When Ready**: Set `USE_TITAN_STORAGE = True` in settings
- **Automatic Fallback**: If Titan fails, files are stored locally
- **Dual Storage**: Files can exist both locally and on Titan

### Required for Titan Setup:
1. SSH access credentials
2. Network connectivity to 192.168.1.250
3. Write permissions on Titan server
4. Install `paramiko` for SFTP support

---

## 🔧 Troubleshooting

### Migration Issues
```bash
# Delete database and start fresh
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Permission Denied Errors
- Ensure you're logged in
- Check if the file/folder belongs to you
- Admins can access everything

### Titan Connection Issues
```bash
# Check network connectivity
ping 192.168.1.250

# Verify SSH access
ssh titan@192.168.1.250
```

### Cryptography Build Errors (macOS)
```bash
xcode-select --install
brew install rust
pip install cryptography
```

### Static File 404
```bash
python manage.py collectstatic
```

---

## 🌍 Environment Variables

Set via `.env` file or shell export:

```bash
export DJANGO_SECRET_KEY="your_dev_secret"
export DEBUG=True
export TITAN_HOST="192.168.1.250"
export TITAN_USERNAME="titan"
export TITAN_PASSWORD="your_password"
export USE_TITAN_STORAGE=False
```

---

## 📝 Development Notes

- Do **not** commit your virtual environment (`venv/`) to Git
- Add sensitive values (`.env`, keys, database passwords) to `.gitignore`
- Use `pip freeze > requirements.txt` to record dependencies
- The development server is **not** for production
- For deployment, use WSGI/ASGI with Gunicorn behind Nginx

---

## 📄 License

This project inherits the license of the IUDX ecosystem. Please check the upstream repository for licensing terms.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add feature"`
4. Push branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📚 Additional Documentation

- **WARP.md** - Development guide for WARP terminal
- **IMPLEMENTATION_SUMMARY.md** - Detailed implementation notes
- **INTEGRATION_GUIDE.md** - API integration guide

---

## 🎯 Quick Start Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install django djangorestframework django-cors-headers werkzeug cryptography pyjwt
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver

# Access
# Main: http://127.0.0.1:8000/
# Admin: http://127.0.0.1:8000/admin/
# API: http://127.0.0.1:8000/api/
```

---

**Repository**: https://github.com/preetgupta-32/folder-manager-iudx  
**Upstream**: https://github.com/datakaveri/dp-enclave-res-server
