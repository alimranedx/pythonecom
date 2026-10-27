from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerRegistrationForm, CustomerLoginForm, UserProfileForm, AddressForm
from .models import CustomerProfile, Address, Wishlist
from orders.models import Order
from product.models import Product
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
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')[:4]
    return render(request, 'accounts/dashboard.html', {
        'recent_orders': orders,
        'addresses': addresses,
        'wishlist_items': wishlist_items,
        'total_orders': Order.objects.filter(user=request.user).count(),
        'total_wishlist': Wishlist.objects.filter(user=request.user).count(),
    })


@login_required
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


@login_required
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


@login_required
def customer_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


@login_required
def customer_order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})


# ---------------- ADDRESS BOOK ----------------
@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
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


@login_required
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


@login_required
def address_delete(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        addr.delete()
        messages.success(request, "Address removed.")
        return redirect('address_list')
    return render(request, 'accounts/address_delete.html', {'address': addr})


# ---------------- USER WISHLIST ----------------
@login_required
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
    return redirect(request.META.get('HTTP_REFERER', 'wishlist_view'))


@login_required
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
