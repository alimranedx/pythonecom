from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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

    # Check for buy_now trigger
    is_buy_now = (
        request.POST.get('buy_now') in ('1', 'true', 'True', True)
        or request.POST.get('action') == 'buy_now'
        or request.GET.get('buy_now') in ('1', 'true', 'True')
    )

    existing_item = CartItem.objects.filter(cart=cart, product=product).first()
    current_qty = existing_item.quantity if existing_item else 0

    if is_buy_now:
        # If item is not in cart, add it with requested quantity;
        # if item is already in cart, ensure it has at least the specified quantity (within stock)
        if not existing_item:
            if quantity > product.stock:
                msg = f"Only {product.stock} units available in stock."
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': msg}, status=400)
                messages.error(request, f"Sorry, {msg}")
                return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'product_list'))
            cart_item = CartService.add_to_cart(cart, product, quantity)
        else:
            if quantity > existing_item.quantity:
                if quantity > product.stock:
                    msg = f"Only {product.stock} units available in stock."
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': msg}, status=400)
                    messages.error(request, f"Sorry, {msg}")
                    return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'product_list'))
                existing_item.quantity = quantity
                existing_item.save()
            cart_item = existing_item

        checkout_url = reverse('checkout')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Proceeding to checkout with '{product.name}'...",
                'redirect_url': checkout_url,
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
        return redirect('checkout')

    # Regular Add to Cart: Check inventory constraint
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
def add_bundle_to_cart(request):
    staff_block_check(request)

    cart = CartService.get_or_create_cart(request)
    if cart is None:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Unable to initialize cart.'}, status=400)
        return redirect('home')

    product_ids = []
    buy_now_val = False

    if request.content_type == 'application/json':
        try:
            import json
            data = json.loads(request.body.decode('utf-8'))
            raw_ids = data.get('product_ids', [])
            if isinstance(raw_ids, list):
                product_ids = raw_ids
            elif isinstance(raw_ids, str):
                product_ids = [x.strip() for x in raw_ids.split(',') if x.strip()]
            buy_now_val = data.get('buy_now') in ('1', 'true', 'True', True) or data.get('action') == 'buy_now'
        except Exception:
            pass
    else:
        raw_list = request.POST.getlist('product_ids[]') or request.POST.getlist('product_ids')
        if not raw_list:
            raw_single = request.POST.get('product_ids', '')
            if raw_single:
                raw_list = [x.strip() for x in raw_single.split(',') if x.strip()]
        product_ids = raw_list
        buy_now_val = (
            request.POST.get('buy_now') in ('1', 'true', 'True', True)
            or request.POST.get('action') == 'buy_now'
            or request.GET.get('buy_now') in ('1', 'true', 'True')
        )

    valid_ids = []
    for pid in product_ids:
        if isinstance(pid, str) and ',' in pid:
            sub_ids = pid.split(',')
        else:
            sub_ids = [pid]
        for sub in sub_ids:
            try:
                val = int(str(sub).strip())
                if val > 0 and val not in valid_ids:
                    valid_ids.append(val)
            except (ValueError, TypeError):
                continue

    # DoS Mitigation: Clamp batch inputs to maximum 15 items to prevent DB memory or query exhaustion
    valid_ids = valid_ids[:15]

    if not valid_ids:
        msg = "No valid products provided for bundle."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))

    products = Product.objects.filter(pk__in=valid_ids, is_active=True, stock__gt=0)
    if not products.exists():
        msg = "None of the selected bundle items are currently available in stock."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.error(request, msg)
        return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'cart_detail'))

    added_items = []
    for prod in products:
        existing_item = CartItem.objects.filter(cart=cart, product=prod).first()
        current_qty = existing_item.quantity if existing_item else 0
        if current_qty < prod.stock:
            CartService.add_to_cart(cart, prod, 1)
            added_items.append(prod.name)

    is_buy_now = bool(buy_now_val)
    checkout_url = reverse('checkout')

    if is_buy_now:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"Added {len(added_items)} bundle items. Redirecting to checkout...",
                'redirect_url': checkout_url,
                'total_items': cart.total_items,
                'added_count': len(added_items),
                'subtotal': str(cart.subtotal),
                'discount_amount': str(cart.discount_amount),
                'shipping_cost': str(cart.shipping_cost),
                'grand_total': str(cart.grand_total),
                'amount_to_free_shipping': str(cart.amount_to_free_shipping),
                'free_shipping_progress_percent': cart.free_shipping_progress_percent,
            })
        return redirect('checkout')

    success_msg = f"Added {len(added_items)} bundle item(s) to your cart."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'total_items': cart.total_items,
            'added_count': len(added_items),
            'subtotal': str(cart.subtotal),
            'discount_amount': str(cart.discount_amount),
            'shipping_cost': str(cart.shipping_cost),
            'grand_total': str(cart.grand_total),
            'amount_to_free_shipping': str(cart.amount_to_free_shipping),
            'free_shipping_progress_percent': cart.free_shipping_progress_percent,
        })

    messages.success(request, success_msg)
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
