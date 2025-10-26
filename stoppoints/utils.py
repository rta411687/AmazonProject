from decimal import Decimal, InvalidOperation
from .models import StopPoint

# -----------------------------
# Helper: Daily Task Limit
# -----------------------------
def get_daily_task_limit(user):
    """
    Returns the daily task limit for a user.
    Falls back to 60 if no setting exists.
    """
    try:
        # Avoid importing from products.utils to prevent circular import
        setting = getattr(user, 'commission_setting', None)
        if setting and getattr(setting, 'daily_task_limit', None):
            return int(setting.daily_task_limit)
    except Exception:
        pass
    return 60

# -----------------------------
# StopPoints logic
# -----------------------------
def add_stop_points_for_user(user, points_list):
    added, skipped = [], []
    daily_limit = get_daily_task_limit(user)
    for point in points_list:
        try:
            point_int = int(point)
            if not (1 <= point_int <= daily_limit):
                skipped.append(point)
                continue
            if StopPoint.objects.filter(user=user, point=point_int).exists():
                skipped.append(point)
                continue
            StopPoint.objects.create(user=user, point=point_int)
            added.append(point_int)
        except (ValueError, TypeError):
            skipped.append(point)
    return added, skipped

def update_stop_point(user, sp_id, new_point=None, new_required_balance=None):
    sp = StopPoint.objects.get(id=sp_id, user=user)
    daily_limit = get_daily_task_limit(user)
    if new_point is not None and str(new_point).strip() != "":
        new_point_int = int(new_point)
        if not (1 <= new_point_int <= daily_limit):
            raise ValueError(f"Stop point must be between 1 and {daily_limit}")
        if StopPoint.objects.filter(user=user, point=new_point_int).exclude(id=sp.id).exists():
            raise ValueError("Another stop point with this number already exists.")
        sp.point = new_point_int
    if new_required_balance is not None and str(new_required_balance).strip() != "":
        try:
            rb = Decimal(str(new_required_balance))
            if rb < 0:
                raise ValueError("Required balance must be non-negative.")
            sp.required_balance = rb
        except InvalidOperation:
            raise ValueError("Invalid required balance amount.")
    sp.save()
    return sp

def reset_stop_points_for_user(user):
    StopPoint.objects.filter(user=user).delete()

def get_next_pending_stoppoint(user, next_task_number):
    return StopPoint.objects.filter(user=user, point__gte=next_task_number, status='pending').order_by('point').first()

def is_task_allowed(user, next_task_number):
    if hasattr(user, 'stoppoint_progress') and user.stoppoint_progress.is_stopped:
        last_cleared_order = user.stoppoint_progress.last_cleared.order if user.stoppoint_progress.last_cleared else 0
        blocking_point = StopPoint.objects.filter(user=user, order__gt=last_cleared_order).order_by('order').first()
        if blocking_point:
            return False, f"User is stopped at task {blocking_point.point}. Recharge of {blocking_point.required_balance} required."
        else:
            return False, "User is stopped, but no specific rule found. Please contact support."

    pending_sp = get_next_pending_stoppoint(user, next_task_number)
    if pending_sp and pending_sp.point == next_task_number:
        return False, f"StopPoint at task {pending_sp.point} requires approval or recharge."

    return True, None
