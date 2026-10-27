from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, Brand
from .forms import ProductForm


def product_list(request):
    """
    Storefront catalog view with comprehensive filtering, searching, and sorting.
    """
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')

    # Keyword Search
    query = request.GET.get('q', '').strip()
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
    if request.GET.get('in_stock') == '1':
        products = products.filter(stock__gt=0)

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

    categories = Category.objects.all()
    brands = Brand.objects.all()

    return render(request, 'product/list.html', {
        'products': products,
        'categories': categories,
        'brands': brands,
        'query': query,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'sort': sort,
        'total_count': products.count(),
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]

    return render(request, 'product/detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': product.reviews.all(),
    })


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


# Legacy / quick CRUD views (also available via custom admin panel)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save()
            return redirect('product_detail', pk=p.pk)
    else:
        form = ProductForm()
    return render(request, 'product/form.html', {'form': form, 'title': 'Add Product'})


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'product/form.html', {'form': form, 'title': 'Edit Product', 'product': product})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'product/confirm_delete.html', {'product': product})
