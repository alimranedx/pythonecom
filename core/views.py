from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from core.validators import get_safe_redirect_url
from core.models import SiteSetting


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
    """
    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    path = getattr(request, 'path_info', '')
    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/404.html', {
            'requested_path': path,
        }, status=404)

    context = {
        'site_settings': SiteSetting.get_settings(),
        'requested_path': path,
    }
    return render(request, '404.html', context, status=404)


def custom_server_error_view(request):
    """
    Production-ready 500 Internal Server Error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    """
    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    import sys
    exc_type, exc_val, exc_tb = sys.exc_info()
    error_type = exc_type.__name__ if exc_type else "SystemError"

    # Safely log exception if not already logged by middleware
    if exc_val:
        try:
            from core.models import SystemErrorLog
            SystemErrorLog.log_exception(request, exc_val)
        except Exception:
            pass

    path = getattr(request, 'path_info', '')
    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/500.html', {
            'error_type': error_type,
        }, status=500)

    context = {
        'site_settings': SiteSetting.get_settings(),
        'error_type': error_type,
    }
    return render(request, '500.html', context, status=500)


def custom_permission_denied_view(request, exception=None):
    """
    Production-ready 403 Forbidden / Access Denied error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    """
    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    path = getattr(request, 'path_info', '')
    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/403.html', {
            'exception_message': str(exception) if exception else None,
        }, status=403)

    context = {
        'site_settings': SiteSetting.get_settings(),
        'exception_message': str(exception) if exception else None,
    }
    return render(request, '403.html', context, status=403)


def custom_bad_request_view(request, exception=None):
    """
    Production-ready 400 Bad Request error handler.
    Distinguishes back-office (/app-admin/) requests from storefront requests.
    """
    if not hasattr(request, 'user'):
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

    path = getattr(request, 'path_info', '')
    if path.startswith('/app-admin/'):
        return render(request, 'admin_panel/400.html', {
            'exception_message': str(exception) if exception else None,
        }, status=400)

    context = {
        'site_settings': SiteSetting.get_settings(),
        'exception_message': str(exception) if exception else None,
    }
    return render(request, '400.html', context, status=400)
