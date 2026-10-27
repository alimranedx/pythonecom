from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from product.models import Product
from .services import CartService
from .models import CartItem


def cart_detail(request):
    cart = CartService.get_or_create_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = CartService.get_or_create_cart(request)

    quantity = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1

    # Check inventory constraint
    existing_item = CartItem.objects.filter(cart=cart, product=product).first()
    current_qty = existing_item.quantity if existing_item else 0
    if current_qty + quantity > product.stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"Only {product.stock} units available in stock."
            }, status=400)
        messages.error(request, f"Sorry, only {product.stock} units of {product.name} are available.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    CartService.add_to_cart(cart, product, quantity)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added '{product.name}' to cart!",
            'total_items': cart.total_items,
            'subtotal': str(cart.subtotal),
            'grand_total': str(cart.grand_total),
        })

    messages.success(request, f"'{product.name}' was added to your cart.")
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))


def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        cart = CartService.get_or_create_cart(request)
        product = get_object_or_404(Product, pk=product_id)
        quantity = int(request.POST.get('quantity', 1))

        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} units available.")
        else:
            CartService.update_quantity(cart, product_id, quantity)
            messages.success(request, "Cart updated.")

    return redirect('cart_detail')


def remove_from_cart(request, product_id):
    cart = CartService.get_or_create_cart(request)
    CartService.remove_item(cart, product_id)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_detail')
