from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from core.validators import get_safe_redirect_url


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
