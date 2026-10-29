from django.urls import reverse
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from core.validators import validate_image_file
from rbac.decorators import require_permission, require_superuser
from .forms import StaffUserCreateForm, StaffUserEditForm, SiteSettingForm
from core.models import SiteSetting
from rbac.services import RBACService
from rbac.models import Role, Permission, UserRole, RolePermission, Module
from product.models import Product, Category, Brand, ProductImage, ProductReview
from product.forms import ProductForm, CategoryForm, BrandForm
from orders.models import Order, OrderItem, DeliverySlot, Coupon
from accounts.models import CustomerProfile, Address


def admin_login(request):
    """
    Dedicated back-office staff authentication portal.
    If the currently logged-in user is not a staff member (e.g. customer),
    clear all existing session and cookies so they can cleanly sign in as staff.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            logout(request)

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome to Back-Office, {user.get_full_name() or user.username}!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access restricted: Staff credentials required.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'admin_panel/login.html')


@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    messages.info(request, "Successfully logged out from admin portal.")
    return redirect('admin_login')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Staff credentials required.")
        return redirect('home')

    paid_orders = Order.objects.filter(payment_status='paid')
    total_revenue = paid_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    paid_count = paid_orders.count()
    aov = (total_revenue / paid_count).quantize(Decimal('0.01')) if paid_count > 0 else Decimal('0.00')

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5)
    total_customers = User.objects.filter(is_staff=False).count()

    # Fulfillment status breakdown
    status_counts = {
        'pending': pending_orders,
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]

    return render(request, 'admin_panel/dashboard.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'aov': aov,
        'total_products': total_products,
        'low_stock_count': low_stock_products.count(),
        'low_stock_products': low_stock_products[:5],
        'total_customers': total_customers,
        'status_counts': status_counts,
        'recent_orders': recent_orders,
    })


# ---------------- CATALOG: PRODUCTS ----------------
@require_permission('catalog.products', 'view')
def admin_product_list(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    stock_status = request.GET.get('stock', '').strip()

    products = Product.objects.select_related('category', 'brand').order_by('-created_at')

    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    if category_id:
        products = products.filter(category_id=category_id)

    if stock_status == 'in_stock':
        products = products.filter(stock__gt=5)
    elif stock_status == 'low_stock':
        products = products.filter(stock__gt=0, stock__lte=5)
    elif stock_status == 'out_of_stock':
        products = products.filter(stock=0)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'admin_panel/products/list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'category_id': category_id,
        'stock_status': stock_status,
        'q': q,
    })


@require_permission('catalog.products', 'create')
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save()
            gallery_files = request.FILES.getlist('gallery_images')
            valid_count = 0
            for f in gallery_files:
                try:
                    validate_image_file(f)
                    ProductImage.objects.create(product=p, image=f)
                    valid_count += 1
                except ValidationError as e:
                    msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                    messages.warning(request, f"Skipped file '{f.name}': {msg}")
            messages.success(request, f"Product '{p.name}' created with {valid_count} gallery image(s).")
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'admin_panel/products/form.html', {'form': form, 'title': 'Create Product'})


@require_permission('catalog.products', 'edit')
def admin_product_edit(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('images'), pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            gallery_files = request.FILES.getlist('gallery_images')
            valid_count = 0
            for f in gallery_files:
                try:
                    validate_image_file(f)
                    ProductImage.objects.create(product=product, image=f)
                    valid_count += 1
                except ValidationError as e:
                    msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                    messages.warning(request, f"Skipped file '{f.name}': {msg}")
            if valid_count > 0:
                messages.success(request, f"Added {valid_count} new gallery image(s).")
            else:
                messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect('admin_product_edit', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/products/form.html', {
        'form': form,
        'title': f"Edit {product.name}",
        'product': product,
        'gallery_images': product.images.all()
    })


@require_permission('catalog.products', 'edit')
def admin_product_image_delete(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product_pk = image.product.pk
    if request.method == 'POST':
        image.delete()
        messages.success(request, "Gallery image deleted.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('admin_product_edit', pk=product_pk)


@require_permission('catalog.products', 'delete')
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' was deleted.")
        return redirect('admin_product_list')
    return render(request, 'admin_panel/products/delete.html', {'product': product})


# ---------------- CATALOG: CATEGORIES ----------------
@require_permission('catalog.categories', 'view')
def admin_category_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).all()
    return render(request, 'admin_panel/categories/list.html', {'categories': categories})


@require_permission('catalog.categories', 'create')
def admin_category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created.")
            return redirect('admin_category_list')
    else:
        form = CategoryForm()
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'title': 'Create Category'})


@require_permission('catalog.categories', 'edit')
def admin_category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{cat.name}' updated.")
            return redirect('admin_category_list')
    else:
        form = CategoryForm(instance=cat)
    return render(request, 'admin_panel/categories/form.html', {'form': form, 'title': f"Edit {cat.name}", 'category': cat})


@require_permission('catalog.categories', 'delete')
def admin_category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f"Category '{name}' deleted.")
        return redirect('admin_category_list')
    return render(request, 'admin_panel/categories/delete.html', {'category': cat})


# ---------------- CATALOG: BRANDS ----------------
@require_permission('catalog.brands', 'view')
def admin_brand_list(request):
    q = request.GET.get('q', '').strip()
    brands = Brand.objects.annotate(product_count=Count('products')).order_by('name')
    if q:
        brands = brands.filter(Q(name__icontains=q) | Q(slug__icontains=q))

    paginator = Paginator(brands, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel/brands/list.html', {
        'brands': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@require_permission('catalog.brands', 'create')
def admin_brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            brand = form.save(commit=False)
            if 'logo' in request.FILES:
                try:
                    validate_image_file(request.FILES['logo'])
                except ValidationError as e:
                    form.add_error('logo', e.messages[0] if hasattr(e, 'messages') else str(e))
                    return render(request, 'admin_panel/brands/form.html', {'form': form, 'title': 'Create Brand'})
            brand.save()
            messages.success(request, f"Brand '{brand.name}' created successfully.")
            return redirect('admin_brand_list')
    else:
        form = BrandForm()
    return render(request, 'admin_panel/brands/form.html', {'form': form, 'title': 'Create Brand'})


@require_permission('catalog.brands', 'edit')
def admin_brand_edit(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            brand = form.save(commit=False)
            if 'logo' in request.FILES:
                try:
                    validate_image_file(request.FILES['logo'])
                except ValidationError as e:
                    form.add_error('logo', e.messages[0] if hasattr(e, 'messages') else str(e))
                    return render(request, 'admin_panel/brands/form.html', {'form': form, 'title': f"Edit {brand.name}", 'brand': brand})
            brand.save()
            messages.success(request, f"Brand '{brand.name}' updated successfully.")
            return redirect('admin_brand_list')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'admin_panel/brands/form.html', {'form': form, 'title': f"Edit {brand.name}", 'brand': brand})


@require_permission('catalog.brands', 'delete')
def admin_brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        name = brand.name
        brand.delete()
        messages.success(request, f"Brand '{name}' was deleted.")
        return redirect('admin_brand_list')
    return render(request, 'admin_panel/brands/delete.html', {'brand': brand})


# ---------------- CATALOG: CUSTOMER REVIEWS ----------------
@require_permission('catalog.reviews', 'view')
def admin_review_list(request):
    q = request.GET.get('q', '').strip()
    rating = request.GET.get('rating', '').strip()

    reviews = ProductReview.objects.select_related('product', 'user').order_by('-created_at')
    if q:
        reviews = reviews.filter(
            Q(product__name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(comment__icontains=q)
        )
    if rating.isdigit():
        reviews = reviews.filter(rating=int(rating))

    paginator = Paginator(reviews, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel/reviews/list.html', {
        'reviews': page_obj,
        'page_obj': page_obj,
        'q': q,
        'rating_filter': rating,
    })


@require_permission('catalog.reviews', 'delete')
def admin_review_delete(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Review deleted successfully.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('admin_review_list')


# ---------------- ORDERS MODULE ----------------
@require_permission('orders.orders', 'view')
def admin_order_list(request):
    def get_filter_list(param_name):
        raw_values = request.GET.getlist(param_name)
        result = []
        for val in raw_values:
            if val:
                for item in str(val).split(','):
                    cleaned = item.strip()
                    if cleaned and cleaned not in result:
                        result.append(cleaned)
        return result

    status_filters = get_filter_list('status')
    payment_status_filters = get_filter_list('payment_status')
    payment_method_filter = request.GET.get('payment_method', '').strip()
    order_id_filter = request.GET.get('order_id', '').strip()
    customer_filter = request.GET.get('customer', '').strip()
    q = request.GET.get('q', '').strip()

    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()
    date_range_str = request.GET.get('date_range', '').strip()

    min_amount = request.GET.get('min_amount', '').strip()
    max_amount = request.GET.get('max_amount', '').strip()

    orders = Order.objects.select_related('user').all()

    # Parse combined date_range string (e.g. '2026/10/28 00:00:00 - 2026/10/29 23:59:59')
    if date_range_str and (not date_from_str or not date_to_str):
        parts = date_range_str.split(' - ') if ' - ' in date_range_str else date_range_str.split(' to ')
        if len(parts) == 2:
            date_from_str = parts[0].strip()
            date_to_str = parts[1].strip()

    def parse_dt(val, is_end=False):
        if not val:
            return None
        clean_val = val.strip().replace('/', '-')
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_val, fmt)
                if fmt == '%Y-%m-%d' and is_end:
                    dt = dt.replace(hour=23, minute=59, second=59)
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt, timezone.get_current_timezone())
                return dt
            except ValueError:
                pass
        return None

    dt_from = parse_dt(date_from_str, is_end=False)
    dt_to = parse_dt(date_to_str, is_end=True)

    if dt_from:
        orders = orders.filter(created_at__gte=dt_from)
    if dt_to:
        orders = orders.filter(created_at__lte=dt_to)

    if status_filters:
        orders = orders.filter(status__in=status_filters)

    if payment_status_filters:
        orders = orders.filter(payment_status__in=payment_status_filters)

    if payment_method_filter:
        orders = orders.filter(payment_method=payment_method_filter)

    if order_id_filter:
        orders = orders.filter(order_number__icontains=order_id_filter)

    if customer_filter:
        orders = orders.filter(
            Q(full_name__icontains=customer_filter) |
            Q(email__icontains=customer_filter) |
            Q(phone__icontains=customer_filter) |
            Q(user__username__icontains=customer_filter)
        )

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    if min_amount:
        try:
            orders = orders.filter(total_amount__gte=Decimal(min_amount))
        except (ValueError, TypeError):
            pass

    if max_amount:
        try:
            orders = orders.filter(total_amount__lte=Decimal(max_amount))
        except (ValueError, TypeError):
            pass

    # Count active non-empty filters
    active_filters_count = sum([
        bool(status_filters),
        bool(payment_status_filters),
        bool(payment_method_filter),
        bool(order_id_filter),
        bool(customer_filter),
        bool(q),
        bool(dt_from or dt_to),
        bool(min_amount),
        bool(max_amount),
    ])

    # Check for CSV Export
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="orders_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Order Number', 'Date (UTC)', 'Customer Name', 'Email', 'Phone',
            'Shipping Address', 'City', 'Country',
            'Subtotal', 'Shipping Fee', 'Total Amount',
            'Order Status', 'Payment Status', 'Payment Method'
        ])

        for o in orders:
            writer.writerow([
                o.order_number,
                o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                o.full_name,
                o.email,
                o.phone,
                o.street_address,
                o.city,
                o.country,
                o.subtotal,
                o.shipping_fee,
                o.total_amount,
                o.get_status_display(),
                o.get_payment_status_display(),
                o.get_payment_method_display(),
            ])
        return response

    total_filtered_orders = orders.count()
    total_filtered_revenue = orders.filter(payment_status='paid').aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')

    per_page_raw = request.GET.get('per_page', '10').strip()
    try:
        per_page = int(per_page_raw)
        if per_page not in [5, 10, 20, 25, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(orders, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    try:
        elided_page_range = paginator.get_elided_page_range(
            page_obj.number, on_each_side=2, on_ends=1
        )
    except Exception:
        elided_page_range = paginator.page_range

    # Clean query string for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_params['per_page'] = per_page
    if status_filters:
        query_params.setlist('status', status_filters)
    elif 'status' in query_params:
        del query_params['status']
    if payment_status_filters:
        query_params.setlist('payment_status', payment_status_filters)
    elif 'payment_status' in query_params:
        del query_params['payment_status']
    querystring = query_params.urlencode()

    status_filter = status_filters[0] if len(status_filters) == 1 else (','.join(status_filters) if status_filters else '')
    payment_status_filter = payment_status_filters[0] if len(payment_status_filters) == 1 else (','.join(payment_status_filters) if payment_status_filters else '')

    return render(request, 'admin_panel/orders/list.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'elided_page_range': elided_page_range,
        'per_page': per_page,
        'per_page_options': [5, 10, 20, 50, 100],
        'ellipsis': getattr(paginator, 'ELLIPSIS', '…'),
        'status_filters': status_filters,
        'status_filter': status_filter,
        'payment_status_filters': payment_status_filters,
        'payment_status_filter': payment_status_filter,
        'payment_method_filter': payment_method_filter,
        'order_id_filter': order_id_filter,
        'customer_filter': customer_filter,
        'date_range': date_range_str,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'active_filters_count': active_filters_count,
        'total_filtered_orders': total_filtered_orders,
        'total_filtered_revenue': total_filtered_revenue,
        'statuses': Order.STATUS_CHOICES,
        'payment_statuses': Order.PAYMENT_STATUS_CHOICES,
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
        'querystring': querystring,
        'q': q,
    })


@require_permission('orders.orders', 'view')
def admin_order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)

    if request.method == 'POST':
        from rbac.services import RBACService
        if not RBACService.user_has_permission(request.user, 'orders.orders', 'edit'):
            messages.error(request, "You do not have permission to modify orders.")
            return redirect('admin_order_detail', pk=order.pk)

        old_status = order.status
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')

        if new_status in dict(Order.STATUS_CHOICES):
            # Auto-restore or adjust inventory on order status transitions
            if new_status == 'cancelled' and old_status != 'cancelled':
                for item in order.items.all():
                    if item.product:
                        item.product.stock += item.quantity
                        item.product.save(update_fields=['stock'])
                messages.info(request, "Restored inventory stock for cancelled order items.")
            elif old_status == 'cancelled' and new_status != 'cancelled':
                for item in order.items.all():
                    if item.product:
                        item.product.stock = max(0, item.product.stock - item.quantity)
                        item.product.save(update_fields=['stock'])
                messages.info(request, "Deducted stock for reopened order items.")

            order.status = new_status

        if new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status

        order.save()
        messages.success(request, f"Order {order.order_number} status updated successfully.")
        return redirect('admin_order_detail', pk=order.pk)

    return render(request, 'admin_panel/orders/detail.html', {'order': order})


@require_permission('orders.orders', 'view')
def admin_order_invoice(request, pk):
    """
    Renders a print-ready, professional order invoice / packing slip
    suitable for browser printing (window.print()) or PDF export.
    """
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    return render(request, 'admin_panel/orders/invoice.html', {'order': order})


# ---------------- CUSTOMERS MODULE ----------------
@require_permission('customers.customers', 'view')
def admin_customer_list(request):
    q = request.GET.get('q', '').strip()
    customers = User.objects.filter(is_staff=False).annotate(
        orders_count=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).order_by('-date_joined')

    if q:
        customers = customers.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )

    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_panel/customers/list.html', {
        'customers': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@require_permission('customers.customers', 'view')
def admin_customer_detail(request, pk):
    """
    Full 360 Customer Profile:
    Personal info, lifetime spend, order history, and saved address book.
    """
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    orders = Order.objects.filter(user=customer).order_by('-created_at')

    total_orders = orders.count()
    settled_orders = orders.filter(payment_status='paid')
    total_spent = settled_orders.aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')
    aov = (total_spent / settled_orders.count()).quantize(Decimal('0.01')) if settled_orders.count() > 0 else Decimal('0.00')

    addresses = Address.objects.filter(user=customer)

    return render(request, 'admin_panel/customers/detail.html', {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'aov': aov,
        'addresses': addresses,
    })


@require_permission('customers.customers', 'edit')
def admin_customer_toggle_status(request, pk):
    """
    Toggles customer account active/suspended state.
    """
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    if request.method == 'POST':
        customer.is_active = not customer.is_active
        customer.save(update_fields=['is_active'])
        state = "activated" if customer.is_active else "suspended"
        messages.success(request, f"Customer account '{customer.username}' has been {state}.")
    return redirect('admin_customer_detail', pk=customer.pk)


# ---------------- ACCESS CONTROL & USER MANAGEMENT (SUPERUSER ONLY) ----------------
@require_superuser
def admin_role_list(request):
    """
    Lists all roles with assigned user counts.
    Strictly restricted to Super Administrators.
    """
    roles = Role.objects.annotate(users_count=Count('user_roles')).all()
    return render(request, 'admin_panel/rbac/roles.html', {'roles': roles})


@require_superuser
def admin_role_create(request):
    """
    Creates a new custom role.
    Strictly restricted to Super Administrators.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            messages.error(request, "Role name is required.")
        elif Role.objects.filter(name=name).exists():
            messages.error(request, "A role with this name already exists.")
        else:
            role = Role.objects.create(name=name, description=description)
            messages.success(request, f"Role '{role.name}' created. Configure its permissions below.")
            return redirect('admin_role_edit', pk=role.pk)
    return render(request, 'admin_panel/rbac/role_create.html')


@require_superuser
def admin_role_edit(request, pk):
    """
    Configures module/submodule permission matrix for a role.
    Excludes the 'rbac' module so only Super Admin maintains access control.
    Strictly restricted to Super Administrators.
    """
    role = get_object_or_404(Role, pk=pk)
    modules = Module.objects.exclude(code='rbac').prefetch_related('submodules__permissions').all()

    if request.method == 'POST':
        perm_ids = request.POST.getlist('permissions')
        selected_perms = Permission.objects.filter(id__in=perm_ids).exclude(submodule__module__code='rbac')

        RolePermission.objects.filter(role=role).delete()
        RolePermission.objects.bulk_create([
            RolePermission(role=role, permission=p) for p in selected_perms
        ])
        messages.success(request, f"Permissions for role '{role.name}' updated successfully.")
        return redirect('admin_role_list')

    assigned_perm_ids = set(role.permissions.values_list('id', flat=True))
    return render(request, 'admin_panel/rbac/role_edit.html', {
        'role': role,
        'modules': modules,
        'assigned_perm_ids': assigned_perm_ids,
    })


@require_superuser
def admin_role_delete(request, pk):
    """
    Deletes a custom role if not in use.
    Strictly restricted to Super Administrators.
    """
    role = get_object_or_404(Role, pk=pk)
    if role.is_system_role:
        messages.error(request, f"Cannot delete '{role.name}': System roles are protected.")
        return redirect('admin_role_list')

    assigned_count = role.user_roles.count()
    if assigned_count > 0:
        messages.error(request, f"Cannot delete '{role.name}': Currently assigned to {assigned_count} staff user(s).")
        return redirect('admin_role_list')

    role_name = role.name
    role.delete()
    messages.success(request, f"Role '{role_name}' deleted successfully.")
    return redirect('admin_role_list')


# ---------------- ADMIN USER MANAGEMENT (SUPERUSER ONLY) ----------------
@require_superuser
def admin_staff_list(request):
    """
    Lists all administrative staff users with role badges, active status,
    and search capabilities.
    Strictly restricted to Super Administrators.
    """
    q = request.GET.get('q', '').strip()
    staff_users = User.objects.filter(is_staff=True).prefetch_related('user_roles__role').order_by('-is_superuser', 'username')
    if q:
        staff_users = staff_users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    roles = Role.objects.all()

    return render(request, 'admin_panel/rbac/staff.html', {
        'staff_users': staff_users,
        'roles': roles,
        'q': q,
    })


@require_superuser
def admin_staff_create(request):
    """
    Creates a new administrative staff user with designated role and credentials.
    Strictly restricted to Super Administrators.
    """
    if request.method == 'POST':
        form = StaffUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.set_password(form.cleaned_data['password'])
            user.save()

            role = form.cleaned_data.get('role')
            if role:
                UserRole.objects.create(user=user, role=role)

            messages.success(request, f"Admin user '{user.username}' created successfully!")
            return redirect('admin_staff_list')
    else:
        form = StaffUserCreateForm()

    return render(request, 'admin_panel/rbac/staff_form.html', {
        'form': form,
        'title': 'Create Admin User',
    })


@require_superuser
def admin_staff_edit(request, pk):
    """
    Edits an existing staff user's details, role assignment, active status,
    and optional password reset.
    Strictly restricted to Super Administrators.
    """
    staff_user = get_object_or_404(User, pk=pk, is_staff=True)

    if request.method == 'POST':
        form = StaffUserEditForm(request.POST, instance=staff_user)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True

            # Safety: Cannot remove own superuser status
            if request.user.pk == staff_user.pk and not form.cleaned_data.get('is_superuser'):
                user.is_superuser = True
                messages.warning(request, "You cannot remove superuser privileges from your own account.")

            # Safety: Cannot deactivate own account
            if request.user.pk == staff_user.pk and not form.cleaned_data.get('is_active'):
                user.is_active = True
                messages.warning(request, "You cannot deactivate your own account.")

            new_password = form.cleaned_data.get('new_password')
            if new_password:
                user.set_password(new_password)

            user.save()

            # Update assigned role
            role = form.cleaned_data.get('role')
            UserRole.objects.filter(user=user).delete()
            if role:
                UserRole.objects.create(user=user, role=role)

            messages.success(request, f"Admin user '{user.username}' updated successfully.")
            return redirect('admin_staff_list')
    else:
        form = StaffUserEditForm(instance=staff_user)

    return render(request, 'admin_panel/rbac/staff_form.html', {
        'form': form,
        'title': f'Edit Admin User: {staff_user.username}',
        'staff_user': staff_user,
    })


@require_superuser
def admin_staff_delete(request, pk):
    """
    Deletes an administrative user.
    Strictly restricted to Super Administrators (self-deletion blocked).
    """
    staff_user = get_object_or_404(User, pk=pk, is_staff=True)

    if request.user.pk == staff_user.pk:
        messages.error(request, "Security protection: You cannot delete your own Super Administrator account.")
        return redirect('admin_staff_list')

    username = staff_user.username
    staff_user.delete()
    messages.success(request, f"Admin user '{username}' deleted successfully.")
    return redirect('admin_staff_list')


# ==========================================
# Delivery Slots & Coupon Management (Chaldal Style)
# ==========================================

@require_permission('orders.orders', 'view')
def admin_delivery_slots_list(request):
    slots = DeliverySlot.objects.all().order_by('order', 'start_time')
    return render(request, 'admin_panel/orders/delivery_slots.html', {'slots': slots})


@require_permission('orders.orders', 'edit')
def admin_delivery_slot_toggle(request, pk):
    slot = get_object_or_404(DeliverySlot, pk=pk)
    slot.is_active = not slot.is_active
    slot.save(update_fields=['is_active'])
    status_str = "activated" if slot.is_active else "deactivated"
    messages.success(request, f"Delivery slot '{slot.title}' has been {status_str}.")
    return redirect('admin_delivery_slots_list')


@require_permission('orders.orders', 'view')
def admin_coupon_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/orders/coupons_list.html', {'coupons': coupons})


@require_permission('orders.orders', 'create')
def admin_coupon_create(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percent')
        discount_value = request.POST.get('discount_value', '0').strip()
        min_order_amount = request.POST.get('min_order_amount', '0').strip()
        max_discount_amount = request.POST.get('max_discount_amount', '').strip() or None
        valid_days = int(request.POST.get('valid_days', '30'))

        if not code or not discount_value:
            messages.error(request, "Code and Discount Value are required.")
            return redirect('admin_coupon_list')

        now = timezone.now()
        Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=Decimal(discount_value),
            min_order_amount=Decimal(min_order_amount or '0.00'),
            max_discount_amount=Decimal(max_discount_amount) if max_discount_amount else None,
            valid_from=now,
            valid_to=now + timedelta(days=valid_days),
            is_active=True,
        )
        messages.success(request, f"Coupon '{code}' created successfully.")
        return redirect('admin_coupon_list')

    return redirect('admin_coupon_list')


@require_permission('orders.orders', 'edit')
def admin_coupon_toggle(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save(update_fields=['is_active'])
    status_str = "activated" if coupon.is_active else "deactivated"
    messages.success(request, f"Coupon '{coupon.code}' has been {status_str}.")
    return redirect('admin_coupon_list')


@require_permission('orders.orders', 'delete')
def admin_coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    code = coupon.code
    coupon.delete()
    messages.success(request, f"Coupon '{code}' was deleted successfully.")
    return redirect('admin_coupon_list')


@require_permission('settings.site_settings', 'view')
def admin_site_settings(request):
    """
    Manage Storefront Branding, Top Header Announcements, Contact Information,
    and Footer Details with granular RBAC permissions.
    """
    setting = SiteSetting.get_settings()
    can_edit = request.user.is_superuser or RBACService.user_has_permission(request.user, 'settings.site_settings', 'edit')

    if request.method == 'POST':
        if not can_edit:
            messages.error(request, 'Permission Denied: You do not have permission to edit store settings.')
            return redirect('admin_site_settings')

        active_tab = request.POST.get('active_tab', '').strip()
        redirect_url = reverse('admin_site_settings')
        if active_tab:
            redirect_url += f'#{active_tab}'

        form = SiteSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store & Brand Settings updated successfully!')
            return redirect(redirect_url)
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        form = SiteSettingForm(instance=setting)

    context = {
        'form': form,
        'setting': setting,
        'can_edit': can_edit,
    }
    return render(request, 'admin_panel/settings/site_settings.html', context)
