"""Middleware for tracking user last activity and online presence."""
from django.utils import timezone
from apps.accounts.models import User


class UserActivityMiddleware:
    """
    Lightweight middleware tracking user last activity.
    Uses a 60-second in-session throttle to avoid hammering the database on every asset or quick hit.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            now = timezone.now()
            last_ping = request.session.get("last_activity_ping")
            
            # Throttle database write: at most once every 60 seconds
            if not last_ping or (now.timestamp() - float(last_ping)) >= 60:
                request.session["last_activity_ping"] = now.timestamp()
                User.objects.filter(id=request.user.id).update(last_activity=now)
                request.user.last_activity = now

        response = self.get_response(request)
        return response
