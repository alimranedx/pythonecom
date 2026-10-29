import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from product.models import Product


class DeliverySlot(TimeStampedModel):
    title = models.CharField(max_length=100, help_text="e.g. Morning Slot (08:00 AM - 11:00 AM)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_express = models.BooleanField(default=False, help_text="Marks slot as Express 1-hour delivery")
    extra_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    order_limit_per_day = models.PositiveIntegerField(default=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        express_tag = " [⚡ Express]" if self.is_express else ""
        return f"{self.title}{express_tag}"


class Coupon(TimeStampedModel):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (৳)'),
    ]

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total allowed redemptions across all users")
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid(self, subtotal=None):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is currently inactive."
        if now < self.valid_from or now > self.valid_to:
            return False, "This coupon has expired or is not active yet."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "This coupon has reached its maximum usage limit."
        if subtotal is not None and subtotal < self.min_order_amount:
            return False, f"Minimum order amount of ৳{self.min_order_amount} required to use this coupon."
        return True, "Coupon is valid."

    def calculate_discount(self, subtotal):
        if subtotal <= 0:
            return Decimal('0.00')
        if self.discount_type == 'percent':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
        else:
            discount = min(self.discount_value, subtotal)
        if self.max_discount_amount and discount > self.max_discount_amount:
            discount = self.max_discount_amount
        return discount.quantize(Decimal('0.01'))

    def __str__(self):
        val = f"{int(self.discount_value)}%" if self.discount_type == 'percent' else f"৳{self.discount_value}"
        return f"{self.code} ({val} OFF)"


class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('processing', 'Processing & Packing'),
        ('shipped', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash On Delivery'),
        ('card', 'Credit / Debit Card'),
        ('mobile_banking', 'Mobile Banking (bKash/Nagad)'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cod')

    # Shipping Details Snapshot
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Bangladesh')
    notes = models.TextField(blank=True)

    # Chaldal Delivery Slot & Area Scheduling
    delivery_area = models.CharField(max_length=100, default='Inside Dhaka')
    delivery_date = models.DateField(null=True, blank=True)
    delivery_slot = models.ForeignKey(DeliverySlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    delivery_slot_display = models.CharField(max_length=150, blank=True, default='')

    # Coupon & Discount Snapshot
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    coupon_code = models.CharField(max_length=50, blank=True, default='')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Financial Totals Snapshot
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()})"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_number}"

    @property
    def line_total(self):
        return self.product_price * self.quantity
