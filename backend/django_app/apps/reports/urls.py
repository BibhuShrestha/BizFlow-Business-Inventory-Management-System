"""URL patterns for reports and daybook."""
from django.urls import path
from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.index, name="index"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("analytics/refresh-ai/", views.analytics_ai_refresh, name="analytics_ai_refresh"),
    path("daybook/", views.daybook, name="daybook"),
    path("daybook/export/csv/", views.export_daybook_csv, name="export_daybook_csv"),
    path("export/daybook-csv/", views.export_daybook_csv, name="export_daybook_csv_alias"),
    path("export/summary-csv/", views.export_summary_csv, name="export_summary_csv"),
]
