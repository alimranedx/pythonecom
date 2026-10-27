from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel
from product.models import Product


class Cart(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)

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
    def shipping_cost(self):
        # Free delivery if subtotal > $50, else flat $5
        if self.subtotal >= Decimal('50.00') or self.subtotal == Decimal('0.00'):
            return Decimal('0.00')
        return Decimal('5.00')

    @property
    def grand_total(self):
        return self.subtotal + self.shipping_cost


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
