"""
Shared Django template context processors.

These run on every request and inject commonly needed data into templates.
Migrated from Flask: app/__init__.py inject_active_company()
"""


def active_company(request):
    """
    Inject the currently active company, user companies, unread notification counts,
    and granular user permissions into every template.
    """
    user = getattr(request, "user", None)
    active_comp = getattr(user, "active_company", None) if user and user.is_authenticated else None
    user_comps = []
    unread_count = 0
    user_perms = set()

    if user and user.is_authenticated:
        try:
            user_comps = list(user.companies.filter(is_active=True))
        except Exception:
            user_comps = []
        try:
            from apps.audit.models import Notification
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
        except Exception:
            unread_count = 0
        try:
            from domain.permissions import get_all_user_permissions
            user_perms = get_all_user_permissions(user)
        except Exception:
            user_perms = set()

    return {
        "active_company": active_comp,
        "user_companies": user_comps,
        "unread_count": unread_count,
        "notifications": unread_count,
        "user_permissions": user_perms,
    }
