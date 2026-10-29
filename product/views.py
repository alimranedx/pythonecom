from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from .models import Product, Category, Brand
from .forms import ProductForm


def product_list(request):
    """
    Storefront catalog view with comprehensive filtering, searching, sorting, and pagination.
    """
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')

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
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Brand Filter
    brand_slug = request.GET.get('brand')
    selected_brand = None
    if brand_slug:
        selected_brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=selected_brand)

    # In Stock Filter
    in_stock = request.GET.get('in_stock', '').strip()
    if in_stock == '1':
        products = products.filter(stock__gt=0)

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

    categories = Category.objects.all()
    brands = Brand.objects.all()

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        from accounts.models import Wishlist
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'product/list.html', {
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
        'total_count': paginator.count,
        'querystring': querystring,
        'user_wishlist_ids': user_wishlist_ids,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    return render(request, 'product/detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': product.reviews.select_related('user').all(),
        'gallery_images': product.images.all(),
    })


def product_add_review(request, pk):
    if not request.user.is_authenticated:
        from django.contrib import messages
        messages.info(request, "Please log in to submit a product review.")
        return redirect('account_login')

    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        from django.contrib import messages
        from .models import ProductReview
        try:
            rating = max(1, min(int(request.POST.get('rating', 5)), 5))
        except (ValueError, TypeError):
            rating = 5
        comment = request.POST.get('comment', '').strip()[:1000]
        if comment:
            ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment,
            )
            messages.success(request, "Thank you! Your product review has been published.")
        else:
            messages.error(request, "Please write a comment for your review.")

    return redirect('product_detail', pk=product.pk)


def product_quick_view(request, pk):
    """
    AJAX endpoint returning product information for quick view modal.
    """
    product = get_object_or_404(Product, pk=pk)
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
