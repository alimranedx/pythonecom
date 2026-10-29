from django.http import HttpRequest
from django.contrib.auth.models import User
from product.models import Product
from .models import Cart, CartItem


class CartService:
    """
    Service Layer encapsulating shopping cart management for both
    guest sessions and authenticated customer profiles.
    Staff sessions on storefront routes are automatically freed/logged out.
    """

    @classmethod
    def get_or_create_cart(cls, request: HttpRequest):
        if request.user.is_authenticated and not request.user.is_staff:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            if request.session.session_key:
                cls.merge_guest_cart(request.session.session_key, request.user)
            return cart

        if not request.session.session_key:
            request.session.create()

        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart

    @classmethod
    def add_to_cart(cls, cart: Cart, product: Product, quantity: int = 1) -> CartItem:
        if cart is None:
            return None
        if quantity <= 0:
            quantity = 1
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
        return item

    @classmethod
    def update_quantity(cls, cart: Cart, product_id: int, quantity: int):
        if cart is None:
            return
        if quantity <= 0:
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        else:
            CartItem.objects.filter(cart=cart, product_id=product_id).update(quantity=quantity)

    @classmethod
    def remove_item(cls, cart: Cart, product_id: int):
        if cart is None:
            return
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()

    @classmethod
    def clear_cart(cls, cart: Cart):
        if cart is None:
            return
        cart.items.all().delete()

    @classmethod
    def merge_guest_cart(cls, session_key: str, user: User):
        """
        Transfers items from an anonymous session cart to the customer's cart upon login.
        """
        try:
            guest_cart = Cart.objects.get(session_key=session_key)
            user_cart, _ = Cart.objects.get_or_create(user=user)

            for guest_item in guest_cart.items.all():
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart, product=guest_item.product
                )
                if not created:
                    user_item.quantity += guest_item.quantity
                    user_item.save()
                else:
                    user_item.quantity = guest_item.quantity
                    user_item.save()

            guest_cart.delete()
        except Cart.DoesNotExist:
            pass
