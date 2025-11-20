from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import EmployerProfile
from django.http import JsonResponse
from jobs.models import Job, JobApplication
from .forms import EmployerProfileForm, ApplicationStatusForm, JobForm


# ✅ Helper function for status change
def change_application_status(app, new_status):
    """Centralized logic for updating JobApplication status."""
    valid_statuses = [choice[0] for choice in JobApplication.STATUS_CHOICES]
    if new_status in valid_statuses:
        app.status = new_status
        app.save()
        return True, app.status
    return False, "Invalid status"


# ✅ Employer Dashboard
class EmployerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "employer/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer_jobs = Job.objects.filter(posted_by=self.request.user)

        # Stats
        context["jobs"] = employer_jobs
        context["total_jobs"] = employer_jobs.count()
        context["total_applications"] = JobApplication.objects.filter(job__posted_by=self.request.user).count()
        context["hired_count"] = JobApplication.objects.filter(job__posted_by=self.request.user, status="Accepted").count()
        context["rejected_count"] = JobApplication.objects.filter(job__posted_by=self.request.user, status="Rejected").count()
        context["pending_count"] = JobApplication.objects.filter(job__posted_by=self.request.user, status="Pending").count()

        # Recent Applications
        context["recent_applications"] = (
            JobApplication.objects.filter(job__posted_by=self.request.user)
            .order_by("-applied_at")[:5]
        )

        # Activity Feed (jobs + applications)
        feed = []
        for job in employer_jobs.order_by("-created_at")[:5]:
            feed.append({"type": "job", "title": job.title, "date": job.created_at})
        for app in context["recent_applications"]:
            feed.append({
                "type": "application",
                "applicant": app.applicant.username,
                "job": app.job.title,
                "date": app.applied_at,
            })
        context["activity_feed"] = sorted(feed, key=lambda x: x["date"], reverse=True)

        return context


# ✅ Employer Job List
class EmployerJobListView(LoginRequiredMixin, ListView):
    model = Job
    template_name = "employer/job_list.html"
    context_object_name = "jobs"

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user)


# ✅ Edit Employer Profile
@login_required
def edit_profile(request):
    profile, created = EmployerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = EmployerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("employer:dashboard")
    else:
        form = EmployerProfileForm(instance=profile)
    return render(request, "employer/edit_profile.html", {"form": form})


# ✅ Employer Job Applications with Search & Filter
class EmployerApplicationsView(LoginRequiredMixin, ListView):
    model = JobApplication
    template_name = "employer/job_applications.html"
    context_object_name = "applications"

    def get_queryset(self):
        job_id = self.kwargs["job_id"]
        queryset = JobApplication.objects.filter(
            job__id=job_id, job__posted_by=self.request.user
        )

        # --- Search ---
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                applicant__username__icontains=search_query
            ) | queryset.filter(
                job__title__icontains=search_query
            )

        # --- Filter by Status ---
        status_filter = self.request.GET.get("status", "")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # --- Filter by Date ---
        date_filter = self.request.GET.get("date", "")
        if date_filter:
            from django.utils.dateparse import parse_date
            parsed_date = parse_date(date_filter)
            if parsed_date:
                queryset = queryset.filter(applied_at__date=parsed_date)

        return queryset.order_by("-applied_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("search", "")
        context["date_filter"] = self.request.GET.get("date", "")
        return context



# ✅ Application Status Update (Class-based)
class ApplicationStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = JobApplication
    form_class = ApplicationStatusForm
    template_name = "employer/application_status_update.html"

    def form_valid(self, form):
        app = form.save(commit=False)
        success, msg = change_application_status(app, form.cleaned_data["status"])
        if not success:
            form.add_error("status", msg)
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("employer:job_applications", kwargs={"job_id": self.object.job.id})

    def get_queryset(self):
        return JobApplication.objects.filter(job__posted_by=self.request.user)


# ✅ Application Status Update (Function-based)
@login_required
def update_application_status(request, pk):
    if request.method == "POST":
        app = get_object_or_404(JobApplication, pk=pk, job__posted_by=request.user)
        new_status = request.POST.get("status")

        success, msg = change_application_status(app, new_status)

        if success:
            return JsonResponse({"success": True, "status": app.status})
        else:
            return JsonResponse({"success": False, "error": msg}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# ✅ Create Job
class EmployerJobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = "employer/create_job.html"
    success_url = reverse_lazy("employer:job_list")

    def form_valid(self, form):
        form.instance.posted_by = self.request.user  # assign employer
        return super().form_valid(form)
