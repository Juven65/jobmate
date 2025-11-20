from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import EmployerProfile

@receiver(post_save, sender=User)
def create_employer_profile(sender, instance, created, **kwargs):
    if created:
        EmployerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_employer_profile(sender, instance, **kwargs):
    instance.employer_profile.save()
