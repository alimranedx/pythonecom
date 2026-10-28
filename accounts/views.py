from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from core.validators import get_safe_redirect_url
from .forms import CustomerRegistrationForm, CustomerLoginForm, UserProfileForm, AddressForm
from .models import CustomerProfile, Address, Wishlist
from orders.models import Order
from product.models import Product
from cart.services import CartService


def customer_required(view_func):
    """
    Enforces strict panel isolation:
    Storefront account areas are exclusively for customers (is_staff=False).
    If a staff/admin user attempts to access customer account sections,
    they are redirected to their dedicated Back-Office Admin Panel.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if request.user.is_staff:
            messages.info(request, "Staff accounts access the Back-Office Admin Panel, not customer areas.")
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def customer_register(request):
    # If logged in user is not a customer (e.g. staff/admin),
    # clear all session and cookies so they can cleanly register as a customer.
    if request.user.is_authenticated:
        if request.user.is_staff:
            logout(request)
        else:
            return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            phone = form.cleaned_data.get('phone', '')
            CustomerProfile.objects.create(user=user, phone=phone)

            guest_session_key = request.session.session_key
            login(request, user)
            if guest_session_key:
                CartService.merge_guest_cart(guest_session_key, user)

            messages.success(request, f"Welcome to PythonEcom, {user.first_name or user.username}!")
            return redirect('customer_dashboard')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def customer_login(request):
    # If logged in user is not a customer (e.g. staff/admin),
    # clear all session and cookies so they can cleanly sign in as a customer.
    if request.user.is_authenticated:
        if request.user.is_staff:
            logout(request)
        else:
            return redirect('customer_dashboard')

    next_url = request.GET.get('next', '') or request.POST.get('next', '')

    if request.method == 'POST':
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            guest_session_key = request.session.session_key
            login(request, user)
            if guest_session_key:
                CartService.merge_guest_cart(guest_session_key, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomerLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def customer_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@customer_required
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = Address.objects.filter(user=request.user)
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')[:4]
    return render(request, 'accounts/dashboard.html', {
        'recent_orders': orders,
        'addresses': addresses,
        'wishlist_items': wishlist_items,
        'total_orders': Order.objects.filter(user=request.user).count(),
        'total_wishlist': Wishlist.objects.filter(user=request.user).count(),
    })


@customer_required
def customer_profile_edit(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('customer_dashboard')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})


@customer_required
def customer_password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Your password was successfully updated!")
            return redirect('customer_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


@customer_required
def customer_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


@customer_required
def customer_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})


# ---------------- ADDRESS BOOK ----------------
@customer_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@customer_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            messages.success(request, "New shipping address added.")
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})


@customer_required
def address_edit(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect('address_list')
    else:
        form = AddressForm(instance=addr)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address', 'address': addr})


@customer_required
def address_delete(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        addr.delete()
        messages.success(request, "Address removed.")
        return redirect('address_list')
    return render(request, 'accounts/address_delete.html', {'address': addr})


# ---------------- USER WISHLIST ----------------
@customer_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'accounts/wishlist.html', {'wishlist_items': wishlist_items})


def wishlist_toggle(request, product_id):
    """
    Toggles a product in customer's wishlist.
    Supports both AJAX JSON responses and standard HTTP redirects.
    """
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'login_required': True, 'redirect_url': '/account/login/'}, status=401)
        messages.info(request, "Please log in to save items to your wishlist.")
        return redirect('account_login')

    if request.user.is_staff:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Staff members cannot maintain customer wishlists.'}, status=403)
        messages.info(request, "Staff accounts access the Back-Office Admin Panel.")
        return redirect('admin_dashboard')

    product = get_object_or_404(Product, pk=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

    if wishlist_item:
        wishlist_item.delete()
        action = 'removed'
        msg = f"Removed '{product.name}' from your wishlist."
    else:
        Wishlist.objects.create(user=request.user, product=product)
        action = 'added'
        msg = f"Saved '{product.name}' to your wishlist!"

    count = Wishlist.objects.filter(user=request.user).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'message': msg,
            'count': count,
        })

    messages.success(request, msg)
    return redirect(get_safe_redirect_url(request, request.META.get('HTTP_REFERER'), 'wishlist_view'))


@customer_required
def wishlist_move_to_cart(request, product_id):
    """
    Moves an item from Wishlist into Cart in one click.
    """
    product = get_object_or_404(Product, pk=product_id)
    cart = CartService.get_or_create_cart(request)
    CartService.add_to_cart(cart, product, quantity=1)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"Moved '{product.name}' to your shopping cart!")
    return redirect('cart_detail')
