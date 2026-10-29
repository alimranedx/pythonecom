from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.http import require_POST, require_http_methods
from core.validators import get_safe_redirect_url
from product.models import Product
from orders.models import Coupon
from .services import CartService
from .models import CartItem


def staff_block_check(request):
    """
    If a staff/admin user is in the session when accessing cart routes,
    clear the staff session immediately so the user can freely shop as a guest.
    """
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
    return None


def cart_detail(request):
    staff_block_check(request)
    cart = CartService.get_or_create_cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def cart_drawer(request):
    staff_block_check(request)
    cart = CartService.get_or_create_cart(request)
    return render(request, 'cart/_drawer_body.html', {'global_cart': cart})


def add_to_cart(request, product_id):
    staff_block_check(request)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = CartService.get_or_create_cart(request)
    if cart is None:
        return redirect('home')

    if product.stock <= 0:
        msg = "This product is currently out of stock."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'product_list'))

    # Sanitize and clamp quantity to prevent DoS integer overflows / negative quantities
    try:
        raw_qty = int(request.POST.get('quantity', 1)) if request.method == 'POST' else 1
        quantity = max(1, min(raw_qty, 100))
    except (ValueError, TypeError):
        quantity = 1

    # Check inventory constraint
    existing_item = CartItem.objects.filter(cart=cart, product=product).first()
    current_qty = existing_item.quantity if existing_item else 0
    if current_qty + quantity > product.stock:
        msg = f"Only {product.stock} units available in stock."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, f"Sorry, {msg}")
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'product_list'))

    cart_item = CartService.add_to_cart(cart, product, quantity)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        action_msg = (
            f"Added '{product.name}' to cart!"
            if cart_item.quantity == quantity
            else f"Increased '{product.name}' quantity to {cart_item.quantity} in cart."
        )
        return JsonResponse({
            'success': True,
            'message': action_msg,
            'total_items': cart.total_items,
            'item_quantity': cart_item.quantity,
            'product_id': product.pk,
            'subtotal': str(cart.subtotal),
            'discount_amount': str(cart.discount_amount),
            'shipping_cost': str(cart.shipping_cost),
            'grand_total': str(cart.grand_total),
            'amount_to_free_shipping': str(cart.amount_to_free_shipping),
            'free_shipping_progress_percent': cart.free_shipping_progress_percent,
        })

    messages.success(request, f"'{product.name}' was added to your cart.")
    return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))


@require_POST
def update_cart_quantity(request, product_id):
    staff_block_check(request)

    cart = CartService.get_or_create_cart(request)
    if cart is None:
        return redirect('home')

    product = get_object_or_404(Product, pk=product_id)

    try:
        raw_qty = int(request.POST.get('quantity', 1))
        quantity = max(0, min(raw_qty, 100))
    except (ValueError, TypeError):
        quantity = 1

    if quantity > product.stock:
        msg = f"Only {product.stock} units available in inventory."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
    else:
        CartService.update_quantity(cart, product_id, quantity)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Cart updated.' if quantity > 0 else 'Item removed from cart.',
                'total_items': cart.total_items,
                'item_quantity': quantity,
                'product_id': product.pk,
                'subtotal': str(cart.subtotal),
                'discount_amount': str(cart.discount_amount),
                'shipping_cost': str(cart.shipping_cost),
                'grand_total': str(cart.grand_total),
                'amount_to_free_shipping': str(cart.amount_to_free_shipping),
                'free_shipping_progress_percent': cart.free_shipping_progress_percent,
            })
        messages.success(request, "Cart updated.")

    return redirect('cart_detail')


@require_http_methods(["GET", "POST"])
def remove_from_cart(request, product_id):
    staff_block_check(request)

    cart = CartService.get_or_create_cart(request)
    if cart is None:
        return redirect('home')

    CartService.remove_item(cart, product_id)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart.',
            'total_items': cart.total_items,
            'item_quantity': 0,
            'product_id': product_id,
            'subtotal': str(cart.subtotal),
            'discount_amount': str(cart.discount_amount),
            'shipping_cost': str(cart.shipping_cost),
            'grand_total': str(cart.grand_total),
            'amount_to_free_shipping': str(cart.amount_to_free_shipping),
            'free_shipping_progress_percent': cart.free_shipping_progress_percent,
        })
    messages.info(request, "Item removed from cart.")
    return redirect('cart_detail')


@require_POST
def apply_coupon(request):
    staff_block_check(request)
    cart = CartService.get_or_create_cart(request)
    if cart is None:
        return redirect('home')

    code = request.POST.get('coupon_code', '').strip().upper()
    if not code:
        msg = "Please enter a valid coupon code."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        msg = f"Coupon code '{code}' is invalid or does not exist."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))

    valid, reason = coupon.is_valid(cart.subtotal)
    if not valid:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': reason}, status=400)
        messages.error(request, reason)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))

    cart.coupon = coupon
    cart.save(update_fields=['coupon'])

    success_msg = f"Coupon '{coupon.code}' applied successfully! Saved ৳{cart.discount_amount}."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'coupon_code': coupon.code,
            'discount_amount': str(cart.discount_amount),
            'subtotal': str(cart.subtotal),
            'shipping_cost': str(cart.shipping_cost),
            'grand_total': str(cart.grand_total),
            'total_items': cart.total_items,
        })

    messages.success(request, success_msg)
    return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))


@require_POST
def remove_coupon(request):
    staff_block_check(request)
    cart = CartService.get_or_create_cart(request)
    if cart is None:
        return redirect('home')

    cart.coupon = None
    cart.save(update_fields=['coupon'])

    msg = "Coupon removed from cart."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': msg,
            'coupon_code': '',
            'discount_amount': '0.00',
            'subtotal': str(cart.subtotal),
            'shipping_cost': str(cart.shipping_cost),
            'grand_total': str(cart.grand_total),
            'total_items': cart.total_items,
        })

    messages.info(request, msg)
    return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))
