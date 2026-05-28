from django.urls import path

from .views import ActivityAuditLogView, ActivityDetailView, ActivityListView

urlpatterns = [
    path("activities/", ActivityListView.as_view(), name="activity-list"),
    path("activities/<uuid:pk>/", ActivityDetailView.as_view(), name="activity-detail"),
    path("activities/<uuid:pk>/audit/", ActivityAuditLogView.as_view(), name="activity-audit"),
]
