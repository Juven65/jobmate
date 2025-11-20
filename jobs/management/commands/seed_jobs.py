from django.core.management.base import BaseCommand
from jobs.models import Job, JobApplication, CustomUser
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Seed the database with dummy job applications"

    def handle(self, *args, **kwargs):
        job = Job.objects.first()
        user = CustomUser.objects.filter(is_employer=False).first()

        if not job:
            self.stdout.write(self.style.ERROR("❌ No Job found. Create a Job first."))
            return

        if not user:
            self.stdout.write(self.style.ERROR("❌ No User found. Create a non-employer user first."))
            return

        for i in range(10):
            JobApplication.objects.create(
                job=job,
                applicant=user,
                full_name=f"Test User {i+1}",
                email=f"test{i+1}@example.com",
                resume="dummy.pdf",
                applied_at=timezone.now() - timedelta(days=i)
            )

        self.stdout.write(self.style.SUCCESS("✅ Successfully seeded 10 Job Applications"))
