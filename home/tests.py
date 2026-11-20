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

        # Create Categories with explicit theme assignments
        self.cat_mega = Category.objects.create(name='General Electronics', slug='general-electronics', theme='mega_market', is_featured=True, order=1)
        self.cat_laptops = Category.objects.create(name='Laptops', slug='laptops', theme='tech_gadgets', is_featured=True, order=10)
        self.cat_phones = Category.objects.create(name='Smartphones', slug='smartphones', theme='tech_gadgets', is_featured=True, order=11)
        self.cat_beauty = Category.objects.create(name='Skin Care', slug='skin-care', theme='beauty_cosmetics', is_featured=True, order=20)
        self.cat_fashion = Category.objects.create(name="Men's Panjabi", slug='mens-panjabi', theme='fashion_lifestyle', is_featured=True, order=30)
        self.cat_grocery = Category.objects.create(name='Rice & Grains', slug='rice-grains', theme='grocery_organic', is_featured=True, order=40)
        self.cat_pharmacy = Category.objects.create(name='Prescriptions', slug='prescriptions', theme='pharmacy_health', is_featured=True, order=50)

        # Create Brands with explicit theme assignments
        self.brand_mega = Brand.objects.create(name='Mega Brand', slug='mega-brand', theme='mega_market')
        self.brand_apple = Brand.objects.create(name='Apple', slug='apple', theme='tech_gadgets')
        self.brand_samsung = Brand.objects.create(name='Samsung', slug='samsung', theme='tech_gadgets')
        self.brand_loreal = Brand.objects.create(name="L'Oreal", slug='loreal', theme='beauty_cosmetics')
        self.brand_aarong = Brand.objects.create(name='Aarong', slug='aarong', theme='fashion_lifestyle')
        self.brand_khaas = Brand.objects.create(name='Khaas Food', slug='khaas-food', theme='grocery_organic')
        self.brand_square = Brand.objects.create(name='Square Pharma', slug='square-pharma', theme='pharmacy_health')

        # Create Products
        self.mega_p1 = Product.objects.create(
            name='Mega Multi Blender', slug='mega-blender', category=self.cat_mega, brand=self.brand_mega, theme='mega_market',
            price=Decimal('3500'), discount_price=Decimal('3000'), stock=20, is_active=True, is_featured=True, is_flash_sale=True
        )

        # Create Tech Products
        self.tech_p1 = Product.objects.create(
            name='MacBook Pro M3', slug='macbook-pro-m3', category=self.cat_laptops, brand=self.brand_apple, theme='tech_gadgets',
            price=Decimal('250000'), discount_price=Decimal('230000'), stock=10, is_active=True, is_featured=True, is_flash_sale=True
        )
        self.tech_p2 = Product.objects.create(
            name='Galaxy S24 Ultra', slug='galaxy-s24-ultra', category=self.cat_phones, brand=self.brand_samsung, theme='tech_gadgets',
            price=Decimal('150000'), discount_price=Decimal('140000'), stock=10, is_active=True, is_featured=True, is_flash_sale=False
        )

        # Create Beauty Products
        self.beauty_p1 = Product.objects.create(
            name='Hyaluronic Acid Serum', slug='hyaluronic-acid', category=self.cat_beauty, brand=self.brand_loreal, theme='beauty_cosmetics',
            price=Decimal('1500'), discount_price=Decimal('1200'), stock=15, is_active=True, is_featured=True, is_flash_sale=True
        )

        # Create Fashion Products
        self.fashion_p1 = Product.objects.create(
            name='Silk Panjabi Festive', slug='silk-panjabi', category=self.cat_fashion, brand=self.brand_aarong, theme='fashion_lifestyle',
            price=Decimal('5500'), stock=8, is_active=True, is_featured=True, is_flash_sale=False
        )

        # Create Grocery Products
        self.grocery_p1 = Product.objects.create(
            name='Kalijeera Rice 5kg', slug='kalijeera-rice', category=self.cat_grocery, brand=self.brand_khaas, theme='grocery_organic',
            price=Decimal('650'), discount_price=Decimal('600'), stock=25, is_active=True, is_featured=False, is_flash_sale=True
        )

        # Create Pharmacy Products
        self.pharma_p1 = Product.objects.create(
            name='Napa Extra Box', slug='napa-extra', category=self.cat_pharmacy, brand=self.brand_square, theme='pharmacy_health',
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

    def test_strict_theme_isolation_no_out_of_niche_leakage(self):
        """When a theme is active, only items strictly belonging to that theme appear (ZERO out-of-niche leakage)."""
        # Pharmacy only has pharma_p1, cat_pharmacy, brand_square
        res = self.client.get('/?theme=pharmacy_health')
        self.assertEqual(res.status_code, 200)

        featured_prods = res.context['featured_products']
        self.assertEqual(len(featured_prods), 1)
        self.assertEqual(featured_prods[0], self.pharma_p1)
        self.assertEqual(featured_prods[0].theme, 'pharmacy_health')

        slider_items = res.context['slider_items']
        self.assertEqual(len(slider_items), 1)
        self.assertEqual(slider_items[0]['product'], self.pharma_p1)

        # Categories: strictly pharmacy_health
        featured_cats = res.context['featured_categories']
        self.assertEqual(len(featured_cats), 1)
        self.assertEqual(featured_cats[0].slug, 'prescriptions')
        self.assertEqual(featured_cats[0].theme, 'pharmacy_health')

        # Brands: strictly pharmacy_health
        brands = res.context['brands']
        self.assertEqual(len(brands), 1)
        self.assertEqual(brands[0].slug, 'square-pharma')
        self.assertEqual(brands[0].theme, 'pharmacy_health')

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

    def test_all_6_themes_strict_isolation_100_percent(self):
        """Verifies that across all 6 themes, 100% of visible categories, brands, and products strictly match that theme."""
        themes = ['mega_market', 'tech_gadgets', 'beauty_cosmetics', 'fashion_lifestyle', 'grocery_organic', 'pharmacy_health']

        for theme in themes:
            allowed_themes = {'mega_market', 'all'} if theme == 'mega_market' else {theme}

            # 1. Test Home Index
            res_home = self.client.get(f'/?theme={theme}')
            self.assertEqual(res_home.status_code, 200)

            # Check featured categories
            for cat in res_home.context['featured_categories']:
                self.assertIn(cat.theme, allowed_themes, f"Out of niche category {cat.name} ({cat.theme}) appeared in {theme}")

            # Check brands
            for brand in res_home.context['brands']:
                self.assertIn(brand.theme, allowed_themes, f"Out of niche brand {brand.name} ({brand.theme}) appeared in {theme}")

            # Check slider products
            for item in res_home.context['slider_items']:
                prod = item['product']
                self.assertIn(prod.theme, allowed_themes, f"Out of niche slider product {prod.name} ({prod.theme}) appeared in {theme}")

            # Check flash sales
            for prod in res_home.context['flash_sales']:
                self.assertIn(prod.theme, allowed_themes, f"Out of niche flash sale product {prod.name} ({prod.theme}) appeared in {theme}")

            # Check featured products
            for prod in res_home.context['featured_products']:
                self.assertIn(prod.theme, allowed_themes, f"Out of niche featured product {prod.name} ({prod.theme}) appeared in {theme}")

            # Check latest products
            for prod in res_home.context['latest_products']:
                self.assertIn(prod.theme, allowed_themes, f"Out of niche latest product {prod.name} ({prod.theme}) appeared in {theme}")

            # Check navigation categories context processor
            for cat in res_home.context['nav_categories']:
                self.assertIn(cat.theme, allowed_themes, f"Out of niche nav category {cat.name} ({cat.theme}) appeared in {theme}")
            for cat in res_home.context['all_categories']:
                self.assertIn(cat.theme, allowed_themes, f"Out of niche all_category {cat.name} ({cat.theme}) appeared in {theme}")

            # 2. Test Product Catalog Listing
            res_catalog = self.client.get(f'/product/?theme={theme}')
            self.assertEqual(res_catalog.status_code, 200)

            for prod in res_catalog.context['products']:
                self.assertIn(prod.theme, allowed_themes, f"Out of niche catalog product {prod.name} ({prod.theme}) appeared in {theme}")

            for cat in res_catalog.context['categories']:
                self.assertIn(cat.theme, allowed_themes, f"Out of niche catalog category {cat.name} ({cat.theme}) appeared in {theme}")

            for brand in res_catalog.context['brands']:
                self.assertIn(brand.theme, allowed_themes, f"Out of niche catalog brand {brand.name} ({brand.theme}) appeared in {theme}")
