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
