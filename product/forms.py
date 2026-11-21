from django import forms
from core.validators import validate_image_file
from .models import Product, Category, Brand


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'brand', 'theme', 'short_description', 'description',
            'price', 'discount_price', 'stock', 'unit', 'image', 'is_featured', 'is_flash_sale', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'category': forms.Select(attrs={'class': 'form-select searchable-select', 'data-placeholder': 'Please Select Category'}),
            'brand': forms.Select(attrs={'class': 'form-select searchable-select', 'data-placeholder': 'Please Select Brand'}),
            'theme': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Select Storefront Theme'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief tagline/catchphrase'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00 (optional)', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Available quantity'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1 kg, 500 gm, 1 ltr, 12 pcs, 1 pc'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_flash_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category' in self.fields:
            self.fields['category'].empty_label = "Please Select Category"
        if 'brand' in self.fields:
            self.fields['brand'].empty_label = "Please Select Brand"
        if 'theme' in self.fields:
            self.fields['theme'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'theme', 'icon', 'parent', 'is_featured', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'leave-blank-for-auto-slug'}),
            'theme': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Select Storefront Theme'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-laptop, bi-phone, bi-tag'}),
            'parent': forms.Select(attrs={'class': 'form-select searchable-select', 'data-placeholder': 'Please Select Parent Category (None - Top Level)'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'parent' in self.fields:
            self.fields['parent'].empty_label = "Please Select Parent Category (None - Top Level)"
        if 'theme' in self.fields:
            self.fields['theme'].required = False
        if 'icon' in self.fields:
            self.fields['icon'].required = False
        if 'slug' in self.fields:
            self.fields['slug'].required = False

    def clean_icon(self):
        return self.cleaned_data.get('icon') or 'bi-tag'


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'theme', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name (e.g. Apple, Nike)'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'leave-blank-for-auto-slug'}),
            'theme': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Select Storefront Theme'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'theme' in self.fields:
            self.fields['theme'].required = False

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            validate_image_file(logo)
        return logo
