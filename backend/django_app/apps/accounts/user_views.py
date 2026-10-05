"""Views for User management, role assignment, and access control."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import login_required_custom, admin_required
from apps.accounts.models import User, Role
from apps.accounts.user_forms import UserCreateForm, UserEditForm
from apps.core_app.pagination import paginate_queryset


@login_required_custom
@admin_required
def user_list(request: HttpRequest) -> HttpResponse:
    """List system users with search, role filtering, and pagination."""
    search = request.GET.get("search", "").strip()
    role_name = request.GET.get("role", "").strip()

    query = User.objects.select_related("role", "active_company").all()

    if search:
        query = query.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    if role_name:
        query = query.filter(role__name__iexact=role_name)

    page_obj = paginate_queryset(request, query.order_by("-created_at"), per_page=15)
    roles = Role.objects.all().order_by("name")
    return render(request, "accounts/user_list.html", {
        "page_obj": page_obj,
        "search": search,
        "selected_role": role_name,
        "roles": roles,
    })


@login_required_custom
@admin_required
def user_create(request: HttpRequest) -> HttpResponse:
    """Create a new user account."""
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f'User "{user.name}" created successfully.')
        return redirect("users:list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Create User"})


@login_required_custom
@admin_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Edit user role, active status, and profile."""
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'User "{user.name}" updated successfully.')
        return redirect("users:list")
    return render(request, "accounts/user_form.html", {"form": form, "user_obj": user, "title": "Edit User"})


@login_required_custom
@admin_required
def user_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Deactivate or delete user."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect("users:list")
    name = user.name
    user.is_active = False
    user.save(update_fields=["is_active"])
    messages.success(request, f'User "{name}" deactivated successfully.')
    return redirect("users:list")
