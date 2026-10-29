from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from cart.services import CartService
from .models import Order, OrderItem, DeliverySlot
from .strategies import PaymentStrategyFactory


class OrderService:
    """
    Business logic layer for Order Placement, Checkout, Delivery Slots, and Inventory Updates.
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
        2. Calculates shipping fees based on area (Dhaka vs Outside Dhaka) and delivery slot.
        3. Applies coupons and records discount savings.
        4. Decrements product inventory.
        5. Snapshots customer details and product pricing.
        6. Processes payment via Strategy Pattern.
        7. Empties the shopping cart.
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

        # Parse delivery slot & area
        delivery_area = shipping_data.get('delivery_area', 'Inside Dhaka')
        delivery_date_str = shipping_data.get('delivery_date')
        delivery_date = None
        if delivery_date_str:
            try:
                delivery_date = datetime.strptime(str(delivery_date_str).strip(), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                delivery_date = None

        delivery_slot = None
        slot_id = shipping_data.get('delivery_slot')
        delivery_slot_display = ''
        extra_slot_fee = Decimal('0.00')

        if slot_id:
            try:
                delivery_slot = DeliverySlot.objects.filter(pk=slot_id, is_active=True).first()
                if delivery_slot:
                    delivery_slot_display = str(delivery_slot)
                    extra_slot_fee = delivery_slot.extra_fee
            except Exception:
                pass

        # Calculate shipping fee
        subtotal = cart.subtotal
        if subtotal >= Cart.FREE_SHIPPING_THRESHOLD and (not delivery_slot or not delivery_slot.is_express):
            shipping_fee = Decimal('0.00')
        elif delivery_area == 'Outside Dhaka':
            shipping_fee = Decimal('99.00')
        else:
            shipping_fee = Decimal('49.00')

        shipping_fee += extra_slot_fee

        # Coupon handling
        coupon = cart.coupon
        discount_amount = cart.discount_amount
        coupon_code = ''
        if coupon:
            valid, _ = coupon.is_valid(subtotal)
            if valid:
                coupon_code = coupon.code
                coupon.used_count += 1
                coupon.save(update_fields=['used_count'])
            else:
                coupon = None
                discount_amount = Decimal('0.00')

        total_amount = max(Decimal('0.00'), subtotal - discount_amount + shipping_fee)
        payment_method = shipping_data.get('payment_method', 'cod')

        # Create Order
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
            delivery_area=delivery_area,
            delivery_date=delivery_date,
            delivery_slot=delivery_slot,
            delivery_slot_display=delivery_slot_display,
            coupon=coupon,
            coupon_code=coupon_code,
            discount_amount=discount_amount,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
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
