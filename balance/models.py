# balance/models.py

from django.db import models
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # spendable
    product_commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # per-task
    referral_commission = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # referral earnings
    cumulative_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))  # lifetime earned

    @property
    def total_balance(self):
        """
        Total lifetime balance (includes current balance + product commissions + referral commissions)
        Never decreases.
        """
        return self.cumulative_total

    def add_recharge(self, amount):
        """
        Adds recharge to current_balance and cumulative_total
        """
        amount = Decimal(amount)
        self.current_balance += amount
        self.cumulative_total += amount
        self.save()

    

    def add_referral_commission(self, amount):
        """
        Adds referral commission to the referrer WITHOUT affecting cumulative_total.
        """
        amount = Decimal(amount)
        self.referral_commission += amount
        self.save(update_fields=['referral_commission'])


    
    def spend_current_balance(self, amount):
        """
        Deducts from current balance only
        """
        amount = Decimal(amount)
        if self.current_balance >= amount:
            self.current_balance -= amount
            self.save()
            return True
        return False
    
    def add_product_commission(self, amount):
        """
        Adds product commission to the wallet:
        - Updates product_commission
        - Updates cumulative_total (lifetime earnings)
        """
        amount = Decimal(amount)
        self.product_commission += amount
        self.cumulative_total += amount
        self.save(update_fields=['product_commission', 'cumulative_total'])





    
    



# -----------------------------
# RechargeRequest model
# -----------------------------
class RechargeRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"


# -----------------------------
# Voucher model
# -----------------------------
class Voucher(models.Model):
    recharge_request = models.OneToOneField(RechargeRequest, on_delete=models.CASCADE)
    file = models.FileField(upload_to="vouchers/")

    def __str__(self):
        return f"Voucher for {self.recharge_request.user.username} - {self.recharge_request.amount}"


# -----------------------------
# RechargeHistory model
# -----------------------------
class RechargeHistory(models.Model):
    STATUS_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    action_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status} - {self.action_date}"


# -----------------------------
# WithdrawalRequest model
# -----------------------------
class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)  # when admin approves/rejects
    reference = models.CharField(max_length=50, blank=True, null=True)  # optional transaction reference

    def __str__(self):
        return f"{self.user.username} - Withdraw {self.amount} - {self.status}"
