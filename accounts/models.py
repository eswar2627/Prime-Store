from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.full_name} - {self.city}"
class DeviceToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='device_tokens',
        on_delete=models.CASCADE
    )
    token = models.CharField(max_length=300, unique=True)
    device_type = models.CharField(
        max_length=20,
        choices=(('android', 'Android'), ('ios', 'iOS')),
        default='android'
    )
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user} - {self.device_type}"