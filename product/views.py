from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import get_template, TemplateDoesNotExist


def staff_member_required(view_func=None, login_url='admin_login'):
    decorator = user_passes_test(lambda u: u.is_active and u.is_staff, login_url=login_url)
    if view_func:
        return decorator(view_func)
    return decorator
from .models import Product, Category, Brand
from .forms import ProductForm
from core.models import SiteSetting
from core.themes import THEMES, DEFAULT_THEME_KEY


def _resolve_theme_info(request):
    """
    Resolves the canonical theme ID, legacy key, and theme filter Q expression
    consistently across preview sessions, query params, and site settings.
    """
    session_preview = None
    if hasattr(request, 'session'):
        session_preview = request.session.get('admin_preview_theme')
    query_preview = (request.GET.get('preview_theme') or request.GET.get('theme')) if hasattr(request, 'GET') else None

    raw_theme = session_preview or query_preview
    if not raw_theme:
        settings = SiteSetting.get_settings()
        raw_theme = getattr(settings, 'active_theme', DEFAULT_THEME_KEY) or DEFAULT_THEME_KEY

    try:
        from core.theme_registry import theme_registry
        theme_id = theme_registry.normalize_id(raw_theme)
        if not theme_id:
            theme_id = theme_registry.default_theme_id
        legacy_key = theme_registry.get_legacy_key(theme_id) or theme_id
    except Exception:
        theme_id = raw_theme
        legacy_key = raw_theme

    keys = {theme_id, legacy_key, raw_theme}
    theme_q = Q(theme__in=list(keys)) | Q(theme='all')

    return theme_id, legacy_key, theme_q


def product_list(request, category_slug=None):
    """
    Storefront catalog view with comprehensive filtering, searching, sorting, and pagination.
    Strictly isolated and scoped to the active or preview theme.
    Supports dynamic template resolution for active theme: themes/{theme_id}/product_list.html.
    """
    # 1. Resolve active theme
    theme_id, active_theme_key, theme_q = _resolve_theme_info(request)

    if hasattr(Product, 'theme'):
        products = Product.objects.filter(is_active=True).filter(theme_q).select_related('category', 'brand')
        categories = Category.objects.filter(theme_q).order_by('order', 'name')
        brands = Brand.objects.filter(theme_q).order_by('name')
    else:
        products = Product.objects.filter(is_active=True).select_related('category', 'brand')
        categories = Category.objects.all().order_by('order', 'name')
        brands = Brand.objects.all().order_by('name')

    # Annotate with reviews rating and count for rating sorting/filtering
    products = products.annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews')
    )

    # Keyword Search (bounded to 100 chars to prevent search query DoS)
    query = request.GET.get('q', '').strip()[:100]
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category Filter
    is_explicit_category_path = bool(category_slug)
    if not category_slug:
        category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = categories.filter(slug=category_slug).first()
        if not selected_category:
            CATEGORY_ALIASES = {
                'electronics-laptops': 'laptops',
                'smartphones-tablets': 'smartphones',
                'fashion-apparel': 'mens-shirts',
                'audio-headphones': 'mobile-accessories',
                'watches-wearables': 'mens-watches',
            }
            alias_slug = CATEGORY_ALIASES.get(category_slug)
            if alias_slug:
                selected_category = categories.filter(slug=alias_slug).first()

        if not selected_category and is_explicit_category_path:
            raise Http404("Category not found")

        if selected_category:
            products = products.filter(category=selected_category)

    # Brand Filter (strictly scoped to active theme's brands)
    brand_slug = request.GET.get('brand')
    selected_brand = None
    if brand_slug:
        selected_brand = brands.filter(slug=brand_slug).first()
        if selected_brand:
            products = products.filter(brand=selected_brand)

    # In Stock Filter
    in_stock = request.GET.get('in_stock', '').strip()
    if in_stock == '1':
        products = products.filter(stock__gt=0)

    # Rating Filter
    rating_param = request.GET.get('rating', '').strip()
    if rating_param:
        try:
            min_rating = float(rating_param)
            products = products.filter(avg_rating__gte=min_rating)
        except (ValueError, TypeError):
            pass

    # Price Range Filter
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            pass

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name_asc':
        products = products.order_by('name')
    elif sort == 'rating':
        products = products.order_by('-avg_rating', '-reviews_count', '-created_at')
    else:
        products = products.order_by('-created_at')

    # Pagination & Per Page limits
    per_page_raw = request.GET.get('per_page', '12').strip()
    try:
        per_page = int(per_page_raw)
        if per_page not in [9, 12, 18, 24, 36, 48]:
            per_page = 12
    except (ValueError, TypeError):
        per_page = 12

    paginator = Paginator(products, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    try:
        elided_page_range = paginator.get_elided_page_range(
            page_obj.number, on_each_side=2, on_ends=1
        )
    except Exception:
        elided_page_range = paginator.page_range

    # Build clean querystring preserving existing filters
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_params['per_page'] = per_page
    querystring = query_params.urlencode()

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        from accounts.models import Wishlist
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    # Dynamic template resolution
    target_templates = [
        f"themes/{theme_id}/product_list.html",
    ]
    if active_theme_key and active_theme_key != theme_id:
        target_templates.append(f"themes/{active_theme_key}/product_list.html")
    if theme_id in ['tech-electronics', 'tech_gadgets'] or active_theme_key in ['tech-electronics', 'tech_gadgets']:
        if "themes/tech-electronics/product_list.html" not in target_templates:
            target_templates.append("themes/tech-electronics/product_list.html")
        if "themes/tech_gadgets/product_list.html" not in target_templates:
            target_templates.append("themes/tech_gadgets/product_list.html")
    if theme_id in ['beauty-skincare', 'beauty_cosmetics'] or active_theme_key in ['beauty-skincare', 'beauty_cosmetics']:
        if "themes/beauty-skincare/product_list.html" not in target_templates:
            target_templates.append("themes/beauty-skincare/product_list.html")
        if "themes/beauty_cosmetics/product_list.html" not in target_templates:
            target_templates.append("themes/beauty_cosmetics/product_list.html")
    if theme_id in ['organic-grocery', 'grocery_organic'] or active_theme_key in ['organic-grocery', 'grocery_organic']:
        if "themes/organic-grocery/product_list.html" not in target_templates:
            target_templates.append("themes/organic-grocery/product_list.html")
        if "themes/grocery_organic/product_list.html" not in target_templates:
            target_templates.append("themes/grocery_organic/product_list.html")

    template_name = 'product/list.html'
    for candidate in target_templates:
        try:
            get_template(candidate)
            template_name = candidate
            break
        except TemplateDoesNotExist:
            continue

    return render(request, template_name, {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'elided_page_range': elided_page_range,
        'ellipsis': getattr(paginator, 'ELLIPSIS', '…'),
        'per_page': per_page,
        'per_page_options': [9, 12, 18, 24, 36],
        'categories': categories,
        'brands': brands,
        'query': query,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'in_stock': in_stock,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'rating': rating_param,
        'total_count': paginator.count,
        'querystring': querystring,
        'user_wishlist_ids': user_wishlist_ids,
        'active_theme_key': active_theme_key,
        'active_theme_id': theme_id,
        'current_theme_id': theme_id,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    # Resolve active theme
    theme_id, active_theme_key, theme_q = _resolve_theme_info(request)

    # Strict Theme Isolation: verify that product belongs to the active storefront theme
    if hasattr(product, 'theme') and product.theme:
        allowed = {theme_id, active_theme_key, 'all'}
        if 'marketplace' in allowed or 'mega_market' in allowed:
            allowed.update({'marketplace', 'mega_market'})
        if 'tech-electronics' in allowed or 'tech_gadgets' in allowed:
            allowed.update({'tech-electronics', 'tech_gadgets'})
        if 'pharmacy-healthcare' in allowed or 'pharmacy_health' in allowed:
            allowed.update({'pharmacy-healthcare', 'pharmacy_health'})
        if 'beauty-skincare' in allowed or 'beauty_cosmetics' in allowed:
            allowed.update({'beauty-skincare', 'beauty_cosmetics'})
        if 'fashion-lifestyle' in allowed or 'fashion_lifestyle' in allowed:
            allowed.update({'fashion-lifestyle', 'fashion_lifestyle'})
        if 'organic-grocery' in allowed or 'grocery_organic' in allowed:
            allowed.update({'organic-grocery', 'grocery_organic'})
        if product.theme not in allowed:
            raise Http404("Product not available in this storefront theme")

    # Scoped related products strictly within the same theme
    related_qs = Product.objects.filter(is_active=True).exclude(pk=product.pk)
    if hasattr(Product, 'theme') and getattr(product, 'theme', None):
        if product.theme in ['marketplace', 'mega_market']:
            related_qs = related_qs.filter(Q(theme__in=['marketplace', 'mega_market']) | Q(theme='all'))
        elif product.theme in ['tech-electronics', 'tech_gadgets']:
            related_qs = related_qs.filter(Q(theme__in=['tech-electronics', 'tech_gadgets']) | Q(theme='all'))
        elif product.theme in ['beauty-skincare', 'beauty_cosmetics']:
            related_qs = related_qs.filter(Q(theme__in=['beauty-skincare', 'beauty_cosmetics']) | Q(theme='all'))
        elif product.theme in ['organic-grocery', 'grocery_organic']:
            related_qs = related_qs.filter(Q(theme__in=['organic-grocery', 'grocery_organic']) | Q(theme='all'))
        else:
            related_qs = related_qs.filter(theme=product.theme)

    if product.category:
        related_products = list(related_qs.filter(category=product.category)[:4])
        if len(related_products) < 4:
            existing_ids = [p.id for p in related_products]
            more = list(related_qs.exclude(id__in=existing_ids)[:(4 - len(related_products))])
            related_products.extend(more)
    else:
        related_products = list(related_qs[:4])

    bundle_qs = Product.objects.filter(is_active=True, stock__gt=0).exclude(pk=product.pk)
    if hasattr(Product, 'theme') and getattr(product, 'theme', None):
        if product.theme in ['marketplace', 'mega_market']:
            bundle_qs = bundle_qs.filter(Q(theme__in=['marketplace', 'mega_market']) | Q(theme='all'))
        elif product.theme in ['tech-electronics', 'tech_gadgets']:
            bundle_qs = bundle_qs.filter(Q(theme__in=['tech-electronics', 'tech_gadgets']) | Q(theme='all'))
        elif product.theme in ['beauty-skincare', 'beauty_cosmetics']:
            bundle_qs = bundle_qs.filter(Q(theme__in=['beauty-skincare', 'beauty_cosmetics']) | Q(theme='all'))
        elif product.theme in ['organic-grocery', 'grocery_organic']:
            bundle_qs = bundle_qs.filter(Q(theme__in=['organic-grocery', 'grocery_organic']) | Q(theme='all'))
        else:
            bundle_qs = bundle_qs.filter(theme=product.theme)

    bundle_items = list(
        bundle_qs.filter(category=product.category)[:2]
    ) if product.category else list(bundle_qs[:2])

    bundle_discount_percent = 5
    bundle_total = product.effective_price
    if bundle_items:
        bundle_total += sum(item.effective_price for item in bundle_items)

    bundle_discount_price = round(bundle_total * Decimal('0.95'), 2)
    bundle_savings = bundle_total - bundle_discount_price

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        from accounts.models import Wishlist
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    # Dynamic template resolution
    detail_candidates = [
        f"themes/{theme_id}/product_detail.html",
    ]
    if active_theme_key and active_theme_key != theme_id:
        detail_candidates.append(f"themes/{active_theme_key}/product_detail.html")
    if 'tech-electronics' in [theme_id, active_theme_key] or 'tech_gadgets' in [theme_id, active_theme_key]:
        if "themes/tech-electronics/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/tech-electronics/product_detail.html")
        if "themes/tech_gadgets/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/tech_gadgets/product_detail.html")
    if 'beauty-skincare' in [theme_id, active_theme_key] or 'beauty_cosmetics' in [theme_id, active_theme_key]:
        if "themes/beauty-skincare/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/beauty-skincare/product_detail.html")
        if "themes/beauty_cosmetics/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/beauty_cosmetics/product_detail.html")
    if 'organic-grocery' in [theme_id, active_theme_key] or 'grocery_organic' in [theme_id, active_theme_key]:
        if "themes/organic-grocery/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/organic-grocery/product_detail.html")
        if "themes/grocery_organic/product_detail.html" not in detail_candidates:
            detail_candidates.append("themes/grocery_organic/product_detail.html")

    template_name = 'product/detail.html'
    for candidate in detail_candidates:
        try:
            get_template(candidate)
            template_name = candidate
            break
        except TemplateDoesNotExist:
            continue

    return render(request, template_name, {
        'product': product,
        'related_products': related_products,
        'reviews': product.reviews.select_related('user').all(),
        'gallery_images': product.images.all(),
        'bundle_items': bundle_items,
        'bundle_discount_percent': bundle_discount_percent,
        'bundle_total': bundle_total,
        'bundle_discount_price': bundle_discount_price,
        'bundle_savings': bundle_savings,
        'user_wishlist_ids': user_wishlist_ids,
        'active_theme_key': active_theme_key,
        'active_theme_id': theme_id,
        'current_theme_id': theme_id,
    })


def product_add_review(request, pk):
    if not request.user.is_authenticated:
        from django.contrib import messages
        messages.info(request, "Please log in to submit a product review.")
        return redirect('account_login')

    product = get_object_or_404(Product, pk=pk)
    if request.method != 'POST':
        return redirect('product_detail', pk=product.pk)

    from django.contrib import messages
    from django.utils.html import strip_tags
    from django.utils import timezone
    from datetime import timedelta
    import html as html_lib
    import re
    from .models import ProductReview

    # Prevent review spamming / rate limiting: 1 review per user per product, throttled updates
    existing_review = ProductReview.objects.filter(product=product, user=request.user).first()
    if existing_review and existing_review.updated_at:
        if (timezone.now() - existing_review.updated_at) < timedelta(seconds=15):
            messages.warning(request, "Please wait a moment before updating your review again.")
            return redirect('product_detail', pk=product.pk)

    # Validate rating strictly between 1 and 5
    try:
        rating = int(request.POST.get('rating', 5))
        if rating < 1:
            rating = 1
        elif rating > 5:
            rating = 5
    except (ValueError, TypeError):
        rating = 5

    # Sanitize review comment to block XSS attacks and strip dangerous tags
    raw_comment = request.POST.get('comment', '').strip()
    raw_comment = re.sub(
        r'<(script|style|iframe|object|embed|applet|noscript)[^>]*>.*?</\1>',
        '',
        raw_comment,
        flags=re.IGNORECASE | re.DOTALL
    )
    raw_comment = re.sub(
        r'<(script|style|iframe|object|embed|applet|noscript)[^>]*\/?>',
        '',
        raw_comment,
        flags=re.IGNORECASE
    )
    clean_comment = strip_tags(raw_comment).strip()
    clean_comment = html_lib.unescape(clean_comment).strip()[:1000]

    if clean_comment and len(clean_comment) >= 2:
        ProductReview.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': clean_comment,
            }
        )
        messages.success(request, "Thank you! Your product review has been published.")
    else:
        messages.error(request, "Please write a valid comment for your review.")

    return redirect('product_detail', pk=product.pk)


def product_quick_view(request, pk):
    """
    AJAX endpoint returning product information for quick view modal.
    Strictly scoped to active storefront theme.
    """
    product = get_object_or_404(Product, pk=pk, is_active=True)

    theme_id, active_theme_key, theme_q = _resolve_theme_info(request)

    if hasattr(product, 'theme') and product.theme:
        allowed = {theme_id, active_theme_key, 'all'}
        if 'marketplace' in allowed or 'mega_market' in allowed:
            allowed.update({'marketplace', 'mega_market'})
        if 'tech-electronics' in allowed or 'tech_gadgets' in allowed:
            allowed.update({'tech-electronics', 'tech_gadgets'})
        if 'pharmacy-healthcare' in allowed or 'pharmacy_health' in allowed:
            allowed.update({'pharmacy-healthcare', 'pharmacy_health'})
        if 'beauty-skincare' in allowed or 'beauty_cosmetics' in allowed:
            allowed.update({'beauty-skincare', 'beauty_cosmetics'})
        if 'fashion-lifestyle' in allowed or 'fashion_lifestyle' in allowed:
            allowed.update({'fashion-lifestyle', 'fashion_lifestyle'})
        if 'organic-grocery' in allowed or 'grocery_organic' in allowed:
            allowed.update({'organic-grocery', 'grocery_organic'})
        if product.theme not in allowed:
            return JsonResponse({'error': 'Product not available in this storefront theme'}, status=404)
    return JsonResponse({
        'id': product.pk,
        'name': product.name,
        'price': str(product.price),
        'discount_price': str(product.discount_price) if product.discount_price else None,
        'effective_price': str(product.effective_price),
        'discount_percent': product.discount_percent,
        'stock': product.stock,
        'in_stock': product.in_stock,
        'category': product.category.name if product.category else 'General',
        'brand': product.brand.name if product.brand else None,
        'short_description': product.short_description or product.description[:150],
        'detail_url': f"/product/{product.pk}/",
    })


# Legacy / quick CRUD views (restricted to staff members)
@staff_member_required(login_url='admin_login')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save()
            return redirect('product_detail', pk=p.pk)
    else:
        form = ProductForm()
    return render(request, 'product/form.html', {'form': form, 'title': 'Add Product'})


@staff_member_required(login_url='admin_login')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'product/form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@staff_member_required(login_url='admin_login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'product/confirm_delete.html', {'product': product})
