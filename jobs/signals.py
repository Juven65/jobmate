from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from jobs.models import Profile
from employer.models import EmployerProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        # ✅ Always create Profile for all users
        Profile.objects.create(user=instance)

        # ✅ Only create EmployerProfile if user is employer
        if instance.is_employer:
            EmployerProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_profiles(sender, instance, **kwargs):
    # ✅ Save Profile if it exists
    if hasattr(instance, "profile"):
        instance.profile.save()

    # ✅ Save EmployerProfile if it exists
    if hasattr(instance, "employerprofile"):
        instance.employerprofile.save()
