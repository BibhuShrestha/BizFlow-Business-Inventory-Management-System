"""
Shared Django template context processors.

These run on every request and inject commonly needed data into templates.
Migrated from Flask: app/__init__.py inject_active_company()
"""
# TODO (Part 6): Implement active_company context processor once Company model exists.


def active_company(request):
    """
    Inject the currently active company, user companies, and unread notification counts into every template.
    """
    user = getattr(request, "user", None)
    active_comp = getattr(user, "active_company", None) if user and user.is_authenticated else None
    user_comps = []
    unread_count = 0

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

    return {
        "active_company": active_comp,
        "user_companies": user_comps,
        "unread_count": unread_count,
        "notifications": unread_count,
    }
