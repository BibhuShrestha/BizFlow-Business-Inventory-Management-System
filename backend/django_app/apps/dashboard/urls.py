"""URL patterns for dashboard application."""
from django.urls import path
from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.index, name="index"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/notifications/", views.notifications_view, name="notifications"),
    path("dashboard/notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("dashboard/notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("dashboard/notifications/settings/", views.notification_settings_view, name="notification_settings"),
    path("dashboard/popups/<int:notification_id>/dismiss/", views.dismiss_popup, name="dismiss_popup"),
    path("dashboard/notifications/unread-count/", views.unread_count_api, name="unread_count_api"),
    path("api/convert-date/", views.convert_date, name="convert_date"),
]

