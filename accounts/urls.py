from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.customer_register, name='account_register'),
    path('login/', views.customer_login, name='account_login'),
    path('logout/', views.customer_logout, name='account_logout'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('profile/edit/', views.customer_profile_edit, name='customer_profile_edit'),
    path('password-change/', views.customer_password_change, name='customer_password_change'),
    path('orders/', views.customer_orders, name='customer_orders'),
    path('orders/<str:order_number>/', views.customer_order_detail, name='customer_order_detail'),

    # Address Book
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/create/', views.address_create, name='address_create'),
    path('addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/move-to-cart/<int:product_id>/', views.wishlist_move_to_cart, name='wishlist_move_to_cart'),
]
