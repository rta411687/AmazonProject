from django.conf import settings
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255, default='Product')
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    file = models.ImageField(upload_to='products/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (#{self.id}) - Price: {self.price}"

class UserProductTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='user_tasks')
    task_number = models.PositiveIntegerField(null=True)  # temporarily nullable
    is_completed = models.BooleanField(default=False)
    commissioned = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['user', 'task_number']
