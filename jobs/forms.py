from django import forms
from django.contrib.auth import get_user_model
from .models import Job, JobApplication, Profile
from django.core.exceptions import ValidationError
import re

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'description', 'location', 'salary', 'image']

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['full_name', 'email', 'resume', 'message']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'full_name', 'address', 'phone', 'bio']

User = get_user_model()

class RegisterForm(forms.ModelForm):
    ROLE_CHOICES = [
        ("jobseeker", "Job Seeker"),
        ("employer", "Employer"),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,  # or Select if you prefer dropdown
        label="Register as"
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username", "email", "role"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # secure hashing

        # ✅ Role handling
        role = self.cleaned_data.get("role")
        if role == "employer":
            user.is_employer = True
        else:
            user.is_employer = False

        if commit:
            user.save()
        return user

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password):
            raise ValidationError(
                "Password must be at least 8 characters long, include an uppercase, lowercase, number, and special character.",
                code="password_strength",
            )

    def get_help_text(self):
        return "Your password must be at least 8 chars long, contain upper/lowercase, number, and special char."