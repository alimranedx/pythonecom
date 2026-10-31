import re
import secrets
import urllib.parse
import requests
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
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
    if request.user.is_authenticated:
        if request.user.is_staff:
            logout(request)
        else:
            return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            guest_session_key = request.session.session_key
            login(request, user, backend='accounts.backends.PhoneOrUsernameBackend')
            if guest_session_key:
                CartService.merge_guest_cart(guest_session_key, user)

            messages.success(request, f"Welcome to ShopBusket, {user.first_name or user.username}!")
            return redirect('customer_dashboard')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def customer_login(request):
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
            # Enforce panel isolation: staff cannot log in through customer storefront
            if user.is_staff:
                messages.error(request, "This account is for administrative staff. Please sign in via the Admin portal.")
                return redirect('admin_login')

            guest_session_key = request.session.session_key
            login(request, user, backend='accounts.backends.PhoneOrUsernameBackend')
            if guest_session_key:
                CartService.merge_guest_cart(guest_session_key, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Invalid mobile number, email, or password.")
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


def google_login(request):
    """
    Initiates Google OAuth 2.0 flow for customer registration or sign-in.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            logout(request)
        else:
            return redirect('customer_dashboard')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()

    if not client_id or not client_secret:
        messages.warning(
            request,
            "Google Sign-In is pending setup. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the .env configuration."
        )
        next_param = request.GET.get('next')
        return redirect(next_param if next_param and url_has_allowed_host_and_scheme(next_param, {request.get_host()}) else 'account_login')

    # Security: Generate CSRF state token
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    # Capture optional post-auth redirect target
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
        request.session['google_oauth_next'] = next_url
    else:
        request.session.pop('google_oauth_next', None)

    # Determine redirect URI
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    if request.is_secure() or 'ecommerce.shopbusket.com' in request.get_host():
        redirect_uri = redirect_uri.replace('http://', 'https://')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


def _sync_google_avatar(profile, picture_url, user_id):
    """
    Downloads and caches the user's Google profile avatar.
    """
    if not picture_url:
        return
    try:
        resp = requests.get(picture_url, timeout=10)
        if resp.status_code == 200 and resp.content:
            filename = f"google_{user_id}.jpg"
            profile.avatar.save(filename, ContentFile(resp.content), save=True)
    except Exception:
        pass


def google_callback(request):
    """
    Handles Google OAuth 2.0 authorization code response.
    Creates new customer account or authenticates existing customer.
    """
    error = request.GET.get('error')
    if error:
        messages.info(request, f"Google authentication was cancelled: {error}")
        return redirect('account_login')

    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.pop('google_oauth_state', None)
    next_url = request.session.pop('google_oauth_next', None)

    if not code or not state or state != saved_state:
        messages.error(request, "Google sign-in session expired or invalid. Please try again.")
        return redirect('account_login')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    if request.is_secure() or 'ecommerce.shopbusket.com' in request.get_host():
        redirect_uri = redirect_uri.replace('http://', 'https://')

    # Exchange authorization code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    try:
        token_resp = requests.post(token_url, data=token_payload, timeout=15)
        token_data = token_resp.json()
    except Exception as e:
        messages.error(request, f"Failed to connect to Google OAuth servers: {e}")
        return redirect('account_login')

    if token_resp.status_code != 200 or 'access_token' not in token_data:
        err_msg = token_data.get('error_description') or token_data.get('error', 'Token exchange failed')
        messages.error(request, f"Google login error: {err_msg}")
        return redirect('account_login')

    access_token = token_data['access_token']

    # Retrieve profile info from Google
    userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    try:
        userinfo_resp = requests.get(userinfo_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=15)
        user_info = userinfo_resp.json()
    except Exception as e:
        messages.error(request, f"Failed to retrieve user profile from Google: {e}")
        return redirect('account_login')

    email = user_info.get('email', '').strip().lower()
    if not email:
        messages.error(request, "Google did not provide a valid email address.")
        return redirect('account_login')

    # Look up existing user
    user = User.objects.filter(email__iexact=email).first()

    if user:
        # Enforce panel isolation: staff accounts must log in via admin portal
        if user.is_staff:
            messages.error(request, "This Google account belongs to an administrative staff user. Please log in through the Admin Portal.")
            return redirect('admin_login')

        profile, _ = CustomerProfile.objects.get_or_create(user=user)

        # Update name if missing
        updated = False
        given_name = user_info.get('given_name') or user_info.get('name', '').split(' ')[0]
        family_name = user_info.get('family_name') or (user_info.get('name', '').split(' ')[1] if ' ' in user_info.get('name', '') else '')
        if not user.first_name and given_name:
            user.first_name = given_name
            updated = True
        if not user.last_name and family_name:
            user.last_name = family_name
            updated = True
        if updated:
            user.save(update_fields=['first_name', 'last_name'])

        # Sync avatar from Google if not yet set
        picture_url = user_info.get('picture')
        if picture_url and not profile.avatar:
            _sync_google_avatar(profile, picture_url, user.pk)
    else:
        # Create a new customer user
        given_name = user_info.get('given_name') or user_info.get('name', '').split(' ')[0]
        family_name = user_info.get('family_name') or (user_info.get('name', '').split(' ')[1] if ' ' in user_info.get('name', '') else '')

        # Generate unique username from email
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0]) or 'customer'
        candidate_username = base_username
        suffix = 1
        while User.objects.filter(username__iexact=candidate_username).exists():
            candidate_username = f"{base_username}_{suffix}"
            suffix += 1

        user = User.objects.create_user(
            username=candidate_username,
            email=email,
            first_name=given_name,
            last_name=family_name,
            is_staff=False,
        )
        user.set_unusable_password()
        user.save()

        profile = CustomerProfile.objects.create(user=user, phone='')
        picture_url = user_info.get('picture')
        if picture_url:
            _sync_google_avatar(profile, picture_url, user.pk)

    # Log in the user
    guest_session_key = request.session.session_key
    login(request, user)
    if guest_session_key:
        CartService.merge_guest_cart(guest_session_key, user)

    display_name = user.first_name or user.username
    messages.success(request, f"Welcome, {display_name}! Successfully authenticated with Google.")

    if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('customer_dashboard')
