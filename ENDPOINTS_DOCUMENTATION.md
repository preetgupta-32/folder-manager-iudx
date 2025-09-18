# Complete Endpoints Documentation - File Management System

## Overview
This document lists all available endpoints in the Django file management system, including both web interface endpoints and REST API endpoints.

---

## 🌐 WEB INTERFACE ENDPOINTS (HTML Views)

### Main Page
- **URL**: `/`
- **Method**: `GET`, `POST`
- **View Function**: `upload_page`
- **Description**: Main dashboard with upload forms and folder creation
- **POST Actions**:
  - File upload (when `request.FILES.get('file')`)
  - Folder upload (when `request.FILES.getlist('folder_upload')`)
  - **Folder creation (when `request.POST.get('create_folder')`)**

### File Operations
- **Download File**: `/download/file/<int:file_id>/`
  - Method: `GET`
  - View: `download_file`
  
- **Delete File**: `/delete-file/`
  - Method: `POST`
  - View: `delete_file`
  - Body: `{"file_id": 123}`

- **Copy File**: `/copy-file/`
  - Method: `POST`
  - View: `copy_file`
  - Body: `{"file_id": 123, "folder_id": 456}`

- **Move File**: `/move-file/`
  - Method: `POST`
  - View: `move_file`
  - Body: `{"file_id": 123, "folder_id": 456}`

### Folder Operations
- **Rename Folder**: `/rename-folder/`
  - Method: `POST`
  - View: `rename_folder`
  - Body: `{"folder_id": 123, "name": "New Name"}`

- **Delete Folder**: `/delete-folder/`
  - Method: `POST`
  - View: `delete_folder`
  - Body: `{"folder_id": 123}`

- **Download Folder (as ZIP)**: `/download-folder/<int:folder_id>/`
  - Method: `GET`
  - View: `download_folder`

- **Folder Detail**: `/folder-detail/<int:folder_id>/`
  - Method: `GET`
  - View: `folder_detail`
  - Returns: HTML partial for folder contents

- **Upload to Specific Folder**: `/upload-to-folder/<int:folder_id>/`
  - Method: `POST`
  - View: `upload_to_folder`
  - Body: FormData with files

### Bulk Operations
- **Delete Multiple Files**: `/delete-multiple-files/`
  - Method: `POST`
  - View: `delete_multiple_files`
  - Body: `{"file_ids": [1, 2, 3]}`

- **Move Multiple Files**: `/move-multiple-files/`
  - Method: `POST`
  - View: `move_multiple_files`
  - Body: `{"file_ids": [1, 2, 3], "folder_id": 456}`

- **Copy Multiple Files**: `/copy-multiple-files/`
  - Method: `POST`
  - View: `copy_multiple_files`
  - Body: `{"file_ids": [1, 2, 3], "folder_id": 456}`

### Utility Endpoints
- **Folder List (JSON)**: `/folder-list-json/`
  - Method: `GET`
  - View: `folder_list_json`
  - Returns: JSON array of folders

---

## 🔌 REST API ENDPOINTS

### Folder API Endpoints
- **List All Folders**: `/api/folders/`
  - Method: `GET`
  - View: `api_folders_list`
  - Query Params: `?user_id=123` (optional)
  - Returns: JSON with folder metadata

- **Create Folder**: `/api/folders/create/`
  - Method: `POST`
  - View: `api_create_folder`
  - Body: 
    ```json
    {
      "name": "My Folder",
      "allowed_type": "csv",
      "user_id": 123,
      "description": "Optional description",
      "is_public": false,
      "parent_id": null
    }
    ```

- **Delete Folder**: `/api/folders/<int:folder_id>/delete/`
  - Method: `DELETE`
  - View: `api_delete_folder`

- **Folder Contents**: `/api/folders/<int:folder_id>/contents/`
  - Method: `GET`
  - View: `api_folder_contents`

### File API Endpoints
- **List All Files**: `/api/files/`
  - Method: `GET`
  - View: `api_files_list`
  - Query Params: `?folder_id=5&user_id=123` (optional)

- **Upload File**: `/api/files/upload/`
  - Method: `POST`
  - View: `api_upload_file`
  - Form Data:
    - `file`: (file upload)
    - `folder_id`: 5
    - `user_id`: 123
    - `description`: "Optional"
    - `is_public`: false
    - `process`: false

- **Delete File**: `/api/files/<int:file_id>/delete/`
  - Method: `DELETE`
  - View: `api_delete_file`

### Processing & Analytics Endpoints
- **File Processing Status**: `/api/files/<int:file_id>/processing-status/`
  - Method: `GET`
  - View: `api_file_processing_status`

- **Get File Chunks**: `/api/files/<int:file_id>/chunks/<int:chunk_number>/`
  - Method: `GET`
  - View: `api_file_chunks`

- **File Inference**: `/api/files/<int:file_id>/inference/`
  - Method: `GET`
  - View: `api_file_inference`

- **Upload Config**: `/api/files/<int:file_id>/config/`
  - Method: `POST`
  - View: `api_upload_config`

- **File Preview**: `/api/files/<int:file_id>/preview/`
  - Method: `GET`
  - View: `api_file_preview`

- **Available Inferences**: `/api/files/<int:file_id>/inferences/`
  - Method: `GET`
  - View: `api_available_inferences`

### User Statistics
- **User Stats**: `/api/user/<int:user_id>/stats/`
  - Method: `GET`
  - View: `api_user_stats`
  - Returns: User's file/folder statistics

---

## 📝 WHEN YOU CREATE A FOLDER

When you create a folder through the **web interface**, here's what happens:

### 1. **Frontend (Browser)**
- User fills the folder creation form
- Clicks "Create Folder" button
- Browser sends POST request to `/`

### 2. **Backend Flow**
```
POST / 
├── Request arrives at upload_page view
├── Checks request.POST.get('create_folder') == '1'
├── Creates FolderForm with POST data
├── Validates form:
│   ├── name (required)
│   ├── allowed_type (default: 'csv')
│   ├── parent (optional)
│   ├── description (optional)
│   └── is_public (default: False)
├── If valid:
│   ├── Saves folder to database
│   └── Returns redirect to '/' (302 response)
└── If invalid:
    └── Returns form with errors (200 response)
```

### 3. **Database Operations**
- Creates new entry in `files_folder` table
- Fields saved:
  - `id` (auto-generated)
  - `name`
  - `parent_id` (if subfolder)
  - `allowed_type`
  - `created_by_id` (if user authenticated)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `description`
  - `is_public`

### 4. **Response**
- Success: 302 Redirect to `/` (page reloads showing new folder)
- Failure: 200 OK with error messages in HTML

---

## 🔄 API FOLDER CREATION

When creating a folder via **API**:

```
POST /api/folders/create/
├── Request arrives at api_create_folder view
├── Parses JSON body
├── Creates Folder object directly
├── Saves to database
└── Returns JSON response:
    ├── Success: {"status": "success", "folder": {...}}
    └── Error: {"status": "error", "message": "..."}
```

---

## 📊 URL PATTERNS STRUCTURE

```python
# Main URLs (temp_site/urls.py)
/  → include('files.urls')

# Files URLs (files/urls.py)
├── Web Interface URLs
│   ├── '' → upload_page
│   ├── 'move-file/' → move_file
│   ├── 'rename-folder/' → rename_folder
│   └── ... (other web endpoints)
│
└── API URLs (from api_urls.py)
    ├── 'api/folders/' → api_folders_list
    ├── 'api/folders/create/' → api_create_folder
    └── ... (other API endpoints)
```

---

## 🔐 Authentication Notes
- Web interface endpoints use CSRF tokens (`{% csrf_token %}`)
- Most action endpoints have `@csrf_exempt` decorator
- API endpoints can use `user_id` parameter for user context
- No built-in authentication currently enforced

---

## 💡 Key Differences

### Web Interface vs API
| Aspect | Web Interface | REST API |
|--------|--------------|----------|
| URL Pattern | `/action/` | `/api/resource/action/` |
| Response | HTML/Redirect | JSON |
| CSRF | Required | Exempt |
| File Upload | Form-based | Multipart/JSON |
| Error Handling | Form validation | JSON errors |

---

## 📞 Testing Endpoints

### Test folder creation via curl:
```bash
# API endpoint
curl -X POST http://localhost:8000/api/folders/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Folder", "allowed_type": "csv"}'

# Web endpoint (needs CSRF token)
# Not easily testable via curl due to CSRF requirements
```

### Test via Python:
```python
import requests

# API endpoint
response = requests.post(
    'http://localhost:8000/api/folders/create/',
    json={'name': 'API Test', 'allowed_type': 'pdf'}
)
print(response.json())
```

---

## 📁 File Upload Flow
When uploading a file:
1. **Single file**: POST to `/` with file in `request.FILES['file']`
2. **Folder upload**: POST to `/` with files in `request.FILES.getlist('folder_upload')`
3. **API upload**: POST to `/api/files/upload/` with multipart form data
4. **Drag-drop to folder**: POST to `/upload-to-folder/<folder_id>/`

Each creates `UploadedFile` object and saves physical file to `media/uploads/`