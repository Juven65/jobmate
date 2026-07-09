from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from .utils import verify_token
from .models import Job, JobApplication, SavedJob, Notification
from .forms import JobForm, JobApplicationForm, ProfileUpdateForm, RegisterForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse
from itertools import chain
from django.utils.timezone import localtime
from .services import get_recommended_jobs
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST

User = get_user_model()

# -----------------------------
# REGISTER + ACTIVATE
# -----------------------------
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # ✅ Use form.save() to set_password and role work
            user = form.save(commit=False)
            user.is_active = False  # require email activation
            user.save()

            # generate token & uid
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = request.get_host()

            # send activation email
            subject = "Activate your JobMate account"
            html_content = render_to_string("email/activate_account.html", {
                "user": user,
                "domain": domain,
                "uid": uid,
                "token": token,
            })
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject,
                text_content,
                "JobMate <juvenpinoy@gmail.com>",
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            role_msg = "Employer" if getattr(user, "is_employer", False) else "Job Seeker"
            messages.success(
                request,
                f"✅ {role_msg} account created! Activation email sent. Please check your inbox."
            )
            return redirect("jobs:login")
    else:
        form = RegisterForm()

    return render(request, "email/register.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:  # ✅ para hindi ma–activate ulit
            user.is_active = True
            user.save()
            messages.success(request, "Your account has been activated! You can now login.")
        else:
            messages.info(request, "Your account is already active. Please login.")
        return redirect("jobs:login")
    else:
        messages.error(request, "Activation link is invalid or expired!")
        return redirect("jobs:register")


def send_activation_email(user, domain, uid, token):
    subject = "Activate your JobMate account"
    from_email = "JobMate <juvenpinoy@gmail.com>"
    to = [user.email]

    html_content = render_to_string("email/activate_account.html", {
        "user": user,
        "domain": domain,
        "uid": uid,
        "token": token,
    })
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, to)
    email.attach_alternative(html_content, "text/html")
    email.send()


# -----------------------------
# PASSWORD RESET FLOW
# -----------------------------
def send_password_reset_email(user, domain, uid, token):
    subject = "Reset your JobMate password"
    html_content = render_to_string("email/reset_password_email.html", {
        "user": user,
        "domain": domain,
        "uid": uid,
        "token": token,
    })
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        "JobMate <juvenpinoy@gmail.com>",
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("jobs:forgot_password")

        current_site = get_current_site(request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        send_password_reset_email(user, current_site.domain, uid, token)

        messages.success(request, "Password reset link has been sent to your email.")
        return redirect("jobs:login")

    return render(request, "email/forgot_password.html")


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            if password == confirm_password:
                user.password = make_password(password)
                user.save()
                messages.success(request, "Password has been reset. You can now login.")
                return redirect("jobs:login")
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, "jobs/reset_password.html", {"uidb64": uidb64, "token": token})
    else:
        return HttpResponse("Reset link is invalid or has expired.")


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was changed successfully!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "jobs/change_password.html", {"form": form})


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect("jobs:login")

    return render(request, "jobs/delete_account_confirm.html")


@login_required
def deactivate_account(request):
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, "Your account has been deactivated. You can contact support to reactivate.")
        return redirect("jobs:login")
    return render(request, "jobs/deactivate_account.html")


# -----------------------------
# VERIFY EMAIL (Token-based)
# -----------------------------
def verify_email(request, token):
    user = verify_token(token)
    if user:
        user.is_verified = True
        user.save()
        messages.success(request, "Your email has been verified! You can now login.")
        return redirect("jobs:login")
    else:
        messages.error(request, "Invalid or expired verification link.")
        return redirect("jobs:register")

# -----------------------------
# ADD JOB
# -----------------------------
@login_required
def add_job(request):
    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, f"✅ Job '{job.title}' has been posted successfully!")
            return redirect("jobs:job_list")
        else:
            messages.error(request, "⚠️ Failed to post job. Please check the form.")
    else:
        form = JobForm()
    return render(request, "jobs/add_job.html", {"form": form})



# -----------------------------
# JOB LIST WITH FILTERS
# -----------------------------
def job_list(request):
    # ✅ Only active jobs visible to jobseekers
    jobs = Job.objects.filter(is_active=True).order_by("-id")

    q = request.GET.get("q", "")
    location = request.GET.get("location", "")
    company = request.GET.get("company", "")

    if q:
        jobs = jobs.filter(title__icontains=q)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if company:
        jobs = jobs.filter(company__icontains=company)

    paginator = Paginator(jobs, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(request, "jobs/job_list.html", {
        "page_obj": page_obj,
        "locations": Job.objects.filter(is_active=True).values_list("location", flat=True).distinct(),
        "companies": Job.objects.filter(is_active=True).values_list("company", flat=True).distinct(),
        "query_params": query_params.urlencode(),
        "notifications": add_notifications_context(request),
    })

# -----------------------------
# JOB DETAIL
# -----------------------------
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if not job.is_active and job.posted_by != request.user:
        messages.warning(request, "⚠️ This job is no longer available.")
        return redirect("job_list")

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "notifications": add_notifications_context(request),
    })


# -----------------------------
# APPLY TO JOB
# -----------------------------
@login_required
def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # ✅ Check kung nakapag-apply na
    existing = JobApplication.objects.filter(job=job, applicant=request.user).first()
    if existing:
        messages.warning(request, "⚠️ You have already applied for this job.")
        return redirect("jobs:job_detail", job_id=job.id)

    # ✅ POST Request (submit form)
    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.applicant = request.user
            app.save()

            # 📨 Notify Employer (link papunta sa employer job applications page)
            Notification.objects.create(
                user=job.posted_by,
                message=f"📩 New application for '{job.title}' by {request.user.username}",
                link=reverse("employer:job_applications", args=[job.id])  # ✅ FIXED link
            )

            messages.success(
                request,
                f"✅ You have successfully applied for '{job.title}' at {job.company}!"
            )
            return redirect("jobs:my_applications")
        else:
            messages.error(request, "⚠️ Failed to submit application. Please check the form.")
    else:
        form = JobApplicationForm()

    # ✅ Render form page kung GET request
    return render(request, "jobs/apply.html", {"form": form, "job": job})

@login_required
def my_applications(request):
    applications = JobApplication.objects.filter(applicant=request.user)

    # reset notification (mark all as seen)
    applications.update(has_seen=True)

    return render(request, "jobs/my_applications.html", {"applications": applications})


# -----------------------------
# JOB APPLICATIONS (For Employer)
# -----------------------------
@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job=job).order_by('-applied_at')
    return render(request, 'jobs/job_applications.html', {'job': job, 'applications': applications})

# -----------------------------
# EDIT JOB
# -----------------------------
@login_required
def job_edit(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Restrict: only the employer who posted this job can edit
    if job.posted_by != request.user:
        raise Http404("You are not allowed to edit this job.")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"✏️ Job '{job.title}' has been updated successfully!")
            return redirect("job_detail", job_id=job.id)
        else:
            messages.error(request, "⚠️ Failed to update job.")
    else:
        form = JobForm(instance=job)

    return render(request, "jobs/job_edit.html", {"form": form})


# -----------------------------
# DELETE JOB (employer can delete only their own job)
# -----------------------------
@login_required
def job_delete(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Restrict: only the employer who posted this job can delete
    if job.posted_by != request.user:
        raise Http404("You are not allowed to delete this job.")

    if request.method == 'POST':
        job.delete()
        messages.success(request, f"🗑️ Job '{job.title}' has been deleted successfully.")
        return redirect('job_list')

    return render(request, 'jobs/job_confirm_delete.html', {'job': job})

@login_required
def employer_dashboard(request):
    # Jobs posted by the employer
    jobs = Job.objects.filter(posted_by=request.user)
    return render(request, "jobs/employer_dashboard.html", {"jobs": jobs})


@login_required
def view_job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    applications = JobApplication.objects.filter(job=job)
    return render(request, "jobs/view_applications.html", {
        "job": job,
        "applications": applications
    })

@staff_member_required
def application_detail(request, app_id):
    application = get_object_or_404(JobApplication, id=app_id)
    return render(request, 'jobs/application_detail.html', {
        'application': application,
        "job": application.job
    })

@login_required
def update_application_status(request, app_id, status):
    application = get_object_or_404(JobApplication, id=app_id)
    job = application.job

    # siguraduhin na employer lang makaka-update
    if job.posted_by != request.user:
        messages.error(request, "❌ You are not allowed to update this application.")
        return redirect("jobs:job_list")

    if status in ["Accepted", "Rejected", "Pending"]:
        application.status = status
        application.has_seen = False  # mark as "new notification"
        application.save()
        messages.success(request, f"✅ Application for {application.applicant.username} has been updated to {status}.")

        # employer feedback
        messages.success(request, f"✅ Application for {application.applicant.username} has been updated to {status}.")

        Notification.objects.create(
            user=application.applicant,
            message=f"✅ Your application for '{application.job.title}' was updated to {status}",
            link=f"/jobs/my_applications/"
        )

    return redirect("view_job_applications", job_id=job.id)


@login_required
def withdraw_application(request, app_id):
    application = get_object_or_404(JobApplication, id=app_id, applicant=request.user)
    job_title = application.job.title
    application.delete()
    messages.info(request, f"ℹ️ Your application for '{job_title}' has been withdrawn.")
    return redirect("my_applications")

def add_notifications_context(request):
    if request.user.is_authenticated:
        return JobApplication.objects.filter(applicant=request.user, has_seen=False).count()
    return 0


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Your profile has been updated successfully!")
            return redirect("jobs:profile")
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, "jobs/profile.html", {"form": form})

@login_required
def save_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if created:
        messages.success(request, f"⭐ You saved '{job.title}' to your favorites!")
    else:
        messages.info(request, f"ℹ️ You already saved '{job.title}'.")
    return redirect("jobs:job_detail", job_id=job.id)


@login_required
def unsave_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    SavedJob.objects.filter(user=request.user, job=job).delete()
    messages.info(request, f"❌ '{job.title}' removed from your saved jobs.")
    return redirect("jobs:saved_jobs")

@login_required
def saved_jobs(request):
    saved = SavedJob.objects.filter(user=request.user).order_by("-saved_at")
    return render(request, "jobs/saved_jobs.html", {"saved": saved})

class CustomLoginView(LoginView):
    template_name = "jobs/login.html"

    def get_success_url(self):
        user = self.request.user

        # 🔑 Superuser → Custom Admin Panel
        if user.is_superuser:
            messages.success(self.request, f"Welcome back, {user.username}!")
            return reverse_lazy("adminpanel:admin_dashboard")

        # 🏢 Employer
        if getattr(user, "is_employer", False):
            messages.success(self.request, f"Welcome back, {user.username}!")
            return reverse_lazy("employer:dashboard")

        # 👤 Job Seeker (default)
        messages.success(self.request, f"✅ Welcome to JobMate, {user.username}, Thanks for visiting!")
        return reverse_lazy("jobs:dashboard")


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have logged out successfully!")
        return super().dispatch(request, *args, **kwargs)


class JobSeekerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "jobs/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        applications = JobApplication.objects.filter(applicant=self.request.user)
        saved = SavedJob.objects.filter(user=self.request.user)

        # Activity feed logic...
        feed = []
        for app in applications:
            feed.append({"type": "application", "job": app.job, "status": app.status, "date": app.applied_at})
        for s in saved:
            feed.append({"type": "saved", "job": s.job, "date": s.saved_at})
        feed = sorted(feed, key=lambda x: x["date"], reverse=True)

        context["activity_feed"] = feed[:10]
        context["recommended_jobs"] = get_recommended_jobs(self.request.user, limit=5)

        return context

@login_required
def fetch_notifications(request):
    # Job application updates
    apps = JobApplication.objects.filter(
        applicant=request.user,
        has_seen=False
    ).exclude(status="Pending").order_by("-updated_at")[:5]

    app_data = [
        {
            "id": a.id,
            "type": "application",
            "job_title": a.job.title,
            "status": a.status,
            "updated_at": localtime(a.updated_at).strftime("%b %d, %Y %H:%M"),
            "url": reverse("jobs:application_detail", args=[a.id])
        }
        for a in apps
    ]

    # System notifications
    notifs = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by("-created_at")[:5]

    notif_data = [
        {
            "id": n.id,
            "type": "system",
            "message": n.message,
            "updated_at": localtime(n.created_at).strftime("%b %d, %Y %H:%M"),
            "url": n.link or "#"
        }
        for n in notifs
    ]

    # Merge + sort by date
    all_data = sorted(
        chain(app_data, notif_data),
        key=lambda x: x["updated_at"],
        reverse=True
    )[:10]

    return JsonResponse({
        "count": len(all_data),
        "notifications": all_data
    })

@login_required
@require_POST
def mark_notifications_seen(request):
    # Mark job applications as seen
    JobApplication.objects.filter(
        applicant=request.user,
        has_seen=False
    ).update(has_seen=True)

    # Mark system notifications as read
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"success": True})

@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"status": "success"})

@login_required
def get_notifications(request):
    notifications = request.user.notifications.all()[:5]  # latest 5
    unread_count = request.user.notifications.filter(is_read=False).count()

    data = {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%b %d, %Y %H:%M"),
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)

@login_required
def all_notifications(request):
    job_notifs = JobApplication.objects.filter(applicant=request.user).order_by("-updated_at")
    sys_notifs = Notification.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "jobs/all_notifications.html", {
        "job_notifs": job_notifs,
        "sys_notifs": sys_notifs,
    })


@login_required
@require_POST
def clear_job_notifications(request):
    JobApplication.objects.filter(applicant=request.user).update(status="Pending")
    messages.success(request, "Job notifications cleared.")
    return redirect("jobs:all_notifications")


@login_required
@require_POST
def clear_system_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, "System notifications cleared.")
    return redirect("jobs:all_notifications")

@login_required
def redirect_after_login(request):
    user = request.user

    if user.is_superuser:
        return redirect("adminpanel:admin_dashboard")
    elif getattr(user, "is_employer", False):
        return redirect("employer:dashboard")
    else:
        return redirect("jobs:dashboard")

def view_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('jobs:all_notifications')
