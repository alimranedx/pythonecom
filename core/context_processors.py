from core.translations import TranslationProxy, to_bn_number
from core.models import SiteSetting


def language_processor(request):
    """
    Exposes storefront bilingual state and translation proxies to templates:
    - CURRENT_LANGUAGE: 'en' or 'bn'
    - IS_BANGLA: True if current language is Bangla ('bn')
    - tr: Translation proxy object for accessing dictionary keys (e.g. {{ tr.add_to_cart }})
    """
    lang = getattr(request, 'CURRENT_LANGUAGE', 'en')
    is_bangla = getattr(request, 'IS_BANGLA', False)

    return {
        'CURRENT_LANGUAGE': lang,
        'IS_BANGLA': is_bangla,
        'tr': TranslationProxy(lang),
    }


def site_settings_processor(request):
    """
    Exposes dynamic store branding, header announcements, contact information,
    and footer details globally to all storefront templates.
    """
    return {
        'site_settings': SiteSetting.get_settings(),
    }


def admin_system_alert_processor(request):
    """
    Exposes system-wide exception alerts to authenticated administrators and staff members
    across all page requests (back-office and storefront).
    """
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and (user.is_staff or user.is_superuser):
        try:
            from core.models import SystemErrorLog
            unresolved = SystemErrorLog.objects.filter(is_resolved=False)
            unresolved_count = unresolved.count()
            latest = unresolved.first() if unresolved_count > 0 else None
            return {
                'has_system_errors': unresolved_count > 0,
                'unresolved_error_count': unresolved_count,
                'latest_system_error': latest,
            }
        except Exception:
            pass

    return {
        'has_system_errors': False,
        'unresolved_error_count': 0,
        'latest_system_error': None,
    }
