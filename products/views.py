from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from balance.models import Wallet
from .models import Product, UserProductTask
from .utils import complete_product_task, get_next_product_for_user
from commission.models import Commission, CommissionSetting

@login_required
def products_view(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)

    # -----------------------------
    # Assign next product
    # -----------------------------
    next_product = get_next_product_for_user(user)
    tasks_done = UserProductTask.objects.filter(user=user, is_completed=True).count()
    next_task_number = tasks_done + 1

    next_task_allowed = True
    block_reason = None

    if tasks_done >= 60:  # fallback daily limit
        next_task_allowed = False
        block_reason = "Daily task limit reached."

    all_products_completed = False
    if not next_product:
        all_products_completed = True
        next_task_allowed = False
        block_reason = "You have finished all products or stopped by StopPoint."

    # Check balance
    if next_product and wallet.current_balance < next_product.price:
        can_proceed = False
        if not block_reason:
            block_reason = "Insufficient balance."
    else:
        can_proceed = next_task_allowed and next_product and (wallet.current_balance >= next_product.price)

    # -----------------------------
    # Handle task completion
    # -----------------------------
    if request.method == "POST" and "next_product" in request.POST:
        if not can_proceed:
            messages.warning(request, block_reason or "Cannot proceed.")
            return redirect("products")

        result = complete_product_task(user, next_product)
        if result.get("warning"):
            messages.warning(request, result.get("warning"))
            return redirect("products")
        return redirect("products")

    # -----------------------------
    # Update wallet totals
    # -----------------------------
    wallet.product_commission = Commission.objects.filter(
        user=user, commission_type='self'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    wallet.referral_commission = Commission.objects.filter(
        user=user, commission_type='referral'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    wallet.cumulative_total = wallet.product_commission + wallet.referral_commission
    wallet.save(update_fields=['product_commission', 'referral_commission', 'cumulative_total'])

    # -----------------------------
    # Today's commissions
    # -----------------------------
    today = timezone.now().date()
    today_product_commission = Commission.objects.filter(
        user=user, commission_type='self', created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_referral_commission = Commission.objects.filter(
        user=user, commission_type='referral', created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "product": next_product,
        "display_task_number": next_task_number,
        "next_task_allowed": next_task_allowed,
        "block_reason": block_reason,
        "daily_limit": 60,
        "can_proceed": can_proceed,
        "all_products_completed": all_products_completed,

        # Wallet
        "current_balance": wallet.current_balance,
        "product_commission": wallet.product_commission,
        "referral_commission": wallet.referral_commission,
        "total_balance": wallet.cumulative_total,

        # Today's commissions
        "today_product_commission": today_product_commission,
        "today_referral_commission": today_referral_commission,
        "today_commission": today_product_commission + today_referral_commission,
    }

    return render(request, "products/products.html", context)
