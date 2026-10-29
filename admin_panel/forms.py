# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from rbac.models import Role, UserRole
from core.models import SiteSetting


class StaffUserCreateForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="Please Select Role (Optional)",
        widget=forms.Select(attrs={'class': 'form-select searchable-select', 'data-placeholder': 'Please Select Role (Optional)'}),
        help_text="Assign an administrative RBAC role to grant module permissions."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. jdoe_admin'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@pythonecom.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class StaffUserEditForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        empty_label="Please Select Role (Optional)",
        widget=forms.Select(attrs={'class': 'form-select searchable-select', 'data-placeholder': 'Please Select Role (Optional)'}),
        help_text="Assign an administrative RBAC role to grant module permissions."
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep existing password'}),
        required=False,
        help_text="Optional: Leave blank to keep the current password."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@pythonecom.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_user_role = self.instance.user_roles.first()
            if current_user_role:
                self.fields['role'].initial = current_user_role.role_id

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = [
            'site_name', 'site_tagline', 'brand_logo', 'brand_favicon',
            'announcement_enabled', 'announcement_text_en', 'announcement_text_bn',
            'customer_care_text_en', 'customer_care_text_bn',
            'contact_phone', 'contact_email', 'contact_address',
            'about_text_en', 'about_text_bn',
            'social_facebook', 'social_twitter', 'social_instagram', 'social_github', 'social_linkedin',
            'newsletter_title_en', 'newsletter_title_bn', 'newsletter_text_en', 'newsletter_text_bn',
            'accepted_payments_text', 'copyright_text', 'subfooter_notice'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PythonEcom'}),
            'site_tagline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Modern E-Commerce Marketplace'}),
            'brand_logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'brand_favicon': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'announcement_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'announcementEnabledCheck'}),
            'announcement_text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Free Express Shipping on orders over ৳500!'}),
            'announcement_text_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '৳৫০০ এর বেশি অর্ডারে ফ্রি এক্সপ্রেস ডেলিভারি!'}),
            'customer_care_text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '24/7 Customer Care'}),
            'customer_care_text_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '২৪/৭ কাস্টমার কেয়ার'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+880 1700-000000'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'support@pythonecom.com'}),
            'contact_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dhaka, Bangladesh'}),
            'about_text_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Company description in English...'}),
            'about_text_bn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'কোম্পানির বিবরণ বাংলায়...'}),
            'social_facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/yourbrand'}),
            'social_twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/yourbrand'}),
            'social_instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/yourbrand'}),
            'social_github': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/yourbrand'}),
            'social_linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/company/yourbrand'}),
            'newsletter_title_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Newsletter'}),
            'newsletter_title_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'নিউজলেটার'}),
            'newsletter_text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subscribe to get special discounts...'}),
            'newsletter_text_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'বিশেষ মূল্যছাড় পেতে সাবস্ক্রাইব করুন...'}),
            'accepted_payments_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cash on Delivery, Cards, bKash / Nagad'}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '© 2026 PythonEcom. All rights reserved.'}),
            'subfooter_notice': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engineered with Clean Architecture'}),
        }
