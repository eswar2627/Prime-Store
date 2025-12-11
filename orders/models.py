from django.db import models
from django.conf import settings
from store.models import Product
from django.utils import timezone
import random
import string

class Order(models.Model):
    STATUS_CHOICES = [
        ("PLACED", "Order Placed"),
        ("PACKED", "Packed"),
        ("SHIPPED", "Shipped"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLACED"
    )
    tracking_number = models.CharField(
        max_length=20, blank=True, null=True, unique=True
    )
    def generate_tracking_number(self):
        return "PS" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    billing_name = models.CharField(max_length=250, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon',
        related_name='orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    class Meta:
        ordering = ['-created']
    def __str__(self):
        return f'Order {self.id}'
    def get_total_before_discount(self):
        return sum(item.get_cost() for item in self.items.all())
    def get_total_discount(self):
        return self.discount
    def get_total_cost(self):
        return self.get_total_before_discount() - self.discount
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=(
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.code
    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f'{self.product.name} ({self.quantity})'
    def get_cost(self):
        return self.price * self.quantity