from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, username=None, phone=None, password=None, fund_password=None,
                    referred_by=None, role='user', **extra_fields):
        """
        Creates a user. Regular users require phone + username + fund password.
        Admins/CS/Super Admin require username + password.
        """
        if role == 'user':
            if not phone:
                raise ValueError('Regular users must provide a phone number')
            if not username:
                raise ValueError('Regular users must provide a username')
        else:
            if not username:
                raise ValueError(f'{role} must have a username')

        user = self.model(
            username=username,
            phone=phone,
            fund_password=fund_password,
            referred_by=referred_by,
            role=role,
            **extra_fields
        )
        user.set_password(password)

        # Auto-generate referral code for Admin or user if missing
        if not user.referral_code:
            user.referral_code = str(uuid.uuid4()).replace('-', '')[:8]

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username=username, password=password, role='superadmin', **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('customerservice', 'Customer Service'),
        ('user', 'Regular User'),
    ]

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    fund_password = models.CharField(max_length=128, null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    # Login fields:
    # - Super Admin, Admin, Customer Service -> username
    # - Regular User -> phone (will handle in auth backend)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or self.phone
    
    def set_fund_password(self, raw_password):
        """Hash and store fund password."""
        self.fund_password = make_password(raw_password)
        self.save(update_fields=['fund_password'])

    def check_fund_password(self, raw_password):
        """Verify fund password. Only regular users have fund passwords."""
        if self.role != 'user' or not self.fund_password:
            return False
        return check_password(raw_password, self.fund_password)


class SuperAdminWallet(models.Model):
    address = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label or self.address

