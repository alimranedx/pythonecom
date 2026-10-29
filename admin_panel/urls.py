from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('', views.admin_dashboard, name='admin_dashboard'),

    # Products
    path('products/', views.admin_product_list, name='admin_product_list'),
    path('products/create/', views.admin_product_create, name='admin_product_create'),
    path('products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('products/images/<int:pk>/delete/', views.admin_product_image_delete, name='admin_product_image_delete'),

    # Categories
    path('categories/', views.admin_category_list, name='admin_category_list'),
    path('categories/create/', views.admin_category_create, name='admin_category_create'),
    path('categories/<int:pk>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('categories/<int:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),

    # Brands
    path('brands/', views.admin_brand_list, name='admin_brand_list'),
    path('brands/create/', views.admin_brand_create, name='admin_brand_create'),
    path('brands/<int:pk>/edit/', views.admin_brand_edit, name='admin_brand_edit'),
    path('brands/<int:pk>/delete/', views.admin_brand_delete, name='admin_brand_delete'),

    # Customer Reviews Moderation
    path('reviews/', views.admin_review_list, name='admin_review_list'),
    path('reviews/<int:pk>/delete/', views.admin_review_delete, name='admin_review_delete'),

    # Orders
    path('orders/', views.admin_order_list, name='admin_order_list'),
    path('orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:pk>/invoice/', views.admin_order_invoice, name='admin_order_invoice'),

    # Customers
    path('customers/', views.admin_customer_list, name='admin_customer_list'),
    path('customers/<int:pk>/', views.admin_customer_detail, name='admin_customer_detail'),
    path('customers/<int:pk>/toggle-status/', views.admin_customer_toggle_status, name='admin_customer_toggle_status'),

    # RBAC: User Management (Super Admin Only)
    path('rbac/users/', views.admin_staff_list, name='admin_staff_list'),
    path('rbac/users/create/', views.admin_staff_create, name='admin_staff_create'),
    path('rbac/users/<int:pk>/edit/', views.admin_staff_edit, name='admin_staff_edit'),
    path('rbac/users/<int:pk>/delete/', views.admin_staff_delete, name='admin_staff_delete'),
    path('rbac/staff/', views.admin_staff_list),  # Backward compatibility alias

    # RBAC: Role & Permission Management (Super Admin Only)
    path('rbac/roles/', views.admin_role_list, name='admin_role_list'),
    path('rbac/roles/create/', views.admin_role_create, name='admin_role_create'),
    path('rbac/roles/<int:pk>/edit/', views.admin_role_edit, name='admin_role_edit'),
    path('rbac/roles/<int:pk>/delete/', views.admin_role_delete, name='admin_role_delete'),
]
