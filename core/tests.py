from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from product.models import Product, Category
from core.translations import get_translation, to_bn_number, TranslationProxy


class BilingualStorefrontTests(TestCase):
    def setUp(self):
        self.client = Client()
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

    def test_invalid_language_falls_back_to_english(self):
        """Invalid language codes fall back safely to English."""
        res = self.client.get('/set-language/invalid_code/')
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.client.session['site_language'], 'en')

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
