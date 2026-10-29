from .services import CartService

def cart_processor(request):
    """
    Exposes cart and cart_items_count globally across all templates.
    Back-office admin routes bypass cart creation completely.
    """
    path = getattr(request, 'path_info', '')
    if path.startswith('/app-admin/') or path.startswith('/admin/'):
        return {
            'global_cart': None,
            'global_cart_items_count': 0,
        }

    try:
        cart = CartService.get_or_create_cart(request)
        return {
            'global_cart': cart,
            'global_cart_items_count': cart.total_items if cart else 0,
        }
    except Exception:
        return {
            'global_cart': None,
            'global_cart_items_count': 0,
        }
