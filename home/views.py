from django.db.models import Q
from django.shortcuts import render
from product.models import Category, Product, Brand
from core.models import SiteSetting
from core.themes import THEMES, DEFAULT_THEME_KEY


def _get_theme_q(active_theme_key):
    if active_theme_key == 'mega_market':
        return Q(theme='mega_market') | Q(theme='all')
    return Q(theme=active_theme_key)


def _filter_theme_categories(active_theme_key, limit=24):
    """
    Returns up to `limit` categories strictly belonging to `active_theme_key`.
    Prioritizes featured categories, then other categories belonging to the SAME theme.
    NEVER falls back across different themes.
    """
    if hasattr(Category, 'theme'):
        theme_q = _get_theme_q(active_theme_key)
        base_cats = Category.objects.filter(theme_q)
    else:
        theme_config = THEMES.get(active_theme_key, THEMES[DEFAULT_THEME_KEY])
        cat_slugs = theme_config.get('category_slugs')
        base_cats = Category.objects.filter(slug__in=cat_slugs) if cat_slugs else Category.objects.all()

    featured = list(base_cats.filter(is_featured=True).order_by('order', 'name')[:limit])
    if len(featured) < limit:
        existing_ids = [c.id for c in featured]
        more = list(
            base_cats.exclude(id__in=existing_ids).order_by('order', 'name')[:(limit - len(featured))]
        )
        featured.extend(more)
    return featured[:limit]


def _filter_theme_brands(active_theme_key, limit=12):
    """
    Returns up to `limit` brands strictly belonging to `active_theme_key`.
    NEVER falls back across different themes.
    """
    if hasattr(Brand, 'theme'):
        theme_q = _get_theme_q(active_theme_key)
        base_brands = Brand.objects.filter(theme_q)
    else:
        theme_config = THEMES.get(active_theme_key, THEMES[DEFAULT_THEME_KEY])
        brand_slugs = theme_config.get('brand_slugs')
        base_brands = Brand.objects.filter(slug__in=brand_slugs) if brand_slugs else Brand.objects.all()

    return list(base_brands.order_by('name')[:limit])


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

    # 2. Filter & Prioritize Categories and Brands (STRICTLY within active theme)
    featured_categories = _filter_theme_categories(active_theme_key, limit=24)
    brands = _filter_theme_brands(active_theme_key, limit=12)

    # 3. Base Querysets for Products strictly scoped to active theme
    if hasattr(Product, 'theme'):
        theme_q = _get_theme_q(active_theme_key)
        all_theme_products = Product.objects.filter(is_active=True).filter(theme_q).select_related('category', 'brand')
    else:
        theme_config = THEMES.get(active_theme_key, THEMES[DEFAULT_THEME_KEY])
        cat_slugs = theme_config.get('category_slugs')
        brand_slugs = theme_config.get('brand_slugs')
        slug_q = Q()
        if cat_slugs:
            slug_q |= Q(category__slug__in=cat_slugs)
        if brand_slugs:
            slug_q |= Q(brand__slug__in=brand_slugs)
        base = Product.objects.filter(is_active=True).select_related('category', 'brand')
        all_theme_products = base.filter(slug_q) if slug_q else base

    # 4. Strict Theme Product Sections (Fallbacks ONLY from the SAME theme products)
    base_slider_qs = (
        all_theme_products
        .filter(Q(is_flash_sale=True) | Q(is_featured=True) | Q(discount_price__isnull=False))
        .order_by('-is_featured', '-is_flash_sale', '-price')
    )
    slider_candidates = list(base_slider_qs[:5])
    if len(slider_candidates) < 5:
        existing_ids = [p.id for p in slider_candidates]
        needed = 5 - len(slider_candidates)
        fallback_slider = list(
            all_theme_products.exclude(id__in=existing_ids).order_by('-price')[:needed]
        )
        slider_candidates.extend(fallback_slider)

    base_flash_qs = all_theme_products.filter(is_flash_sale=True).order_by('-discount_price', '-price')
    flash_sales = list(base_flash_qs[:12])
    if len(flash_sales) < 12:
        existing_ids = [p.id for p in flash_sales]
        needed = 12 - len(flash_sales)
        fallback_flash = list(
            all_theme_products.filter(discount_price__isnull=False).exclude(id__in=existing_ids).order_by('-price')[:needed]
        )
        flash_sales.extend(fallback_flash)
        if len(flash_sales) < 12:
            existing_ids = [p.id for p in flash_sales]
            needed_more = 12 - len(flash_sales)
            fallback_any = list(
                all_theme_products.exclude(id__in=existing_ids).order_by('-price')[:needed_more]
            )
            flash_sales.extend(fallback_any)

    base_featured_qs = all_theme_products.filter(is_featured=True).order_by('-created_at')
    featured_products = list(base_featured_qs[:8])
    if len(featured_products) < 8:
        existing_ids = [p.id for p in featured_products]
        needed = 8 - len(featured_products)
        fallback_featured = list(
            all_theme_products.exclude(id__in=existing_ids).order_by('-created_at')[:needed]
        )
        featured_products.extend(fallback_featured)

    latest_products = list(all_theme_products.order_by('-created_at')[:8])

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
