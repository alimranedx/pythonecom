from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from cart.services import CartService
from accounts.models import Address
from .models import Order
from .services import OrderService


def checkout(request):
    cart = CartService.get_or_create_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your shopping cart is empty. Add products before proceeding to checkout.")
        return redirect('product_list')

    # Pre-fill address if authenticated
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['email'] = request.user.email
        initial_data['full_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        default_addr = Address.objects.filter(user=request.user, is_default=True).first()
        if default_addr:
            initial_data['phone'] = default_addr.phone
            initial_data['street_address'] = default_addr.street_address
            initial_data['city'] = default_addr.city
            initial_data['postal_code'] = default_addr.postal_code
            initial_data['country'] = default_addr.country

    if request.method == 'POST':
        shipping_data = {
            'full_name': request.POST.get('full_name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'street_address': request.POST.get('street_address', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'postal_code': request.POST.get('postal_code', '').strip(),
            'country': request.POST.get('country', 'Bangladesh').strip(),
            'notes': request.POST.get('notes', '').strip(),
            'payment_method': request.POST.get('payment_method', 'cod'),
        }

        # Basic validations
        required_fields = ['full_name', 'email', 'phone', 'street_address', 'city']
        missing = [f for f in required_fields if not shipping_data.get(f)]
        if missing:
            messages.error(request, "Please fill in all required shipping fields.")
            return render(request, 'orders/checkout.html', {'cart': cart, 'initial': shipping_data})

        try:
            order = OrderService.create_order_from_cart(
                cart=cart,
                shipping_data=shipping_data,
                user=request.user if request.user.is_authenticated else None,
            )
            messages.success(request, f"Order {order.order_number} confirmed! Thank you for shopping with us.")
            return redirect('order_confirmation', order_number=order.order_number)
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
            return render(request, 'orders/checkout.html', {'cart': cart, 'initial': shipping_data})
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during checkout: {e}")
            return render(request, 'orders/checkout.html', {'cart': cart, 'initial': shipping_data})

    return render(request, 'orders/checkout.html', {'cart': cart, 'initial': initial_data})


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/confirmation.html', {'order': order})
