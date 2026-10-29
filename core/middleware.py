from django.contrib.auth import logout


class SessionRoleIsolationMiddleware:
    """
    Enforces strict mutual exclusion between Admin and Customer sessions in a single browser:
    
    1. Storefront routes (root '/', '/product/', '/cart/', etc.):
       If a staff/admin user is logged in, their session is automatically cleared (logout)
       so the root storefront is completely free for guest or customer shopping.
       
    2. Admin routes ('/app-admin/', '/admin/'):
       If a regular customer user is logged in, their session is automatically cleared (logout)
       so the admin portal remains strictly isolated for staff authentication.
       
    This ensures that in a single browser, an admin session can never leak into or block
    the storefront, and a customer session can never leak into the admin panel.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Skip static assets, media files, and browser metadata requests
        ignored_prefixes = ('/static/', '/media/', '/favicon.ico', '/robots.txt', '/apple-touch-icon')
        if not any(path.startswith(prefix) for prefix in ignored_prefixes):
            is_admin_route = path.startswith('/app-admin/') or path.startswith('/admin/')

            if request.user.is_authenticated:
                if not is_admin_route and request.user.is_staff:
                    # Clear staff session when directly navigating customer/storefront routes
                    storefront_routes = ('/cart/', '/orders/checkout', '/account/')
                    if path == '/' or path.startswith('/product/') or any(path.startswith(p) for p in storefront_routes):
                        logout(request)
                elif is_admin_route and not request.user.is_staff:
                    # Customer user accessed admin route -> clear customer session
                    logout(request)

        response = self.get_response(request)
        return response


class LanguageRoutingMiddleware:
    """
    Enforces bilingual language routing (English & Bangla) for root/storefront routes,
    while guaranteeing that the administrative portal (/app-admin/, /admin/)
    always strictly remains in English.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        is_admin_route = path.startswith('/app-admin/') or path.startswith('/admin/')

        if is_admin_route:
            # Force English strictly for all administrative routes
            lang = 'en'
        else:
            # For storefront routes, read language preference from session or cookie
            lang = request.session.get('site_language')
            if not lang:
                lang = request.COOKIES.get('site_language', 'en')
            if lang not in ('en', 'bn'):
                lang = 'en'

        request.LANGUAGE_CODE = lang
        request.CURRENT_LANGUAGE = lang
        request.IS_BANGLA = (lang == 'bn')

        response = self.get_response(request)

        # Synchronize cookie for storefront responses
        if not is_admin_route and request.COOKIES.get('site_language') != lang:
            response.set_cookie('site_language', lang, max_age=365 * 24 * 60 * 60, samesite='Lax')

        return response
