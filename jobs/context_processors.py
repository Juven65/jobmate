# context_processors.py
from .models import JobApplication, Notification
from django.db.models import Q

def application_notifications(request):
    """Context processor to provide real-time notifications across all templates."""
    if not request.user.is_authenticated:
        return {"updated_count": 0, "notifications": []}

    user = request.user

    # 🔹 Job Seeker: notifications for status updates
    jobseeker_notifs = JobApplication.objects.filter(
        applicant=user,
        has_seen=False
    ).exclude(status="Pending").select_related("job")

    # 🔹 Employer: notifications for new job applications
    employer_notifs = JobApplication.objects.filter(
        job__posted_by=user,   # ✅ fixed field name
        has_seen=False
    ).select_related("job", "applicant")

    # 🔹 System-wide notifications (optional)
    system_notifs = Notification.objects.filter(
        Q(user=user) | Q(user=None),
        is_read=False
    ) if hasattr(Notification, "objects") else []

    # 🔹 Combine and cap results
    all_notifs = list(jobseeker_notifs[:5]) + list(employer_notifs[:5]) + list(system_notifs[:5])
    updated_count = len(all_notifs)

    return {
        "updated_count": updated_count,
        "notifications": all_notifs[:5],  # Limit to latest 5
    }
