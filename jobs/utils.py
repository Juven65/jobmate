from django.core.signing import TimestampSigner
signer = TimestampSigner()

def generate_token(user):
    return signer.sign(user.pk)

def verify_token(token, max_age=3600):  # 1 hour expiry
    from django.core.signing import BadSignature, SignatureExpired
    from .models import CustomUser
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return CustomUser.objects.get(pk=user_id)
    except (BadSignature, SignatureExpired, CustomUser.DoesNotExist):
        return None