from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Get profile role
                role = getattr(request.user.profile, "role", None)

                # 🔑 Admin override (staff/superuser)
                if request.user.is_superuser or request.user.is_staff:
                    return view_func(request, *args, **kwargs)

                # Check kung pasok sa allowed roles
                if role in allowed_roles:
                    return view_func(request, *args, **kwargs)

                raise PermissionDenied  # Forbidden page (403)
            return redirect("login")  # Kung di naka-login
        return wrapper
    return decorator
