from decimal import Decimal
from django.db import transaction
from balance.models import Wallet
from .models import Commission, CommissionSetting

def get_commission_rates(user):
    """
    Fetch the latest dynamic commission rates for the user.
    """
    setting = CommissionSetting.objects.filter(user=user).order_by("-updated_at").first()
    return {
        "product_rate": Decimal(setting.product_rate) if setting else Decimal("0.00"),
        "referral_rate": Decimal(setting.referral_rate) if setting else Decimal("0.00"),
    }

@transaction.atomic
def process_product_completion(user, product):
    """
    Handles product completion:
    - Deduct product price
    - Add product commission to user
    - Add referral commission to referrer (if any)
    - Update wallet totals
    - Create Commission records
    Returns dict of commission amounts
    """
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if wallet.current_balance < product.price:
        return {"warning": f"Insufficient balance for Product {product.id}"}

    # Deduct product price
    wallet.current_balance -= product.price

    # Calculate product commission
    rates = get_commission_rates(user)
    product_commission_amount = (Decimal(product.price) * rates['product_rate'] / Decimal("100.00")).quantize(Decimal("0.01"))
    wallet.product_commission += product_commission_amount
    wallet.cumulative_total += product_commission_amount

    # Record product commission
    Commission.objects.create(
        user=user,
        product_name=f"Product {product.id}",
        amount=product_commission_amount,
        commission_type='self',
        triggered_by=user,
    )

    # Referral commission
    referral_amount = Decimal("0.00")
    referrer = getattr(user, "referred_by", None)
    if referrer:
        # Compute referral amount using product price to match other helpers
        referral_amount = (Decimal(product.price) * rates['referral_rate'] / Decimal("100.00")).quantize(Decimal("0.01"))

        # Idempotency: if referral commission already recorded for this referrer + product + triggered_by, skip wallet update
        existing = Commission.objects.filter(
            user=referrer,
            product_name=f"Product {product.id}",
            commission_type='referral',
            triggered_by=user
        ).first()

        if existing:
            referral_amount = existing.amount
        else:
            ref_wallet, _ = Wallet.objects.get_or_create(user=referrer)
            ref_wallet.referral_commission += referral_amount
            ref_wallet.cumulative_total += referral_amount
            ref_wallet.save(update_fields=['referral_commission','cumulative_total'])

            # Record referral commission
            Commission.objects.create(
                user=referrer,
                product_name=f"Product {product.id}",
                amount=referral_amount,
                commission_type='referral',
                triggered_by=user,
            )

    # Save user's wallet
    wallet.save(update_fields=['current_balance','product_commission','referral_commission','cumulative_total'])

    return {
        "product_commission": product_commission_amount,
        "referral_commission": referral_amount,
        "warning": None
    }
