from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerRegistrationForm, CustomerLoginForm, AddressForm
from .models import CustomerProfile, Address
from orders.models import Order
from cart.services import CartService


def customer_register(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            phone = form.cleaned_data.get('phone', '')
            CustomerProfile.objects.create(user=user, phone=phone)

            # Auto-login after registration
            login(request, user)
            if request.session.session_key:
                CartService.merge_guest_cart(request.session.session_key, user)

            messages.success(request, f"Welcome to PythonEcom, {user.first_name or user.username}!")
            return redirect('customer_dashboard')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def customer_login(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    next_url = request.GET.get('next', 'customer_dashboard')

    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.session.session_key:
                CartService.merge_guest_cart(request.session.session_key, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(next_url if next_url else 'customer_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomerLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def customer_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/dashboard.html', {
        'recent_orders': orders,
        'addresses': addresses,
        'total_orders': Order.objects.filter(user=request.user).count(),
    })


@login_required
def customer_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


@login_required
def customer_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})
