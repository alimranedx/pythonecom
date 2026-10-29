from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
