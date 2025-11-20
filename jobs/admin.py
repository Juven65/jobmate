from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Job, JobApplication, Profile, SavedJob

# ✅ Custom User
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "email", "is_staff", "is_active", "is_verified")
    list_filter = ("is_staff", "is_active", "is_verified")
    search_fields = ("username", "email")
    ordering = ("username",)


# ✅ Job
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title", "company", "category", "location",
        "posted_at", "posted_by", "is_active"
    )
    search_fields = ("title", "company")
    list_filter = ("category", "posted_at", "is_active")  # ✅ may filter na for active/inactive
    readonly_fields = ("created_at", "updated_at", "posted_at")

    actions = ["make_active", "make_inactive"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # bagong Job
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)

    # ✅ Bulk actions
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} job(s) marked as active.")
    make_active.short_description = "Mark selected jobs as active"

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} job(s) marked as inactive.")
    make_inactive.short_description = "Mark selected jobs as inactive"


# ✅ Job Application
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "full_name", "email", "applied_at", "status")
    search_fields = ("full_name", "email", "job__title")
    list_filter = ("applied_at", "job", "status")
    readonly_fields = ("created_at", "updated_at", "applied_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # bagong Application
            obj.applicant = request.user
        super().save_model(request, obj, form, change)


# ✅ Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "full_name", "phone", "created_at", "updated_at")
    search_fields = ("user__username", "full_name", "phone")
    list_filter = ("role", "created_at")
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # bagong Profile
            obj.user = request.user
        super().save_model(request, obj, form, change)


# ✅ Saved Job
@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "saved_at")
    search_fields = ("user__username", "job__title")
    readonly_fields = ("created_at", "updated_at", "saved_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # bagong Saved Job
            obj.user = request.user
        super().save_model(request, obj, form, change)
