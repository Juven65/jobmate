from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser


# ✅ BaseModel for universal timestamps
class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)  # 🔹 instead of auto_now_add
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# ✅ Custom User Model
class CustomUser(AbstractUser):
    is_verified = models.BooleanField(default=False)
    is_employer = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Job(BaseModel):
    CATEGORY_CHOICES = [
        ('IT', 'Information Technology'),
        ('ENG', 'Engineering'),
        ('MKT', 'Marketing'),
        ('SALES', 'Sales'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    image = models.ImageField(upload_to='job_images/', null=True, blank=True)

    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs")
    posted_at = models.DateTimeField(auto_now_add=True)

    # 🔹 NEW FIELD
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide this job posting")

    def __str__(self):
        return f"{self.title} - {self.company}"


class JobApplication(BaseModel):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_applications")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    resume = models.FileField(upload_to="resumes/")
    message = models.TextField(blank=True, null=True)
    has_seen = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    applied_at = models.DateTimeField(auto_now_add=True)  # 🔹 descriptive field

    def __str__(self):
        return f"{self.full_name} applied for {self.job.title}"


class Profile(BaseModel):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ('employer', 'Employer'),
        ('jobseeker', 'Job Seeker'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='jobseeker')
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default.png')
    full_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class SavedJob(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)  # 🔹 descriptive field

    class Meta:
        unique_together = ("user", "job")

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"
