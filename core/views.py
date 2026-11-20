import logging
import urllib.parse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from core.validators import get_safe_redirect_url

# Automated scanner probe signatures (e.g. .env, .git, wp-login, phpmyadmin, shell.php, /etc/passwd, .., cgi-bin)
SCANNER_PROBE_SIGNATURES = (
    '.env',
    '.git',
    'wp-login',
    'wp-admin',
    'phpmyadmin',
    'shell.php',
    '/etc/passwd',
    'etc/passwd',
    '..',
    'cgi-bin',
    'web.config',
    '.aws',
    '.ssh',
    '.ds_store',
    'actuator',
    'telescope',
    'swagger-ui',
    'admin.php',
    'xmlrpc.php',
    'config.json',
)


def _get_client_ip(request):
    """Safely extracts client IP address accounting for proxies and forwarders."""
    meta = getattr(request, 'META', {})
    x_forwarded = meta.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return meta.get('REMOTE_ADDR', '')


def _safe_get_user(request):
    """Safely extracts the username or returns 'Anonymous' without DB crash risks."""
    try:
        if not hasattr(request, 'user'):
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            return getattr(user, 'username', str(user))
    except Exception:
        pass
    return 'Anonymous'


def _safe_get_site_settings():
    """Safely loads SiteSetting singleton with graceful fallback if DB is unreachable."""
    try:
        from core.models import SiteSetting
        return SiteSetting.get_settings()
    except Exception:
        return None


@require_GET
def set_language_view(request, lang_code):
    """
    Switch storefront language between 'en' (English) and 'bn' (Bangla).
    Administrative routes (/app-admin/) ignore this setting and strictly remain English.
    """
    if lang_code not in ('en', 'bn'):
        lang_code = 'en'

    request.session['site_language'] = lang_code

    redirect_to = get_safe_redirect_url(
        request,
        request.META.get('HTTP_REFERER'),
        'home'
    )

    response = redirect(redirect_to)
    response.set_cookie('site_language', lang_code, max_age=365 * 24 * 60 * 60, samesite='Lax')
    return response


def custom_page_not_found_view(request, exception=None):
    """
    Production-ready 404 Page Not Found error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    Detects automated scanner probe attacks (.env, .git, wp-login, phpmyadmin, etc.)
    and logs a security warning footprint to django.security.ScannerProbe with client IP and path.
    """
    path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
    ip = _get_client_ip(request)
    path_lower = path.lower()
    unquoted_path = urllib.parse.unquote(path_lower)

    # Check for automated scanner probe signatures
    matched_signature = next(
        (sig for sig in SCANNER_PROBE_SIGNATURES if sig in path_lower or sig in unquoted_path),
        None
    )
    if matched_signature:
        scanner_logger = logging.getLogger('django.security.ScannerProbe')
        scanner_logger.warning(
            f"Scanner probe footprint detected (404): IP={ip} path={path} matched_probe='{matched_signature}'"
        )

    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/404.html', {
            'requested_path': path,
        }, status=404)

    context = {
        'site_settings': _safe_get_site_settings(),
        'requested_path': path,
    }
    return render(request, '404.html', context, status=404)


def custom_server_error_view(request):
    """
    Production-ready 500 Internal Server Error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    Verifies graceful fallback logging if DB is temporarily unreachable.
    """
    import sys

    logger = logging.getLogger('django.request')

    exc_type, exc_val, exc_tb = sys.exc_info()
    error_type = exc_type.__name__ if exc_type else "SystemError"

    # Safely log exception: first attempt DB via SystemErrorLog, with graceful fallback to logger
    if exc_val:
        try:
            from core.models import SystemErrorLog
            SystemErrorLog.log_exception(request, exc_val)
        except Exception as db_exc:
            logger.error(
                f"Graceful fallback: DB unreachable when recording SystemErrorLog. "
                f"Exception: {exc_val} on {getattr(request, 'method', 'GET')} {getattr(request, 'path_info', '')}. DB error: {db_exc}",
                exc_info=True
            )
    else:
        logger.error(
            f"500 Internal Server Error encountered on {getattr(request, 'method', 'GET')} {getattr(request, 'path_info', '')}"
        )

    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    path = getattr(request, 'path_info', '')
    is_admin = path.startswith('/app-admin/')

    template_name = 'admin_panel/500.html' if is_admin else '500.html'
    context = {
        'site_settings': _safe_get_site_settings(),
        'error_type': error_type,
    }

    try:
        return render(request, template_name, context, status=500)
    except Exception as render_err:
        logger.error(f"Fallback rendering 500 error page due to: {render_err}", exc_info=True)
        from django.http import HttpResponseServerError
        return HttpResponseServerError(
            "<!DOCTYPE html><html><head><title>500 - Server Error</title></head>"
            "<body style='font-family: sans-serif; text-align: center; padding: 50px;'>"
            "<h1>500 - Internal Server Error</h1>"
            "<p>Our server encountered a temporary issue. Please try again shortly.</p>"
            "</body></html>",
            content_type="text/html; charset=utf-8"
        )


def custom_permission_denied_view(request, exception=None):
    """
    Production-ready 403 Forbidden / Access Denied error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    Logs security warning footprint to django.security.PermissionDenied with
    client IP, path, method, user, and exception message to track unauthorized
    privilege escalation or IDOR attempts.
    """
    ip = _get_client_ip(request)
    path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
    method = getattr(request, 'method', 'GET')
    user = _safe_get_user(request)
    exc_message = str(exception) if exception else 'Permission Denied / Access Restricted'

    perm_logger = logging.getLogger('django.security.PermissionDenied')
    perm_logger.warning(
        f"PermissionDenied (403 Forbidden): IP={ip} path={path} method={method} user={user} exception='{exc_message}'"
    )

    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/403.html', {
            'exception_message': exc_message,
        }, status=403)

    context = {
        'site_settings': _safe_get_site_settings(),
        'exception_message': exc_message,
    }
    return render(request, '403.html', context, status=403)


def custom_csrf_failure_view(request, reason=""):
    """
    Production-ready CSRF failure error handler (403 Forbidden).
    Logs CSRF violation footprint with client IP, path, method, user agent, and failure reason.
    Renders branded 403 error page with clear user-friendly explanation:
    'Session security token expired. Please refresh the page and try again.'
    """
    ip = _get_client_ip(request)
    path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
    method = getattr(request, 'method', 'POST')
    user = _safe_get_user(request)
    user_agent = getattr(request, 'META', {}).get('HTTP_USER_AGENT', 'Unknown')
    csrf_reason = str(reason) if reason else 'CSRF token missing or incorrect'

    csrf_logger = logging.getLogger('django.security.csrf')
    csrf_logger.warning(
        f"CSRF Violation (403): IP={ip} path={path} method={method} user={user} user_agent='{user_agent}' reason='{csrf_reason}'"
    )

    user_friendly_message = 'Session security token expired. Please refresh the page and try again.'

    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/403.html', {
            'exception_message': user_friendly_message,
            'csrf_failure': True,
        }, status=403)

    context = {
        'site_settings': _safe_get_site_settings(),
        'exception_message': user_friendly_message,
        'csrf_failure': True,
    }
    return render(request, '403.html', context, status=403)


def custom_bad_request_view(request, exception=None):
    """
    Production-ready 400 Bad Request error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    Logs security warning footprint to django.security.SuspiciousOperation with
    client IP, path, method, user, and reason.
    """
    ip = _get_client_ip(request)
    path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
    method = getattr(request, 'method', 'GET')
    user = _safe_get_user(request)
    reason = str(exception) if exception else 'Bad Request / Suspicious Operation'

    suspicious_logger = logging.getLogger('django.security.SuspiciousOperation')
    suspicious_logger.warning(
        f"SuspiciousOperation (400 Bad Request): IP={ip} path={path} method={method} user={user} reason='{reason}'"
    )

    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/400.html', {
            'exception_message': reason,
        }, status=400)

    context = {
        'site_settings': _safe_get_site_settings(),
        'exception_message': reason,
    }
    return render(request, '400.html', context, status=400)
