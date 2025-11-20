from django.db.models import Q
from .models import Job, JobApplication, SavedJob

def get_recommended_jobs(user, limit=5):
    """
    Return personalized job recommendations for a given user.
    Looks at past applications, saved jobs, and profile skills.
    """
    if not user.is_authenticated:
        return Job.objects.none()

    applications = JobApplication.objects.filter(applicant=user).select_related("job")
    saved = SavedJob.objects.filter(user=user).select_related("job")

    applied_ids = applications.values_list("job_id", flat=True)
    saved_ids = saved.values_list("job_id", flat=True)
    exclude_ids = list(applied_ids) + list(saved_ids)

    q_filter = Q()

    # 1️⃣ Based on past applied/saved jobs
    for app in applications:
        q_filter |= Q(title__icontains=app.job.title) | Q(company__icontains=app.job.company)
    for s in saved:
        q_filter |= Q(title__icontains=s.job.title) | Q(company__icontains=s.job.company)

    # 2️⃣ Based on user skills (Profile.skills = comma separated string)
    profile = getattr(user, "profile", None)
    if profile and profile.skills:
        skills = [skill.strip() for skill in profile.skills.split(",") if skill.strip()]
        for skill in skills:
            q_filter |= Q(title__icontains=skill) | Q(description__icontains=skill)

    # 3️⃣ Query
    if q_filter:
        jobs = Job.objects.filter(q_filter).exclude(id__in=exclude_ids).order_by("-id")
    else:
        jobs = Job.objects.exclude(id__in=exclude_ids).order_by("-id")

    return jobs[:limit]
