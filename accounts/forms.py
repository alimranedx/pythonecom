import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from core.validators import validate_image_file
from .models import CustomerProfile, Address
from .backends import normalize_phone_number


class CustomerRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name (Optional)',
            'autocomplete': 'family-name',
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01XXXXXXXXX',
            'type': 'tel',
            'autocomplete': 'tel',
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address (optional)',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password (min 6 characters)',
            'autocomplete': 'new-password',
        })
    )
    confirm_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        })
    )

    def clean_phone(self):
        raw_phone = self.cleaned_data.get('phone', '')
        norm_phone = normalize_phone_number(raw_phone)

        # Bangladeshi mobile numbers: 11 digits starting with 01
        if not (len(norm_phone) == 11 and norm_phone.startswith('01') and norm_phone.isdigit()):
            digits_only = re.sub(r'\D', '', str(raw_phone))
            if not (10 <= len(digits_only) <= 15):
                raise forms.ValidationError("Please enter a valid 11-digit mobile number (e.g. 017XXXXXXXX).")
            norm_phone = digits_only

        # Check uniqueness against CustomerProfile and User.username
        if CustomerProfile.objects.filter(phone=norm_phone).exists() or User.objects.filter(username__iexact=norm_phone).exists():
            raise forms.ValidationError("An account with this mobile number already exists. Please sign in.")

        return norm_phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError("An account with this email address already exists. Please sign in or use another email.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self):
        phone = self.cleaned_data['phone']
        email = self.cleaned_data.get('email', '')
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data.get('last_name', '')
        password = self.cleaned_data['password']

        user = User.objects.create_user(
            username=phone,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
        )
        CustomerProfile.objects.create(user=user, phone=phone)
        return user


class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Phone Number or Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter mobile number or email',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}))
    avatar = forms.ImageField(required=False, validators=[validate_image_file], widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    cropped_avatar_base64 = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Optional email address'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        if hasattr(self.instance, 'profile'):
            self.fields['phone'].initial = self.instance.profile.phone

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        profile.phone = self.cleaned_data.get('phone', '')
        if self.cleaned_data.get('avatar'):
            profile.avatar = self.cleaned_data['avatar']
        elif self.cleaned_data.get('cropped_avatar_base64'):
            b64_data = self.cleaned_data['cropped_avatar_base64']
            if 'data:image' in b64_data and ';base64,' in b64_data:
                import base64
                import time
                from django.core.files.base import ContentFile
                header, imgstr = b64_data.split(';base64,')
                ext = header.split('/')[-1]
                if ext == 'jpeg': ext = 'jpg'
                filename = f"avatar_{user.id}_{int(time.time())}.{ext}"
                profile.avatar.save(filename, ContentFile(base64.b64decode(imgstr)), save=False)
        profile.full_clean()
        profile.save()
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'street_address', 'apartment', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}),
            'apartment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apt, Suite, Unit (optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State / Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
