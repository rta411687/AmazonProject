from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wallet.models import UserWalletAddress, CRYPTO_NETWORK_CHOICES
from products.models import UserProductTask
from products.utils import get_daily_task_limit

@login_required
def bind_user_wallet_view(request):
    user = request.user
    wallet = UserWalletAddress.objects.filter(user=user).first()

    # 1️⃣ Check if all tasks are completed
    completed_tasks_count = UserProductTask.objects.filter(user=user, is_completed=True).count()
    if completed_tasks_count < get_daily_task_limit(user):
        messages.error(
            request,
            f"You must complete all {get_daily_task_limit(user)} tasks before binding your wallet. Completed: {completed_tasks_count}"
        )
        return render(request, "wallet/bind_wallet.html", {
            "wallet": wallet,
            "networks": CRYPTO_NETWORK_CHOICES,
            "tasks_completed": completed_tasks_count
        })

    # 2️⃣ If wallet already exists, users cannot change it
    if wallet:
        messages.info(
            request,
            f"Wallet already bound: {wallet.address} on {wallet.network}. "
            "Contact Customer Service for any updates."
        )
        return render(request, "wallet/bind_wallet.html", {
            "wallet": wallet,
            "networks": CRYPTO_NETWORK_CHOICES,
            "tasks_completed": completed_tasks_count
        })

    # 3️⃣ Handle wallet binding form submission
    if request.method == "POST" and not wallet:
        address = request.POST.get("address", "").strip()
        network = request.POST.get("network", "")

        # Input validation
        if not address:
            messages.error(request, "Wallet address is required.")
        elif network not in dict(CRYPTO_NETWORK_CHOICES):
            messages.error(request, "Invalid network selected.")
        elif UserWalletAddress.objects.filter(address=address).exists():
            messages.error(request, "This wallet address is already linked to another account.")
        else:
            # Create the wallet
            UserWalletAddress.objects.create(user=user, address=address, network=network)
            messages.success(request, "Wallet bound successfully. Contact Customer Service for updates.")
            return redirect("wallet:bind_user_wallet")

    # 4️⃣ Render template
    return render(request, "wallet/bind_wallet.html", {
        "wallet": wallet,
        "networks": CRYPTO_NETWORK_CHOICES,
        "tasks_completed": completed_tasks_count
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wallet.models import UserWalletAddress, CRYPTO_NETWORK_CHOICES
from balance.models import Wallet  # assuming you track user balance here
from decimal import Decimal






from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from wallet.models import UserWalletAddress, WalletHistory
from products.models import UserProductTask
from products.utils import get_daily_task_limit

def bind_user_wallet_view(request):
    user = request.user
    wallet = UserWalletAddress.objects.filter(user=user).first()
    completed_tasks_count = UserProductTask.objects.filter(user=user, is_completed=True).count()

    # Determine if user can bind wallet
    can_bind_wallet = (completed_tasks_count >= get_daily_task_limit(user)) and (wallet is None)

    # Handle wallet binding form submission
    if request.method == "POST" and can_bind_wallet:
        address = request.POST.get("address", "").strip()

        # Input validation
        if not address:
            messages.error(request, "Wallet address is required.")
        elif UserWalletAddress.objects.filter(address=address).exists():
            messages.error(request, "This wallet address is already linked to another user.")
        else:
            # Check WalletHistory for previous usage by other users
            previous_usage = WalletHistory.objects.filter(address=address).exclude(user=user).first()
            if previous_usage:
                print(f"WARNING: Address {address} was previously used by {previous_usage.user.username}")

            # Bind wallet
            wallet = UserWalletAddress.objects.create(user=user, address=address, network="N/A")  # Network only for withdraw
            WalletHistory.objects.create(user=user, address=address, network="N/A")
            messages.success(request, "Wallet bound successfully. Contact Customer Service for updates.")
            return redirect("wallet:bind_user_wallet")

    return render(request, "wallet/bind_wallet.html", {
        "wallet": wallet,
        "tasks_completed": completed_tasks_count,
        "daily_limit": get_daily_task_limit(user),
        "can_bind_wallet": can_bind_wallet,
    })
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from wallet.models import UserWalletAddress
from balance.utils import get_wallet_balance




from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from wallet.models import UserWalletAddress, UserWithdrawal
from balance.utils import get_wallet_balance, update_wallet_balance
from products.models import UserProductTask

MIN_LEFTOVER_CENTS = 0.05  # Minimum balance to leave after withdrawal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from wallet.models import UserWalletAddress, UserWithdrawal
from balance.utils import get_wallet_balance, update_wallet_balance
from products.models import UserProductTask


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from .models import UserWalletAddress, UserWithdrawal
from balance.utils import get_wallet_balance, update_wallet_balance  # adjust import if needed
from accounts.models import CustomUser

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from wallet.models import UserWalletAddress, UserWithdrawal
from balance.utils import get_wallet_balance, update_wallet_balance
from products.models import UserProductTask  # if you reset tasks after withdraw

MIN_LEFTOVER_CENTS = 0.05  # leave at least 5 cents

@login_required
def withdraw_view(request):
    user = request.user
    wallet = UserWalletAddress.objects.filter(user=user).first()
    balance = get_wallet_balance(user)

    # 1️⃣ Wallet must be bound
    if not wallet:
        messages.error(request, "You must bind your wallet before making a withdrawal.")
        return redirect("wallet:bind_user_wallet")

    if request.method == "POST":
        network = request.POST.get("network")
        fund_password = request.POST.get("fund_password")

        # 2a️⃣ Validate fund password
        if not user.check_fund_password(fund_password):
            messages.error(request, "Invalid fund password.")
            return redirect("wallet:withdraw")

        # 2b️⃣ Ensure a network was selected
        if not network:
            messages.error(request, "Please select a network protocol.")
            return redirect("wallet:withdraw")

        # 2c️⃣ Check balance is sufficient
        if balance <= MIN_LEFTOVER_CENTS:
            messages.error(
                request,
                f"Insufficient balance. Minimum {MIN_LEFTOVER_CENTS} must remain."
            )
            return redirect("wallet:withdraw")

        # 2d️⃣ Calculate withdrawable amount
        withdraw_amount = round(balance - MIN_LEFTOVER_CENTS, 8)

        # 2e️⃣ Deduct balance immediately
        update_wallet_balance(user, withdraw_amount, action="subtract")

        # 2f️⃣ Log withdrawal as PENDING
        UserWithdrawal.objects.create(
            user=user,
            amount=withdraw_amount,
            network=network,
            status="PENDING"
        )

        # 2g️⃣ Notify user
        messages.success(
            request,
            f"Withdrawal request of {withdraw_amount} {network} submitted successfully. Admin will approve shortly."
        )
        return redirect("wallet:bind_user_wallet")

    # 3️⃣ Render form with available networks
    #networks = [n[0] for n in UserWalletAddress._meta.get_field('network').choices]
    networks = UserWalletAddress._meta.get_field('network').choices


    return render(request, "wallet/withdraw.html", {
        "wallet": wallet,
        "balance": balance,
        "networks": networks,
        "min_leftover": MIN_LEFTOVER_CENTS
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import UserWithdrawal, UserWalletAddress

# Only admin can approve/reject
def is_admin(user):
    return user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def approve_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(UserWithdrawal, id=withdrawal_id, status="PENDING")
    withdrawal.status = "APPROVED"
    withdrawal.save()
    messages.success(request, f"Withdrawal of {withdrawal.amount} approved.")
    return redirect('accounts:admin_dashboard')

@login_required
@user_passes_test(is_admin)
def reject_withdrawal(request, withdrawal_id):
    withdrawal = get_object_or_404(UserWithdrawal, id=withdrawal_id, status="PENDING")
    wallet = getattr(withdrawal.user, 'userwalletaddress', None)
    if wallet:
        wallet.balance += Decimal(withdrawal.amount)
        wallet.save()
    withdrawal.status = "REJECTED"
    withdrawal.save()
    messages.success(request, f"Withdrawal of {withdrawal.amount} rejected and refunded.")
    return redirect('accounts:admin_dashboard')

