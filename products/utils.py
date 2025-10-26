from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from balance.models import Wallet
from .models import UserProductTask, Product
from commission.models import Commission, CommissionSetting
from stoppoints.utils import is_task_allowed, get_next_pending_stoppoint


# -----------------------------
# Daily Task Limit
# -----------------------------
def get_daily_task_limit(user):
    """
    Returns the daily task limit for a user.
    Falls back to CommissionSetting.daily_task_limit or 60.
    """
    try:
        setting = CommissionSetting.objects.filter(user=user).order_by('-updated_at').first()
        if setting and getattr(setting, 'daily_task_limit', None) is not None:
            return int(setting.daily_task_limit)
    except Exception:
        pass
    return 60


# -----------------------------
# Get Next Product for User
# -----------------------------
def get_next_product_for_user(user):
    """
    Assigns the next available product for the user.
    Respects daily limit, StopPoints, and already assigned products.
    """
    tasks_done = UserProductTask.objects.filter(user=user).count()
    daily_limit = get_daily_task_limit(user)
    if tasks_done >= daily_limit:
        return None

    next_task_number = tasks_done + 1

    # StopPoint check
    allowed, reason = is_task_allowed(user, next_task_number)
    if not allowed:
        return None  # StopPoint blocks next task

    # Find next unassigned product
    assigned_ids = UserProductTask.objects.filter(user=user).values_list('product_id', flat=True)
    next_product = Product.objects.filter(is_active=True).exclude(id__in=assigned_ids).first()
    if not next_product:
        return None

    # Assign task
    UserProductTask.objects.create(user=user, product=next_product, task_number=next_task_number)
    return next_product


# -----------------------------
# Complete Product Task
# -----------------------------
def complete_product_task(user, product):
    """
    Complete a product task for the user.
    Applies product and referral commissions.
    """
    task = UserProductTask.objects.filter(user=user, product=product, is_completed=False).first()
    if not task:
        return {"warning": "Task already completed or does not exist."}

    # StopPoint check
    allowed, reason = is_task_allowed(user, task.task_number)
    if not allowed:
        return {"warning": reason}

    wallet, _ = Wallet.objects.get_or_create(user=user)
    if wallet.current_balance < product.price:
        return {"warning": "Insufficient balance."}

    user_commission_setting, _ = CommissionSetting.objects.get_or_create(user=user)

    # Referrer info
    referrer = getattr(user, "referred_by", None)
    referrer_wallet = None
    referrer_commission_setting = None
    referral_amount = Decimal("0.00")

    if referrer and referrer.role == 'user':
        referrer_wallet, _ = Wallet.objects.get_or_create(user=referrer)
        referrer_commission_setting, _ = CommissionSetting.objects.get_or_create(user=referrer)

    with transaction.atomic():
        # Deduct product price
        wallet.current_balance -= product.price

        # Product commission
        product_commission = (product.price * user_commission_setting.product_rate / 100).quantize(Decimal("0.01"))
        wallet.product_commission += product_commission
        wallet.cumulative_total += product_commission
        wallet.save(update_fields=['current_balance', 'product_commission', 'cumulative_total'])

        # Record product commission
        Commission.objects.create(
            user=user,
            product_name=f"Product {product.id}",
            commission_type='self',
            amount=product_commission,
            triggered_by=user
        )

        # Mark task completed
        task.is_completed = True
        task.save(update_fields=['is_completed'])

        # Referral commission
        if referrer_wallet and referrer_commission_setting:
            existing = Commission.objects.filter(
                user=referrer,
                product_name=f"Product {product.id}",
                commission_type='referral',
                triggered_by=user
            ).first()

            if existing:
                referral_amount = existing.amount
            else:
                referral_amount = (product.price * referrer_commission_setting.referral_rate / 100).quantize(Decimal("0.01"))
                referrer_wallet.referral_commission += referral_amount
                referrer_wallet.cumulative_total += referral_amount
                referrer_wallet.save(update_fields=['referral_commission', 'cumulative_total'])

                Commission.objects.create(
                    user=referrer,
                    product_name=f"Product {product.id}",
                    commission_type='referral',
                    amount=referral_amount,
                    triggered_by=user
                )

    return {
        "warning": None,
        "product_commission": product_commission,
        "referral_commission": referral_amount
    }
