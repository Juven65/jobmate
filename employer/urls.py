from django.urls import path
from . import views

app_name = "employer"

urlpatterns = [
    path("dashboard/", views.EmployerDashboardView.as_view(), name="dashboard"),
    path("jobs/", views.EmployerJobListView.as_view(), name="job_list"),
    path("jobs/create/", views.EmployerJobCreateView.as_view(), name="create_job"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),

    # Applications
    path("jobs/<int:job_id>/applications/", views.EmployerApplicationsView.as_view(), name="job_applications"),
    path("application/<int:pk>/status/", views.ApplicationStatusUpdateView.as_view(), name="application_status_update"),
    path("application/<int:pk>/update-status/", views.update_application_status, name="update_application_status"),
]
