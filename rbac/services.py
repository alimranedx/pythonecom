from django.contrib.auth.models import User
from .models import Module, Submodule, Permission, Role, UserRole, RolePermission


class RBACService:
    """
    Centralized service for evaluating permissions, managing roles,
    and generating dynamic navigation trees based on user privileges.
    """

    @classmethod
    def get_user_permission_codes(cls, user: User) -> set:
        """
        Returns a set of all permission codes granted to the user across all assigned roles.
        Cached on the user instance to avoid redundant database lookups.
        """
        if not user.is_authenticated:
            return set()

        # Cache on request.user object for the lifecycle of the request
        if hasattr(user, '_cached_rbac_perms'):
            return user._cached_rbac_perms

        if user.is_superuser:
            # Superusers implicitly possess all permissions in the system
            codes = set(Permission.objects.values_list('code', flat=True))
            user._cached_rbac_perms = codes
            return codes

        # Fetch permissions assigned via user roles
        codes = set(
            Permission.objects.filter(
                roles__user_roles__user=user
            ).values_list('code', flat=True)
        )
        user._cached_rbac_perms = codes
        return codes

    @classmethod
    def user_has_permission(cls, user: User, submodule_code: str, action: str) -> bool:
        """
        Checks if the user has a specific action permission on a submodule.
        Example: user_has_permission(user, 'catalog.products', 'edit')
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        # Non-superusers can NEVER possess RBAC or User Management permissions
        if submodule_code.startswith('rbac'):
            return False

        target_code = f"{submodule_code}.{action}"
        user_perms = cls.get_user_permission_codes(user)
        return target_code in user_perms

    @classmethod
    def get_user_allowed_menu(cls, user: User):
        """
        Builds the navigation hierarchy (Module -> Submodules) filtered
        exclusively by the submodules the user has 'view' permissions for.
        Access Control / User & Role Management is strictly visible to Super Administrators only.
        """
        if not user.is_authenticated or not user.is_staff:
            return []

        user_perms = cls.get_user_permission_codes(user)

        # Prefetch submodules to avoid N+1 query issue
        modules = Module.objects.prefetch_related('submodules').all()
        menu_tree = []

        for module in modules:
            # Access Control / User & Role Management is strictly for Superusers only
            if module.code == 'rbac' and not user.is_superuser:
                continue

            allowed_submodules = []
            for sub in module.submodules.all():
                if sub.code.startswith('rbac.') and not user.is_superuser:
                    continue
                view_perm_code = f"{sub.code}.view"
                if user.is_superuser or view_perm_code in user_perms:
                    allowed_submodules.append(sub)

            if allowed_submodules:
                menu_tree.append({
                    'module': module,
                    'submodules': allowed_submodules,
                })

        return menu_tree

    @classmethod
    def assign_role(cls, user: User, role: Role):
        """
        Assigns a role to a staff user, idempotently.
        """
        UserRole.objects.get_or_create(user=user, role=role)
        if hasattr(user, '_cached_rbac_perms'):
            delattr(user, '_cached_rbac_perms')
