
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

CRYPTO_NETWORK_CHOICES = [
    ('TRX-20', 'TRX-20 (TRON)'),
    ('ERC-20', 'ERC-20 (Ethereum)'),
    ('BEP-20', 'BEP-20 (Binance Smart Chain)'),
    ('Polygon', 'Polygon (MATIC)'),
    ('Solana', 'Solana (SOL)'),
    ('Avalanche', 'Avalanche (AVAX)'),
    ('Fantom', 'Fantom (FTM)'),
    ('Arbitrum', 'Arbitrum (ARB)'),
    ('Optimism', 'Optimism (OP)'),
    ('Cardano', 'Cardano (ADA)'),
]

class UserWalletAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, unique=True)
    network = models.CharField(max_length=20, choices=CRYPTO_NETWORK_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Wallet Address"
        verbose_name_plural = "User Wallet Addresses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.network} | {self.address}"
    


class WalletHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_history')
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=20, choices=CRYPTO_NETWORK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='wallet_changed_by')

    class Meta:
        verbose_name = "Wallet History"
        verbose_name_plural = "Wallet Histories"
        ordering = ['-created_at']
        unique_together = ('address', 'network')

    def __str__(self):
        return f"{self.user.username} | {self.network} | {self.address}"

class UserWithdrawal(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=8)  # safe for crypto
    network = models.CharField(max_length=20, choices=CRYPTO_NETWORK_CHOICES)
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0.0")) 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # track approval updates

    class Meta:
        verbose_name = "User Withdrawal"
        verbose_name_plural = "User Withdrawals"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.amount} {self.network} | {self.status}"
