from django import template
from rbac.services import RBACService

register = template.Library()


@register.simple_tag
def has_perm(user, submodule_code, action='view'):
    """
    Template tag to test permission in templates.
    Usage:
        {% load rbac_tags %}
        {% has_perm request.user 'catalog.products' 'create' as can_create_product %}
        {% if can_create_product %}
            <a href="...">Add Product</a>
        {% endif %}
    """
    return RBACService.user_has_permission(user, submodule_code, action)


@register.simple_tag
def get_admin_menu(user):
    """
    Returns the dynamic menu tree permitted for this user.
    Usage:
        {% get_admin_menu request.user as menu_tree %}
    """
    return RBACService.get_user_allowed_menu(user)
