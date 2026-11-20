from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from core.models import SiteSetting
from core.themes import THEMES, DEFAULT_THEME_KEY
from product.models import Category, Brand, Product


class StorefrontThemeFilteringTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.setting = SiteSetting.get_settings()

        # Create Categories
        self.cat_laptops = Category.objects.create(name='Laptops', slug='laptops', is_featured=True, order=10)
        self.cat_phones = Category.objects.create(name='Smartphones', slug='smartphones', is_featured=True, order=11)
        self.cat_beauty = Category.objects.create(name='Skin Care', slug='skin-care', is_featured=True, order=20)
        self.cat_fashion = Category.objects.create(name="Men's Panjabi", slug='mens-panjabi', is_featured=True, order=30)
        self.cat_grocery = Category.objects.create(name='Rice & Grains', slug='rice-grains', is_featured=True, order=40)
        self.cat_pharmacy = Category.objects.create(name='Prescriptions', slug='prescriptions', is_featured=True, order=50)

        # Create Brands
        self.brand_apple = Brand.objects.create(name='Apple', slug='apple')
        self.brand_samsung = Brand.objects.create(name='Samsung', slug='samsung')
        self.brand_loreal = Brand.objects.create(name="L'Oreal", slug='loreal')
        self.brand_aarong = Brand.objects.create(name='Aarong', slug='aarong')
        self.brand_khaas = Brand.objects.create(name='Khaas Food', slug='khaas-food')
        self.brand_square = Brand.objects.create(name='Square Pharma', slug='square-pharma')

        # Create Tech Products
        self.tech_p1 = Product.objects.create(
            name='MacBook Pro M3', slug='macbook-pro-m3', category=self.cat_laptops, brand=self.brand_apple,
            price=Decimal('250000'), discount_price=Decimal('230000'), stock=10, is_active=True, is_featured=True, is_flash_sale=True
        )
        self.tech_p2 = Product.objects.create(
            name='Galaxy S24 Ultra', slug='galaxy-s24-ultra', category=self.cat_phones, brand=self.brand_samsung,
            price=Decimal('150000'), discount_price=Decimal('140000'), stock=10, is_active=True, is_featured=True, is_flash_sale=False
        )

        # Create Beauty Products
        self.beauty_p1 = Product.objects.create(
            name='Hyaluronic Acid Serum', slug='hyaluronic-acid', category=self.cat_beauty, brand=self.brand_loreal,
            price=Decimal('1500'), discount_price=Decimal('1200'), stock=15, is_active=True, is_featured=True, is_flash_sale=True
        )

        # Create Fashion Products
        self.fashion_p1 = Product.objects.create(
            name='Silk Panjabi Festive', slug='silk-panjabi', category=self.cat_fashion, brand=self.brand_aarong,
            price=Decimal('5500'), stock=8, is_active=True, is_featured=True, is_flash_sale=False
        )

        # Create Grocery Products
        self.grocery_p1 = Product.objects.create(
            name='Kalijeera Rice 5kg', slug='kalijeera-rice', category=self.cat_grocery, brand=self.brand_khaas,
            price=Decimal('650'), discount_price=Decimal('600'), stock=25, is_active=True, is_featured=False, is_flash_sale=True
        )

        # Create Pharmacy Products
        self.pharma_p1 = Product.objects.create(
            name='Napa Extra Box', slug='napa-extra', category=self.cat_pharmacy, brand=self.brand_square,
            price=Decimal('480'), stock=100, is_active=True, is_featured=True, is_flash_sale=False
        )

    def test_theme_dictionaries_slug_definitions(self):
        """core/themes.py defines category_slugs and brand_slugs for all 6 themes."""
        self.assertIsNone(THEMES['mega_market']['category_slugs'])
        self.assertIsNone(THEMES['mega_market']['brand_slugs'])

        self.assertIn('laptops', THEMES['tech_gadgets']['category_slugs'])
        self.assertIn('apple', THEMES['tech_gadgets']['brand_slugs'])

        self.assertIn('skin-care', THEMES['beauty_cosmetics']['category_slugs'])
        self.assertIn('loreal', THEMES['beauty_cosmetics']['brand_slugs'])

        self.assertIn('mens-panjabi', THEMES['fashion_lifestyle']['category_slugs'])
        self.assertIn('aarong', THEMES['fashion_lifestyle']['brand_slugs'])

        self.assertIn('rice-grains', THEMES['grocery_organic']['category_slugs'])
        self.assertIn('khaas-food', THEMES['grocery_organic']['brand_slugs'])

        self.assertIn('prescriptions', THEMES['pharmacy_health']['category_slugs'])
        self.assertIn('square-pharma', THEMES['pharmacy_health']['brand_slugs'])

    def test_context_processor_preview_theme_via_query_param(self):
        """core/context_processors.py allows ?theme=<key> preview parameter."""
        # Default active theme in DB is mega_market
        res_default = self.client.get('/')
        self.assertEqual(res_default.status_code, 200)
        self.assertEqual(res_default.context['CURRENT_THEME_KEY'], 'mega_market')

        # Preview tech_gadgets
        res_tech = self.client.get('/?theme=tech_gadgets')
        self.assertEqual(res_tech.status_code, 200)
        self.assertEqual(res_tech.context['CURRENT_THEME_KEY'], 'tech_gadgets')
        self.assertEqual(res_tech.context['CURRENT_THEME_DATA']['key'], 'tech_gadgets')

        # Preview beauty_cosmetics
        res_beauty = self.client.get('/?theme=beauty_cosmetics')
        self.assertEqual(res_beauty.status_code, 200)
        self.assertEqual(res_beauty.context['CURRENT_THEME_KEY'], 'beauty_cosmetics')
        self.assertEqual(res_beauty.context['CURRENT_THEME_DATA']['key'], 'beauty_cosmetics')

        # Invalid preview param falls back to site settings
        res_invalid = self.client.get('/?theme=nonexistent_theme_xyz')
        self.assertEqual(res_invalid.status_code, 200)
        self.assertEqual(res_invalid.context['CURRENT_THEME_KEY'], 'mega_market')

    def test_preview_theme_param_overrides_db_active_theme(self):
        """Query param ?theme=<key> takes precedence over DB setting for testing/admin."""
        self.setting.active_theme = 'tech_gadgets'
        self.setting.save()

        # Without param: tech_gadgets
        res1 = self.client.get('/')
        self.assertEqual(res1.context['CURRENT_THEME_KEY'], 'tech_gadgets')

        # With param: overrides to beauty_cosmetics
        res2 = self.client.get('/?theme=beauty_cosmetics')
        self.assertEqual(res2.context['CURRENT_THEME_KEY'], 'beauty_cosmetics')
        self.assertEqual(res2.context['featured_categories'][0].slug, 'skin-care')

    def test_theme_filtering_and_prioritization_tech_gadgets(self):
        """When tech_gadgets is active, tech categories, brands, and products are prioritized."""
        res = self.client.get('/?theme=tech_gadgets')
        self.assertEqual(res.status_code, 200)

        # Categories: Laptops & Smartphones prioritized first
        cat_slugs = [c.slug for c in res.context['featured_categories']]
        self.assertIn('laptops', cat_slugs[:2])
        self.assertIn('smartphones', cat_slugs[:2])

        # Brands: Apple and Samsung prioritized first
        brand_slugs = [b.slug for b in res.context['brands']]
        self.assertIn('apple', brand_slugs[:2])
        self.assertIn('samsung', brand_slugs[:2])

        # Slider items prioritize tech products
        slider_prods = [item['product'] for item in res.context['slider_items']]
        self.assertTrue(len(slider_prods) > 0)
        self.assertIn(self.tech_p1, slider_prods)

        # Featured products prioritize tech products first
        featured_prods = res.context['featured_products']
        self.assertIn(featured_prods[0].category.slug, ['laptops', 'smartphones'])
        self.assertIn(featured_prods[1].category.slug, ['laptops', 'smartphones'])

    def test_theme_filtering_and_prioritization_beauty(self):
        """When beauty_cosmetics is active, beauty categories and brands are prioritized."""
        res = self.client.get('/?theme=beauty_cosmetics')
        self.assertEqual(res.status_code, 200)

        # Skin care first
        cat_slugs = [c.slug for c in res.context['featured_categories']]
        self.assertEqual(cat_slugs[0], 'skin-care')

        # Brand L'Oreal first
        brand_slugs = [b.slug for b in res.context['brands']]
        self.assertEqual(brand_slugs[0], 'loreal')

        # Flash sale prioritizes beauty product first
        flash_sales = res.context['flash_sales']
        self.assertEqual(flash_sales[0], self.beauty_p1)

    def test_theme_filtering_and_prioritization_grocery(self):
        """When grocery_organic is active, grocery categories and brands are prioritized."""
        res = self.client.get('/?theme=grocery_organic')
        self.assertEqual(res.status_code, 200)

        cat_slugs = [c.slug for c in res.context['featured_categories']]
        self.assertEqual(cat_slugs[0], 'rice-grains')

        brand_slugs = [b.slug for b in res.context['brands']]
        self.assertEqual(brand_slugs[0], 'khaas-food')

        flash_sales = res.context['flash_sales']
        self.assertEqual(flash_sales[0], self.grocery_p1)

    def test_theme_filtering_and_prioritization_pharmacy(self):
        """When pharmacy_health is active, pharmacy categories, brands, and products are prioritized."""
        res = self.client.get('/?theme=pharmacy_health')
        self.assertEqual(res.status_code, 200)

        cat_slugs = [c.slug for c in res.context['featured_categories']]
        self.assertEqual(cat_slugs[0], 'prescriptions')

        brand_slugs = [b.slug for b in res.context['brands']]
        self.assertEqual(brand_slugs[0], 'square-pharma')

        featured_prods = res.context['featured_products']
        self.assertEqual(featured_prods[0], self.pharma_p1)

    def test_graceful_fallback_when_theme_items_are_fewer_than_slice_limit(self):
        """When a theme has fewer products than slice limits, other active products fill sections."""
        # Pharmacy only has 1 product (pharma_p1)
        res = self.client.get('/?theme=pharmacy_health')
        self.assertEqual(res.status_code, 200)

        featured_prods = res.context['featured_products']
        # Pharma product is at index 0
        self.assertEqual(featured_prods[0], self.pharma_p1)
        # But section is NOT sparse: other active products fill the list
        self.assertGreater(len(featured_prods), 1)

        slider_items = res.context['slider_items']
        self.assertGreater(len(slider_items), 1)

        # Categories: prescriptions is first, but total categories include others
        featured_cats = res.context['featured_categories']
        self.assertEqual(featured_cats[0].slug, 'prescriptions')
        self.assertGreater(len(featured_cats), 1)

        # Brands: square-pharma is first, but total brands include others
        brands = res.context['brands']
        self.assertEqual(brands[0].slug, 'square-pharma')
        self.assertGreater(len(brands), 1)

    def test_db_setting_switch_active_theme(self):
        """When SiteSetting.active_theme is updated in DB, storefront reflects it without query param."""
        self.setting.active_theme = 'fashion_lifestyle'
        self.setting.save()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['CURRENT_THEME_KEY'], 'fashion_lifestyle')

        cat_slugs = [c.slug for c in res.context['featured_categories']]
        self.assertEqual(cat_slugs[0], 'mens-panjabi')

        brand_slugs = [b.slug for b in res.context['brands']]
        self.assertEqual(brand_slugs[0], 'aarong')

    def test_mega_market_all_categories_and_brands(self):
        """mega_market has None category_slugs and brand_slugs, allowing all items without filtering."""
        res = self.client.get('/?theme=mega_market')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['CURRENT_THEME_KEY'], 'mega_market')
        self.assertTrue(len(res.context['featured_categories']) > 0)
        self.assertTrue(len(res.context['brands']) > 0)
        self.assertTrue(len(res.context['slider_items']) > 0)
