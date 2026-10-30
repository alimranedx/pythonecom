from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from core.views import set_language_view

urlpatterns = [
    path('set-language/<str:lang_code>/', set_language_view, name='set_language'),
    path('admin/', admin.site.urls),  # Django's raw admin (superuser fallback)
    path('app-admin/', include('admin_panel.urls')),  # Custom RBAC Back-office Dashboard
    path('product/', include('product.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('account/', include('accounts.urls')),
    path('', include('home.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
