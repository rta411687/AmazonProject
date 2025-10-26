from decimal import Decimal
from django.db import transaction
from balance.models import Wallet, RechargeRequest, Voucher, RechargeHistory

# -----------------------------
# Wallet Utilities
# -----------------------------

def get_wallet(user):
    """Get or create wallet for a user."""
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet

def get_wallet_balance(user):
    """
    Returns total dynamic balance: current + product + referral
    """
    wallet = get_wallet(user)
    return wallet.current_balance + wallet.product_commission + wallet.referral_commission

@transaction.atomic
def update_wallet(user, amount, action="add", balance_type="current"):
    """
    Generic wallet update
    balance_type: current, product_commission, referral_commission
    action: add or subtract
    """
    wallet = get_wallet(user)
    amount = Decimal(amount)

    if balance_type == "current":
        if action == "add":
            wallet.current_balance += amount
            wallet.cumulative_total += amount
        elif action == "subtract":
            if wallet.current_balance >= amount:
                wallet.current_balance -= amount
            else:
                return False
    elif balance_type == "product_commission":
        if action == "add":
            wallet.product_commission += amount
            wallet.cumulative_total += amount
        elif action == "subtract":
            if wallet.product_commission >= amount:
                wallet.product_commission -= amount
            else:
                return False
    elif balance_type == "referral_commission":
        if action == "add":
            wallet.referral_commission += amount
            wallet.cumulative_total += amount
        elif action == "subtract":
            if wallet.referral_commission >= amount:
                wallet.referral_commission -= amount
            else:
                return False
    else:
        return False

    wallet.save(update_fields=["current_balance", "product_commission", "referral_commission", "cumulative_total"])
    return wallet

# -----------------------------
# Recharge Utilities
# -----------------------------

@transaction.atomic
def create_recharge_request(user, amount):
    """
    Create a pending recharge request
    """
    amount = Decimal(amount)
    recharge = RechargeRequest.objects.create(user=user, amount=amount)
    return recharge

@transaction.atomic
def approve_recharge(recharge_request):
    """
    Approve recharge request:
    - update wallet current_balance ONLY
    - mark recharge approved
    - create RechargeHistory
    """
    if recharge_request.status != "pending":
        raise ValueError("Recharge already processed")

    # Only current_balance updated, NO referral commission
    update_wallet(recharge_request.user, recharge_request.amount, action="add", balance_type="current")

    recharge_request.status = "approved"
    recharge_request.save()

    RechargeHistory.objects.create(
        user=recharge_request.user,
        amount=recharge_request.amount,
        status="approved"
    )
    return recharge_request

@transaction.atomic
def reject_recharge(recharge_request):
    """
    Reject recharge request:
    - mark rejected
    - log in history
    """
    if recharge_request.status != "pending":
        raise ValueError("Recharge already processed")

    recharge_request.status = "rejected"
    recharge_request.save()

    RechargeHistory.objects.create(
        user=recharge_request.user,
        amount=recharge_request.amount,
        status="rejected"
    )
    return recharge_request

# -----------------------------
# Voucher Utilities
# -----------------------------

@transaction.atomic
def upload_voucher(recharge_request, file):
    """
    Upload or update voucher for recharge
    """
    voucher, _ = Voucher.objects.get_or_create(recharge_request=recharge_request)
    voucher.file = file
    voucher.save()
    return voucher
