from .services import CartService

def cart_processor(request):
    """
    Exposes cart and cart_items_count globally across all templates.
    """
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
