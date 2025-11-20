from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from jobs import views as jobs_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("jobs/", include("jobs.urls", namespace="jobs")),
    path("employer/", include("employer.urls")),
    path("adminpanel/", include("adminpanel.urls")),

    # ✅ root redirect (choose saan papunta by default)
    path("", lambda request: redirect("jobs:login")),
    # Login redirect
    path("redirect-after-login/", jobs_views.redirect_after_login, name="redirect_after_login"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
