import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password):
            raise ValidationError(
                _("Password must be at least 8 characters long and contain an uppercase letter, a lowercase letter, a number, and a special character."),
                code="password_strength",
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, including uppercase, lowercase, number, and special character."
        )
