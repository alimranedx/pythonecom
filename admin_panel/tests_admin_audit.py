from decimal import Decimal
import html
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from core.models import SiteSetting, SystemErrorLog
from core.themes import theme_registry, THEMES
from product.models import Category, Brand, Product, ProductImage, ProductReview
from orders.models import Order, OrderItem, DeliverySlot, Coupon
from accounts.models import CustomerProfile, Address
from rbac.models import Module, Submodule, Permission, Role, UserRole, RolePermission
from rbac.services import RBACService


class AdminThemeSystemAuditTests(TestCase):
    """
    Comprehensive tests for Back-Office Theme Management:
    - Theme Manager (/app-admin/themes/)
    - Theme Customizer (/app-admin/themes/<id>/customize/)
    - Theme Activation (/app-admin/themes/<id>/activate/)
    - Theme Preview & Exit (/app-admin/themes/<id>/preview/, /app-admin/themes/preview/exit/)
    - Theme Reset (/app-admin/themes/<id>/reset/)
    """
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='theme_superadmin',
            email='themesuper@test.com',
            password='AdminPassword123'
        )
        self.client.force_login(self.superuser)

        self.setting = SiteSetting.get_settings()
        self.setting.active_theme = 'marketplace'
        self.setting.save()

    def test_theme_manager_view(self):
        url = reverse('admin_theme_manager')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        content = html.unescape(res.content.decode('utf-8'))

        self.assertIn('Storefront Theme Engine', content)
        self.assertIn('LIVE ACTIVE', content)
        # Verify all registered themes appear in cards
        for theme in theme_registry.get_all():
            self.assertIn(theme.name, content)
            self.assertIn(theme.benchmark, content)

    def test_theme_preview_and_exit_preview(self):
        # 1. Preview organic-grocery
        preview_url = reverse('admin_theme_preview', kwargs={'theme_id': 'organic-grocery'})
        res = self.client.get(preview_url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, '/')
        self.assertEqual(self.client.session.get('admin_preview_theme'), 'organic-grocery')

        # 2. Verify Theme Manager shows preview banner
        mgr_res = self.client.get(reverse('admin_theme_manager'))
        self.assertEqual(mgr_res.status_code, 200)
        self.assertIn('Staff Isolated Preview Mode Active', mgr_res.content.decode('utf-8'))
        self.assertIn('organic-grocery', mgr_res.content.decode('utf-8'))

        # 3. Exit preview
        exit_url = reverse('admin_theme_exit_preview')
        exit_res = self.client.get(exit_url)
        self.assertEqual(exit_res.status_code, 302)
        self.assertNotIn('admin_preview_theme', self.client.session)

    def test_theme_activate_post(self):
        activate_url = reverse('admin_theme_activate', kwargs={'theme_id': 'tech-electronics'})
        res = self.client.post(activate_url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.setting.refresh_from_db()
        self.assertEqual(self.setting.active_theme, 'tech-electronics')
        self.assertIn("Theme &#x27;Tech &amp; Gadgets&#x27; has been successfully activated", res.content.decode('utf-8'))

    def test_theme_activate_invalid_id(self):
        activate_url = reverse('admin_theme_activate', kwargs={'theme_id': 'non_existent_theme'})
        res = self.client.post(activate_url, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("is not recognized", res.content.decode('utf-8'))

    def test_theme_customize_get_all_themes(self):
        """
        Verify GET request to theme customizer works for every theme without template error.
        """
        for theme in theme_registry.get_all():
            url = reverse('admin_theme_customize', kwargs={'theme_id': theme.id})
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, f"Theme customize failed for '{theme.id}'")
            content = res.content.decode('utf-8')
            self.assertIn('Customize Theme:', content)
            self.assertIn('Design Tokens', content)
            self.assertIn('Custom CSS Stylesheet', content)

    def test_theme_customize_post_and_reset(self):
        theme_id = 'organic-grocery'
        customize_url = reverse('admin_theme_customize', kwargs={'theme_id': theme_id})

        # POST customization settings
        post_data = {
            'custom_css': '/* Custom Grocery Style */\n.grocery-hero { border: 2px solid green; }',
            'show_delivery_ribbon': 'on',
            'pantry_grid_columns': '4',
        }
        res = self.client.post(customize_url, post_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("saved successfully", res.content.decode('utf-8'))

        # Verify DB persisted
        from core.models import ThemeCustomization
        cust = ThemeCustomization.objects.get(theme_id=theme_id)
        self.assertIn('.grocery-hero', cust.custom_css)

        # POST Reset customization
        reset_url = reverse('admin_theme_reset_customization', kwargs={'theme_id': theme_id})
        res_reset = self.client.post(reset_url, follow=True)
        self.assertEqual(res_reset.status_code, 200)
        self.assertIn("have been reset to schema defaults", res_reset.content.decode('utf-8'))

        cust.refresh_from_db()
        self.assertEqual(cust.custom_css, '')


class AdminStoreSettingsAuditTests(TestCase):
    """
    Comprehensive tests for Store & Brand Settings (/app-admin/settings/)
    """
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='settings_superadmin',
            email='settings@test.com',
            password='AdminPassword123'
        )
        self.client.force_login(self.superuser)
        self.setting = SiteSetting.get_settings()

    def test_settings_get(self):
        url = reverse('admin_site_settings')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        content = html.unescape(res.content.decode('utf-8'))
        self.assertIn('Store & Brand Settings', content)
        self.assertIn('Brand Identity', content)
        self.assertIn('Header & Announcement', content)
        self.assertIn('Footer & Social Links', content)
        self.assertIn('Theme & Industry Niches', content)
        self.assertIn('Newsletter & Notices', content)

    def test_settings_post_update(self):
        url = reverse('admin_site_settings')
        post_data = {
            'active_tab': 'brand-panel',
            'site_name': 'Fresh Mart Superstore',
            'site_tagline': 'Fast, Clean & Trustworthy',
            'active_theme': 'organic-grocery',
            'announcement_enabled': 'on',
            'announcement_text_en': 'Winter mega sale live now!',
            'announcement_text_bn': 'শীতকালীন মেগা অফার চলছে!',
            'customer_care_text_en': '24/7 Hotline',
            'customer_care_text_bn': '২৪/৭ গ্রাহক সেবা',
            'contact_phone': '+8801700000000',
            'contact_email': 'support@freshmart.test',
            'contact_address': 'House 12, Road 4, Dhanmondi, Dhaka',
            'about_text_en': 'Your trusted online shopping companion.',
            'about_text_bn': 'আপনার বিশ্বস্ত অনলাইন শপিং সহযোগী।',
            'accepted_payments_text': 'bKash, Nagad, Visa, Mastercard, COD',
            'copyright_text': '© 2026 Fresh Mart Superstore. All Rights Reserved.',
            'subfooter_notice': '100% Encrypted & Safe Payments',
        }
        res = self.client.post(url, post_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Store &amp; Brand Settings updated successfully!", res.content.decode('utf-8'))

        self.setting.refresh_from_db()
        self.assertEqual(self.setting.site_name, 'Fresh Mart Superstore')
        self.assertEqual(self.setting.contact_phone, '+8801700000000')
        self.assertEqual(self.setting.active_theme, 'organic-grocery')

    def test_settings_quick_switch_theme(self):
        url = reverse('admin_site_settings')
        post_data = {
            'quick_switch_theme': 'beauty-skincare',
            'active_tab': 'theme-panel',
        }
        res = self.client.post(url, post_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Storefront theme successfully switched to", res.content.decode('utf-8'))

        self.setting.refresh_from_db()
        self.assertEqual(self.setting.active_theme, 'beauty-skincare')


class AdminSystemErrorsAuditTests(TestCase):
    """
    Comprehensive tests for System Error Monitoring (/app-admin/system-errors/)
    """
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='errors_superadmin',
            email='errors@test.com',
            password='AdminPassword123'
        )
        self.client.force_login(self.superuser)

        # Clear existing logs and create deterministic test fixtures
        SystemErrorLog.objects.all().delete()
        self.err1 = SystemErrorLog.objects.create(
            error_type='ZeroDivisionError',
            message='division by zero in math calculation',
            path='/test/calc/',
            method='GET',
            is_resolved=False
        )
        self.err2 = SystemErrorLog.objects.create(
            error_type='ValueError',
            message='invalid literal for int() with base 10: abc',
            path='/test/parse/',
            method='POST',
            is_resolved=False
        )
        self.err3 = SystemErrorLog.objects.create(
            error_type='KeyError',
            message='missing key in payload',
            path='/test/api/',
            method='POST',
            is_resolved=True,
            resolved_by=self.superuser,
            resolved_at=timezone.now()
        )

    def test_system_errors_list_view(self):
        url = reverse('admin_system_errors')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        self.assertIn('System Exception & Error Monitoring', content)
        self.assertIn('ZeroDivisionError', content)
        self.assertIn('ValueError', content)
        self.assertIn('Unresolved (2)', content)

    def test_system_errors_filters_and_search(self):
        url = reverse('admin_system_errors')

        # Filter resolved
        res_resolved = self.client.get(f"{url}?status=resolved")
        self.assertEqual(res_resolved.status_code, 200)
        self.assertIn('KeyError', res_resolved.content.decode('utf-8'))
        self.assertNotIn('ZeroDivisionError', res_resolved.content.decode('utf-8'))

        # Search query
        res_search = self.client.get(f"{url}?status=all&q=ZeroDivisionError")
        self.assertEqual(res_search.status_code, 200)
        self.assertIn('ZeroDivisionError', res_search.content.decode('utf-8'))
        self.assertNotIn('KeyError', res_search.content.decode('utf-8'))

    def test_resolve_single_error(self):
        resolve_url = reverse('admin_resolve_error', kwargs={'pk': self.err1.pk})
        res = self.client.get(resolve_url, follow=True)
        self.assertEqual(res.status_code, 200)

        self.err1.refresh_from_db()
        self.assertTrue(self.err1.is_resolved)
        self.assertEqual(self.err1.resolved_by, self.superuser)

    def test_resolve_all_errors(self):
        resolve_all_url = reverse('admin_resolve_all_errors')
        res = self.client.post(resolve_all_url, follow=True)
        self.assertEqual(res.status_code, 200)

        unresolved_count = SystemErrorLog.objects.filter(is_resolved=False).count()
        self.assertEqual(unresolved_count, 0)

    def test_clear_resolved_errors(self):
        clear_url = reverse('admin_clear_resolved_errors')
        res = self.client.post(clear_url, follow=True)
        self.assertEqual(res.status_code, 200)

        resolved_count = SystemErrorLog.objects.filter(is_resolved=True).count()
        self.assertEqual(resolved_count, 0)


class AdminSidebarAndRBACAuditTests(TestCase):
    """
    Tests ensuring every submodule link generated in the sidebar works cleanly
    and permissions are strictly enforced.
    """
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='rbac_superadmin',
            email='rbacsuper@test.com',
            password='AdminPassword123'
        )

        self.staff_user = User.objects.create_user(
            username='catalog_staff',
            email='catalogstaff@test.com',
            password='Password123!',
            is_staff=True
        )

        # Grant catalog.products (view) to catalog_staff via Role
        catalog_role = Role.objects.create(name='Catalog Staff', description='Manages products')
        sub = Submodule.objects.get(code='catalog.products')
        perm = Permission.objects.get(code='catalog.products.view')
        RolePermission.objects.create(role=catalog_role, permission=perm)
        UserRole.objects.create(user=self.staff_user, role=catalog_role)

    def test_all_sidebar_submodule_links_render_and_return_200_for_superadmin(self):
        self.client.force_login(self.superuser)

        # Retrieve dynamic menu tree
        menu_tree = RBACService.get_user_allowed_menu(self.superuser)
        self.assertTrue(len(menu_tree) > 0)

        checked_urls = []
        for item in menu_tree:
            for sub in item['submodules']:
                self.assertNotEqual(sub.menu_url, '#', f"Submodule {sub.code} ({sub.url_name}) should not resolve to '#'")
                res = self.client.get(sub.menu_url)
                self.assertEqual(res.status_code, 200, f"Sidebar link {sub.menu_url} returned status {res.status_code}")
                checked_urls.append(sub.menu_url)

        # Ensure all core submodules are present
        expected_urls = [
            reverse('admin_product_list'),
            reverse('admin_category_list'),
            reverse('admin_brand_list'),
            reverse('admin_review_list'),
            reverse('admin_order_list'),
            reverse('admin_customer_list'),
            reverse('admin_staff_list'),
            reverse('admin_role_list'),
            reverse('admin_site_settings'),
            reverse('admin_theme_manager'),
            reverse('admin_system_errors'),
        ]
        for url in expected_urls:
            self.assertIn(url, checked_urls)

    def test_restricted_staff_cannot_access_unauthorized_routes(self):
        self.client.force_login(self.staff_user)

        # Staff can view product list
        res_prod = self.client.get(reverse('admin_product_list'))
        self.assertEqual(res_prod.status_code, 200)

        # Staff CANNOT view settings (raises PermissionDenied -> 403)
        res_settings = self.client.get(reverse('admin_site_settings'))
        self.assertIn(res_settings.status_code, [302, 403])

        # Staff CANNOT view RBAC staff management (redirected to dashboard -> 302)
        res_staff = self.client.get(reverse('admin_staff_list'))
        self.assertIn(res_staff.status_code, [302, 403])

        # Staff CANNOT view RBAC roles management (redirected to dashboard -> 302)
        res_roles = self.client.get(reverse('admin_role_list'))
        self.assertIn(res_roles.status_code, [302, 403])

        # Dynamic menu for catalog staff only contains permitted submodules
        menu_tree = RBACService.get_user_allowed_menu(self.staff_user)
        module_codes = [m['module'].code for m in menu_tree]
        self.assertEqual(module_codes, ['catalog'])
        sub_codes = [sub.code for m in menu_tree for sub in m['submodules']]
        self.assertEqual(sub_codes, ['catalog.products'])


class AdminCatalogOrdersCustomersCrudAuditTests(TestCase):
    """
    Verifies full CRUD and toggle actions for Products, Categories, Brands,
    Reviews, Orders, Coupons, Delivery Slots, and Customers.
    """
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='crud_superadmin',
            email='crud@test.com',
            password='AdminPassword123'
        )
        self.client.force_login(self.superuser)

        self.category = Category.objects.create(name='Pantry', slug='pantry')
        self.brand = Brand.objects.create(name='Khaas Food', slug='khaas-food')
        self.product = Product.objects.create(
            name='Mustard Oil 1L',
            slug='mustard-oil-1l',
            category=self.category,
            brand=self.brand,
            description='Authentic wood-milled mustard oil.',
            price=Decimal('350.00'),
            stock=25,
            is_active=True
        )

    def test_category_crud(self):
        # Create
        res = self.client.post(reverse('admin_category_create'), {
            'name': 'Fresh Produce',
            'slug': 'fresh-produce',
            'order': 0,
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        new_cat = Category.objects.get(slug='fresh-produce')

        # Edit
        edit_res = self.client.post(reverse('admin_category_edit', kwargs={'pk': new_cat.pk}), {
            'name': 'Fresh Produce Updated',
            'slug': 'fresh-produce',
            'order': 1,
        }, follow=True)
        self.assertEqual(edit_res.status_code, 200)
        new_cat.refresh_from_db()
        self.assertEqual(new_cat.name, 'Fresh Produce Updated')
        self.assertEqual(new_cat.order, 1)

        # Delete
        del_res = self.client.post(reverse('admin_category_delete', kwargs={'pk': new_cat.pk}), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(Category.objects.filter(slug='fresh-produce').exists())

    def test_brand_crud(self):
        # Create
        res = self.client.post(reverse('admin_brand_create'), {
            'name': 'PRAN Organic',
            'slug': 'pran-organic',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        brand = Brand.objects.get(slug='pran-organic')

        # Edit
        edit_res = self.client.post(reverse('admin_brand_edit', kwargs={'pk': brand.pk}), {
            'name': 'PRAN Organic Natural',
            'slug': 'pran-organic',
        }, follow=True)
        self.assertEqual(edit_res.status_code, 200)
        brand.refresh_from_db()
        self.assertEqual(brand.name, 'PRAN Organic Natural')

        # Delete
        del_res = self.client.post(reverse('admin_brand_delete', kwargs={'pk': brand.pk}), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(Brand.objects.filter(slug='pran-organic').exists())

    def test_product_crud(self):
        # Create
        res = self.client.post(reverse('admin_product_create'), {
            'name': 'Sundarbans Honey 500g',
            'slug': 'sundarbans-honey-500g',
            'category': self.category.pk,
            'brand': self.brand.pk,
            'description': '100% pure raw honey harvested from the Sundarbans mangrove forest.',
            'price': '450.00',
            'stock': 15,
            'unit': '500 gm',
            'is_active': 'on'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        prod = Product.objects.get(slug='sundarbans-honey-500g')

        # Edit
        edit_res = self.client.post(reverse('admin_product_edit', kwargs={'pk': prod.pk}), {
            'name': 'Sundarbans Raw Honey 500g',
            'slug': 'sundarbans-honey-500g',
            'category': self.category.pk,
            'brand': self.brand.pk,
            'description': 'Updated 100% pure raw honey from Sundarbans.',
            'price': '480.00',
            'stock': 12,
            'unit': '500 gm',
            'is_active': 'on'
        }, follow=True)
        self.assertEqual(edit_res.status_code, 200)
        prod.refresh_from_db()
        self.assertEqual(prod.name, 'Sundarbans Raw Honey 500g')
        self.assertEqual(prod.price, Decimal('480.00'))

        # Delete
        del_res = self.client.post(reverse('admin_product_delete', kwargs={'pk': prod.pk}), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(Product.objects.filter(slug='sundarbans-honey-500g').exists())

    def test_review_moderation(self):
        customer = User.objects.create_user(username='reviewer', email='reviewer@test.com', password='Password123!')
        review = ProductReview.objects.create(
            product=self.product,
            user=customer,
            rating=5,
            comment='Pure scent and taste! Highly recommended.'
        )

        list_res = self.client.get(reverse('admin_review_list'))
        self.assertEqual(list_res.status_code, 200)
        self.assertIn('Pure scent and taste!', list_res.content.decode('utf-8'))

        del_res = self.client.post(reverse('admin_review_delete', kwargs={'pk': review.pk}), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())

    def test_delivery_slots_management(self):
        slot = DeliverySlot.objects.create(
            title='Morning Express',
            start_time='08:00:00',
            end_time='11:00:00',
            order=1,
            is_active=True
        )

        list_res = self.client.get(reverse('admin_delivery_slots_list'))
        self.assertEqual(list_res.status_code, 200)
        self.assertIn('Morning Express', list_res.content.decode('utf-8'))

        # Toggle slot
        toggle_res = self.client.get(reverse('admin_delivery_slot_toggle', kwargs={'pk': slot.pk}), follow=True)
        self.assertEqual(toggle_res.status_code, 200)
        slot.refresh_from_db()
        self.assertFalse(slot.is_active)

    def test_coupons_management(self):
        # Create coupon
        res = self.client.post(reverse('admin_coupon_create'), {
            'code': 'GROCERY10',
            'discount_type': 'percent',
            'discount_value': '10',
            'min_order_amount': '500',
            'valid_days': '15',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        coupon = Coupon.objects.get(code='GROCERY10')

        # Toggle coupon
        toggle_res = self.client.get(reverse('admin_coupon_toggle', kwargs={'pk': coupon.pk}), follow=True)
        self.assertEqual(toggle_res.status_code, 200)
        coupon.refresh_from_db()
        self.assertFalse(coupon.is_active)

        # Delete coupon
        del_res = self.client.get(reverse('admin_coupon_delete', kwargs={'pk': coupon.pk}), follow=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertFalse(Coupon.objects.filter(code='GROCERY10').exists())

    def test_orders_detail_and_invoice(self):
        order = Order.objects.create(
            order_number='ORD-TEST-999',
            full_name='Test Buyer',
            email='buyer@test.com',
            phone='+8801811111111',
            total_amount=Decimal('700.00'),
            status='pending',
            payment_status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            product_price=Decimal('350.00'),
            quantity=2
        )

        # Order list
        res_list = self.client.get(reverse('admin_order_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertIn('ORD-TEST-999', res_list.content.decode('utf-8'))

        # Order detail
        res_detail = self.client.get(reverse('admin_order_detail', kwargs={'pk': order.pk}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn('ORD-TEST-999', res_detail.content.decode('utf-8'))

        # Order invoice
        res_invoice = self.client.get(reverse('admin_order_invoice', kwargs={'pk': order.pk}))
        self.assertEqual(res_invoice.status_code, 200)
        self.assertIn('ORD-TEST-999', res_invoice.content.decode('utf-8'))

    def test_customer_detail_and_toggle_status(self):
        customer = User.objects.create_user(
            username='regular_customer',
            email='customer@test.com',
            password='Password123!',
            is_staff=False,
            is_active=True
        )

        # Customer list
        res_list = self.client.get(reverse('admin_customer_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertIn('regular_customer', res_list.content.decode('utf-8'))

        # Customer detail
        res_detail = self.client.get(reverse('admin_customer_detail', kwargs={'pk': customer.pk}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn('regular_customer', res_detail.content.decode('utf-8'))

        # Toggle customer status
        toggle_res = self.client.post(reverse('admin_customer_toggle_status', kwargs={'pk': customer.pk}), follow=True)
        self.assertEqual(toggle_res.status_code, 200)
        customer.refresh_from_db()
        self.assertFalse(customer.is_active)
