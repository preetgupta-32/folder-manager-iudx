# Folder Manager IUDX

A Django-based web application for managing folders and files with support for uploads, allowed file types, and API endpoints for AJAX/REST access.

---

## Features

* Create and manage folders with type restrictions (e.g., PDF-only folders).
* Upload files to folders with secure filename handling.
* Browse folder contents through a web interface.
* REST API endpoints for AJAX/JS clients.
* Authentication via Django sessions (forms) and JWT tokens (API).
* Optional encryption support using `cryptography.Fernet`.

---

## Requirements

* Python 3.10+
* pip (Python package manager)
* Git
* (macOS) Xcode Command Line Tools (for building some packages)
* (optional) Homebrew for installing dependencies like Rust

---

## Installation & Local Setup

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
pip install "django>=4.2" djangorestframework werkzeug PyJWT cryptography python-dotenv pillow requests django-cors-headers
```

If you see `ModuleNotFoundError` for any library, install it via:

```bash
pip install <package-name>
```

### 4. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create superuser (admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 6. Run development server

```bash
python manage.py runserver
```

The site will be available at: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 7. Collect static files (optional)

```bash
python manage.py collectstatic
```

---

## Project Structure

```
folder-manager-iudx/
├── files/                 # Main app with models, views, APIs
│   ├── models.py          # Folder and File models
│   ├── views.py           # Template-based views
│   ├── api.py             # REST API views (return JSON)
│   ├── urls.py            # URLs for views
│   ├── api_urls.py        # URLs for API endpoints
├── temp_site/             # Django project settings & URLs
├── static/                # CSS, JS files
├── templates/             # HTML templates
├── manage.py              # Django entry point
└── ...
```

---

## Usage

### Web Interface

* Navigate to `/` → list folders and upload files.
* Create new folders by filling in the form.
* Upload files directly to selected folders.
* Visit `/folder-detail/<id>/` to see files in a folder.

### REST API (AJAX/JS clients)

Common endpoints (defined in `files/api_urls.py`):

* `GET /api/folders/` → list folders (JSON)
* `POST /api/folders/` → create folder (expects JSON `{name, parent, allowed_type}`)
* `GET /api/folders/<id>/` → folder details
* `POST /api/files/` → upload file
* `DELETE /api/files/<id>/` → delete file
* `POST /api/login/` → obtain JWT token

Example AJAX call (JavaScript):

```js
fetch('/api/folders/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrftoken,
    'Authorization': `Bearer ${jwtToken}`
  },
  body: JSON.stringify({ name: "New Folder", parent: 1, allowed_type: "pdf" })
})
.then(res => res.json())
.then(data => console.log("Created folder:", data));
```

---

## Environment Variables

Set via `.env` file or shell export:

```bash
export DJANGO_SECRET_KEY="your_dev_secret"
export DEBUG=True
export DATABASE_URL="sqlite:///db.sqlite3"
```

---

## Development Notes

* Do **not** commit your virtual environment (`venv/`) to Git.
* Add sensitive values (`.env`, keys, database passwords) to `.gitignore`.
* Use `pip freeze > requirements.txt` to record dependencies for collaborators.
* The development server is **not** for production. For deployment, use WSGI/ASGI with Gunicorn, Daphne, or Uvicorn behind Nginx.

---

## Troubleshooting

* **`ModuleNotFoundError`**: Install the missing library with `pip install <name>`.
* **Cryptography build errors (macOS)**:

  ```bash
  xcode-select --install
  brew install rust
  pip install cryptography
  ```
* **Database errors**: Delete `db.sqlite3` (local dev only), re-run migrations.
* **Static file 404**: Run `python manage.py collectstatic`.

---

## License

This project inherits the license of the IUDX ecosystem. Please check the upstream repository for licensing terms.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add feature"`
4. Push branch: `git push origin feature/my-feature`
5. Open a Pull Request
