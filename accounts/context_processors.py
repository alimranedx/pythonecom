from .models import Wishlist

def wishlist_processor(request):
    """
    Exposes wishlist_count and user_wishlist_ids globally to templates.
    Storefront wishlists are strictly for customer users (is_staff=False).
    """
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and not user.is_staff:
        user_wishlist_ids = set(
            Wishlist.objects.filter(user=user).values_list('product_id', flat=True)
        )
        return {
            'global_wishlist_count': len(user_wishlist_ids),
            'user_wishlist_ids': user_wishlist_ids,
        }
    return {
        'global_wishlist_count': 0,
        'user_wishlist_ids': set(),
    }
