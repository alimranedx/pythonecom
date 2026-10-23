# PythonEcom - Django Project

A Django-based ecommerce project.

---

## 🖥️ Requirements

Make sure the following are installed on your PC before starting:

- [Python 3.10+](https://www.python.org/downloads/) ✅
- [Git](https://git-scm.com/downloads) ✅
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

A virtual environment keeps your project's packages separate from other projects.

```bash
python -m venv venv
```

---

### Step 3 — Activate the Virtual Environment

**On Windows:**
```bash
venv\Scripts\activate
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

> ✅ You will see `(venv)` at the start of your terminal line when it's active.

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

> This installs all required packages like Django automatically.

---

### Step 5 — Run Database Migrations

```bash
python manage.py migrate
```

> This sets up the database (SQLite) on your new PC.

---

### Step 6 — (Optional) Create a Superuser for Admin Panel

```bash
python manage.py createsuperuser
```

> Follow the prompts to set a username, email, and password.

---

### Step 7 — Run the Development Server

```bash
python manage.py runserver
```

---

## 🌐 Open in Browser

| Page         | URL                              |
|--------------|----------------------------------|
| Product Page | http://127.0.0.1:8000/product/   |
| Admin Panel  | http://127.0.0.1:8000/admin/     |

---

## 📁 Project Structure

```
pythonecom/
│
├── pythonecom/         # Main project folder (settings, urls)
│   ├── settings.py     # Project configuration
│   ├── urls.py         # Root URL configuration
│   └── wsgi.py
│
├── product/            # Product app
│   ├── models.py       # Database models
│   ├── views.py        # Page logic
│   ├── urls.py         # App URL configuration
│   └── admin.py
│
├── manage.py           # Django management tool
├── requirements.txt    # Project dependencies
└── README.md           # This file
```

---

## 🔧 Common Commands

| Task                        | Command                           |
|-----------------------------|-----------------------------------|
| Start server                | `python manage.py runserver`      |
| Make new migrations         | `python manage.py makemigrations` |
| Apply migrations            | `python manage.py migrate`        |
| Create admin user           | `python manage.py createsuperuser`|
| Open Django shell           | `python manage.py shell`          |
| Collect static files        | `python manage.py collectstatic`  |

---

## ⚠️ Notes

- The `db.sqlite3` file is **not included** in the repo (it's in `.gitignore`). That's why you must run `migrate` after cloning.
- Never share your `SECRET_KEY` publicly. For production, move it to an environment variable.
- `DEBUG = True` is for development only. Set it to `False` in production.
