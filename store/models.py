from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=(("flat", "Flat"), ("percent", "Percent"))
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0)  # 0 = unlimited
    used_count = models.PositiveIntegerField(default=0)
    def is_valid(self):
        if not self.active:
            return False
        if self.expiry_date < timezone.now():
            return False
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False
        return True
    def __str__(self):
        return self.code
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name
class Product(models.Model):
    category = models.ForeignKey(
        "Category",
        related_name='products',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model_name = models.CharField(max_length=150, blank=True, null=True)
    operating_system = models.CharField(max_length=100, blank=True, null=True)
    storage_capacity = models.CharField(max_length=100, blank=True, null=True)
    screen_size = models.CharField(max_length=100, blank=True, null=True)
    material_composition = models.CharField(max_length=255, blank=True, null=True)
    style = models.CharField(max_length=255, blank=True, null=True)
    fit_type = models.CharField(max_length=255, blank=True, null=True)
    length = models.CharField(max_length=255, blank=True, null=True)
    pattern = models.CharField(max_length=255, blank=True, null=True)
    care_instructions = models.CharField(max_length=255, blank=True, null=True)
    country_of_origin = models.CharField(max_length=255, blank=True, null=True)
    colour = models.CharField(max_length=100, blank=True, null=True)
    hard_disk_size = models.CharField(max_length=100, blank=True, null=True)
    cpu_model = models.CharField(max_length=100, blank=True, null=True)
    ram_size = models.CharField(max_length=100, blank=True, null=True)
    graphics_card = models.CharField(max_length=150, blank=True, null=True)
    graphics_coprocessor = models.CharField(max_length=150, blank=True, null=True)
    about_this_item = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/%Y/%m/%d", blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    sales_count = models.PositiveIntegerField(default=0)
    is_limited_offer = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})
    def __str__(self):
        return self.name
    def average_rating(self):
        avg = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return avg or 0
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="gallery",   # product.gallery.all()
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/gallery/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Image for {self.product.name}"
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='wishlist_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlisted_by', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created']
    def __str__(self):
        return f"{self.user} → {self.product}"
class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[
        (1, '★1'), (2, '★2'), (3, '★3'),
        (4, '★4'), (5, '★5')
    ])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created']
    def __str__(self):
        return f"{self.user.username} review for {self.product.name}"
    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.product.slug])
class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='cart_items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name='cart_items',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('user', 'product')
    def __str__(self):
        return f"{self.user} - {self.product} x {self.quantity}"
    @property
    def total_price(self):
        return self.product.price * self.quantity