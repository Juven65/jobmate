from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = "adminpanel"

urlpatterns = [
    # Redirect root of adminpanel → dashboard
    path("", lambda request: redirect("adminpanel:admin_dashboard"), name="adminpanel_home"),

    # Dashboard
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("applications-trend-data/", views.applications_trend_data, name="applications_trend_data"),
    path("applications/", views.applications_overview, name="applications_overview"),

    # === Employer Management ===
    path("employers/", views.employers_overview, name="employers_overview"),
    path("employers/delete/<int:user_id>/", views.delete_user, name="delete_user"),
    path("employers/activate/<int:user_id>/", views.activate_user, name="activate_user"),
    path("employers/deactivate/<int:user_id>/", views.deactivate_user, name="deactivate_user"),
    path("employers/<int:pk>/", views.employer_detail, name="employer_detail"),
    path("users/", views.user_list, name="user_list"),

    # === Employer Management ===
    path("inbox/", views.inbox, name="inbox"),
    path("sent/", views.sent_messages, name="sent_messages"),
    path("message/<int:pk>/", views.message_detail, name="message_detail"),

    # Send to specific user
    path("message/send/<int:user_id>/", views.send_message, name="send_message"),

    path("message/send/", views.send_message_form, name="send_message_form"),
]
