from django.urls import path

from .views import (
    IngestionErrorListView,
    IngestionRunDetailView,
    IngestionRunListView,
    IngestionUploadView,
)

urlpatterns = [
    path("ingestion/upload/", IngestionUploadView.as_view(), name="ingestion-upload"),
    path("ingestion/runs/", IngestionRunListView.as_view(), name="ingestion-run-list"),
    path("ingestion/runs/<uuid:pk>/", IngestionRunDetailView.as_view(), name="ingestion-run-detail"),
    path("ingestion/runs/<uuid:run_id>/errors/", IngestionErrorListView.as_view(), name="ingestion-errors"),
]
