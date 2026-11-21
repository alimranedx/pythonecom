from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from core.validators import validate_image_file
from rbac.models import Role, UserRole
from core.models import SiteSetting
from product.forms import ProductForm, CategoryForm, BrandForm


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
            'active_theme',
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
            'active_theme': forms.Select(attrs={'class': 'form-select', 'id': 'activeThemeSelect'}),
            'site_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Easy Purchase'}),
            'site_tagline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Modern E-Commerce Marketplace'}),
            'brand_logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'brand_favicon': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'announcement_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'announcementEnabledCheck'}),
            'announcement_text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Free Express Shipping on orders over ৳500!'}),
            'announcement_text_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '৳৫০০ এর বেশি অর্ডারে ফ্রি এক্সপ্রেস ডেলিভারি!'}),
            'customer_care_text_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '24/7 Customer Care'}),
            'customer_care_text_bn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '২৪/৭ কাস্টমার কেয়ার'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+880 1700-000000'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'support@easypuchase.com'}),
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
            'copyright_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '© 2026 Easy Purchase. All rights reserved.'}),
            'subfooter_notice': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engineered with Clean Architecture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'active_theme' in self.fields:
            self.fields['active_theme'].required = False

    def clean_active_theme(self):
        theme = self.cleaned_data.get('active_theme')
        if not theme and self.instance and self.instance.active_theme:
            return self.instance.active_theme
        return theme or 'mega_market'

    def clean_brand_logo(self):
        logo = self.cleaned_data.get('brand_logo')
        if logo:
            validate_image_file(logo)
        return logo

    def clean_brand_favicon(self):
        favicon = self.cleaned_data.get('brand_favicon')
        if favicon:
            validate_image_file(favicon)
        return favicon

class AdminProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError("Username cannot be empty.")
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken by another account.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError("Email address cannot be empty.")
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already associated with another account.")
        return email


class AdminPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ThemeCustomizeForm(forms.Form):
    """
    Dynamic configuration form generated from a theme's customization_schema.
    Supports typed setting definitions (boolean, select, text, color, number)
    organized by sections (header, homepage, product_display, footer, etc.)
    and custom CSS overrides.
    """
    custom_css = forms.CharField(
        required=False,
        label="Custom CSS Overrides",
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 6,
            'placeholder': '/* Enter custom CSS rules to override theme styling */'
        }),
        help_text="Custom scoped CSS rules applied specifically when this theme is active."
    )

    def __init__(self, schema=None, initial_data=None, initial_css='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema = schema or {}
        self.section_groups = []
        self._schema_field_names = set()

        if initial_css:
            self.fields['custom_css'].initial = initial_css

        # Normalize schema into list of section dicts:
        # Each section: {'id': ..., 'title': ..., 'icon': ..., 'description': ..., 'fields': [...]}
        normalized_sections = self._parse_schema(self.schema)

        for sec in normalized_sections:
            sec_fields = []
            for item in sec.get('settings', []):
                key = item.get('key')
                if not key:
                    continue
                self._schema_field_names.add(key)
                field_type = item.get('type', 'text').lower()
                label = item.get('label', key.replace('_', ' ').title())
                help_text = item.get('help_text', item.get('description', ''))
                default_val = item.get('default')

                # Determine initial value: initial_data takes priority, then default_val
                curr_val = None
                if initial_data and key in initial_data:
                    curr_val = initial_data[key]
                elif default_val is not None:
                    curr_val = default_val

                if field_type == 'boolean':
                    field = forms.BooleanField(
                        required=False,
                        label=label,
                        initial=bool(curr_val) if curr_val is not None else False,
                        help_text=help_text,
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                    )
                elif field_type == 'select':
                    raw_choices = item.get('choices', [])
                    choices = []
                    for c in raw_choices:
                        if isinstance(c, (list, tuple)) and len(c) >= 2:
                            choices.append((str(c[0]), str(c[1])))
                        else:
                            choices.append((str(c), str(c).replace('_', ' ').title()))
                    field = forms.ChoiceField(
                        required=False,
                        label=label,
                        choices=choices,
                        initial=str(curr_val) if curr_val is not None else '',
                        help_text=help_text,
                        widget=forms.Select(attrs={'class': 'form-select'})
                    )
                elif field_type == 'color':
                    field = forms.CharField(
                        required=False,
                        label=label,
                        initial=str(curr_val) if curr_val is not None else '#000000',
                        help_text=help_text,
                        widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'style': 'width: 60px; height: 38px; padding: 4px;'})
                    )
                elif field_type in ('number', 'integer'):
                    field = forms.IntegerField(
                        required=False,
                        label=label,
                        initial=curr_val,
                        help_text=help_text,
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                elif field_type == 'textarea':
                    field = forms.CharField(
                        required=False,
                        label=label,
                        initial=str(curr_val) if curr_val is not None else '',
                        help_text=help_text,
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    )
                else:  # default text
                    field = forms.CharField(
                        required=False,
                        label=label,
                        initial=str(curr_val) if curr_val is not None else '',
                        help_text=help_text,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )

                self.fields[key] = field
                sec_fields.append({
                    'key': key,
                    'type': field_type,
                    'label': label,
                    'help_text': help_text,
                    'bound_field': self[key],
                })

            self.section_groups.append({
                'id': sec.get('id', 'general'),
                'title': sec.get('title', 'General'),
                'icon': sec.get('icon', 'bi-sliders'),
                'description': sec.get('description', ''),
                'fields': sec_fields
            })

    def _parse_schema(self, schema):
        sections = []
        if isinstance(schema, list):
            for sec in schema:
                if isinstance(sec, dict):
                    settings_list = sec.get('settings') or sec.get('fields') or []
                    if isinstance(settings_list, dict):
                        transformed = []
                        for k, v in settings_list.items():
                            item = dict(v) if isinstance(v, dict) else {'type': 'text'}
                            item['key'] = k
                            transformed.append(item)
                        settings_list = transformed
                    sections.append({
                        'id': sec.get('id', 'section'),
                        'title': sec.get('title', sec.get('name', 'Section')),
                        'icon': sec.get('icon', 'bi-sliders'),
                        'description': sec.get('description', ''),
                        'settings': settings_list
                    })
        elif isinstance(schema, dict):
            # Dict of sections e.g. {'header': {'title': '...', 'fields': {...}}} or {'sections': [...]}
            if 'sections' in schema and isinstance(schema['sections'], list):
                return self._parse_schema(schema['sections'])
            for sec_id, sec_data in schema.items():
                if isinstance(sec_data, dict):
                    title = sec_data.get('title', sec_id.replace('_', ' ').title())
                    icon = sec_data.get('icon', 'bi-sliders')
                    desc = sec_data.get('description', '')
                    settings_list = sec_data.get('settings') or sec_data.get('fields') or []
                    if isinstance(settings_list, dict):
                        transformed = []
                        for k, v in settings_list.items():
                            item = dict(v) if isinstance(v, dict) else {'type': 'text'}
                            item['key'] = k
                            transformed.append(item)
                        settings_list = transformed
                    sections.append({
                        'id': sec_id,
                        'title': title,
                        'icon': icon,
                        'description': desc,
                        'settings': settings_list
                    })
        return sections

    def get_customization_data(self):
        """
        Extracts cleaned values belonging to schema fields as a JSON-serializable dict.
        """
        data = {}
        for key in self._schema_field_names:
            if key in self.cleaned_data:
                data[key] = self.cleaned_data[key]
        return data

    def get_custom_css(self):
        return self.cleaned_data.get('custom_css', '').strip()


