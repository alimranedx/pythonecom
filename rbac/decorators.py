from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from .services import RBACService


def require_permission(submodule_code: str, action: str = 'view'):
    """
    Decorator for Admin Panel views ensuring that the logged-in staff member
    has the designated permission.
    Example:
        @require_permission('catalog.products', 'edit')
        def product_edit(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin_login')

            if not request.user.is_staff:
                messages.error(request, "Staff privileges required to access the admin portal.")
                return redirect('home')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not RBACService.user_has_permission(request.user, submodule_code, action):
                messages.error(
                    request,
                    f"Access Denied: You do not have '{action}' permission for this section ({submodule_code})."
                )
                raise PermissionDenied(f"Missing required permission: {submodule_code}.{action}")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_superuser(view_func):
    """
    Strict security guard: ONLY Super Administrators (is_superuser=True)
    are permitted to manage admin users, user roles, and role permissions.
    Standard staff/admin users are strictly blocked and redirected.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')

        if not request.user.is_staff:
            messages.error(request, "Staff privileges required to access the admin portal.")
            return redirect('home')

        if not request.user.is_superuser:
            messages.error(
                request,
                "Access Denied: Only Super Administrators can manage admin users, roles, and permissions."
            )
            return redirect('admin_dashboard')

        return view_func(request, *args, **kwargs)
    return _wrapped_view
