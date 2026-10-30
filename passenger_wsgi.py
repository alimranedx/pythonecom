import os
import sys
import traceback
from pathlib import Path

# Project root directory
APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Ensure virtualenv site-packages is in sys.path
VENV_PACKAGES = Path('/home/shopbusk/virtualenv/ecommerce.shopbusket.com/3.10/lib/python3.10/site-packages')
if VENV_PACKAGES.exists() and str(VENV_PACKAGES) not in sys.path:
    sys.path.insert(0, str(VENV_PACKAGES))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonecom.settings')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception:
    error_trace = traceback.format_exc()
    def application(environ, start_response):
        status = '200 OK'
        body = f"<html><body><h2>Django Startup Error</h2><pre>{error_trace}</pre></body></html>".encode('utf-8')
        response_headers = [
            ('Content-type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(body)))
        ]
        start_response(status, response_headers)
        return [body]
