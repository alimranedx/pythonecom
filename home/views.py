from django.db.models import Q
from django.shortcuts import render
from product.models import Category, Product, Brand


def index(request):
    featured_categories = Category.objects.filter(is_featured=True)[:12]
    flash_sales = Product.objects.filter(is_active=True, is_flash_sale=True)[:12]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    brands = Brand.objects.all()[:8]

    # Best deals / featured / flash sale products for hero slider
    slider_candidates = (
        Product.objects.filter(is_active=True)
        .filter(Q(is_flash_sale=True) | Q(is_featured=True) | Q(discount_price__isnull=False))
        .select_related('category', 'brand')
        .distinct()
        .order_by('-is_featured', '-is_flash_sale', '-price')[:5]
    )

    slider_themes = [
        {
            'gradient': 'linear-gradient(135deg, #090e1a 0%, #1e293b 50%, #0f172a 100%)',
            'badge': 'Mega Deal of the Week',
            'icon': 'bi-stars',
            'badge_class': 'bg-primary',
            'tagline': 'Supercharged for Pros & Visionaries',
            'accent': '#38bdf8',
        },
        {
            'gradient': 'linear-gradient(135deg, #180928 0%, #2e1065 50%, #0f172a 100%)',
            'badge': 'Flash Sale • Limited Time',
            'icon': 'bi-lightning-charge-fill',
            'badge_class': 'bg-danger',
            'tagline': 'Next-Generation AI Flagship Experience',
            'accent': '#e879f9',
        },
        {
            'gradient': 'linear-gradient(135deg, #022c22 0%, #064e3b 50%, #022c22 100%)',
            'badge': 'Performance & Lifestyle',
            'icon': 'bi-fire',
            'badge_class': 'bg-warning text-dark',
            'tagline': 'Engineered for Supreme Comfort & Speed',
            'accent': '#34d399',
        },
        {
            'gradient': 'linear-gradient(135deg, #111827 0%, #1f2937 50%, #030712 100%)',
            'badge': 'Premium Bestseller',
            'icon': 'bi-award-fill',
            'badge_class': 'bg-info text-dark',
            'tagline': 'Forged in Titanium • Pure Power',
            'accent': '#93c5fd',
        },
        {
            'gradient': 'linear-gradient(135deg, #31135e 0%, #4a044e 50%, #1e1b4b 100%)',
            'badge': 'Exclusive Best Offer',
            'icon': 'bi-gem',
            'badge_class': 'bg-danger',
            'tagline': 'Adventure-Ready Precision Technology',
            'accent': '#f43f5e',
        },
    ]

    slider_items = []
    for idx, product in enumerate(slider_candidates):
        theme = slider_themes[idx % len(slider_themes)]
        savings = (product.price - product.discount_price) if product.has_discount else 0
        slider_items.append({
            'product': product,
            'theme': theme,
            'savings': savings,
            'rating': 4.9 if (idx % 2 == 0) else 4.8,
            'reviews_count': 128 + (idx * 43),
        })

    return render(request, 'home/index.html', {
        'slider_items': slider_items,
        'featured_categories': featured_categories,
        'flash_sales': flash_sales,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'brands': brands,
    })
