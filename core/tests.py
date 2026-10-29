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

        proxy_bn = TranslationProxy('bn')
        self.assertEqual(proxy_bn.home, 'হোম')
        self.assertEqual(proxy_bn.add_to_cart, 'ব্যাগে যোগ করুন')

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


    def test_site_setting_singleton_and_helpers(self):
        """SiteSetting model provides singleton access, defaults, and multi-language helpers."""
        setting = SiteSetting.get_settings()
        self.assertIsNotNone(setting)
        self.assertEqual(setting.site_name, 'PythonEcom')
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
        res_post = self.client.post('/app-admin/settings/', post_data, follow=True)
        self.assertEqual(res_post.status_code, 200)

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
