from django.urls import path

from .views import (
    ApprovedModelsView,
    GenerationJobDetailView,
    GenerationJobListCreateView,
    RateGenerationJobView,
)

app_name = "generations"

urlpatterns = [
    path("models/", ApprovedModelsView.as_view(), name="approved-models"),
    path("jobs/", GenerationJobListCreateView.as_view(), name="jobs-list-create"),
    path("jobs/<uuid:id>/", GenerationJobDetailView.as_view(), name="jobs-detail"),
    path("jobs/<uuid:id>/rate/", RateGenerationJobView.as_view(), name="jobs-rate"),
]
