
import uuid

from accounts.models import CustomUser
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from products.models import UserProductTask
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from commission.utils import get_total_commission





def superadminlogin(request):
    """
    Super Admin login page.
    Only users with role='superadmin' can log in.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user and user.role == 'superadmin':
            login(request, user)
            return redirect('accounts:superadmin_dashboard')
  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid credentials or not a Super Admin.")
            return redirect('superadminlogin')

    return render(request, "accounts/superadminlogin.html")

User = get_user_model()

def is_superadmin(user):
    return user.is_authenticated and user.role == 'superadmin'

def generate_admin_referral_code():
    """Generate a unique 6-character uppercase referral code for Admins."""
    return ''.join(random.choices(string.ascii_uppercase, k=6))



@login_required
@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    # Fetch all Admins and Customer Service accounts
    admins_cs = User.objects.filter(role__in=['admin', 'customerservice'])

    # Fetch the single superadmin wallet (if exists)
    wallet = SuperAdminWallet.objects.first()

    if request.method == "POST":
        action = request.POST.get("action")
        target_id = request.POST.get("user_id")
        target_user = None

        # Fetch target user for delete or reset password actions
        if action in ["delete", "reset_password"]:
            target_user = get_object_or_404(User, id=target_id, role__in=['admin', 'customerservice'])

        # Create new Admin or Customer Service
        if action == "create":
            username = request.POST.get("username")
            password = request.POST.get("password")
            role = request.POST.get("role")

            if not all([username, password, role]):
                messages.error(request, "All fields are required.")
            elif role not in ['admin', 'customerservice']:
                messages.error(request, "Invalid role selected.")
            elif User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            else:
                referral_code = generate_admin_referral_code() if role == "admin" else None
                User.objects.create_user(
                    username=username,
                    password=password,
                    role=role,
                    referral_code=referral_code
                )
                messages.success(request, f"{role.capitalize()} created successfully.")
            return redirect('accounts:superadmin_dashboard')

        # Delete Admin or Customer Service
        elif action == "delete" and target_user:
            target_user.delete()
            messages.success(request, f"{target_user.role.capitalize()} deleted successfully.")
            return redirect('accounts:superadmin_dashboard')

        # Reset password for Admin or Customer Service
        elif action == "reset_password" and target_user:
            new_password = request.POST.get("new_password")
            if not new_password:
                messages.error(request, "Password cannot be empty.")
            else:
                target_user.set_password(new_password)
                target_user.save()
                messages.success(request, f"{target_user.role.capitalize()} password reset successfully.")
            return redirect('accounts:superadmin_dashboard')

        # Handle Super Admin Wallet (single wallet logic)
        elif action == "wallet_create":
            address = request.POST.get("address")
            label = request.POST.get("label", "")
            if not address:
                messages.error(request, "Wallet address is required.")
            else:
                if wallet:  # update existing
                    wallet.address = address
                    wallet.label = label
                    wallet.save()
                    messages.success(request, "Wallet updated successfully.")
                else:  # create new
                    SuperAdminWallet.objects.create(address=address, label=label)
                    messages.success(request, "Wallet created successfully.")
            return redirect('accounts:superadmin_dashboard')

    return render(request, "accounts/superadmin_dashboard.html", {
        "admins_cs": admins_cs,
        "wallet": wallet  # pass wallet to template
    })
def adminlogin(request):
    """
    Admin login page.
    Only users with role='admin' can log in.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user and user.role == 'admin':
            login(request, user)
            return redirect('accounts:admin_dashboard')

        else:
            messages.error(request, "Invalid credentials or not an Admin.")
            return redirect('adminlogin')

    return render(request, "accounts/adminlogin.html")

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'








def customerservicelogin(request):
    """
    Customer Service login page.
    Only users with role='customerservice' can log in.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user and user.role == 'customerservice':
            login(request, user)
            return redirect('accounts:customerservice_dashboard')
        else:
            messages.error(request, "Invalid credentials or not Customer Service.")
            return redirect('accounts:customerservicelogin')

    return render(request, "accounts/customerservicelogin.html")

@user_passes_test(lambda u: u.is_authenticated and u.role == 'customerservice')
# at top of your views file






@user_passes_test(lambda u: u.is_authenticated and u.role == 'customerservice')
def customerservice_dashboard(request):
    """
    Customer Service dashboard:
    - View all Regular Users
    - Reset login and fund passwords
    - Delete Regular Users (wipes all fields safely before delete)
      Deleting a user does NOT affect their referrals.
    """
    regular_users = CustomUser.objects.filter(role='user')

    if request.method == "POST":
        action = request.POST.get("action")
        target_id = request.POST.get("user_id")
        target_user = get_object_or_404(CustomUser, id=target_id, role='user')

        if action == "delete":
            # Only wipe unique fields required for deletion
            suffix = uuid.uuid4().hex[:6]
            target_user.username = f"deleted_{suffix}"
            target_user.phone = f"deleted_{suffix}"
            target_user.password = ''
            target_user.fund_password = ''
            target_user.referral_code = None
            target_user.save(update_fields=[
                'username','phone','password','fund_password','referral_code'
            ])

            # Delete the user; referrals remain completely intact
            target_user.delete()
            messages.success(request, "Regular User deleted successfully.")
            return redirect('accounts:customerservice_dashboard')

        elif action == "reset_login_password":
            new_password = request.POST.get("new_password")
            if not new_password:
                messages.error(request, "Login password cannot be empty.")
            else:
                target_user.set_password(new_password)
                target_user.save(update_fields=['password'])
                messages.success(request, f"Login password for {target_user.username} reset successfully.")
            return redirect('accounts:customerservice_dashboard')

        elif action == "reset_fund_password":
            new_fund_password = request.POST.get("new_fund_password")
            if not new_fund_password:
                messages.error(request, "Fund password cannot be empty.")
            else:
                target_user.fund_password = new_fund_password
                target_user.save(update_fields=['fund_password'])
                messages.success(request, f"Fund password for {target_user.username} reset successfully.")
            return redirect('accounts:customerservice_dashboard')

    return render(request, "accounts/customerservice_dashboard.html", {"regular_users": regular_users})



def user_register(request):
    """
    Regular User registration:
    - Requires phone, username, password, fund password
    - Accepts Admin or Regular User referral code
    - Admin referral codes can be used unlimited times
    - Regular User referral codes can only be used once
    - Generates own 6-character uppercase referral code
    """
    if request.method == "POST":
        phone = request.POST.get("phone")
        username = request.POST.get("username")
        password = request.POST.get("password")
        fund_password = request.POST.get("fund_password")
        referral_code_input = request.POST.get("referral_code")

        # Validate all fields not empty
        if not all([phone, username, password, fund_password, referral_code_input]):
            messages.error(request, "All fields are required.")
            return redirect('accounts:user_register')

        # -------------------------
        # New input validation rules
        # -------------------------
        import re
        # 1. phone number must be + and numbers only, max 15
        if not re.fullmatch(r'^\+?\d{1,15}$', phone):
            messages.error(request, "Phone number must be numeric and may start with + (max 15 digits).")
            return redirect('accounts:user_register')

        # 2. username length 6–15
        if not (6 <= len(username) <= 15):
            messages.error(request, "Username must be between 6 and 15 characters.")
            return redirect('accounts:user_register')

        # 3. password length 6–15
        if not (6 <= len(password) <= 15):
            messages.error(request, "Password must be between 6 and 15 characters.")
            return redirect('accounts:user_register')

        # 4. fund password length 6–15
        if not (6 <= len(fund_password) <= 15):
            messages.error(request, "Fund password must be between 6 and 15 characters.")
            return redirect('accounts:user_register')

        # 5. referral code exactly 6
        if len(referral_code_input) != 6:
            messages.error(request, "Referral code must be exactly 6 characters.")
            return redirect('accounts:user_register')
        # -------------------------

        # Find owner of referral code
        referrer = User.objects.filter(referral_code=referral_code_input).first()
        if not referrer or referrer.role not in ['admin', 'user']:
            messages.error(request, "Invalid referral code.")
            return redirect('accounts:user_register')

        # Enforce Regular User referral limit (only one user)
        if referrer.role == 'user':
            already_referred = User.objects.filter(referred_by=referrer).exists()
            if already_referred:
                messages.error(request, "This user's referral code has already been used.")
                return redirect('accounts:user_register')

        # Check unique username and phone
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('accounts:user_register')

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists.")
            return redirect('accounts:user_register')

        # Generate own 6-character uppercase referral code
        user_referral_code = ''.join(random.choices(string.ascii_uppercase, k=6))

        # Create Regular User
        User.objects.create(
            username=username,
            phone=phone,
            password=make_password(password),
            fund_password=fund_password,
            role='user',
            referral_code=user_referral_code,
            referred_by=referrer
        )

        messages.success(request, "Registration successful! Please login.")
        return redirect('accounts:user_login')  # <-- redirect to user login page

    return render(request, "accounts/user_register.html")



from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def user_login(request):
    """
    Regular User login:
    - Can login using username or phone
    - Must have role='user'
    - Redirects to products page after successful login
    """
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # phone or username
        password = request.POST.get("password")

        user = None
        try:
            user = User.objects.get(role='user', username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(role='user', phone=identifier)
            except User.DoesNotExist:
                messages.error(request, "Invalid credentials.")
                return redirect('accounts:user_login')

        if user and user.check_password(password):
            login(request, user)
            return redirect('products')  # Redirect to products page
        else:
            messages.error(request, "Invalid credentials.")
            return redirect('accounts:user_login')

    return render(request, "accounts/user_login.html")









@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def payment_view(request):
    return render(request, 'accounts/payment.html')

@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')

@login_required
def faq_view(request):
    return render(request, 'accounts/faq.html')

@login_required
def home_view(request):
    return render(request, 'accounts/home.html')

@login_required
def balance_view(request):
    return render(request, 'accounts/balance.html')

@login_required
def activities_view(request):
    return render(request, 'accounts/activities.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


# accounts/views.py  (or wherever your admin_dashboard lives)
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import CustomUser
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from balance.models import RechargeHistory, RechargeRequest, Voucher

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import CustomUser
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from balance.models import RechargeRequest, Voucher
# (also import approve_recharge / reject_recharge from wherever you defined them)

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


from stoppoints.models import StopPoint

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from accounts.models import CustomUser
from stoppoints.models import StopPoint
from balance.models import RechargeRequest, Voucher




def is_admin(user):
    return user.is_authenticated and user.role == "admin"





from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import SuperAdminWallet

def is_superadmin(user):
    return user.is_authenticated and user.role == 'superadmin'

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from accounts.models import SuperAdminWallet
# your existing superadmin check function

@login_required
@user_passes_test(is_superadmin)
def manage_superadmin_wallets(request):
    # Fetch all existing wallets
    wallets = SuperAdminWallet.objects.all()

    if request.method == "POST":
        action = request.POST.get("action")

        # CREATE a new wallet
        if action == "wallet_create":
            address = request.POST.get("address")
            label = request.POST.get("label", "")
            if not address:
                messages.error(request, "Wallet address is required.")
            elif SuperAdminWallet.objects.filter(address=address).exists():
                messages.error(request, "This wallet address already exists.")
            else:
                SuperAdminWallet.objects.create(address=address, label=label)
                messages.success(request, "Wallet created successfully.")
            return redirect("accounts:superadmin_dashboard")

        # UPDATE an existing wallet
        elif action == "wallet_update":
            wallet_id = request.POST.get("wallet_id")
            wallet = get_object_or_404(SuperAdminWallet, id=wallet_id)
            address = request.POST.get("address")
            label = request.POST.get("label", "")
            if not address:
                messages.error(request, "Wallet address is required.")
            elif SuperAdminWallet.objects.filter(address=address).exclude(id=wallet.id).exists():
                messages.error(request, "Another wallet with this address already exists.")
            else:
                wallet.address = address
                wallet.label = label
                wallet.save()
                messages.success(request, "Wallet updated successfully.")
            return redirect("accounts:superadmin_dashboard")

        # DELETE a wallet
        elif action == "wallet_delete":
            wallet_id = request.POST.get("wallet_id")
            wallet = get_object_or_404(SuperAdminWallet, id=wallet_id)
            wallet.delete()
            messages.success(request, "Wallet deleted successfully.")
            return redirect("accounts:superadmin_dashboard")

    return render(request, "accounts/superadmin_wallets.html", {"wallets": wallets})





from wallet.models import UserWalletAddress, UserWithdrawal  # include withdrawals


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

from balance.models import RechargeRequest, Voucher
from wallet.models import UserWithdrawal
from stoppoints.models import StopPoint
from commission.models import CommissionSetting  # Correct import

from accounts.utils import is_admin  # your existing utility

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from accounts.models import CustomUser
from stoppoints.models import StopPoint
from balance.models import RechargeRequest, Voucher
from wallet.models import UserWalletAddress, UserWithdrawal
from commission.models import CommissionSetting
from commission.utils import get_total_commission
from accounts.utils import is_admin


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Handle admin actions from the dashboard (e.g., set per-user daily task limit)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'set_daily_limit':
            user_id = request.POST.get('user_id')
            daily_limit = request.POST.get('daily_limit')
            try:
                daily_limit_int = int(daily_limit)
                if daily_limit_int < 1:
                    messages.error(request, 'Daily limit must be at least 1.')
                else:
                    cs, _ = CommissionSetting.objects.get_or_create(user_id=user_id)
                    cs.daily_task_limit = daily_limit_int
                    cs.save(update_fields=['daily_task_limit'])
                    messages.success(request, f"Daily task limit updated for user {user_id} to {daily_limit_int}.")
            except (TypeError, ValueError):
                messages.error(request, 'Invalid daily limit value.')
            return redirect('accounts:admin_dashboard')

    users = CustomUser.objects.filter(role='user')

    for user_obj in users:
        # Stop points
        stop_points = StopPoint.objects.filter(user=user_obj).order_by('point')
        user_obj.stop_points = stop_points

        # Pending recharges
        user_obj.pending_recharges = RechargeRequest.objects.filter(user=user_obj, status="pending")
        for recharge in user_obj.pending_recharges:
            recharge.voucher = Voucher.objects.filter(recharge_request=recharge).first()

        # Wallet address & balance
        try:
            user_obj.wallet_address = UserWalletAddress.objects.get(user=user_obj)
            wallet_balance = user_obj.wallet_address.balance
        except UserWalletAddress.DoesNotExist:
            user_obj.wallet_address = None
            wallet_balance = 0

        # Withdrawals
        user_obj.withdrawals = UserWithdrawal.objects.filter(user=user_obj).order_by('-created_at')

        # Commission details
        cs = CommissionSetting.objects.filter(user=user_obj).last()
        user_obj.commission_setting = cs
        if cs:
            user_obj.product_rate = getattr(cs, 'product_rate', 0)
            user_obj.referral_rate = getattr(cs, 'referral_rate', 0)
            user_obj.daily_task_limit = getattr(cs, 'daily_task_limit', 60)
        else:
            user_obj.product_rate = 0
            user_obj.referral_rate = 0
            user_obj.daily_task_limit = 60

        # Total commission
        user_obj.total_commission = get_total_commission(user_obj)

        # Task progress per stop point: True=stop reached, False=not reached
        user_obj.task_progress = []
        for sp in stop_points:
            if wallet_balance >= sp.required_balance:
                user_obj.task_progress.append(True)  # Red bar
            else:
                user_obj.task_progress.append(False)  # Green bar

    context = {
        "users": users,
    }
    return render(request, "accounts/admin_dashboard.html", context)
