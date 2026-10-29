from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from product.models import Product


class Cart(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    coupon = models.ForeignKey('orders.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')

    FREE_SHIPPING_THRESHOLD = Decimal('500.00')
    STANDARD_SHIPPING_FEE = Decimal('49.00')

    def __str__(self):
        owner = self.user.username if self.user else f"Guest ({self.session_key})"
        return f"Cart #{self.pk} - {owner}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def discount_amount(self):
        if self.coupon:
            valid, _ = self.coupon.is_valid(self.subtotal)
            if valid:
                return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def shipping_cost(self):
        if self.subtotal == Decimal('0.00') or self.subtotal >= self.FREE_SHIPPING_THRESHOLD:
            return Decimal('0.00')
        return self.STANDARD_SHIPPING_FEE

    @property
    def grand_total(self):
        total = self.subtotal - self.discount_amount + self.shipping_cost
        return max(Decimal('0.00'), total)

    @property
    def amount_to_free_shipping(self):
        if self.subtotal >= self.FREE_SHIPPING_THRESHOLD or self.subtotal == Decimal('0.00'):
            return Decimal('0.00')
        return self.FREE_SHIPPING_THRESHOLD - self.subtotal

    @property
    def free_shipping_progress_percent(self):
        if self.subtotal >= self.FREE_SHIPPING_THRESHOLD:
            return 100
        if self.subtotal == Decimal('0.00'):
            return 0
        return min(100, int((self.subtotal / self.FREE_SHIPPING_THRESHOLD) * 100))


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.product.effective_price * self.quantity
