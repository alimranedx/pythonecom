from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from cart.services import CartService
from accounts.models import Address
from .models import Order, DeliverySlot
from .services import OrderService
from .bkash import BKashService


def checkout(request):
    if request.user.is_authenticated and request.user.is_staff:
        from django.contrib.auth import logout
        logout(request)

    cart = CartService.get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your shopping cart is empty. Add products before proceeding to checkout.")
        return redirect('product_list')

    # Available Delivery Slots & Dates
    delivery_slots = DeliverySlot.objects.filter(is_active=True).order_by('order', 'start_time')
    today = timezone.localdate()
    available_dates = [
        {'label': 'Today', 'sublabel': today.strftime('%a, %d %b'), 'value': today.strftime('%Y-%m-%d')},
        {'label': 'Tomorrow', 'sublabel': (today + timedelta(days=1)).strftime('%a, %d %b'), 'value': (today + timedelta(days=1)).strftime('%Y-%m-%d')},
        {'label': (today + timedelta(days=2)).strftime('%A'), 'sublabel': (today + timedelta(days=2)).strftime('%d %b'), 'value': (today + timedelta(days=2)).strftime('%Y-%m-%d')},
    ]

    # Pre-fill address if authenticated
    initial_data = {
        'delivery_area': 'Inside Dhaka',
        'delivery_date': available_dates[0]['value'],
        'city': 'Dhaka',
        'country': 'Bangladesh',
    }

    first_slot = delivery_slots.first()
    if first_slot:
        initial_data['delivery_slot'] = first_slot.pk

    if request.user.is_authenticated:
        initial_data['email'] = request.user.email
        initial_data['full_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        default_addr = Address.objects.filter(user=request.user, is_default=True).first()
        if default_addr:
            initial_data['phone'] = default_addr.phone
            initial_data['street_address'] = default_addr.street_address
            initial_data['city'] = default_addr.city or 'Dhaka'
            initial_data['postal_code'] = default_addr.postal_code
            initial_data['country'] = default_addr.country or 'Bangladesh'

    if request.method == 'POST':
        shipping_data = {
            'full_name': request.POST.get('full_name', '').strip()[:120],
            'email': request.POST.get('email', '').strip()[:120],
            'phone': request.POST.get('phone', '').strip()[:30],
            'street_address': request.POST.get('street_address', '').strip()[:255],
            'city': request.POST.get('city', '').strip()[:100],
            'postal_code': request.POST.get('postal_code', '').strip()[:20],
            'country': request.POST.get('country', 'Bangladesh').strip()[:100],
            'notes': request.POST.get('notes', '').strip()[:500],
            'delivery_area': request.POST.get('delivery_area', 'Inside Dhaka').strip()[:100],
            'delivery_date': request.POST.get('delivery_date', available_dates[0]['value']).strip()[:20],
            'delivery_slot': request.POST.get('delivery_slot', '').strip(),
            'payment_method': request.POST.get('payment_method', 'cod'),
        }

        # Basic validations
        required_fields = ['full_name', 'email', 'phone', 'street_address', 'city']
        missing = [f for f in required_fields if not shipping_data.get(f)]
        if missing:
            messages.error(request, "Please fill in all required shipping fields.")
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'initial': shipping_data,
                'delivery_slots': delivery_slots,
                'available_dates': available_dates,
            })

        try:
            order = OrderService.create_order_from_cart(
                cart=cart,
                shipping_data=shipping_data,
                user=request.user if request.user.is_authenticated else None,
            )
            request.session['last_order_number'] = order.order_number
            # bKash Online Gateway Redirection
            if order.payment_method == 'bkash':
                callback_url = request.build_absolute_uri('/orders/bkash/callback/')
                success, bkash_res = BKashService.create_payment(order, callback_url)
                if success and bkash_res.get('bkash_url'):
                    order.payment_id = bkash_res.get('payment_id', '')
                    order.save(update_fields=['payment_id'])
                    request.session['bkash_order_number'] = order.order_number
                    return redirect(bkash_res['bkash_url'])
                else:
                    err_msg = bkash_res.get('message', 'Failed to initialize bKash checkout.')
                    messages.warning(request, f"bKash Gateway Notice: {err_msg}")
                    return redirect('order_confirmation', order_number=order.order_number)

            messages.success(request, f"Order {order.order_number} confirmed! Thank you for shopping with us.")
            return redirect('order_confirmation', order_number=order.order_number)
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'initial': shipping_data,
                'delivery_slots': delivery_slots,
                'available_dates': available_dates,
            })
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during checkout: {e}")
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'initial': shipping_data,
                'delivery_slots': delivery_slots,
                'available_dates': available_dates,
            })

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'initial': initial_data,
        'delivery_slots': delivery_slots,
        'available_dates': available_dates,
    })


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    # IDOR Protection: Restrict viewing customer receipts only to the order owner, authorized session, or staff members
    if order.user:
        if order.user != request.user and not (request.user.is_authenticated and request.user.is_staff):
            raise PermissionDenied("You do not have permission to view this order confirmation.")
    else:
        if request.session.get('last_order_number') != order.order_number and not (request.user.is_authenticated and request.user.is_staff):
            raise PermissionDenied("You do not have permission to view this order confirmation.")
    return render(request, 'orders/confirmation.html', {'order': order})


def bkash_callback(request):
    """
    Handles bKash redirect callback after customer acts on the bKash checkout page.
    Query parameters sent by bKash: ?paymentID=...&status=success|failure|cancel
    """
    payment_id = request.GET.get('paymentID')
    status = request.GET.get('status')

    order_number = request.session.get('bkash_order_number')
    order = None
    if payment_id:
        order = Order.objects.filter(payment_id=payment_id).first()
    if not order and order_number:
        order = Order.objects.filter(order_number=order_number).first()

    if not order:
        messages.error(request, "bKash transaction order record could not be found.")
        return redirect('home')

    request.session['last_order_number'] = order.order_number

    if status == 'success':
        success, exec_res = BKashService.execute_payment(payment_id)
        if success:
            order.payment_status = 'paid'
            order.status = 'processing'
            order.transaction_id = exec_res.get('trx_id', '')
            order.save(update_fields=['payment_status', 'status', 'transaction_id'])
            messages.success(
                request,
                f"bKash Payment Completed Successfully! TrxID: {order.transaction_id}. Thank you!"
            )
            return redirect('order_confirmation', order_number=order.order_number)
        else:
            order.payment_status = 'failed'
            order.save(update_fields=['payment_status'])
            err_msg = exec_res.get('message', 'Execution verification failed.')
            messages.error(request, f"bKash execution failed: {err_msg}")
            return redirect('order_confirmation', order_number=order.order_number)

    elif status == 'cancel':
        messages.warning(request, "bKash payment was cancelled.")
        return redirect('order_confirmation', order_number=order.order_number)
    else:
        order.payment_status = 'failed'
        order.save(update_fields=['payment_status'])
        messages.error(request, "bKash payment unsuccessful or failed.")
        return redirect('order_confirmation', order_number=order.order_number)


def retry_bkash_payment(request, order_number):
    """
    Allows a customer to retry an incomplete or failed bKash payment without re-ordering.
    """
    order = get_object_or_404(Order, order_number=order_number)
    if order.payment_status == 'paid':
        messages.info(request, "This order is already marked as paid.")
        return redirect('order_confirmation', order_number=order.order_number)

    callback_url = request.build_absolute_uri('/orders/bkash/callback/')
    success, bkash_res = BKashService.create_payment(order, callback_url)
    if success and bkash_res.get('bkash_url'):
        order.payment_id = bkash_res.get('payment_id', '')
        order.save(update_fields=['payment_id'])
        request.session['bkash_order_number'] = order.order_number
        return redirect(bkash_res['bkash_url'])
    else:
        err_msg = bkash_res.get('message', 'Unable to reach bKash gateway.')
        messages.error(request, f"bKash Gateway Notice: {err_msg}")
        return redirect('order_confirmation', order_number=order.order_number)


def order_invoice(request, order_number):
    """
    Renders customer-facing printable order invoice.
    Protected with IDOR validation (scoped to order owner, authorized session, or staff).
    """
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), order_number=order_number)
    if order.user:
        if order.user != request.user and not (request.user.is_authenticated and request.user.is_staff):
            raise PermissionDenied("You do not have permission to view this invoice.")
    else:
        if request.session.get('last_order_number') != order.order_number and not (request.user.is_authenticated and request.user.is_staff):
            raise PermissionDenied("You do not have permission to view this invoice.")

    return render(request, 'orders/invoice.html', {'order': order})


