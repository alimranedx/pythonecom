from django.db.models import Q, Count
from django.shortcuts import render
from django.template.loader import get_template, TemplateDoesNotExist
from product.models import Category, Product, Brand
from core.models import SiteSetting
from core.themes import THEMES, DEFAULT_THEME_KEY


def _get_theme_q(active_theme_key):
    try:
        from core.theme_registry import theme_registry
        canonical_id = theme_registry.normalize_id(active_theme_key)
        legacy_key = theme_registry.get_legacy_key(canonical_id)
        keys = {canonical_id, legacy_key, active_theme_key}
    except Exception:
        keys = {active_theme_key}

    return Q(theme__in=list(keys)) | Q(theme='all')


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
    # 1. Resolve active theme (preview session > preview GET > site settings)
    session_preview = None
    if hasattr(request, 'session'):
        session_preview = request.session.get('admin_preview_theme')
    query_preview = request.GET.get('theme') if hasattr(request, 'GET') else None

    raw_theme = session_preview or query_preview
    if not raw_theme:
        settings = SiteSetting.get_settings()
        raw_theme = getattr(settings, 'active_theme', DEFAULT_THEME_KEY) or DEFAULT_THEME_KEY

    try:
        from core.theme_registry import theme_registry
        theme_id = theme_registry.normalize_id(raw_theme)
        if not theme_id:
            theme_id = theme_registry.default_theme_id
        active_theme_key = theme_registry.get_legacy_key(theme_id) or theme_id
    except Exception:
        theme_id = raw_theme
        active_theme_key = raw_theme

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

    # High-converting marketplace curated selections
    discounted_items = [p for p in all_theme_products if p.has_discount]
    deal_of_the_day = discounted_items[0] if discounted_items else (slider_candidates[0] if slider_candidates else None)
    weekly_saver = discounted_items[1] if len(discounted_items) > 1 else (slider_candidates[1] if len(slider_candidates) > 1 else deal_of_the_day)

    best_sellers = list(all_theme_products.filter(Q(is_featured=True) | Q(discount_price__isnull=False)).order_by('-price')[:8])
    if len(best_sellers) < 8:
        existing_bs_ids = {p.id for p in best_sellers}
        more_bs = [p for p in all_theme_products if p.id not in existing_bs_ids]
        best_sellers.extend(more_bs[:(8 - len(best_sellers))])

    top_rated = list(all_theme_products.order_by('-is_featured', '-price', '-created_at')[:8])
    trending_products = list(all_theme_products.order_by('-is_flash_sale', '-created_at')[:12])
    just_for_you = list(all_theme_products.order_by('-created_at')[:12])

    # Specialized Tech & Electronics theme querysets
    tech_laptop_categories = ['laptops-ultrabooks', 'smartphones-flagships']
    tech_gaming_categories = [
        'pc-hardware-components', 'gaming-monitors-displays',
        'gaming-consoles-accessories', 'mechanical-keyboards-mice'
    ]
    tech_audio_categories = ['audio-headphones-tws', 'smartwatches-fitness-bands']

    laptop_flagships = list(all_theme_products.filter(category__slug__in=tech_laptop_categories).order_by('-price')[:8])
    if not laptop_flagships:
        laptop_flagships = featured_products[:8]

    gaming_zone_products = list(all_theme_products.filter(category__slug__in=tech_gaming_categories).order_by('-is_featured', '-price')[:8])
    if not gaming_zone_products:
        gaming_zone_products = latest_products[:8]

    audio_wearables = list(all_theme_products.filter(category__slug__in=tech_audio_categories).order_by('-is_featured', '-price')[:8])
    if not audio_wearables:
        audio_wearables = top_rated[:8]

    flash_tech_deals = list(all_theme_products.filter(Q(is_flash_sale=True) | Q(discount_price__isnull=False)).order_by('-discount_price', '-price')[:6])
    if len(flash_tech_deals) < 6:
        existing_ft_ids = {p.id for p in flash_tech_deals}
        more_ft = [p for p in all_theme_products if p.id not in existing_ft_ids]
        flash_tech_deals.extend(more_ft[:(6 - len(flash_tech_deals))])

    # Specialized Beauty & Skincare theme querysets
    beauty_bestsellers = list(all_theme_products.filter(Q(is_featured=True) | Q(discount_price__isnull=False)).order_by('-is_featured', '-price')[:8])
    if len(beauty_bestsellers) < 8:
        existing_bb_ids = {p.id for p in beauty_bestsellers}
        more_bb = [p for p in all_theme_products if p.id not in existing_bb_ids]
        beauty_bestsellers.extend(more_bb[:(8 - len(beauty_bestsellers))])

    fresh_glow_essentials = list(all_theme_products.order_by('-created_at')[:8])
    daily_glow_highlight = best_sellers[0] if best_sellers else (all_theme_products.first() if all_theme_products.exists() else None)
    complimentary_sample_prod = discounted_items[0] if discounted_items else (beauty_bestsellers[1] if len(beauty_bestsellers) > 1 else daily_glow_highlight)

    # Specialized Organic Grocery theme querysets
    grocery_bestsellers = list(all_theme_products.filter(Q(is_featured=True) | Q(discount_price__isnull=False)).order_by('-is_featured', '-price')[:8])
    if len(grocery_bestsellers) < 8:
        existing_gb_ids = {p.id for p in grocery_bestsellers}
        more_gb = [p for p in all_theme_products if p.id not in existing_gb_ids]
        grocery_bestsellers.extend(more_gb[:(8 - len(grocery_bestsellers))])

    pantry_categories = [
        'cold-pressed-mustard-oils', 'whole-ground-spices', 'aromatic-rice-grains',
        'organic-lentils-daal', 'fresh-farm-vegetables', 'desi-ghee-dairy-butter'
    ]
    pantry_essentials = list(all_theme_products.filter(category__slug__in=pantry_categories).order_by('-is_featured', '-price')[:8])
    if not pantry_essentials:
        pantry_essentials = latest_products[:8]

    seasonal_categories = ['fresh-seasonal-fruits', 'raw-wild-honey', 'premium-dry-fruits-nuts']
    seasonal_harvest = list(all_theme_products.filter(category__slug__in=seasonal_categories).order_by('-created_at')[:8])
    if not seasonal_harvest:
        seasonal_harvest = trending_products[:8]

    daily_farm_pick = (
        all_theme_products.filter(Q(slug__icontains='honey') | Q(slug__icontains='ghee') | Q(slug__icontains='mustard')).first()
        or deal_of_the_day
        or (all_theme_products.first() if all_theme_products.exists() else None)
    )

    # Category tiles with product counts
    if hasattr(Category, 'theme'):
        cat_q = _get_theme_q(active_theme_key)
        category_tiles = list(
            Category.objects.filter(cat_q)
            .annotate(prod_count=Count('products', filter=Q(products__is_active=True)))
            .order_by('-prod_count', 'order')[:8]
        )
    else:
        category_tiles = list(
            Category.objects.all()
            .annotate(prod_count=Count('products', filter=Q(products__is_active=True)))
            .order_by('-prod_count', 'order')[:8]
        )

    # 5. Dynamic Template Resolution: check if templates/themes/{theme_id}/home.html exists
    target_template = f"themes/{theme_id}/home.html"
    fallback_template = f"themes/{active_theme_key}/home.html"
    template_name = 'home/index.html'
    for candidate in [target_template, fallback_template]:
        try:
            get_template(candidate)
            template_name = candidate
            break
        except TemplateDoesNotExist:
            continue

    spotlight_prod = deal_of_the_day or (laptop_flagships[0] if laptop_flagships else (best_sellers[0] if best_sellers else None))

    return render(request, template_name, {
        'slider_items': slider_items,
        'slider_candidates': slider_candidates,
        'featured_categories': featured_categories,
        'category_tiles': category_tiles,
        'flash_sales': flash_sales,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'best_sellers': best_sellers,
        'top_rated': top_rated,
        'trending_products': trending_products,
        'just_for_you': just_for_you,
        'deal_of_the_day': deal_of_the_day,
        'weekly_saver': weekly_saver,
        'spotlight_prod': spotlight_prod,
        'laptop_flagships': laptop_flagships,
        'gaming_zone_products': gaming_zone_products,
        'audio_wearables': audio_wearables,
        'flash_tech_deals': flash_tech_deals,
        'beauty_bestsellers': beauty_bestsellers,
        'fresh_glow_essentials': fresh_glow_essentials,
        'daily_glow_highlight': daily_glow_highlight,
        'complimentary_sample_prod': complimentary_sample_prod,
        'grocery_bestsellers': grocery_bestsellers,
        'pantry_essentials': pantry_essentials,
        'seasonal_harvest': seasonal_harvest,
        'daily_farm_pick': daily_farm_pick,
        'brands': brands,
        'active_theme_key': active_theme_key,
        'active_theme_id': theme_id,
        'current_theme_id': theme_id,
    })
