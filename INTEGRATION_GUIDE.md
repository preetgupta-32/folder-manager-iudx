# File Management System Integration Guide

## Overview
This document explains how to integrate your file management system into an existing project. There are several approaches depending on your main project's technology stack.

## Integration Options

### Option 1: Django App Integration (Same Framework)

If the main project is Django-based:

1. **Copy the `files` app** to their project directory
2. **Add to their INSTALLED_APPS**:
   ```python
   INSTALLED_APPS = [
       # ... their existing apps
       'files',
   ]
   ```

3. **Include URLs** in their main `urls.py`:
   ```python
   from django.urls import path, include
   
   urlpatterns = [
       # ... their existing URLs
       path('files/', include('files.urls')),
       path('', include('files.api_urls')),  # For API endpoints
   ]
   ```

4. **Run migrations**:
   ```bash
   python manage.py makemigrations files
   python manage.py migrate
   ```

5. **Update settings** for media files:
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```

---

### Option 2: API Integration (Different Framework)

If the main project uses React, Vue, Laravel, etc.:

#### 2.1 Keep Your Django App as a Service
- Run your file management system on a separate port (e.g., `:8001`)
- Use the API endpoints to communicate with it

#### 2.2 API Endpoints Available:

**List Folders:**
```
GET /api/folders/
GET /api/folders/?user_id=123
```

**List Files:**
```
GET /api/files/
GET /api/files/?folder_id=5&user_id=123
```

**Create Folder:**
```
POST /api/folders/create/
Content-Type: application/json

{
    "name": "My Folder",
    "allowed_type": "pdf",
    "user_id": 123,
    "description": "Optional description",
    "is_public": false
}
```

**Upload File:**
```
POST /api/files/upload/
Content-Type: multipart/form-data

Form fields:
- file: (file upload)
- folder_id: 5
- user_id: 123
- description: "Optional description"
- is_public: false
```

**Delete File:**
```
DELETE /api/files/123/delete/
```

**Delete Folder:**
```
DELETE /api/folders/5/delete/
```

**User Statistics:**
```
GET /api/user/123/stats/
```

---

### Option 3: Database Integration

If they want to merge databases:

#### 3.1 Export Your Data
```bash
python manage.py dumpdata files > files_data.json
```

#### 3.2 Adapt Models to Their Schema
- Modify the User foreign keys to match their user model
- Adjust field names if needed
- Update file upload paths

#### 3.3 Import Process
1. Create models in their database
2. Migrate data from JSON export
3. Update file paths and references

---

## User Integration

### Current User System (None)
Your app currently has no user authentication. For integration:

### Option A: Use Their Authentication
```python
# In views.py, add authentication checks
from django.contrib.auth.decorators import login_required

@login_required
def upload_page(request):
    # ... existing code
    # Set user context: request.user
```

### Option B: API with User ID
Pass user_id in API requests to associate files with users.

---

## Database Migration Steps

### Step 1: Backup Current Data
```bash
python manage.py dumpdata files > backup_files.json
```

### Step 2: Create Migration for New Fields
```bash
python manage.py makemigrations files
python manage.py migrate
```

### Step 3: Update Views to Use User Context
Add user assignment in all file/folder creation views.

---

## File Storage Integration

### Current: Local Storage
Files stored in `media/uploads/`

### For Production:
1. **AWS S3**: Update `DEFAULT_FILE_STORAGE`
2. **Google Cloud**: Configure cloud storage
3. **CDN**: Add media URL configuration

---

## Security Considerations

### 1. File Type Validation
Already implemented - files validated against folder allowed_type

### 2. File Size Limits
Add to settings:
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024   # 50MB
```

### 3. User Permissions
- `is_public` field controls file visibility
- `created_by`/`uploaded_by` fields track ownership

---

## Testing the Integration

### 1. API Testing
Use tools like Postman or curl:

```bash
# List folders
curl -X GET "http://localhost:8000/api/folders/"

# Create folder
curl -X POST "http://localhost:8000/api/folders/create/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Folder", "allowed_type": "pdf"}'

# Upload file
curl -X POST "http://localhost:8000/api/files/upload/" \
     -F "file=@test.pdf" \
     -F "folder_id=1"
```

### 2. Django Integration Testing
1. Create test users
2. Test file upload with user context
3. Verify permissions and ownership

---

## Next Steps

1. **Determine their tech stack** - Django, React, PHP, etc.
2. **Choose integration approach** based on compatibility
3. **Set up development environment** for testing
4. **Migrate user system** if needed
5. **Test file operations** with their data
6. **Deploy and monitor** the integration

---

## Support Files Included

- `models.py` - Enhanced with user fields and metadata
- `api.py` - REST API endpoints for integration
- `api_urls.py` - API URL configuration
- Migration files for database updates

---

## Questions to Ask Your Mentors

1. What framework/language is the main project using?
2. What database system are they using?
3. Do they have existing file upload functionality?
4. What's their user authentication system?
5. Do they prefer API integration or direct database integration?
6. What are their file storage requirements (local, cloud, CDN)?
7. Any specific security or permission requirements? 