# PythonEcom - Django Project

A Django-based ecommerce project with MySQL database.

---

## 🖥️ Requirements

Make sure the following are installed on your PC before starting:

- [Python 3.10+](https://www.python.org/downloads/) ✅
- [Git](https://git-scm.com/downloads) ✅
- [MySQL 8.0+](https://dev.mysql.com/downloads/) ✅ (or use [Laragon](https://laragon.org/))
- pip (comes with Python) ✅

---

## 🚀 Setup Guide (After Cloning)

Follow these steps **in order** to get the project running on a new PC.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/alimranedx/pythonecom.git
cd pythonecom
```

---

### Step 2 — Create a Virtual Environment

```bash
python -m venv .venv
```

---

### Step 3 — Activate the Virtual Environment

**On Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**On Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**On Mac/Linux:**
```bash
source .venv/bin/activate
```

> ✅ You will see `(.venv)` at the start of your terminal line when it's active.

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

> This installs all required packages like Django and mysqlclient automatically.

---

### Step 5 — Create MySQL Database

Open MySQL (Workbench, HeidiSQL, Laragon, or CLI) and run:

```sql
CREATE DATABASE pythonecom_db;
```

---

### Step 6 — Configure Database in `settings.py`

Open `pythonecom/settings.py` and update the `DATABASES` section:

```python
DATABASES = {
    'default': {
        'ENGINE': 'pythonecom.custom_mysql_backend',
        'NAME': 'pythonecom_db',
        'USER': 'root',           # your MySQL username
        'PASSWORD': '',           # your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

### Step 7 — Run Database Migrations

```bash
python manage.py migrate
```

> This creates all required tables in your MySQL database.

---

### Step 8 — (Optional) Create Superuser for Admin Panel

```bash
python manage.py createsuperuser
```

> Follow the prompts to set a username, email, and password.

---

### Step 9 — Run the Development Server

```bash
python manage.py runserver
```

---

## 🌐 Open in Browser

| Page           | URL                                |
|----------------|------------------------------------|
| Home Page      | http://127.0.0.1:8000/             |
| Product List   | http://127.0.0.1:8000/products/    |
| Add Product    | http://127.0.0.1:8000/products/create/ |
| Admin Panel    | http://127.0.0.1:8000/admin/       |

---

## 📁 Project Structure

```
pythonecom/
│
├── pythonecom/                    # Main project folder
│   ├── settings.py                # Project configuration
│   ├── urls.py                    # Root URL configuration
│   ├── custom_mysql_backend/      # Custom MySQL backend (version fix)
│   │   ├── __init__.py
│   │   └── base.py
│   └── wsgi.py
│
├── home/                          # Home app
│   ├── views.py
│   ├── urls.py
│   └── templates/home/
│       └── index.html
│
├── product/                       # Product app (CRUD)
│   ├── models.py                  # Product model
│   ├── views.py                   # CRUD views
│   ├── urls.py                    # Product URLs
│   ├── forms.py                   # Product form
│   └── templates/product/
│       ├── list.html
│       ├── detail.html
│       ├── form.html
│       └── confirm_delete.html
│
├── manage.py                      # Django management tool
├── requirements.txt               # Project dependencies
└── README.md                      # This file
```

---

## 🔧 Common Commands

| Task                        | Command                             |
|-----------------------------|-------------------------------------|
| Start server                | `python manage.py runserver`        |
| Make new migrations         | `python manage.py makemigrations`   |
| Apply migrations            | `python manage.py migrate`          |
| Create admin user           | `python manage.py createsuperuser`  |
| Freeze dependencies         | `pip freeze > requirements.txt`     |
| Open Django shell           | `python manage.py shell`            |

---

## ⚠️ Notes

- The `db.sqlite3` file is **not included** in the repo — MySQL is used instead.
- `__pycache__/` and `.venv/` are excluded from git via `.gitignore`.
- Never share your `SECRET_KEY` publicly. Move it to a `.env` file for production.
- `DEBUG = True` is for development only. Set it to `False` in production.
- The `custom_mysql_backend` is a workaround for using MySQL 8.0.x with Django 5.x.
