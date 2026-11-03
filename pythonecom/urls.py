from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from core.views import set_language_view

urlpatterns = [
    path('set-language/<str:lang_code>/', set_language_view, name='set_language'),
    path('app-admin/', include('admin_panel.urls')),  # Custom RBAC Back-office Dashboard
    path('product/', include('product.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('account/', include('accounts.urls')),
    path('', include('home.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

# Custom production error handlers
handler404 = 'core.views.custom_page_not_found_view'
handler500 = 'core.views.custom_server_error_view'
handler403 = 'core.views.custom_permission_denied_view'
handler400 = 'core.views.custom_bad_request_view'
