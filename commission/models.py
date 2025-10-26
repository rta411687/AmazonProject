from django.db import models
from django.conf import settings
from decimal import Decimal

User = settings.AUTH_USER_MODEL

# -----------------------------
# Commission Settings
# -----------------------------
class CommissionSetting(models.Model):
    """
    Admin sets product and referral commission rates per user.
    Each user can have only one setting row.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="commission_setting")
    product_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100%
    referral_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # 0-100%
    daily_task_limit = models.PositiveIntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commission Setting"
        verbose_name_plural = "Commission Settings"

    def __str__(self):
        return f"{self.user.username} - Product Commission: {self.product_rate}% | Referral Commission: {self.referral_rate}%"


# -----------------------------
# Commission Records
# -----------------------------
class Commission(models.Model):
    COMMISSION_TYPES = (
        ('self', 'Self Earned'),
        ('referral', 'Referral Earned'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commissions")
    product_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    commission_type = models.CharField(max_length=10, choices=COMMISSION_TYPES, default='self')
    triggered_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='triggered_commissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commission"
        verbose_name_plural = "Commissions"

    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Commission: {self.amount:.2f} ({self.commission_type})"
