from django.db.models import Q
from django.shortcuts import render
from product.models import Category, Product, Brand
from core.models import SiteSetting
from core.themes import THEMES, DEFAULT_THEME_KEY


def _filter_and_prioritize_categories(cat_slugs, limit=24):
    """
    Returns up to `limit` categories. If `cat_slugs` is provided, categories matching
    those slugs are prioritized at the front. If the count is below `limit`, gracefully falls back
    to include other featured categories, followed by remaining active categories.
    """
    if not cat_slugs:
        featured = list(Category.objects.filter(is_featured=True).order_by('order', 'name')[:limit])
        if len(featured) < limit:
            existing_ids = [c.id for c in featured]
            more = list(
                Category.objects.exclude(id__in=existing_ids).order_by('order', 'name')[:(limit - len(featured))]
            )
            featured.extend(more)
        return featured

    # Prioritize theme-specific categories matching slug list
    theme_cats = list(Category.objects.filter(slug__in=cat_slugs).order_by('order', 'name'))

    # Graceful fallback: supplement with other featured categories, then any categories
    if len(theme_cats) < limit:
        existing_ids = [c.id for c in theme_cats]
        needed = limit - len(theme_cats)
        other_featured = list(
            Category.objects.filter(is_featured=True)
            .exclude(id__in=existing_ids)
            .order_by('order', 'name')[:needed]
        )
        theme_cats.extend(other_featured)

        if len(theme_cats) < limit:
            existing_ids = [c.id for c in theme_cats]
            needed_more = limit - len(theme_cats)
            other_cats = list(
                Category.objects.exclude(id__in=existing_ids)
                .order_by('order', 'name')[:needed_more]
            )
            theme_cats.extend(other_cats)

    return theme_cats[:limit]


def _filter_and_prioritize_brands(brand_slugs, limit=12):
    """
    Returns up to `limit` brands. If `brand_slugs` is provided, brands matching
    those slugs are placed first. Falls back to other brands if fewer than `limit`.
    """
    if not brand_slugs:
        return list(Brand.objects.all().order_by('name')[:limit])

    theme_brands = list(Brand.objects.filter(slug__in=brand_slugs).order_by('name'))

    if len(theme_brands) < limit:
        existing_ids = [b.id for b in theme_brands]
        needed = limit - len(theme_brands)
        other_brands = list(
            Brand.objects.exclude(id__in=existing_ids).order_by('name')[:needed]
        )
        theme_brands.extend(other_brands)

    return theme_brands[:limit]


def _filter_and_prioritize_products(base_qs, theme_q, limit, fallback_qs=None):
    """
    Returns up to `limit` products from `base_qs`, prioritizing those matching `theme_q`.
    If fewer than `limit` match, gracefully falls back to include other active products
    so no section is ever empty or sparse.
    """
    if not theme_q:
        return list(base_qs[:limit])

    # 1. Primary: Products in base_qs matching active theme
    theme_matches = list(base_qs.filter(theme_q).distinct()[:limit])
    count = len(theme_matches)

    # 2. Graceful fallback: other products from base_qs
    if count < limit:
        matched_ids = [p.id for p in theme_matches]
        needed = limit - count
        base_fallback = list(base_qs.exclude(id__in=matched_ids).distinct()[:needed])
        theme_matches.extend(base_fallback)

        # 3. Secondary fallback: pull from general active products if base_qs was sparse
        if len(theme_matches) < limit and fallback_qs is not None:
            all_ids = [p.id for p in theme_matches]
            needed_more = limit - len(theme_matches)
            secondary_fallback = list(fallback_qs.exclude(id__in=all_ids).distinct()[:needed_more])
            theme_matches.extend(secondary_fallback)

    return theme_matches


def index(request):
    # 1. Resolve active theme (preview via ?theme=<key> takes precedence for testing/admin)
    preview_theme = request.GET.get('theme') if hasattr(request, 'GET') else None
    if preview_theme and preview_theme in THEMES:
        active_theme_key = preview_theme
    else:
        settings = SiteSetting.get_settings()
        active_theme_key = getattr(settings, 'active_theme', DEFAULT_THEME_KEY) or DEFAULT_THEME_KEY
        if active_theme_key not in THEMES:
            active_theme_key = DEFAULT_THEME_KEY

    theme_config = THEMES.get(active_theme_key, THEMES[DEFAULT_THEME_KEY])
    cat_slugs = theme_config.get('category_slugs')
    brand_slugs = theme_config.get('brand_slugs')

    # Build Q filter for theme products
    theme_q = Q()
    if cat_slugs:
        theme_q |= Q(category__slug__in=cat_slugs)
    if brand_slugs:
        theme_q |= Q(brand__slug__in=brand_slugs)

    # 2. Filter & Prioritize Categories and Brands
    featured_categories = _filter_and_prioritize_categories(cat_slugs, limit=24)
    brands = _filter_and_prioritize_brands(brand_slugs, limit=12)

    # 3. Base Querysets for Products with Select Related
    all_active_products = Product.objects.filter(is_active=True).select_related('category', 'brand')

    base_slider_qs = (
        all_active_products
        .filter(Q(is_flash_sale=True) | Q(is_featured=True) | Q(discount_price__isnull=False))
        .order_by('-is_featured', '-is_flash_sale', '-price')
    )
    slider_candidates = _filter_and_prioritize_products(
        base_slider_qs,
        theme_q,
        limit=5,
        fallback_qs=all_active_products.order_by('-price')
    )

    base_flash_qs = all_active_products.filter(is_flash_sale=True).order_by('-discount_price', '-price')
    flash_sales = _filter_and_prioritize_products(
        base_flash_qs,
        theme_q,
        limit=12,
        fallback_qs=all_active_products.filter(discount_price__isnull=False).order_by('-price')
    )

    base_featured_qs = all_active_products.filter(is_featured=True).order_by('-created_at')
    featured_products = _filter_and_prioritize_products(
        base_featured_qs,
        theme_q,
        limit=8,
        fallback_qs=all_active_products.order_by('-created_at')
    )

    base_latest_qs = all_active_products.order_by('-created_at')
    latest_products = _filter_and_prioritize_products(
        base_latest_qs,
        theme_q,
        limit=8
    )

    # 4. Hero Slider Customizations
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
        'slider_candidates': slider_candidates,
        'featured_categories': featured_categories,
        'flash_sales': flash_sales,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'brands': brands,
        'active_theme_key': active_theme_key,
    })
