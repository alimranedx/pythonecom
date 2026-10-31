import re
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from .models import CustomerProfile


def normalize_phone_number(raw_phone):
    """
    Normalizes a mobile or telephone number into standard digits format.
    Handles Bangladeshi numbers:
      - 01712345678 -> 01712345678
      - +8801712345678 -> 01712345678
      - 8801712345678 -> 01712345678
      - 017-1234-5678 -> 01712345678
    """
    if not raw_phone:
        return ''
    cleaned = re.sub(r'[\s\-\(\)\+]', '', str(raw_phone)).strip()
    if cleaned.startswith('880') and len(cleaned) == 13:
        return cleaned[2:]
    elif cleaned.startswith('88') and len(cleaned) == 12:
        return '0' + cleaned[2:]
    return cleaned


class PhoneOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend allowing customers to log in using:
    1. Mobile Phone Number (CustomerProfile.phone or User.username)
    2. Email Address (User.email)
    3. Standard Username (User.username)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identifier = str(username).strip()
        norm_phone = normalize_phone_number(identifier)
        user = None

        # 1. Look up by phone number if digits-like
        if norm_phone and norm_phone.isdigit() and len(norm_phone) >= 10:
            profile = CustomerProfile.objects.filter(phone=norm_phone).select_related('user').first()
            if profile and profile.user:
                user = profile.user
            else:
                user = User.objects.filter(username__iexact=norm_phone).first()

        # 2. Look up by email address if '@' is present
        if not user and '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()

        # 3. Look up by direct username
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()

        # Verify password and active status
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
