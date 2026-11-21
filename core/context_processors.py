from core.translations import TranslationProxy, to_bn_number
from core.models import SiteSetting
from core.themes import THEMES, THEME_CHOICES, DEFAULT_THEME_KEY, get_theme_data


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
    footer details, and dynamic theme tokens globally to all templates.
    Injects:
    - site_settings
    - CURRENT_THEME_KEY: Active or preview theme identifier
    - CURRENT_THEME_ID: Normalized canonical theme ID (e.g. 'pharmacy-healthcare')
    - CURRENT_THEME_DATA: Fully resolved language-aware theme dictionary
    - CURRENT_THEME_CONFIG: Applied dynamic customization settings dict
    - IS_THEME_PREVIEW: Boolean flag indicating if current view is an isolated admin preview
    - THEME_CHOICES: Canonical theme choices for forms
    - ALL_THEMES: Registry mapping of all available themes
    Supports:
    1. Admin preview session via request.session.get('admin_preview_theme')
    2. URL preview parameter (?theme=<id_or_key>) for authenticated staff users or testing
    """
    from core.theme_registry import theme_registry
    from core.models import SiteSetting, ThemeCustomization
    from core.themes import THEMES, THEME_CHOICES, DEFAULT_THEME_KEY, get_theme_data

    settings = SiteSetting.get_settings()
    active_theme_raw = getattr(settings, 'active_theme', DEFAULT_THEME_KEY) or DEFAULT_THEME_KEY

    theme_to_render = active_theme_raw
    is_preview = False

    # 1. Check admin preview session (set from back-office Theme Manager)
    session = getattr(request, 'session', None)
    if session:
        session_preview = session.get('admin_preview_theme')
        if session_preview and theme_registry.is_valid(session_preview):
            user = getattr(request, 'user', None)
            # Staff users or sessions marked with admin preview get the preview theme
            if user and getattr(user, 'is_authenticated', False):
                if user.is_staff or user.is_superuser:
                    theme_to_render = session_preview
                    is_preview = True
            else:
                # In session preview mode
                theme_to_render = session_preview
                is_preview = True

    # 2. Check preview query parameter (?theme=<id_or_key> or ?preview_theme=<id_or_key>)
    if hasattr(request, 'GET'):
        preview_param = request.GET.get('preview_theme') or request.GET.get('theme')
        if preview_param and theme_registry.is_valid(preview_param):
            user = getattr(request, 'user', None)
            is_staff = user and getattr(user, 'is_authenticated', False) and (user.is_staff or user.is_superuser)
            # Allow query preview for staff or in development/testing
            theme_to_render = preview_param
            norm_param = theme_registry.normalize_id(preview_param)
            norm_active = theme_registry.normalize_id(active_theme_raw)
            if request.GET.get('preview_theme') or norm_param != norm_active or is_staff:
                is_preview = True

    canonical_id = theme_registry.normalize_id(theme_to_render)
    if not canonical_id:
        canonical_id = theme_registry.default_theme_id
        theme_to_render = canonical_id

    # Load theme customization config overrides
    custom_config = {}
    custom_css = ""
    try:
        customization = ThemeCustomization.objects.filter(theme_id=canonical_id).first()
        if customization:
            custom_config = customization.get_effective_config()
            custom_css = customization.custom_css or ""
    except Exception:
        pass

    is_bangla = getattr(request, 'IS_BANGLA', False)
    theme_data = get_theme_data(theme_to_render, is_bangla=is_bangla, custom_config=custom_config)

    return {
        'site_settings': settings,
        'CURRENT_THEME_KEY': theme_to_render,
        'CURRENT_THEME_ID': canonical_id,
        'CURRENT_THEME_DATA': theme_data,
        'CURRENT_THEME_CONFIG': custom_config,
        'THEME_CUSTOM_CSS': custom_css,
        'IS_THEME_PREVIEW': is_preview,
        'THEME_CHOICES': THEME_CHOICES,
        'ALL_THEMES': THEMES,
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


def navigation_categories_processor(request):
    """
    Exposes active categories globally to navigation menus and mobile drawer:
    - nav_categories: Top 6 featured categories for the desktop horizontal sub-navbar.
    - all_categories: All active categories for the 'Browse Categories' dropdown and mobile menu.
    Strictly isolated to the current active/preview theme.
    Resolves both canonical IDs and legacy theme keys cleanly.
    """
    try:
        from product.models import Category
        from core.models import SiteSetting
        from core.theme_registry import theme_registry
        from core.themes import THEMES, DEFAULT_THEME_KEY
        from django.db.models import Q

        # Resolve active theme key
        theme_key = None
        session = getattr(request, 'session', None)
        if session:
            sess_preview = session.get('admin_preview_theme')
            if sess_preview and theme_registry.is_valid(sess_preview):
                theme_key = sess_preview

        if not theme_key and hasattr(request, 'GET'):
            preview = request.GET.get('preview_theme') or request.GET.get('theme')
            if preview and theme_registry.is_valid(preview):
                theme_key = preview

        if not theme_key:
            settings = SiteSetting.get_settings()
            theme_key = getattr(settings, 'active_theme', DEFAULT_THEME_KEY) or DEFAULT_THEME_KEY

        canonical_id = theme_registry.normalize_id(theme_key) or theme_key
        legacy_key = theme_registry.get_legacy_key(canonical_id)

        if hasattr(Category, 'theme'):
            # Marketplace (Daraz / Amazon style) shows global catalog categories
            if canonical_id == 'marketplace' or legacy_key == 'mega_market':
                theme_q = (
                    Q(theme='marketplace') |
                    Q(theme='mega_market') |
                    Q(theme='all')
                )
            else:
                theme_q = (
                    Q(theme=canonical_id) |
                    Q(theme=legacy_key)
                )
            base_cats = Category.objects.filter(theme_q)
        else:
            base_cats = Category.objects.all()

        featured = list(
            base_cats.filter(is_featured=True)
            .order_by('order', 'name')
            .only('id', 'name', 'slug', 'icon', 'order', 'is_featured')[:6]
        )
        if len(featured) < 6:
            existing_ids = [c.id for c in featured]
            supplements = list(
                base_cats.exclude(id__in=existing_ids)
                .order_by('order', 'name')
                .only('id', 'name', 'slug', 'icon', 'order', 'is_featured')[:(6 - len(featured))]
            )
            featured.extend(supplements)

        all_cats = list(
            base_cats.order_by('order', 'name')
            .only('id', 'name', 'slug', 'icon', 'order', 'is_featured')
        )
        return {
            'nav_categories': featured,
            'all_categories': all_cats,
        }
    except Exception:
        return {
            'nav_categories': [],
            'all_categories': [],
        }
