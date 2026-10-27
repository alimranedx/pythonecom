from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ProductForm

# LIST - show all products
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product/list.html', {'products': products})

# DETAIL - show single product
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product/detail.html', {'product': product})

# CREATE - add new product
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product/form.html', {'form': form, 'title': 'Add Product'})

# UPDATE - edit existing product
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'product/form.html', {'form': form, 'title': 'Edit Product'})

# DELETE - remove product
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'product/confirm_delete.html', {'product': product})