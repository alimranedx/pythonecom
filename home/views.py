from django.shortcuts import render
from product.models import Category, Product, Brand


def index(request):
    featured_categories = Category.objects.filter(is_featured=True)[:6]
    flash_sales = Product.objects.filter(is_active=True, is_flash_sale=True)[:4]
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    brands = Brand.objects.all()[:8]

    return render(request, 'home/index.html', {
        'featured_categories': featured_categories,
        'flash_sales': flash_sales,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'brands': brands,
    })
