from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from cart.models import Cart
from cart.services import CartService
from product.models import Product
from .models import Order, OrderItem, DeliverySlot, Coupon
from .strategies import PaymentStrategyFactory


class OrderService:
    """
    Business logic layer for Order Placement, Checkout, Delivery Slots, and Inventory Updates.
    Employs the Unit of Work pattern through atomic database transactions and row-level locks.
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
        1. Validates cart non-empty and quantities positive.
        2. Locks product rows using SELECT FOR UPDATE to prevent race conditions and overselling.
        3. Validates stock and product active status.
        4. Calculates server-side subtotal and shipping fees (never trusting client inputs).
        5. Validates coupons with row lock and per-customer abuse checks.
        6. Creates the immutable Order and OrderItems snapshots.
        7. Decrements inventory atomically.
        8. Executes Payment Strategy.
        9. Empties the shopping cart.
        """
        items = list(cart.items.select_related('product').all())
        if not items:
            raise ValidationError("Cannot checkout with an empty shopping cart.")

        # 1. Row-level Lock on Products to prevent race conditions & overselling
        product_ids = [item.product_id for item in items]
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        # 2. Strict Stock & Product Status Validation
        for item in items:
            product = locked_products.get(item.product_id)
            if not product or not product.is_active:
                raise ValidationError(f"The item '{item.product.name}' is currently unavailable.")
            if item.quantity <= 0:
                raise ValidationError(f"Invalid quantity for item '{item.product.name}'.")
            if product.stock < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock}, requested: {item.quantity}."
                )

        # 3. Parse Delivery Area & Slot
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

        # 4. Calculate Subtotal from Database Prices (Tamper-Proof)
        subtotal = sum(
            (locked_products[item.product_id].effective_price * item.quantity)
            for item in items
        ).quantize(Decimal('0.01'))

        # Calculate shipping fee
        if subtotal >= Cart.FREE_SHIPPING_THRESHOLD and (not delivery_slot or not delivery_slot.is_express):
            shipping_fee = Decimal('0.00')
        elif delivery_area == 'Outside Dhaka':
            shipping_fee = Decimal('99.00')
        else:
            shipping_fee = Decimal('49.00')

        shipping_fee = (shipping_fee + extra_slot_fee).quantize(Decimal('0.01'))

        # 5. Coupon Handling with Row-Level Lock & Per-User Abuse Protection
        coupon = None
        coupon_code = ''
        discount_amount = Decimal('0.00')

        if cart.coupon_id:
            try:
                coupon = Coupon.objects.select_for_update().get(pk=cart.coupon_id)
                valid, reason = coupon.is_valid(subtotal)
                if not valid:
                    coupon = None
                else:
                    # Per-user reuse prevention for authenticated customers
                    if user and user.is_authenticated:
                        already_used = Order.objects.filter(
                            user=user,
                            coupon=coupon,
                        ).exclude(status='cancelled').exists()
                        if already_used:
                            raise ValidationError(f"You have already redeemed the coupon '{coupon.code}'.")

                    coupon_code = coupon.code
                    discount_amount = coupon.calculate_discount(subtotal)
                    # Atomically update usage count
                    Coupon.objects.filter(pk=coupon.pk).update(used_count=F('used_count') + 1)
            except Coupon.DoesNotExist:
                coupon = None

        # Sanitize total: ensure non-negative and properly quantized
        discount_amount = min(discount_amount, subtotal).quantize(Decimal('0.01'))
        total_amount = max(Decimal('0.00'), subtotal - discount_amount + shipping_fee).quantize(Decimal('0.01'))
        payment_method = shipping_data.get('payment_method', 'cod')

        # 6. Create Order Snapshot
        order = Order.objects.create(
            user=user if (user and user.is_authenticated) else None,
            full_name=shipping_data.get('full_name', '').strip()[:150],
            email=shipping_data.get('email', '').strip()[:150],
            phone=shipping_data.get('phone', '').strip()[:30],
            street_address=shipping_data.get('street_address', '').strip()[:255],
            city=shipping_data.get('city', '').strip()[:100],
            postal_code=shipping_data.get('postal_code', '').strip()[:20],
            country=shipping_data.get('country', 'Bangladesh')[:100],
            notes=shipping_data.get('notes', '').strip()[:500],
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

        # 7. Create Order Items & Atomically Decrement Inventory on Locked Rows
        for item in items:
            product = locked_products[item.product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.effective_price,
                quantity=item.quantity,
            )
            product.stock -= item.quantity
            product.save(update_fields=['stock'])

        # 8. Execute Payment Strategy
        strategy = PaymentStrategyFactory.get_strategy(payment_method)
        strategy.process_payment(order, payment_data)

        # 9. Clear shopping cart after successful order creation
        CartService.clear_cart(cart)

        return order
