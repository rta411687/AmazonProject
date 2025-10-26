# balance/views.py
from decimal import Decimal
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.utils import timezone

from balance.models import Wallet, RechargeRequest, RechargeHistory, Voucher
from balance.services import (
    get_wallet_balance,
    create_recharge_request,
    update_wallet,
    upload_voucher,
    approve_recharge,
    reject_recharge,
)
from accounts.models import SuperAdminWallet
from commission.models import Commission

# -----------------------------
# Admin check
# -----------------------------
def is_admin(user):
    return user.is_authenticated and user.role in ["admin", "superadmin"]

# -----------------------------
# Wallet Dashboard
# -----------------------------
# -----------------------------
# Wallet Dashboard
# -----------------------------
@login_required
def wallet_dashboard(request):
    from django.db.models import Sum
    from django.utils import timezone
    from commission.models import Commission
    from decimal import Decimal

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    pending_recharge = RechargeRequest.objects.filter(user=request.user, status="pending").first()
    history = RechargeHistory.objects.filter(user=request.user).order_by("-action_date")

    # -----------------------------
    # Today's Commissions
    # -----------------------------
    today = timezone.now().date()

    # Today's product commission
    today_product_commission = Commission.objects.filter(
        user=request.user,
        commission_type='self',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Today's referral commission
    today_referral_commission = Commission.objects.filter(
        user=request.user,
        commission_type='referral',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Combined
    today_commission = today_product_commission + today_referral_commission

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "wallet": wallet,  # full wallet object
        "recharge_amounts": [500, 1000, 1500, 2000, 3000, 4000, 5000, 10000],
        "pending_recharge": pending_recharge,
        "history": history,
        "today_product_commission": today_product_commission,
        "today_referral_commission": today_referral_commission,
        "today_commission": today_commission,
    }
    return render(request, "balance/wallet_dashboard.html", context)




# -----------------------------
# Recharge Amount Selection
# -----------------------------
@login_required
def recharge_amount(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        if not amount:
            messages.error(request, "No amount specified.")
            return redirect("balance:wallet_dashboard")
        try:
            amount = Decimal(amount)
        except:
            messages.error(request, "Invalid amount.")
            return redirect("balance:wallet_dashboard")

        recharge = create_recharge_request(request.user, amount)
        return redirect("balance:upload_voucher", recharge_id=recharge.id)
    return redirect("balance:wallet_dashboard")


# -----------------------------
# Upload Voucher
# -----------------------------
@login_required
def upload_voucher_view(request, recharge_id):
    recharge_request = get_object_or_404(RechargeRequest, id=recharge_id, user=request.user)
    voucher = Voucher.objects.filter(recharge_request=recharge_request).first()

    if request.method == "POST" and request.FILES.get("voucher_file"):
        file = request.FILES["voucher_file"]
        upload_voucher(recharge_request, file)
        messages.success(request, "Voucher uploaded successfully. Await admin approval.")
        return redirect("balance:upload_voucher", recharge_id=recharge_request.id)

    superadmin_wallet = SuperAdminWallet.objects.first()
    context = {
        "recharge_request": recharge_request,
        "voucher": voucher,
        "superadmin_wallet": superadmin_wallet,
    }
    return render(request, "balance/upload_voucher.html", context)


# -----------------------------
# Approve Voucher (Admin)
# -----------------------------
@login_required
@user_passes_test(is_admin)
def approve_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    recharge_request = voucher.recharge_request
    user = recharge_request.user

    if request.method == "POST":
        approve_recharge(recharge_request)

        # Delete voucher file safely
        if voucher.file and os.path.isfile(voucher.file.path):
            os.remove(voucher.file.path)
        voucher.delete()

        wallet = Wallet.objects.get(user=user)
        messages.success(request, f"Voucher for {user.username} approved. Total balance: {wallet.total_balance}")

    return redirect("accounts:admin_dashboard")


# -----------------------------
# Reject Voucher (Admin)
# -----------------------------
@login_required
@user_passes_test(is_admin)
def reject_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    recharge_request = voucher.recharge_request
    user = recharge_request.user

    if request.method == "POST":
        reject_recharge(recharge_request)

        if voucher.file and os.path.isfile(voucher.file.path):
            os.remove(voucher.file.path)
        voucher.delete()

        messages.info(request, f"Voucher for {user.username} has been rejected.")

    return redirect("accounts:admin_dashboard")


# -----------------------------
# Update Recharge Amount (Admin)
# -----------------------------
@login_required
@user_passes_test(is_admin)
def update_recharge_amount(request, recharge_id):
    recharge = get_object_or_404(RechargeRequest, id=recharge_id)
    if request.method == "POST":
        amount = request.POST.get("amount")
        if amount:
            try:
                recharge.amount = Decimal(amount)
                recharge.save()
                messages.success(request, f"Recharge amount updated to {recharge.amount}")
            except:
                messages.error(request, "Invalid amount")
    return redirect("accounts:admin_dashboard")
