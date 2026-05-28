from django.urls import path

from .views import ActivityEditView, BulkReviewView, ReviewDashboardView

urlpatterns = [
    path("review/dashboard/", ReviewDashboardView.as_view(), name="review-dashboard"),
    path("review/bulk/", BulkReviewView.as_view(), name="review-bulk"),
    path("review/activities/<uuid:pk>/edit/", ActivityEditView.as_view(), name="activity-edit"),
]
