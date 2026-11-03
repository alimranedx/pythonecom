from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from product.models import Product, Category, Brand

User = get_user_model()


class ProductCatalogPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics', icon='bi-laptop')
        self.brand = Brand.objects.create(name='TechCorp', slug='techcorp')

        # Create 25 products for pagination testing
        self.products = []
        for i in range(25):
            p = Product.objects.create(
                name=f'Product Item {i:02d}',
                slug=f'product-item-{i:02d}',
                sku=f'SKU-TEST-{i:02d}',
                category=self.category,
                brand=self.brand,
                price=Decimal(f'{100 + i * 10}.00'),
                stock=20,
                unit='1 pc',
                is_active=True
            )
            self.products.append(p)

    def test_default_pagination_12_items_per_page(self):
        res = self.client.get('/product/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['products']), 12)
        self.assertEqual(res.context['paginator'].count, 25)
        self.assertEqual(res.context['paginator'].num_pages, 3)
        html = res.content.decode('utf-8')
        self.assertIn('Page <strong>1</strong> of <strong>3</strong>', html)
        self.assertIn('page=2', html)

    def test_custom_per_page_limit(self):
        # per_page = 9 should produce 3 pages (25 / 9 = 3 pages: 9, 9, 7)
        res = self.client.get('/product/?per_page=9')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['products']), 9)
        self.assertEqual(res.context['paginator'].num_pages, 3)

    def test_page_2_navigation_and_links(self):
        res = self.client.get('/product/?page=2&per_page=12')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['page_obj'].number, 2)
        html = res.content.decode('utf-8')
        self.assertIn('page=1', html)
        self.assertIn('page=3', html)

    def test_filter_preservation_in_pagination(self):
        # Filter by category and sort with pagination
        res = self.client.get('/product/?category=electronics&sort=price_desc&per_page=12')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        self.assertIn('category=electronics', html)
        self.assertIn('sort=price_desc', html)
        self.assertIn('per_page=12', html)

    def test_invalid_page_number_fallback(self):
        # get_page handles page numbers > total pages gracefully by returning last page
        res = self.client.get('/product/?page=999')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['page_obj'].number, 3)


class ProductCategoryNavigationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat_laptops = Category.objects.create(name='Laptops & Computers', slug='laptops', icon='bi-laptop', is_featured=True, order=1)
        self.cat_phones = Category.objects.create(name='Smartphones & Mobiles', slug='smartphones', icon='bi-phone', is_featured=True, order=2)
        self.cat_watches = Category.objects.create(name="Men's Luxury Watches", slug='mens-watches', icon='bi-smartwatch', is_featured=False, order=3)
        self.brand = Brand.objects.create(name='Apple', slug='apple')

        self.laptop_prod = Product.objects.create(
            name='MacBook Air M2',
            slug='macbook-air-m2',
            category=self.cat_laptops,
            brand=self.brand,
            price=Decimal('999.00'),
            stock=10,
            is_active=True
        )

    def test_dynamic_navigation_context_processor(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('nav_categories', res.context)
        self.assertIn('all_categories', res.context)
        nav_slugs = [c.slug for c in res.context['nav_categories']]
        self.assertIn('laptops', nav_slugs)
        self.assertIn('smartphones', nav_slugs)
        html = res.content.decode('utf-8')
        self.assertIn('Laptops &amp; Computers', html)

    def test_category_query_filter_exact_slug(self):
        res = self.client.get('/product/?category=laptops')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['selected_category'], self.cat_laptops)
        self.assertEqual(len(res.context['products']), 1)

    def test_category_query_filter_alias_resolution(self):
        # 'electronics-laptops' should resolve via alias to 'laptops'
        res = self.client.get('/product/?category=electronics-laptops')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['selected_category'], self.cat_laptops)
        self.assertEqual(len(res.context['products']), 1)

    def test_category_url_path_alias_resolution(self):
        # /product/category/electronics-laptops/ should resolve to 'laptops'
        res = self.client.get('/product/category/electronics-laptops/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['selected_category'], self.cat_laptops)

    def test_invalid_category_query_param_graceful_handling(self):
        # A nonexistent category query param should not throw 404
        res = self.client.get('/product/?category=nonexistent_xyz')
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.context['selected_category'])

    def test_invalid_category_path_returns_404(self):
        # A nonexistent category direct path should return 404
        res = self.client.get('/product/category/completely-fake-category/')
        self.assertEqual(res.status_code, 404)
