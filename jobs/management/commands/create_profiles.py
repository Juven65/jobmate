from django.core.management.base import BaseCommand
from django.conf import settings
from jobs.models import Profile
from employer.models import EmployerProfile

User = settings.AUTH_USER_MODEL

class Command(BaseCommand):
    help = "Create missing Profile and EmployerProfile for existing users"

    def handle(self, *args, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        created_profiles = 0
        created_employers = 0

        for user in User.objects.all():
            # ✅ Create Profile if missing
            if not hasattr(user, "profile"):
                Profile.objects.create(user=user)
                created_profiles += 1

            # ✅ Create EmployerProfile if missing and user is employer
            if user.is_employer and not hasattr(user, "employerprofile"):
                EmployerProfile.objects.create(user=user)
                created_employers += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created {created_profiles} Profile(s) and {created_employers} EmployerProfile(s)."
            )
        )
