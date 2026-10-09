"""Views for User management, role assignment, and access control."""
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import login_required_custom, admin_required
from apps.accounts.models import User, Role
from apps.accounts.user_forms import UserCreateForm, UserEditForm
from apps.core_app.pagination import paginate_queryset


@login_required_custom
@admin_required
def user_list(request: HttpRequest) -> HttpResponse:
    """List system users with search, role filtering, account status, online presence, and pagination."""
    search = request.GET.get("search", "").strip()
    role_name = request.GET.get("role", "").strip()
    account_status = request.GET.get("status", "").strip().lower()
    online_status = request.GET.get("online", "").strip().lower()
    sort = request.GET.get("sort", "-created_at").strip()

    now = timezone.now()
    timeout_minutes = getattr(settings, "USER_ONLINE_TIMEOUT_MINUTES", 15)
    online_threshold = now - timedelta(minutes=timeout_minutes)

    query = User.objects.select_related("role", "active_company").all()

    # Search filter
    if search:
        query = query.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    # Role filter
    if role_name:
        query = query.filter(role__name__iexact=role_name)

    # Account status filter (Active vs Disabled)
    if account_status == "active":
        query = query.filter(is_active=True)
    elif account_status in ("disabled", "inactive"):
        query = query.filter(is_active=False)

    # Online status filter (Online within last X minutes vs Offline)
    if online_status == "online":
        query = query.filter(last_activity__gte=online_threshold)
    elif online_status == "offline":
        query = query.filter(Q(last_activity__lt=online_threshold) | Q(last_activity__isnull=True))

    # Sorting
    valid_sorts = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "name": "name",
        "-name": "-name",
        "-last_activity": "-last_activity",
        "-last_login": "-last_login",
    }
    order_field = valid_sorts.get(sort, "-created_at")
    query = query.order_by(order_field)

    # Pagination
    page_obj = paginate_queryset(request, query, per_page=15)
    roles = Role.objects.all().order_by("name")

    # High-level user activity statistics for Admin overview
    total_users = User.objects.count()
    online_users = User.objects.filter(last_activity__gte=online_threshold).count()
    offline_users = max(0, total_users - online_users)
    active_accounts = User.objects.filter(is_active=True).count()
    disabled_accounts = User.objects.filter(is_active=False).count()
    new_users_30d = User.objects.filter(created_at__gte=now - timedelta(days=30)).count()

    stats = {
        "total_users": total_users,
        "online_users": online_users,
        "offline_users": offline_users,
        "active_accounts": active_accounts,
        "disabled_accounts": disabled_accounts,
        "new_users_30d": new_users_30d,
        "online_timeout_minutes": timeout_minutes,
    }

    return render(request, "accounts/user_list.html", {
        "page_obj": page_obj,
        "users": page_obj,  # Preserves both users and page_obj for zero template friction
        "search": search,
        "selected_role": role_name,
        "selected_status": account_status,
        "selected_online": online_status,
        "selected_sort": sort,
        "roles": roles,
        "stats": stats,
    })


@login_required_custom
@admin_required
def user_create(request: HttpRequest) -> HttpResponse:
    """Create a new user account with strict validation and feedback."""
    form = UserCreateForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.name}" ({user.email}) created successfully.')
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"status": "success", "id": user.id, "name": user.name})
            return redirect("users:list")
        else:
            messages.error(request, "Please correct the highlighted errors below to create the user.")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Create User"})


@login_required_custom
@admin_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit user role, active status, and profile."""
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.name}" updated successfully.')
            return redirect("users:list")
        else:
            messages.error(request, "Please correct the highlighted errors below to save changes.")
    return render(request, "accounts/user_form.html", {"form": form, "user_obj": user, "title": f"Edit User - {user.name}"})


@require_POST
@login_required_custom
@admin_required
def user_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Deactivate or toggle user account status."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate or delete your own account.")
        return redirect("users:list")
    
    # Toggle active status or deactivate
    action = request.POST.get("action", "deactivate")
    if action == "activate":
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, f'User "{user.name}" account activated successfully.')
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f'User "{user.name}" account deactivated.')

    return redirect("users:list")
