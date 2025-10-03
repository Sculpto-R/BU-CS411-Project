from django.core import signing
from django.conf import settings

SALT = 'accounts.email.confirmation'

def make_email_token(email):
    signer = signing.TimestampSigner(salt=SALT)
    return signer.sign(email)

def check_email_token(token, max_age=None):
    signer = signing.TimestampSigner(salt=SALT)
    if max_age is None:
        max_age = getattr(settings, 'EMAIL_VERIFICATION_EXPIRY', 3 * 24 * 3600)
    try:
        email = signer.unsign(token, max_age=max_age)
        return email
    except signing.SignatureExpired:
        return None
    except signing.BadSignature:
        return None
