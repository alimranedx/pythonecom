from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from product.models import Product, Category
from core.models import SiteSetting
from rbac.models import Module, Submodule, Permission, Role, UserRole, RolePermission
from core.translations import get_translation, to_bn_number, TranslationProxy


class BilingualStorefrontTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            username='customer_user',
            email='customer@example.com',
            password='Password123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin_lang_test',
            email='admin_lang@test.com',
            password='Password123'
        )
        self.category = Category.objects.create(name='Daily Groceries', slug='daily-groceries')
        self.product = Product.objects.create(
            name='Fresh Milk',
            category=self.category,
            price=Decimal('120.00'),
            stock=25,
            is_featured=True,
            is_active=True
        )

    def test_default_root_route_is_english(self):
        """Root route '/' defaults to English without language preference."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['CURRENT_LANGUAGE'], 'en')
        self.assertFalse(res.context['IS_BANGLA'])
        content = res.content.decode('utf-8')
        self.assertIn('Free Express Shipping', content)
        self.assertIn('Shop by Category', content)
        self.assertIn('Trending Products', content)
        self.assertIn('Add to Cart', content)

    def test_switch_language_to_bangla(self):
        """Calling /set-language/bn/ sets session & cookie and redirects."""
        res = self.client.get('/set-language/bn/', HTTP_REFERER='/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.client.session['site_language'], 'bn')

        # Now load root route '/' with Bangla session
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertEqual(res_home.context['CURRENT_LANGUAGE'], 'bn')
        self.assertTrue(res_home.context['IS_BANGLA'])
        content = res_home.content.decode('utf-8')
        self.assertIn('ফ্রি এক্সপ্রেস ডেলিভারি', content)
        self.assertIn('ক্যাটাগরি অনুযায়ী কিনুন', content)
        self.assertIn('জনপ্রিয় পণ্যসমূহ', content)
        self.assertIn('ব্যাগে যোগ করুন', content)

    def test_switch_language_back_to_english(self):
        """Switching to Bangla then back to English works seamlessly."""
        self.client.get('/set-language/bn/')
        self.assertEqual(self.client.session['site_language'], 'bn')

        res = self.client.get('/set-language/en/', HTTP_REFERER='/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.client.session['site_language'], 'en')

        res_home = self.client.get('/')
        self.assertEqual(res_home.context['CURRENT_LANGUAGE'], 'en')
        self.assertFalse(res_home.context['IS_BANGLA'])
        content = res_home.content.decode('utf-8')
        self.assertIn('Trending Products', content)
        self.assertIn('Add to Cart', content)

    def test_catalog_page_bilingual(self):
        """Catalog page /product/ renders properly in English and Bangla."""
        # 1. English
        self.client.get('/set-language/en/')
        res_en = self.client.get('/product/')
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode('utf-8')
        self.assertIn('All Products', content_en)
        self.assertIn('Show:', content_en)
        self.assertIn('Sort:', content_en)
        self.assertIn('Filters', content_en)

        # 2. Bangla
        self.client.get('/set-language/bn/')
        res_bn = self.client.get('/product/')
        self.assertEqual(res_bn.status_code, 200)
        content_bn = res_bn.content.decode('utf-8')
        self.assertIn('সকল পণ্য', content_bn)
        self.assertIn('দেখান:', content_bn)
        self.assertIn('সাজান:', content_bn)
        self.assertIn('ফিল্টার', content_bn)
        self.assertIn('ব্যাগে যোগ করুন', content_bn)

    def test_product_detail_page_bilingual(self):
        """Product Detail page /product/<id>/ renders properly in English and Bangla."""
        url = f'/product/{self.product.pk}/'

        # 1. English
        self.client.get('/set-language/en/')
        res_en = self.client.get(url)
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode('utf-8')
        self.assertIn('In Stock', content_en)
        self.assertIn('Quantity:', content_en)
        self.assertIn('Add to Shopping Bag', content_en)
        self.assertIn('Detailed Description', content_en)

        # 2. Bangla
        self.client.get('/set-language/bn/')
        res_bn = self.client.get(url)
        self.assertEqual(res_bn.status_code, 200)
        content_bn = res_bn.content.decode('utf-8')
        self.assertIn('স্টকে আছে', content_bn)
        self.assertIn('পরিমাণ:', content_bn)
        self.assertIn('শপিং ব্যাগে যোগ করুন', content_bn)
        self.assertIn('বিস্তারিত বিবরণ', content_bn)

    def test_cart_detail_page_bilingual(self):
        """Cart page /cart/ renders properly in English and Bangla."""
        # Add item to cart
        self.client.post(f'/cart/add/{self.product.pk}/')

        # 1. English
        self.client.get('/set-language/en/')
        res_en = self.client.get('/cart/')
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode('utf-8')
        self.assertIn('Continue Shopping', content_en)
        self.assertIn('Order Summary', content_en)
        self.assertIn('Proceed to Checkout', content_en)

        # 2. Bangla
        self.client.get('/set-language/bn/')
        res_bn = self.client.get('/cart/')
        self.assertEqual(res_bn.status_code, 200)
        content_bn = res_bn.content.decode('utf-8')
        self.assertIn('আরও কেনাকাটা করুন', content_bn)
        self.assertIn('অর্ডার বিবরণী', content_bn)
        self.assertIn('অর্ডার সম্পন্ন করুন', content_bn)

    def test_checkout_page_bilingual(self):
        """Checkout page /orders/checkout/ renders properly in English and Bangla."""
        self.client.post(f'/cart/add/{self.product.pk}/')

        # 1. English
        self.client.get('/set-language/en/')
        res_en = self.client.get('/orders/checkout/')
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode('utf-8')
        self.assertIn('Express Checkout', content_en)
        self.assertIn('Full Name', content_en)
        self.assertIn('Inside Dhaka City', content_en)

        # 2. Bangla
        self.client.get('/set-language/bn/')
        res_bn = self.client.get('/orders/checkout/')
        self.assertEqual(res_bn.status_code, 200)
        content_bn = res_bn.content.decode('utf-8')
        self.assertIn('এক্সপ্রেস চেকআউট', content_bn)
        self.assertIn('পুরো নাম', content_bn)
        self.assertIn('ঢাকা শহরের ভেতর', content_bn)

    def test_account_auth_pages_bilingual(self):
        """Account login and register pages render properly in English and Bangla."""
        # 1. Login English vs Bangla
        self.client.get('/set-language/en/')
        res_login_en = self.client.get('/account/login/')
        self.assertIn('Customer Sign In', res_login_en.content.decode('utf-8'))

        self.client.get('/set-language/bn/')
        res_login_bn = self.client.get('/account/login/')
        self.assertIn('কাস্টমার লগইন', res_login_bn.content.decode('utf-8'))

        # 2. Register English vs Bangla
        self.client.get('/set-language/en/')
        res_reg_en = self.client.get('/account/register/')
        self.assertIn('Create Account', res_reg_en.content.decode('utf-8'))

        self.client.get('/set-language/bn/')
        res_reg_bn = self.client.get('/account/register/')
        self.assertIn('রেজিস্টার', res_reg_bn.content.decode('utf-8'))

    def test_admin_portal_strictly_enforces_english(self):
        """
        Even if the user session/cookie has selected 'bn',
        the admin portal (/app-admin/) is ALWAYS forced to English.
        """
        # Set session to Bangla
        self.client.get('/set-language/bn/')
        self.assertEqual(self.client.session['site_language'], 'bn')

        # Login as admin and visit back-office
        self.client.force_login(self.superuser)
        res_admin = self.client.get('/app-admin/')
        self.assertEqual(res_admin.status_code, 200)

        # Middleware forces LANGUAGE_CODE to 'en'
        self.assertEqual(res_admin.wsgi_request.LANGUAGE_CODE, 'en')
        self.assertEqual(res_admin.context['CURRENT_LANGUAGE'], 'en')
        self.assertFalse(res_admin.context['IS_BANGLA'])

        content = res_admin.content.decode('utf-8')
        self.assertIn('Dashboard Overview', content)
        self.assertIn('Total Revenue', content)
        self.assertIn('Recent Orders', content)

    def test_translation_helpers_and_num_converter(self):
        """Unit tests for translation proxy and Bengali numeral converter."""
        # Numerals
        self.assertEqual(to_bn_number(500), '৫০০')
        self.assertEqual(to_bn_number('1234567890'), '১২৩৪৫৬৭৮৯০')

        # Translation proxy
        proxy_en = TranslationProxy('en')
        self.assertEqual(proxy_en.home, 'Home')
        self.assertEqual(proxy_en.add_to_cart, 'Add to Cart')
        self.assertEqual(proxy_en.products, 'Products')

        proxy_bn = TranslationProxy('bn')
        self.assertEqual(proxy_bn.home, 'হোম')
        self.assertEqual(proxy_bn.add_to_cart, 'ব্যাগে যোগ করুন')
        self.assertEqual(proxy_bn.products, 'পণ্য')

        # Fallback for unknown keys
        self.assertEqual(proxy_bn.unknown_key_123, 'unknown_key_123')

    def test_storefront_dark_and_light_theme_support(self):
        """Storefront pages provide dark and light theme infrastructure."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        # Check theme attributes and early script
        self.assertIn('data-bs-theme="light"', content)
        self.assertIn('pythonecom_theme', content)
        self.assertIn('theme-toggle-btn', content)
        self.assertIn('toggleTheme()', content)

    def test_storefront_mobile_responsive_elements(self):
        """Storefront provides full mobile responsive UI (bottom nav, drawer, viewport)."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        # Mobile viewport
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1.0">', content)
        # Mobile bottom navigation bar
        self.assertIn('mobile-bottom-nav', content)
        # Mobile left offcanvas menu drawer
        self.assertIn('id="mobileMenuOffcanvas"', content)

        # Catalog mobile filter drawer
        res_cat = self.client.get('/product/')
        self.assertEqual(res_cat.status_code, 200)
        content_cat = res_cat.content.decode('utf-8')
        self.assertIn('id="catalogFilterOffcanvas"', content_cat)

    def test_admin_portal_strictly_isolated_from_dark_theme(self):
        """Admin portal must strictly remain light-themed and isolate from customer mobile nav."""
        self.client.force_login(self.superuser)
        res_admin = self.client.get('/app-admin/')
        self.assertEqual(res_admin.status_code, 200)
        content = res_admin.content.decode('utf-8')

        # Explicitly light theme locked
        self.assertIn('data-bs-theme="light"', content)
        # No customer theme toggle or customer mobile bottom nav
        self.assertNotIn('theme-toggle-btn', content)
        self.assertNotIn('mobile-bottom-nav', content)
        self.assertNotIn('id="mobileMenuOffcanvas"', content)
        # Admin sidebar scrollbar container and scroll styling
        self.assertIn('sidebar-content', content)
        self.assertIn('overflow-y: auto;', content)


    def test_site_setting_singleton_and_helpers(self):
        """SiteSetting model provides singleton access, defaults, and multi-language helpers."""
        setting = SiteSetting.get_settings()
        self.assertIsNotNone(setting)
        self.assertEqual(setting.site_name, 'Easy Purchase')
        self.assertEqual(setting.contact_phone, '+880 1700-000000')

        # Multi-language helpers
        self.assertEqual(setting.get_announcement_text(is_bangla=False), setting.announcement_text_en)
        self.assertEqual(setting.get_announcement_text(is_bangla=True), setting.announcement_text_bn)
        self.assertEqual(setting.get_customer_care_text(is_bangla=False), setting.customer_care_text_en)
        self.assertEqual(setting.get_customer_care_text(is_bangla=True), setting.customer_care_text_bn)
        self.assertEqual(setting.get_about_text(is_bangla=False), setting.about_text_en)
        self.assertEqual(setting.get_about_text(is_bangla=True), setting.about_text_bn)

    def test_site_settings_rendered_dynamically_on_storefront(self):
        """Storefront root '/' dynamically renders branding, contacts, and notices from SiteSetting."""
        setting = SiteSetting.get_settings()
        setting.contact_phone = '+880 1999-888777'
        setting.site_name = 'MegaStore BD'
        setting.copyright_text = '© 2026 MegaStore BD Custom Copyright'
        setting.save()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        self.assertIn('+880 1999-888777', content)
        self.assertIn('MegaStore BD', content)
        self.assertIn('© 2026 MegaStore BD Custom Copyright', content)

    def test_admin_site_settings_view_and_update(self):
        """Admin with permission can view and update Store & Brand Settings."""
        self.client.force_login(self.superuser)

        # 1. GET settings page
        res = self.client.get('/app-admin/settings/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Store & Brand Settings', content)
        self.assertIn('Brand Identity', content)
        self.assertIn('Header & Announcement', content)

        # 2. POST update settings
        post_data = {
            'site_name': 'UpdatedBrandEcom',
            'site_tagline': 'Best Online Shopping in BD',
            'announcement_enabled': 'on',
            'announcement_text_en': 'Super Sale: Free Delivery on All Orders!',
            'announcement_text_bn': 'ধামাকা অফার: সব অর্ডারে ফ্রি ডেলিভারি!',
            'customer_care_text_en': '24/7 VIP Care',
            'customer_care_text_bn': '২৪/৭ ভিআইপি কেয়ার',
            'contact_phone': '+880 1888-000111',
            'contact_email': 'info@updatedbrand.com',
            'contact_address': 'Gulshan-2, Dhaka',
            'about_text_en': 'Top notch e-commerce experience.',
            'about_text_bn': 'সেরা অনলাইন শপিং অভিজ্ঞতা।',
            'social_facebook': 'https://facebook.com/updatedbrand',
            'social_twitter': 'https://twitter.com/updatedbrand',
            'social_instagram': 'https://instagram.com/updatedbrand',
            'social_github': 'https://github.com/updatedbrand',
            'social_linkedin': 'https://linkedin.com/company/updatedbrand',
            'newsletter_title_en': 'Exclusive Newsletter',
            'newsletter_title_bn': 'এক্সক্লুসিভ নিউজলেটার',
            'newsletter_text_en': 'Get daily coupons and discounts.',
            'newsletter_text_bn': 'প্রতিদিনের কুপন ও অফার পান।',
            'accepted_payments_text': 'Cash on Delivery, bKash, Nagad, Visa',
            'copyright_text': '© 2026 UpdatedBrandEcom All Rights Reserved',
            'subfooter_notice': 'Secured with Django RBAC',
        }
        # Verify tab anchor preservation on POST
        post_data['active_tab'] = 'newsletter-panel'
        res_post_redirect = self.client.post('/app-admin/settings/', post_data, follow=False)
        self.assertEqual(res_post_redirect.status_code, 302)
        self.assertEqual(res_post_redirect.url, '/app-admin/settings/#newsletter-panel')

        res_post = self.client.get('/app-admin/settings/')
        self.assertEqual(res_post.status_code, 200)
        self.assertIn('settings-nav-tabs', res_post.content.decode('utf-8'))

        # Verify DB updated
        setting = SiteSetting.get_settings()
        self.assertEqual(setting.site_name, 'UpdatedBrandEcom')
        self.assertEqual(setting.contact_phone, '+880 1888-000111')

        # Verify Storefront reflects the updated brand & phone
        res_store = self.client.get('/')
        content_store = res_store.content.decode('utf-8')
        self.assertIn('UpdatedBrandEcom', content_store)
        self.assertIn('+880 1888-000111', content_store)
        self.assertIn('Super Sale: Free Delivery on All Orders!', content_store)

    def test_admin_site_settings_rbac_permission_guards(self):
        """Staff members require explicit 'settings.site_settings' view/edit permissions."""
        # Ensure module and submodule exist
        mod, _ = Module.objects.update_or_create(code='settings', defaults={'name': 'Settings', 'order': 5})
        sub, _ = Submodule.objects.update_or_create(code='settings.site_settings', defaults={'module': mod, 'name': 'Store & Brand Settings', 'url_name': 'admin_site_settings'})
        p_view, _ = Permission.objects.update_or_create(code='settings.site_settings.view', defaults={'submodule': sub, 'action': 'view', 'name': 'View Settings'})
        p_edit, _ = Permission.objects.update_or_create(code='settings.site_settings.edit', defaults={'submodule': sub, 'action': 'edit', 'name': 'Edit Settings'})

        # Staff user without permissions
        staff_user = User.objects.create_user(username='staff_noperm', email='noperm@test.com', password='Password123', is_staff=True)
        self.client.force_login(staff_user)

        # Without 'view' permission: 403 Forbidden
        res_blocked = self.client.get('/app-admin/settings/')
        self.assertEqual(res_blocked.status_code, 403)

        # Grant 'view' permission via role
        role_viewer = Role.objects.create(name='Settings Viewer')
        RolePermission.objects.create(role=role_viewer, permission=p_view)
        UserRole.objects.create(user=staff_user, role=role_viewer)
        delattr(staff_user, '_cached_rbac_perms') if hasattr(staff_user, '_cached_rbac_perms') else None

        # Now can view
        res_view = self.client.get('/app-admin/settings/')
        self.assertEqual(res_view.status_code, 200)
        self.assertIn('Read-Only Access', res_view.content.decode('utf-8'))

        # But POST without 'edit' permission is blocked with error message
        res_post_denied = self.client.post('/app-admin/settings/', {'site_name': 'HackedName'}, follow=True)
        self.assertEqual(res_post_denied.status_code, 200)
        self.assertIn('Permission Denied', res_post_denied.content.decode('utf-8'))
        # DB must NOT change to HackedName
        self.assertNotEqual(SiteSetting.get_settings().site_name, 'HackedName')

        # Now grant 'edit' permission
        RolePermission.objects.create(role=role_viewer, permission=p_edit)
        delattr(staff_user, '_cached_rbac_perms') if hasattr(staff_user, '_cached_rbac_perms') else None

        # POST with edit permission succeeds
        res_post_allowed = self.client.post('/app-admin/settings/', {
            'site_name': 'StaffApprovedBrand',
            'announcement_text_en': 'Approved Announcement',
            'announcement_text_bn': 'অনুমোদিত ঘোষণা',
            'contact_phone': '+880 1234-567890',
            'about_text_en': 'Approved About',
            'about_text_bn': 'অনুমোদিত বিবরণ',
            'copyright_text': '© 2026 StaffApprovedBrand',
        }, follow=True)
        self.assertEqual(res_post_allowed.status_code, 200)
        self.assertEqual(SiteSetting.get_settings().site_name, 'StaffApprovedBrand')

    def test_seed_ecommerce_command_loads_fixture_and_syncs(self):
        """Calling 'python manage.py seed_ecommerce' executes cleanly and verifies all data."""
        from django.core.management import call_command
        import io
        out = io.StringIO()
        call_command('seed_ecommerce', stdout=out)
        output_str = out.getvalue()
        self.assertIn('[SUCCESS] All E-Commerce Database Data Ready!', output_str)
        self.assertTrue(SiteSetting.objects.exists())


class ProductionErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_custom_404_view_renders_404_template(self):
        """Requesting non-existent route returns HTTP 404 with custom 404.html template."""
        response = self.client.get('/this-path-does-not-exist-at-all-12345/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, '404', status_code=404)

    def test_custom_500_view_renders_cleanly(self):
        """Direct invocation of custom_server_error_view returns HTTP 500 without leaking sensitive data."""
        from django.test import RequestFactory
        from core.views import custom_server_error_view
        factory = RequestFactory()
        request = factory.get('/')
        response = custom_server_error_view(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'500', response.content)
        self.assertIn(b'Internal Server Error', response.content)

    def test_custom_403_view_renders_cleanly(self):
        """custom_permission_denied_view returns HTTP 403 with 403.html."""
        from django.test import RequestFactory
        from core.views import custom_permission_denied_view
        factory = RequestFactory()
        request = factory.get('/app-admin/settings/')
        response = custom_permission_denied_view(request)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'403', response.content)

    def test_custom_400_view_renders_cleanly(self):
        """custom_bad_request_view returns HTTP 400 with 400.html."""
        from django.test import RequestFactory
        from core.views import custom_bad_request_view
        factory = RequestFactory()
        request = factory.get('/')
        response = custom_bad_request_view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'400', response.content)

    def test_custom_error_views_bifurcate_backoffice_and_storefront(self):
        """All error handlers cleanly separate back-office layout from storefront layout."""
        from django.test import RequestFactory
        from core.views import (
            custom_bad_request_view,
            custom_permission_denied_view,
            custom_page_not_found_view,
            custom_server_error_view,
        )
        factory = RequestFactory()

        # Admin routes render back-office templates
        admin_req = factory.get('/app-admin/unknown-page/')
        res_404_admin = custom_page_not_found_view(admin_req)
        self.assertEqual(res_404_admin.status_code, 404)
        self.assertIn(b'Back-Office Page Not Found', res_404_admin.content)
        self.assertNotIn(b'Free Express Shipping', res_404_admin.content)

        res_403_admin = custom_permission_denied_view(admin_req)
        self.assertEqual(res_403_admin.status_code, 403)
        self.assertIn(b'ACCESS RESTRICTED', res_403_admin.content)
        self.assertNotIn(b'Free Express Shipping', res_403_admin.content)

        res_400_admin = custom_bad_request_view(admin_req)
        self.assertEqual(res_400_admin.status_code, 400)
        self.assertIn(b'Invalid or Malformed Request', res_400_admin.content)
        self.assertNotIn(b'Free Express Shipping', res_400_admin.content)

        res_500_admin = custom_server_error_view(admin_req)
        self.assertEqual(res_500_admin.status_code, 500)
        self.assertIn(b'Internal Server Exception', res_500_admin.content)
        self.assertNotIn(b'Free Express Shipping', res_500_admin.content)

        # Storefront routes render storefront templates
        store_req = factory.get('/some-store-page/')
        res_404_store = custom_page_not_found_view(store_req)
        self.assertEqual(res_404_store.status_code, 404)
        self.assertIn(b'Free Express Shipping', res_404_store.content)

        res_403_store = custom_permission_denied_view(store_req)
        self.assertEqual(res_403_store.status_code, 403)
        self.assertIn(b'Free Express Shipping', res_403_store.content)


class SystemExceptionLoggingAndNotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser('admin_tester', 'admin@example.com', 'AdminPass123!')
        self.customer_user = User.objects.create_user('customer_tester', 'cust@example.com', 'CustPass123!')

    def test_unhandled_exception_is_logged_to_database(self):
        """When an exception occurs during request processing, SystemErrorLog records it."""
        from django.test import RequestFactory
        from core.middleware import SystemExceptionLoggingMiddleware
        from core.models import SystemErrorLog

        factory = RequestFactory()
        request = factory.get('/test-failing-route/')
        request.user = self.customer_user

        middleware = SystemExceptionLoggingMiddleware(lambda req: None)
        test_exc = ZeroDivisionError("division by zero test")
        middleware.process_exception(request, test_exc)

        log = SystemErrorLog.objects.filter(error_type='ZeroDivisionError').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.path, '/test-failing-route/')
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.user, self.customer_user)
        self.assertFalse(log.is_resolved)

    def test_admin_system_alert_processor_flags_unresolved_errors(self):
        """Admin context processor alerts staff users when unresolved errors exist."""
        from core.models import SystemErrorLog
        from core.context_processors import admin_system_alert_processor
        from django.test import RequestFactory

        SystemErrorLog.objects.create(
            error_type='RuntimeError',
            message='Test error message',
            traceback='Traceback...',
            path='/broken-endpoint/',
            method='POST',
            is_resolved=False
        )

        factory = RequestFactory()

        # Admin user browsing
        req_admin = factory.get('/app-admin/')
        req_admin.user = self.admin_user
        ctx_admin = admin_system_alert_processor(req_admin)
        self.assertTrue(ctx_admin['has_system_errors'])
        self.assertEqual(ctx_admin['unresolved_error_count'], 1)
        self.assertIsNotNone(ctx_admin['latest_system_error'])

        # Regular customer browsing (should NOT receive admin alerts)
        req_cust = factory.get('/')
        req_cust.user = self.customer_user
        ctx_cust = admin_system_alert_processor(req_cust)
        self.assertFalse(ctx_cust['has_system_errors'])
        self.assertEqual(ctx_cust['unresolved_error_count'], 0)

    def test_admin_can_view_and_resolve_errors(self):
        """Staff member can view system errors and mark them resolved."""
        from core.models import SystemErrorLog
        err = SystemErrorLog.objects.create(
            error_type='ValueError',
            message='Invalid literal',
            traceback='Traceback...',
            path='/product/detail/',
            is_resolved=False
        )

        self.client.force_login(self.admin_user)
        resp = self.client.get('/app-admin/system-errors/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'ValueError')
        self.assertContains(resp, '/product/detail/')

        # Resolve error
        resolve_resp = self.client.get(f'/app-admin/system-errors/{err.id}/resolve/')
        self.assertEqual(resolve_resp.status_code, 302)

        err.refresh_from_db()
        self.assertTrue(err.is_resolved)
        self.assertEqual(err.resolved_by, self.admin_user)
    def test_unpermitted_staff_gets_backoffice_403_on_system_errors(self):
        """Staff member without system errors permission receives back-office 403 page."""
        staff_user = User.objects.create_user('limited_staff', 'staff@test.com', 'StaffPass123!', is_staff=True)
        self.client.force_login(staff_user)
        resp = self.client.get('/app-admin/system-errors/')
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'admin_panel/403.html')
        content = resp.content.decode('utf-8')
        self.assertIn('ACCESS RESTRICTED', content)
        self.assertIn('Back to Dashboard', content)
        # Verify customer storefront components are NOT rendered
        self.assertNotIn('Free Express Shipping', content)
        self.assertNotIn('Search products, brands, or categories...', content)

    def test_staff_with_system_errors_perm_can_access(self):
        """Staff user with settings.system_errors.view role permission can access error logs."""
        from rbac.models import Module, Submodule, Permission, Role, UserRole
        staff_user = User.objects.create_user('dev_staff', 'dev@test.com', 'DevPass123!', is_staff=True)
        mod, _ = Module.objects.get_or_create(code='settings', defaults={'name': 'Settings'})
        sub, _ = Submodule.objects.get_or_create(code='settings.system_errors', defaults={'module': mod, 'name': 'System Error Logs'})
        perm, _ = Permission.objects.get_or_create(submodule=sub, action='view', code='settings.system_errors.view', defaults={'name': 'View System Errors'})
        role = Role.objects.create(name='Dev Role')
        role.permissions.add(perm)
        UserRole.objects.create(user=staff_user, role=role)

        self.client.force_login(staff_user)
        resp = self.client.get('/app-admin/system-errors/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/settings/system_errors.html')


    def test_staff_with_site_settings_fallback_perm_can_access(self):
        """Staff user with settings.site_settings.view backward compatibility can access error logs."""
        from rbac.models import Module, Submodule, Permission, Role, UserRole
        staff_user = User.objects.create_user('admin_staff', 'admin2@test.com', 'AdminPass123!', is_staff=True)
        mod, _ = Module.objects.get_or_create(code='settings', defaults={'name': 'Settings'})
        sub, _ = Submodule.objects.get_or_create(code='settings.site_settings', defaults={'module': mod, 'name': 'Store & Brand Settings'})
        perm, _ = Permission.objects.get_or_create(submodule=sub, action='view', code='settings.site_settings.view', defaults={'name': 'View Site Settings'})
        role = Role.objects.create(name='Store Settings Manager')
        role.permissions.add(perm)
        UserRole.objects.create(user=staff_user, role=role)

        self.client.force_login(staff_user)
        resp = self.client.get('/app-admin/system-errors/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'admin_panel/settings/system_errors.html')


class SecurityAuditFootprintAndHeadersTests(TestCase):
    """
    Verification of security headers, CSRF failure handling, production error
    views, and security audit footprint logging across all HTTP error handlers.
    """

    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='audit_tester', password='Password123!')

    def test_security_headers_and_settings(self):
        """Verify strict referrer policy, opener policy, upload limit, and CSRF failure view setting."""
        from django.conf import settings
        self.assertEqual(settings.SECURE_REFERRER_POLICY, 'strict-origin-when-cross-origin')
        self.assertEqual(settings.SECURE_CROSS_ORIGIN_OPENER_POLICY, 'same-origin-allow-popups')
        self.assertEqual(settings.DATA_UPLOAD_MAX_NUMBER_FIELDS, 1000)
        self.assertEqual(settings.CSRF_FAILURE_VIEW, 'core.views.custom_csrf_failure_view')

        # Live HTTP request check via SecurityMiddleware
        response = self.client.get('/')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
        self.assertEqual(response.headers.get('Cross-Origin-Opener-Policy'), 'same-origin-allow-popups')

    def test_custom_bad_request_view_audit_logging(self):
        """400 view logs footprint to django.security.SuspiciousOperation with IP, path, method, user, and reason."""
        from core.views import custom_bad_request_view

        req = self.factory.get('/product/malformed-query/?foo=bar', HTTP_X_FORWARDED_FOR='192.168.1.50')
        req.user = self.user

        with self.assertLogs('django.security.SuspiciousOperation', level='WARNING') as cm:
            resp = custom_bad_request_view(req, exception=Exception("Invalid request parameter encoding"))

        self.assertEqual(resp.status_code, 400)
        log_output = " ".join(cm.output)
        self.assertIn('192.168.1.50', log_output)
        self.assertIn('/product/malformed-query/', log_output)
        self.assertIn('GET', log_output)
        self.assertIn('audit_tester', log_output)
        self.assertIn('Invalid request parameter encoding', log_output)

        # Admin route check
        req_admin = self.factory.get('/app-admin/invalid-route/')
        req_admin.user = self.user
        resp_admin = custom_bad_request_view(req_admin, exception=Exception("Bad Admin Token"))
        self.assertEqual(resp_admin.status_code, 400)
        self.assertIn(b'400', resp_admin.content)

    def test_custom_permission_denied_view_audit_logging(self):
        """403 view logs footprint to django.security.PermissionDenied with IP, path, method, user, and exception."""
        from core.views import custom_permission_denied_view

        req = self.factory.post('/orders/sensitive-export/', HTTP_X_FORWARDED_FOR='10.0.0.99')
        req.user = self.user

        with self.assertLogs('django.security.PermissionDenied', level='WARNING') as cm:
            resp = custom_permission_denied_view(req, exception=Exception("IDOR attempt: unauthorized order ID access"))

        self.assertEqual(resp.status_code, 403)
        log_output = " ".join(cm.output)
        self.assertIn('10.0.0.99', log_output)
        self.assertIn('/orders/sensitive-export/', log_output)
        self.assertIn('POST', log_output)
        self.assertIn('audit_tester', log_output)
        self.assertIn('IDOR attempt: unauthorized order ID access', log_output)

        # Admin route check
        req_admin = self.factory.get('/app-admin/secret-settings/')
        req_admin.user = self.user
        resp_admin = custom_permission_denied_view(req_admin, exception=Exception("Staff role required"))
        self.assertEqual(resp_admin.status_code, 403)
        self.assertIn(b'ACCESS RESTRICTED', resp_admin.content)

    def test_custom_csrf_failure_view_audit_logging_and_branding(self):
        """Dedicated CSRF failure view logs footprint and renders user-friendly 403 error page."""
        from core.views import custom_csrf_failure_view

        req = self.factory.post(
            '/account/login/',
            HTTP_X_FORWARDED_FOR='203.0.113.195',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        )
        req.user = self.user

        with self.assertLogs('django.security.csrf', level='WARNING') as cm:
            resp = custom_csrf_failure_view(req, reason="CSRF cookie not set.")

        self.assertEqual(resp.status_code, 403)
        log_output = " ".join(cm.output)
        self.assertIn('203.0.113.195', log_output)
        self.assertIn('/account/login/', log_output)
        self.assertIn('POST', log_output)
        self.assertIn('Mozilla/5.0', log_output)
        self.assertIn('CSRF cookie not set.', log_output)

        # Confirm user-friendly message rendered in page content
        content = resp.content.decode('utf-8')
        self.assertIn('Session security token expired. Please refresh the page and try again.', content)

        # Admin route check
        req_admin = self.factory.post('/app-admin/login/', HTTP_USER_AGENT='TestAgent')
        req_admin.user = self.user
        resp_admin = custom_csrf_failure_view(req_admin, reason="CSRF token missing.")
        self.assertEqual(resp_admin.status_code, 403)
        content_admin = resp_admin.content.decode('utf-8')
        self.assertIn('Session security token expired. Please refresh the page and try again.', content_admin)

    def test_custom_page_not_found_scanner_probe_detection(self):
        """Scanner probe paths log security footprint to django.security.ScannerProbe with IP and path."""
        from core.views import custom_page_not_found_view

        probe_paths = [
            '/.env',
            '/.git/config',
            '/wp-login.php',
            '/phpmyadmin/index.php',
            '/shell.php',
            '/etc/passwd',
            '/static/../../etc/passwd',
            '/cgi-bin/vulnerable.cgi',
        ]

        for probe in probe_paths:
            req = self.factory.get(probe, HTTP_X_FORWARDED_FOR='198.51.100.42')
            with self.assertLogs('django.security.ScannerProbe', level='WARNING') as cm:
                resp = custom_page_not_found_view(req)
            self.assertEqual(resp.status_code, 404)
            log_output = " ".join(cm.output)
            self.assertIn('198.51.100.42', log_output)
            self.assertIn('Scanner probe footprint detected', log_output)

        # Legitimate 404 path should NOT trigger scanner probe logging
        req_legit = self.factory.get('/nonexistent-catalog-item-12345/', HTTP_X_FORWARDED_FOR='198.51.100.42')
        # Custom logging check to ensure ScannerProbe is NOT called
        import logging
        probe_logger = logging.getLogger('django.security.ScannerProbe')
        captured = []
        handler = logging.Handler()
        handler.emit = lambda record: captured.append(record.getMessage())
        probe_logger.addHandler(handler)
        try:
            resp_legit = custom_page_not_found_view(req_legit)
            self.assertEqual(resp_legit.status_code, 404)
            self.assertEqual(len(captured), 0, f"Expected no probe logs for legit path, got {captured}")
        finally:
            probe_logger.removeHandler(handler)

    def test_custom_server_error_graceful_fallback_when_db_unreachable(self):
        """500 handler logs to django.request and recovers gracefully when database is completely down."""
        from unittest.mock import patch
        from django.db import OperationalError
        from core.views import custom_server_error_view

        req = self.factory.get('/checkout/process/', HTTP_X_FORWARDED_FOR='172.16.0.5')

        # Simulate total database outage for both SystemErrorLog and SiteSetting
        with patch('core.models.SystemErrorLog.log_exception', side_effect=OperationalError("MySQL server has gone away")):
            with patch('core.models.SiteSetting.get_settings', side_effect=OperationalError("Can't connect to MySQL server")):
                with self.assertLogs('django.request', level='ERROR') as cm:
                    # Provide an active exception via sys.exc_info() simulation
                    import sys
                    try:
                        raise ValueError("Checkout calculation error")
                    except ValueError:
                        resp = custom_server_error_view(req)

                self.assertEqual(resp.status_code, 500)
                log_output = " ".join(cm.output)
                self.assertIn('Graceful fallback: DB unreachable when recording SystemErrorLog', log_output)
                self.assertIn('MySQL server has gone away', log_output)
                # Confirm 500 HTML still rendered cleanly
                content = resp.content.decode('utf-8')
                self.assertIn('500', content)
                self.assertIn('Internal Server Error', content)

    def test_add_bundle_to_cart_clamps_oversized_product_ids_to_15(self):
        """
        Verify that cart/views.py:add_bundle_to_cart properly clamps oversized
        product ID lists to a maximum of 15 items without error (DoS mitigation).
        """
        import json
        bundle_cat = Category.objects.create(name='DoS Bundle Cat', slug='dos-bundle-cat')
        prods = [
            Product.objects.create(
                name=f"Bulk Protection Item {i}",
                slug=f"bulk-protection-item-{i}",
                category=bundle_cat,
                price=Decimal("25.00"),
                stock=10,
                is_active=True,
            )
            for i in range(25)
        ]
        oversized_ids = [p.pk for p in prods]  # 25 IDs submitted

        # 1. Test POST with array parameter product_ids[] via AJAX
        res_ajax = self.client.post(
            '/cart/add-bundle/',
            {'product_ids[]': oversized_ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_ajax.status_code, 200)
        data_ajax = res_ajax.json()
        self.assertTrue(data_ajax['success'])
        self.assertEqual(data_ajax['added_count'], 15)
        self.assertEqual(data_ajax['total_items'], 15)

        # 2. Test JSON body payload with oversized list
        res_json = self.client.post(
            '/cart/add-bundle/',
            json.dumps({'product_ids': oversized_ids}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_json.status_code, 200)
        data_json = res_json.json()
        self.assertTrue(data_json['success'])
        # Confirms no crash and strictly clamped to 15 items
        self.assertLessEqual(data_json['added_count'], 15)


class ThemeEngineTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='theme_admin',
            email='theme_admin@example.com',
            password='AdminPassword123'
        )
        self.regular_user = User.objects.create_user(
            username='regular_customer',
            email='customer@example.com',
            password='CustomerPassword123'
        )

    def test_theme_registry_completeness(self):
        """All 6 theme definitions exist and have required tokens and 4 trust pillars."""
        from core.themes import THEMES, THEME_CHOICES
        expected_keys = [
            'mega_market',
            'tech_gadgets',
            'beauty_cosmetics',
            'fashion_lifestyle',
            'grocery_organic',
            'pharmacy_health'
        ]
        self.assertEqual(len(THEMES), 6)
        self.assertEqual(len(THEME_CHOICES), 6)

        for key in expected_keys:
            self.assertIn(key, THEMES)
            theme = THEMES[key]
            # Required keys
            for token in [
                'name', 'subtitle', 'benchmark', 'primary', 'primary_hover',
                'primary_light', 'accent', 'text_on_primary',
                'hero_gradient_start', 'hero_gradient_end', 'dark_primary', 'dark_accent',
                'badge_radius', 'button_radius', 'card_radius',
                'hero_headline_en', 'hero_headline_bn', 'hero_tagline_en', 'hero_tagline_bn',
                'hero_badge_en', 'hero_badge_bn', 'trust_pillars'
            ]:
                self.assertIn(token, theme, f"Missing token '{token}' in theme '{key}'")

            # Must have exactly 4 trust pillars with icons and bilingual descriptions
            self.assertEqual(len(theme['trust_pillars']), 4, f"Theme '{key}' must have exactly 4 trust pillars")
            for pillar in theme['trust_pillars']:
                self.assertIn('icon', pillar)
                self.assertIn('title_en', pillar)
                self.assertIn('title_bn', pillar)
                self.assertIn('desc_en', pillar)
                self.assertIn('desc_bn', pillar)

    def test_get_theme_and_fallback(self):
        """get_theme returns requested theme and safely falls back to mega_market for unknown keys."""
        from core.themes import get_theme
        tech = get_theme('tech_gadgets')
        self.assertEqual(tech['key'], 'tech_gadgets')
        self.assertEqual(tech['name'], 'Tech & Gadgets')

        fallback = get_theme('non_existent_key')
        self.assertEqual(fallback['key'], 'mega_market')

    def test_get_theme_data_bilingual_resolution(self):
        """get_theme_data resolves language-aware headline, tagline, and trust pillars."""
        from core.themes import get_theme_data
        en_data = get_theme_data('grocery_organic', is_bangla=False)
        self.assertIn('Farm-Fresh', en_data['hero_headline'])
        self.assertEqual(en_data['trust_pillars'][0]['title'], en_data['trust_pillars'][0]['title_en'])

        bn_data = get_theme_data('grocery_organic', is_bangla=True)
        self.assertIn('খাঁটি অর্গানিক', bn_data['hero_headline'])
        self.assertEqual(bn_data['trust_pillars'][0]['title'], bn_data['trust_pillars'][0]['title_bn'])

    def test_site_setting_active_theme_persistence(self):
        """SiteSetting model default is mega_market, and updates persist properly."""
        setting = SiteSetting.get_settings()
        self.assertEqual(setting.active_theme, 'mega_market')

        setting.active_theme = 'pharmacy_health'
        setting.save()

        refetched = SiteSetting.get_settings()
        self.assertEqual(refetched.active_theme, 'pharmacy_health')
        theme_data = refetched.get_theme_data()
        self.assertEqual(theme_data['key'], 'pharmacy_health')
        self.assertEqual(theme_data['benchmark'], 'Arogga Style')

    def test_site_settings_context_processor(self):
        """Context processor injects CURRENT_THEME_KEY, CURRENT_THEME_DATA, and THEME_CHOICES."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'fashion_lifestyle'
        setting.save()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['CURRENT_THEME_KEY'], 'fashion_lifestyle')
        self.assertEqual(res.context['CURRENT_THEME_DATA']['name'], 'Fashion & Lifestyle')
        self.assertEqual(len(res.context['THEME_CHOICES']), 6)

    def test_admin_switch_theme_via_quick_button(self):
        """Admin can activate theme via quick_switch_theme button on settings page."""
        self.client.login(username='theme_admin', password='AdminPassword123')
        res = self.client.post('/app-admin/settings/', {
            'quick_switch_theme': 'beauty_cosmetics'
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        setting = SiteSetting.get_settings()
        self.assertEqual(setting.active_theme, 'beauty_cosmetics')

    def test_admin_switch_theme_via_form_dropdown(self):
        """Admin can save theme via standard SiteSettingForm submission."""
        self.client.login(username='theme_admin', password='AdminPassword123')
        setting = SiteSetting.get_settings()
        res = self.client.post('/app-admin/settings/', {
            'active_theme': 'tech_gadgets',
            'site_name': setting.site_name,
            'site_tagline': setting.site_tagline,
            'announcement_enabled': 'on',
            'announcement_text_en': setting.announcement_text_en,
            'announcement_text_bn': setting.announcement_text_bn,
            'contact_phone': setting.contact_phone,
            'contact_email': setting.contact_email,
            'contact_address': setting.contact_address,
            'about_text_en': setting.about_text_en,
            'about_text_bn': setting.about_text_bn,
            'copyright_text': setting.copyright_text,
            'subfooter_notice': setting.subfooter_notice,
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, 'tech_gadgets')

    def test_non_staff_cannot_change_theme(self):
        """Unauthenticated or customer users cannot change theme."""
        res = self.client.post('/app-admin/settings/', {
            'quick_switch_theme': 'grocery_organic'
        })
        self.assertEqual(res.status_code, 302)
        setting = SiteSetting.get_settings()
        self.assertNotEqual(setting.active_theme, 'grocery_organic')


class ThemeTemplatesFrontEndTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            name='Test Smartphone Flagship',
            category=self.category,
            price=Decimal('79999.00'),
            stock=15,
            is_featured=True,
            is_active=True
        )

    def test_dynamic_root_css_tokens_injected(self):
        """base.html must inject dynamic :root CSS variables matching CURRENT_THEME_DATA."""
        setting = SiteSetting.get_settings()
        from core.themes import THEMES
        for theme_key, theme in THEMES.items():
            setting.active_theme = theme_key
            setting.save()

            res = self.client.get('/')
            self.assertEqual(res.status_code, 200)
            content = res.content.decode('utf-8')

            # Verify dynamic tokens
            self.assertIn(f"--primary-color: {theme['primary']};", content)
            self.assertIn(f"--card-border-radius: {theme['card_radius']};", content)
            self.assertIn(f"--btn-border-radius: {theme['button_radius']};", content)
            self.assertIn(f"--badge-border-radius: {theme['badge_radius']};", content)

    def test_announcement_bar_and_branding_accents(self):
        """Header announcement bar and accents dynamically reflect the active theme."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'tech_gadgets'
        setting.save()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Tech &amp; Gadgets', content)

    def test_home_page_trust_pillars_rendered(self):
        """home/index.html displays the active theme's 4 custom trust pillars."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'grocery_organic'
        setting.save()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        # Check grocery trust highlights
        self.assertIn('100% Organic &amp; Chemical-Free', content)
        self.assertIn('1-Hour Express Delivery', content)
        self.assertIn('Fresh Daily Harvest', content)

    def test_product_detail_multiple_image_view_and_trust_box(self):
        """Product detail template provides multiple image view, zoom lens, lightbox modal, and dynamic trust pillars."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'beauty_cosmetics'
        setting.save()

        res = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        # Interactive gallery and lightbox elements
        self.assertIn('id="zoomContainer"', content)
        self.assertIn('id="circleLens"', content)
        self.assertIn('id="galleryThumbs"', content)
        self.assertIn('class="gallery-thumbnails-strip', content)
        self.assertIn('id="productLightboxModal"', content)
        self.assertIn('id="lightboxImg"', content)
        self.assertIn('openLightboxModal', content)
        self.assertIn('switchProductImage', content)

        # Dynamic delivery & trust box pillars for beauty_cosmetics
        self.assertIn('100% Authentic Import', content)
        self.assertIn('Dermatologically Tested', content)
        self.assertIn('Cruelty-Free &amp; Safe', content)


class ThemeVerifierAssuranceTests(TestCase):
    """End-to-end verification tests for Theme Engine registry, token resolution, and context processor."""
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('verifier_admin', 'vadmin@example.com', 'Pass12345!')

    def test_all_six_themes_token_resolution_and_context(self):
        from core.themes import THEMES
        setting = SiteSetting.get_settings()
        for key in THEMES.keys():
            setting.active_theme = key
            setting.save()
            res = self.client.get('/')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.context['CURRENT_THEME_KEY'], key)
            self.assertEqual(res.context['CURRENT_THEME_DATA']['key'], key)
            self.assertIn('--primary-color', res.content.decode('utf-8'))





