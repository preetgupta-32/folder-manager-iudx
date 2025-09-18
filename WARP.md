# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview
This is a Django-based file management system with advanced processing capabilities. The system provides both web interface and REST API for file and folder management, with support for file chunking, processing, and inference features.

## Development Commands

### Project Setup
```bash
# Activate virtual environment (if exists)
source venv/bin/activate

# Install dependencies (no requirements.txt found, install manually if needed)
python3 -m pip install django werkzeug cryptography PyJWT

# Run migrations
python3 manage.py migrate

# Create superuser (if needed)
python3 manage.py createsuperuser

# Start development server
python3 manage.py runserver

# Start development server on different port (for API service mode)
python3 manage.py runserver 8001
```

### Database Operations
```bash
# Create new migrations after model changes
python3 manage.py makemigrations files

# Apply migrations
python3 manage.py migrate

# Reset database (careful - this deletes all data)
rm db.sqlite3
python3 manage.py migrate

# Export data for backup/integration
python3 manage.py dumpdata files > files_backup.json

# Load data from backup
python3 manage.py loaddata files_backup.json
```

### Testing
```bash
# Run all tests
python3 manage.py test

# Run tests for files app only
python3 manage.py test files

# Run specific test class or method
python3 manage.py test files.tests.TestModelName
```

### Development Tools
```bash
# Django shell for debugging
python3 manage.py shell

# Check for common issues
python3 manage.py check

# Collect static files (for production)
python3 manage.py collectstatic
```

## Architecture Overview

### Core Components
- **Django Project**: `temp_site/` - Main project configuration
- **Files App**: `files/` - Primary application handling file management
- **Models**: Folder and UploadedFile with advanced processing capabilities
- **Dual Interface**: Web UI + REST API for maximum flexibility

### Key Models
- **Folder**: Hierarchical folder structure with file type restrictions and user ownership
- **UploadedFile**: File storage with processing metadata, chunking, and inference tracking

### Processing System
The system implements a Flask-reference pattern for advanced file processing:
- **Hash-based directories**: Files get SHA-512 hash-based processing directories
- **Chunking**: Large files can be split into JSON chunks for processing
- **Inference**: ML/AI inference results storage
- **Configuration**: Processing config files for each uploaded file

### API Architecture
- **REST endpoints**: `/api/` prefix for all API calls
- **Web interface**: Direct URLs for browser-based file management
- **User integration**: Supports both authenticated and user-ID based access
- **File type validation**: Folder-level restrictions on allowed file types

## File Structure
```
temp_site/
├── temp_site/          # Django project settings
│   ├── settings.py     # Main configuration
│   ├── urls.py         # Root URL routing
│   └── wsgi.py         # WSGI configuration
├── files/              # Main application
│   ├── models.py       # Folder and UploadedFile models
│   ├── views.py        # Web interface views
│   ├── api.py          # REST API endpoints
│   ├── urls.py         # Web interface URLs
│   ├── api_urls.py     # API URLs
│   ├── forms.py        # Django forms
│   └── templates/      # HTML templates
├── media/              # File uploads storage
└── manage.py           # Django management script
```

## Integration Patterns

### API Integration (Microservice)
Run as separate service on port 8001:
```bash
python3 manage.py runserver 8001
```
Use API endpoints for integration with other frameworks (React, Vue, Laravel).

### Django App Integration
Copy `files/` app to existing Django project and include in `INSTALLED_APPS`.

### Database Integration
Export data with `dumpdata`, adapt models to match existing user system.

## Key API Endpoints
- `GET /api/folders/` - List folders with metadata
- `GET /api/files/` - List files with processing status
- `POST /api/folders/create/` - Create new folder
- `POST /api/files/upload/` - Upload file with processing options
- `GET /api/files/{id}/processing-status/` - Check processing status
- `GET /api/files/{id}/chunks/{num}/` - Access processed chunks
- `DELETE /api/files/{id}/delete/` - Delete file and cleanup

## Processing Features
- **File chunking**: Automatic splitting of large files into processable chunks
- **Inference storage**: ML/AI model results storage per file
- **Configuration management**: Processing parameters stored per file
- **Status tracking**: Raw → Processing → Processed → Error states
- **Hash-based organization**: Files organized by SHA-512 hash for efficient processing

## Security Considerations
- File type validation based on folder restrictions
- User ownership tracking for folders and files
- Public/private file visibility controls
- File size limits configurable in settings
- Processing directory isolation per file

## Development Notes
- Uses SQLite for development (configurable for production)
- Media files stored in `media/uploads/` with folder-based organization
- Processing files stored in hash-based directories under `media/`
- Supports both form-based and API-based file uploads
- Template system uses Bootstrap-style components