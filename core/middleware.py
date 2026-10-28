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

        # Skip static assets and media files
        if not path.startswith('/static/') and not path.startswith('/media/'):
            is_admin_route = path.startswith('/app-admin/') or path.startswith('/admin/')

            if request.user.is_authenticated:
                if not is_admin_route and request.user.is_staff:
                    # Staff user accessed storefront route -> clear staff session, free root panel
                    logout(request)
                elif is_admin_route and not request.user.is_staff:
                    # Customer user accessed admin route -> clear customer session
                    logout(request)

        response = self.get_response(request)
        return response
