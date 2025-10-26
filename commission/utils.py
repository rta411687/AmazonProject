from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from balance.models import Wallet
from commission.models import Commission, CommissionSetting
from django.contrib.auth import get_user_model

User = get_user_model()


# -----------------------------
# Commission Rates
# -----------------------------
def get_product_commission_rate(user):
    """
    Returns the product commission rate for a user.
    Defaults to 0.00 if not set.
    """
    setting = CommissionSetting.objects.filter(user=user).order_by('-updated_at').first()
    return Decimal(setting.product_rate) if setting else Decimal('0.00')


def get_referral_rate(referrer):
    """
    Returns the referral commission rate for a referrer.
    Defaults to 0.00 if not set.
    """
    if not referrer or referrer.role != 'user':
        return Decimal('0.00')

    setting = CommissionSetting.objects.filter(user=referrer).first()
    return Decimal(setting.referral_rate) if setting else Decimal('0.00')


# -----------------------------
# Product Commission
# -----------------------------
@transaction.atomic
def calculate_product_commission(user, product):
    """
    Calculates product commission WITHOUT updating wallet.
    Returns a Commission instance or None if rate <= 0.
    """
    rate = get_product_commission_rate(user)
    if rate <= 0:
        return None

    amount = (Decimal(product.price) * rate / Decimal('100.00')).quantize(Decimal('0.01'))

    commission = Commission.objects.create(
        user=user,
        product_name=getattr(product, 'file', f'Product {product.id}'),
        amount=amount,
        commission_type='self',
    )
    return commission


# -----------------------------
# Referral Commission
# -----------------------------
@transaction.atomic
def add_referral_commission_atomic(referrer, referred_user, product):
    """
    Adds referral commission to the referrer based on product price.
    Updates wallet and commission record.
    """
    if not referrer or referrer.role != 'user' or referred_user.role != 'user':
        return Decimal('0.00')

    referral_rate = get_referral_rate(referrer)
    if referral_rate <= 0:
        return Decimal('0.00')

    product_name = getattr(product, 'file', f'Product {product.id}')

    # Idempotency
    existing = Commission.objects.filter(
        user=referrer,
        product_name=product_name,
        commission_type='referral',
        triggered_by=referred_user
    ).first()

    if existing:
        return existing.amount

    referral_amount = (Decimal(product.price) * referral_rate / Decimal('100.00')).quantize(Decimal('0.01'))

    wallet, _ = Wallet.objects.get_or_create(user=referrer)
    wallet.referral_commission += referral_amount
    wallet.cumulative_total += referral_amount
    wallet.save(update_fields=['referral_commission', 'cumulative_total'])

    Commission.objects.create(
        user=referrer,
        product_name=product_name,
        commission_type='referral',
        amount=referral_amount,
        triggered_by=referred_user
    )

    return referral_amount


# -----------------------------
# Total Commission
# -----------------------------
def get_total_commission(user):
    """
    Returns the total commission earned by the user (self + referral).
    """
    total = Commission.objects.filter(user=user).aggregate(total=Sum('amount'))['total']
    return total if total else Decimal('0.00')
