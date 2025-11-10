# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Django-based file management system with folder organization, file upload capabilities, and REST API endpoints. The system is designed to integrate with external Flask enclaves for secure file processing.

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux

# Install Django and dependencies (no requirements.txt found, so manual install)
pip install django djangorestframework django-cors-headers werkzeug cryptography pyjwt
```

### Database Operations
```bash
# Run initial migrations
python manage.py makemigrations files
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Reset database (careful - deletes all data)
rm db.sqlite3
python manage.py migrate
```

### Development Server
```bash
# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8001

# Access the application
# Main UI: http://localhost:8000/
# Admin: http://localhost:8000/admin/
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test files

# Run with verbose output
python manage.py test --verbosity=2
```

### Shell & Data Manipulation
```bash
# Django interactive shell
python manage.py shell

# Django shell with auto-imports
python manage.py shell_plus  # requires django-extensions

# Database shell
python manage.py dbshell
```

## High-Level Architecture

### Core Components

**1. Django Application Structure**
- **temp_site/**: Main Django project configuration
  - `settings.py`: Configuration including file upload limits, encryption settings, JWT settings, and Flask enclave integration
  - `urls.py`: Root URL routing
  
- **files/**: Main application module handling file management
  - `models.py`: Core data models (Folder, UploadedFile) with processing capabilities
  - `views.py`: Web interface views for file/folder operations
  - `api.py`: REST API endpoints for programmatic access
  - `forms.py`: Django forms for validation
  - `api_urls.py`: API URL configuration

**2. Data Flow Architecture**

The system follows a dual-path architecture:

```
User Request
    ├── Web Interface (HTML/Forms)
    │   └── views.py → templates → JavaScript
    └── REST API (JSON)
        └── api.py → JSON responses
```

**3. File Processing Pipeline**

Files undergo hash-based processing with this flow:
1. File upload → Generate SHA512 hash from filename
2. Create processing directory: `media/{hash}/`
3. Store chunks as compressed JSON: `{hash}/chunk_{n}.json.gz`
4. Store inference results: `{hash}/inference/`
5. Store configuration: `{hash}/config.json`

**4. Storage Architecture**
- **Media Files**: `media/uploads/` - Physical file storage
- **Processing**: `media/{hash}/` - Hash-based processing directories
- **Database**: SQLite by default, tracks metadata and relationships
- **Temp Cache**: `tmp/file_cache/` - File processing cache

### Key Design Patterns

**1. Folder Type Enforcement**
Each folder has an `allowed_type` field that restricts file uploads to specific extensions (csv, pdf, json, parquet). This is enforced at multiple levels:
- Form validation during upload
- API validation
- Move/copy operations

**2. Public by Default**
Both files and folders have `is_public=True` by default, making content accessible without authentication. This can be changed per deployment needs.

**3. Processing State Management**
Files track their processing state through multiple boolean flags:
- `has_chunks`: File has been chunked for processing
- `has_inference`: Inference results available
- `has_config`: Configuration uploaded
- `processing_status`: Overall status (raw/processing/processed/error)

**4. User Context Tracking**
While authentication is not enforced, the system tracks:
- `created_by`: User who created folder
- `uploaded_by`: User who uploaded file
- Timestamps for audit trails

### Integration Points

**1. Flask Enclave Integration**
Settings configured for secure processing enclave:
- `FLASK_ENCLAVE_URL`: External processing service
- JWT validation for secure communication
- Encryption support (Fernet, RSA)

**2. API Endpoints for External Systems**
- `/api/folders/` - Folder management
- `/api/files/` - File operations
- `/api/files/{id}/processing-status/` - Check processing
- `/api/files/{id}/chunks/{n}/` - Retrieve processed chunks

**3. Database Models Extensibility**
Models include integration fields ready for:
- Multi-tenant systems (user_id tracking)
- Hierarchical folder structures (parent relationships)
- File processing workflows (status tracking)

### Security Considerations

**1. CSRF Protection**
- Web endpoints use Django CSRF tokens
- API endpoints are CSRF-exempt for integration

**2. File Validation**
- Extension checking against folder allowed_type
- Secure filename sanitization using werkzeug
- File size limits enforced in settings

**3. Processing Isolation**
- Hash-based directories prevent path traversal
- Each file gets unique processing space
- Cleanup on file deletion

## API Testing Examples

```bash
# List all folders
curl http://localhost:8000/api/folders/

# Create a folder
curl -X POST http://localhost:8000/api/folders/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Folder", "allowed_type": "csv"}'

# Upload a file
curl -X POST http://localhost:8000/api/files/upload/ \
  -F "file=@test.csv" \
  -F "folder_id=1"

# Check processing status
curl http://localhost:8000/api/files/1/processing-status/
```

## Important Configuration

**File Upload Limits** (in settings.py):
- `FILE_UPLOAD_MAX_MEMORY_SIZE`: 10MB
- `DATA_UPLOAD_MAX_MEMORY_SIZE`: 50MB
- `MAX_FILE_SIZE`: 4GB (for processing)

**Allowed File Types**:
- CSV, Parquet, JSON, TXT, PDF, JPG, PNG, DOCX

**Processing Settings**:
- Chunk size: 1000 records
- Inference timeout: 300 seconds
- Uses gzip compression for chunks