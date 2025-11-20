from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from .views import JobSeekerDashboardView, CustomLoginView, CustomLogoutView
from . import views

app_name = "jobs"

urlpatterns = [
    # Jobs
    path("", views.job_list, name="job_list"),
    path("add/", views.add_job, name="add_job"),
    path("<int:job_id>/", views.job_detail, name="job_detail"),
    path("<int:job_id>/edit/", views.job_edit, name="job_edit"),
    path("<int:job_id>/delete/", views.job_delete, name="job_delete"),

    # Applications
    path("<int:job_id>/apply/", views.apply_to_job, name="apply_to_job"),
    path("<int:job_id>/applications/", views.job_applications, name="job_applications"),
    path("applications/<int:app_id>/", views.application_detail, name="application_detail"),
    path("applications/<int:app_id>/update/<str:status>/", views.update_application_status, name="update_application_status"),
    path("employer/job/<int:job_id>/applications/", views.view_job_applications, name="view_job_applications"),

    # Saved jobs & profile
    path("profile/", views.profile_view, name="profile"),
    path("save-job/<int:job_id>/", views.save_job, name="save_job"),
    path("unsave-job/<int:job_id>/", views.unsave_job, name="unsave_job"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("notifications/mark-seen/", views.mark_notifications_seen, name="mark_notifications_seen"),
    path("notifications/fetch/", views.fetch_notifications, name="fetch_notifications"),
    path("get-notifications/", views.get_notifications, name="get_notifications"),
    path("mark-notifications-read/", views.mark_notifications_read, name="mark_notifications_read"),
    path("notifications/", views.all_notifications, name="all_notifications"),
    path("notifications/clear-jobs/", views.clear_job_notifications, name="clear_job_notifications"),
    path("notifications/clear-system/", views.clear_system_notifications, name="clear_system_notifications"),
    path("notification/<int:notif_id>/", views.view_notification, name="view_notification"),

    # Employer dashboard
    path("employer/dashboard/", views.employer_dashboard, name="employer_dashboard"),

    path("dashboard/", JobSeekerDashboardView.as_view(), name="dashboard"),

    # Auth
    #path("login/", auth_views.LoginView.as_view(template_name="jobs/login.html"), name="login"),



    #path("logout/", auth_views.LogoutView.as_view(next_page="jobs:login"), name="logout"),
    path("register/", views.register, name="register"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),


    # Password reset (built-in Django views)
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),

    # Custom forgot/reset (your own flow)
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/<uidb64>/<token>/", views.reset_password, name="reset_password"),

    # Change password
    path("change-password/",
         auth_views.PasswordChangeView.as_view(
             template_name="jobs/change_password.html",
             success_url=reverse_lazy("jobs:password_change_done")
         ),
         name="change_password"),
    path("change-password-done/",
         auth_views.PasswordChangeDoneView.as_view(
             template_name="jobs/change_password_done.html"
         ),
         name="password_change_done"),

    # Account management
    path("delete-account/", views.delete_account, name="delete_account"),
    path("deactivate-account/", views.deactivate_account, name="deactivate_account"),
]
