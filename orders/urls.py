from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('bkash/callback/', views.bkash_callback, name='bkash_callback'),
    path('bkash/retry/<str:order_number>/', views.retry_bkash_payment, name='retry_bkash_payment'),
    path('invoice/<str:order_number>/', views.order_invoice, name='order_invoice'),
]
