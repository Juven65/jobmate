from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date
from .models import Message
from .forms import MessageForm
from jobs.models import Job, JobApplication
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q

CustomUser = get_user_model()


User = get_user_model()

@login_required
def send_message(request, user_id):
    receiver = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        Message.objects.create(
            sender=request.user,
            receiver=receiver,
            subject=subject,
            body=body
        )
        return redirect("adminpanel:inbox")  # gawa ka ng inbox page

    return render(request, "adminpanel/messages/send_message.html", {"receiver": receiver})

# 🔹 Custom decorator: Superuser only
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return render(request, "403.html")  # forbidden page
    return wrapper

# ✅ MAIN ADMIN DASHBOARD
@login_required
@admin_required
def admin_dashboard(request):
    job = Job.objects.all()
    applications = JobApplication.objects.all()
    timeframe = request.GET.get("timeframe", "7")  # default = 7 days
    today = timezone.now().date()

    if timeframe == "30":
        start_date = today - timedelta(days=29)
    elif timeframe == "all":
        start_date = None
    else:  # default = 7 days
        start_date = today - timedelta(days=6)

    # === Employers Search + Filter ===
    employers = CustomUser.objects.filter(is_employer=True)

    # Search by keyword
    q = request.GET.get("q")
    if q:
        employers = employers.filter(username__icontains=q)

    # Filter by active/inactive
    status = request.GET.get("status")
    if status == "active":
        employers = employers.filter(is_active=True)
    elif status == "inactive":
        employers = employers.filter(is_active=False)

    # Limit to recent (optional)
    filtered_employers = (
        employers.annotate(job_count=Count("jobs"))
        .order_by("-date_joined")[:10]
    )

    # === BASIC STATS ===
    total_users = CustomUser.objects.count()
    total_employers = CustomUser.objects.filter(is_employer=True).count()
    total_seekers = CustomUser.objects.filter(is_employer=False).count()
    total_jobs = Job.objects.count()
    total_applications = JobApplication.objects.count()

    # === ACTIVE USERS ===
    active_employers = (
        CustomUser.objects.filter(is_employer=True, jobs__isnull=False)
        .distinct()
        .count()
    )
    active_seekers = (
        CustomUser.objects.filter(is_employer=False, job_applications__isnull=False)
        .distinct()
        .count()
    )

    # === RECENT ===
    recent_jobs = Job.objects.order_by("-created_at")[:5]
    recent_applications = JobApplication.objects.order_by("-applied_at")[:5]
    recent_applicants = CustomUser.objects.filter(is_employer=False).order_by("-date_joined")[:5]
    recent_employers = CustomUser.objects.filter(is_employer=True).order_by("-date_joined")[:5]

    # === PIE CHART (Applicants vs Employers) ===
    total_applicants = total_seekers

    # === BAR CHART (Jobs per Employer) ===
    jobs_per_employer = (
        Job.objects.values("posted_by__username")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    employers_names = [item["posted_by__username"] for item in jobs_per_employer]
    job_counts = [item["count"] for item in jobs_per_employer]

    # === LINE CHART (Applications trend) ===
    applications_query = JobApplication.objects.all()
    if start_date:
        applications_query = applications_query.filter(applied_at__date__gte=start_date)

    applications_per_day = (
        applications_query.annotate(date=TruncDate("applied_at"))
        .values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )
    dates = [item["date"].strftime("%Y-%m-%d") for item in applications_per_day]
    applications_count = [item["total"] for item in applications_per_day]

    # === JOBS PER MONTH (for extra bar chart) ===
    jobs_per_month = (
        Job.objects.annotate(month=TruncDate("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    chart_labels = [item["month"].strftime("%Y-%m-%d") for item in jobs_per_month]
    chart_data = [item["total"] for item in jobs_per_month]

    # === CONTEXT ===
    context = {
        "total_users": total_users,
        "total_employers": total_employers,
        "total_seekers": total_seekers,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "active_employers": active_employers,
        "active_seekers": active_seekers,
        "recent_jobs": recent_jobs,
        "recent_applications": recent_applications,
        "recent_applicants": recent_applicants,
        "recent_employers": recent_employers,
        "total_applicants": total_applicants,
        "employers": employers_names,
        "job_counts": job_counts,
        "dates": dates,
        "applications_count": applications_count,
        "timeframe": timeframe,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "filtered_employers": filtered_employers,
    }

    return render(request, "adminpanel/dashboard.html", context)


# ✅ Trend data for AJAX
@login_required
@admin_required
def applications_trend_data(request):
    timeframe = request.GET.get("timeframe", "7")
    today = timezone.now().date()

    if timeframe == "30":
        start_date = today - timedelta(days=29)
    elif timeframe == "all":
        start_date = JobApplication.objects.order_by("applied_at").first().applied_at.date()
    else:
        start_date = today - timedelta(days=6)

    # Query applications
    applications_query = JobApplication.objects.filter(applied_at__date__gte=start_date)

    applications_per_day = (
        applications_query.annotate(date=TruncDate("applied_at"))
        .values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )

    # Build dict {date: count}
    applications_dict = {item["date"]: item["total"] for item in applications_per_day}

    # Fill missing days with zero
    dates = []
    applications_count = []
    current_date = start_date
    while current_date <= today:
        dates.append(current_date.strftime("%Y-%m-%d"))
        applications_count.append(applications_dict.get(current_date, 0))
        current_date += timedelta(days=1)

    return JsonResponse({
        "dates": dates,
        "applications_count": applications_count,
    })

@admin_required
def activate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_employer=True)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.username} has been activated.")
    return redirect("adminpanel:employers_overview")

@admin_required
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, is_employer=True)
    user.is_active = False
    user.save()
    messages.warning(request, f"{user.username} has been deactivated.")
    return redirect("adminpanel:employers_overview")


@login_required
@admin_required
@require_POST
def delete_user(request, user_id):
    print("✅ DELETE triggered with user_id:", user_id)  # Debug
    user = get_object_or_404(CustomUser, id=user_id, is_employer=True)
    username = user.username
    user.delete()
    messages.success(request, f"Employer '{username}' has been deleted.")
    return redirect("adminpanel:employers_overview")

@login_required
def inbox(request):
    messages = Message.objects.filter(receiver=request.user).order_by("-timestamp")
    return render(request, "adminpanel/messages/inbox.html", {"messages": messages})

@login_required
def sent_messages(request):
    messages = Message.objects.filter(sender=request.user).order_by("-timestamp")
    return render(request, "adminpanel/messages/sent.html", {"messages": messages})

@login_required
def send_message_form(request):
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            messages.success(request, "Message sent successfully ✅")
            return redirect("adminpanel:inbox")
    else:
        form = MessageForm()
    return render(request, "adminpanel/messages/send.html", {"form": form})

@login_required
def message_detail(request, pk):
    msg = get_object_or_404(Message, id=pk)

    if msg.receiver == request.user and not msg.is_read:
        msg.is_read = True
        msg.save()

    return render(request, "adminpanel/messages/detail.html", {"message": msg})


@login_required
@admin_required
def user_list(request):
    query = request.GET.get("q", "")
    role = request.GET.get("role", "")

    users = CustomUser.objects.all().select_related("profile")

    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    if role:
        users = users.filter(profile__role=role)

    context = {"users": users}
    return render(request, "adminpanel/user_list.html", context)


def applications_overview(request):
    applications = JobApplication.objects.select_related("job", "applicant").all().order_by("-applied_at")
    return render(request, "adminpanel/applications_overview.html", {"applications": applications})

@login_required
@admin_required
def employers_overview(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    employers = CustomUser.objects.filter(is_employer=True)

    if search_query:
        employers = employers.filter(username__icontains=search_query)

    if status_filter == "active":
        employers = employers.filter(is_active=True)
    elif status_filter == "inactive":
        employers = employers.filter(is_active=False)

    # 🔹 Add pagination
    paginator = Paginator(employers.order_by("-date_joined"), 5)  # 5 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "adminpanel/employers_overview.html", context)

@login_required
@admin_required
def employer_detail(request, pk):
    employer = get_object_or_404(User, pk=pk, is_employer=True)

    # Get jobs posted by this employer
    jobs = Job.objects.filter(posted_by=employer)

    # Get applications for jobs posted by this employer
    applications = JobApplication.objects.filter(job__posted_by=employer)

    return render(request, "adminpanel/employer_detail.html", {
        "employer": employer,
        "jobs": jobs,
        "applications": applications,
    })


