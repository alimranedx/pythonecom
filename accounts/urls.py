from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.customer_register, name='account_register'),
    path('login/', views.customer_login, name='account_login'),
    path('logout/', views.customer_logout, name='account_logout'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('orders/', views.customer_orders, name='customer_orders'),
    path('orders/<str:order_number>/', views.customer_order_detail, name='customer_order_detail'),
]
