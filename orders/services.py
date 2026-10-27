from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from cart.services import CartService
from .models import Order, OrderItem
from .strategies import PaymentStrategyFactory


class OrderService:
    """
    Business logic layer for Order Placement, Checkout, and Inventory Updates.
    Employs the Unit of Work pattern through atomic database transactions.
    """

    @classmethod
    @transaction.atomic
    def create_order_from_cart(
        cls,
        cart: Cart,
        shipping_data: Dict[str, Any],
        user=None,
        payment_data: Dict[str, Any] = None,
    ) -> Order:
        """
        Atomically checks out a shopping cart:
        1. Validates inventory availability.
        2. Reserves and decrements product inventory.
        3. Snapshots customer details and product pricing.
        4. Processes payment via Strategy Pattern.
        5. Empties the shopping cart.
        """
        items = list(cart.items.select_related('product').all())
        if not items:
            raise ValidationError("Cannot checkout with an empty shopping cart.")

        # Inventory check
        for item in items:
            if item.product.stock < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for '{item.product.name}'. Available: {item.product.stock}, requested: {item.quantity}."
                )

        # Create Order
        payment_method = shipping_data.get('payment_method', 'cod')
        order = Order.objects.create(
            user=user if (user and user.is_authenticated) else None,
            full_name=shipping_data.get('full_name', ''),
            email=shipping_data.get('email', ''),
            phone=shipping_data.get('phone', ''),
            street_address=shipping_data.get('street_address', ''),
            city=shipping_data.get('city', ''),
            postal_code=shipping_data.get('postal_code', ''),
            country=shipping_data.get('country', 'Bangladesh'),
            notes=shipping_data.get('notes', ''),
            subtotal=cart.subtotal,
            shipping_fee=cart.shipping_cost,
            total_amount=cart.grand_total,
            payment_method=payment_method,
            payment_status='pending',
            status='pending',
        )

        # Create Order Items & Decrement Inventory
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.effective_price,
                quantity=item.quantity,
            )
            # Atomically decrement stock
            item.product.stock -= item.quantity
            item.product.save(update_fields=['stock'])

        # Execute Payment Strategy
        strategy = PaymentStrategyFactory.get_strategy(payment_method)
        strategy.process_payment(order, payment_data)

        # Clear shopping cart after successful checkout
        CartService.clear_cart(cart)

        return order
