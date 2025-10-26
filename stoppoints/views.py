from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from balance.models import RechargeRequest
from accounts.models import CustomUser
from stoppoints.models import StopPoint, StopPointProgress
from stoppoints.utils import add_stop_points_for_user, update_stop_point, reset_stop_points_for_user

def is_admin(user):
    return user.is_authenticated and user.role == "admin"

@login_required
@user_passes_test(is_admin)
def add_stop_points_view(request, user_id):
    """
    Admin adds multiple stop points for a user.
    Expects POST with arrays:
      - stop_point[]
      - required_balance[]
    """
    user = get_object_or_404(CustomUser, id=user_id, role="user")
    if request.method == "POST":
        points = request.POST.getlist("stop_point[]")
        balances = request.POST.getlist("required_balance[]")

        if not points or not balances or len(points) != len(balances):
            messages.error(request, "Stop Points and Required Balances must match and not be empty.")
            return redirect("accounts:admin_dashboard")

        stop_data = []
        skipped = []
        added = []
        for p, b in zip(points, balances):
            try:
                point_int = int(p)
                balance_float = float(b)
                stop_data.append((point_int, balance_float))
            except ValueError:
                skipped.append(f"{p}:{b}")

        if stop_data:
            added, skipped_util = add_stop_points_for_user(user, stop_data)
            added.extend(added)
            skipped.extend(skipped_util)

        if added:
            messages.success(request, f"Added stop points: {', '.join([str(a[0]) for a in added])}")
        if skipped:
            messages.info(request, f"Skipped invalid entries: {', '.join(map(str, skipped))}")

    return redirect("accounts:admin_dashboard")


@login_required
@user_passes_test(is_admin)
def update_stop_point_view(request, user_id):
    """
    Update a specific stop point for a user.
    Expects POST:
      - stop_point_id
      - new_point (optional)
      - new_required_balance (optional)
    """
    user = get_object_or_404(CustomUser, id=user_id, role="user")
    if request.method == "POST":
        sp_id = request.POST.get("stop_point_id")
        new_point = request.POST.get("new_point", "").strip()
        new_required_balance = request.POST.get("new_required_balance", "").strip()
        try:
            sp = update_stop_point(
                user,
                sp_id,
                new_point=int(new_point) if new_point else None,
                new_required_balance=float(new_required_balance) if new_required_balance else None
            )
            messages.success(request, f"Stop point updated: point={sp.point}, required_balance={sp.required_balance}")
        except Exception as e:
            messages.error(request, f"Failed to update stop point: {str(e)}")
    return redirect("accounts:admin_dashboard")


@login_required
@user_passes_test(is_admin)
def reset_stop_points_view(request, user_id):
    """
    Resets all stop points for the user, clears corresponding balances, and progress.
    """
    user = get_object_or_404(CustomUser, id=user_id, role="user")

    # Reset stop points
    reset_stop_points_for_user(user)

    # Reset pending recharges linked to stop points
    RechargeRequest.objects.filter(user=user, status="pending").update(amount=0)

    # Reset progress
    progress, _ = StopPointProgress.objects.get_or_create(user=user)
    progress.is_stopped = False
    progress.last_cleared = None
    progress.save(update_fields=["is_stopped", "last_cleared"])

    messages.success(request, f"All stop points and corresponding balances reset for {user.username}")
    return redirect("accounts:admin_dashboard")
