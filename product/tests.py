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


class ProductHTMLSanitizationTests(TestCase):
    def test_render_safe_html_with_standard_tags(self):
        from product.templatetags.product_tags import render_safe_html
        raw_html = (
            '<h5>Product Overview</h5>'
            '<p class="lead">Premium quality <strong>smartwatch</strong> with <em>heart monitor</em>.</p>'
            '<ul><li>Battery: 48h</li><li>Water resistant: 50m</li></ul>'
            '<table class="table"><thead><tr><th>Feature</th><th>Value</th></tr></thead>'
            '<tbody><tr><td>Weight</td><td>45g</td></tr></tbody></table>'
        )
        rendered = render_safe_html(raw_html)
        self.assertIn('<h5>Product Overview</h5>', rendered)
        self.assertIn('<strong>smartwatch</strong>', rendered)
        self.assertIn('<em>heart monitor</em>', rendered)
        self.assertIn('<ul><li>Battery: 48h</li>', rendered)
        self.assertIn('<table class="table">', rendered)
        self.assertIn('<td>Weight</td>', rendered)

    def test_render_safe_html_strips_dangerous_scripts(self):
        from product.templatetags.product_tags import render_safe_html
        malicious = '<p>Normal text</p><script>alert("XSS Attack!");</script><b>Bold Text</b>'
        rendered = render_safe_html(malicious)
        self.assertNotIn('<script>', rendered)
        self.assertNotIn('alert("XSS Attack!");', rendered)
        self.assertIn('<p>Normal text</p>', rendered)
        self.assertIn('<b>Bold Text</b>', rendered)

    def test_render_safe_html_strips_inline_event_handlers(self):
        from product.templatetags.product_tags import render_safe_html
        malicious = (
            '<img src="valid.png" onerror="alert(1)" onload="evil()">'
            '<div onclick="doBadThings()" onmouseover="stealCookies()">Container</div>'
        )
        rendered = render_safe_html(malicious)
        self.assertNotIn('onerror', rendered)
        self.assertNotIn('onload', rendered)
        self.assertNotIn('onclick', rendered)
        self.assertNotIn('onmouseover', rendered)
        self.assertNotIn('alert(1)', rendered)
        self.assertNotIn('evil()', rendered)

    def test_render_safe_html_strips_javascript_urls(self):
        from product.templatetags.product_tags import render_safe_html
        malicious = '<a href="javascript:alert(document.cookie)">Click here</a>'
        rendered = render_safe_html(malicious)
        self.assertNotIn('javascript:', rendered)
        self.assertNotIn('alert(', rendered)

    def test_render_safe_html_strips_iframes_and_objects(self):
        from product.templatetags.product_tags import render_safe_html
        malicious = '<iframe src="https://evil.com"></iframe><object data="bad.swf"></object><embed src="bad.swf">'
        rendered = render_safe_html(malicious)
        self.assertNotIn('<iframe', rendered)
        self.assertNotIn('<object', rendered)
        self.assertNotIn('<embed', rendered)

    def test_render_safe_html_plain_text_with_newlines(self):
        from product.templatetags.product_tags import render_safe_html
        plain = "High quality 100% cotton.\nBreathable and durable.\n\nMachine wash cold."
        rendered = render_safe_html(plain)
        # Plain text should convert newlines to <p> and <br />
        self.assertTrue('<p>' in rendered or '<br>' in rendered or '<br />' in rendered)
        self.assertIn('High quality 100% cotton.', rendered)
        self.assertIn('Machine wash cold.', rendered)

    def test_render_safe_html_entity_encoded_tags(self):
        from product.templatetags.product_tags import render_safe_html
        encoded = (
            "&lt;p&gt;The Powder Canister is a finely milled setting powder.&lt;/p&gt;\n"
            "&lt;h5&gt;Product Features &amp; Specifications:&lt;/h5&gt;\n"
            "&lt;ul&gt;\n"
            "&lt;li&gt;&lt;strong&gt;Brand:&lt;/strong&gt; L'Oreal&lt;/li&gt;\n"
            "&lt;/ul&gt;"
        )
        rendered = render_safe_html(encoded)
        self.assertNotIn('&lt;p&gt;', rendered)
        self.assertNotIn('&lt;h5&gt;', rendered)
        self.assertIn('<p>The Powder Canister', rendered)
        self.assertIn('<h5>Product Features', rendered)
        self.assertIn('<li><strong>Brand:</strong>', rendered)

    def test_render_safe_html_entity_encoded_with_malicious_script(self):
        from product.templatetags.product_tags import render_safe_html
        encoded_xss = "&lt;p&gt;Safe text&lt;/p&gt;&lt;script&gt;alert('xss')&lt;/script&gt;"
        rendered = render_safe_html(encoded_xss)
        self.assertNotIn('<script', rendered)
        self.assertNotIn("alert('xss')", rendered)
        self.assertIn('<p>Safe text</p>', rendered)

    def test_clean_plain_summary_strips_tags_before_truncating(self):
        from product.templatetags.product_tags import clean_plain_summary
        rich_content = (
            '<p><h5><strong>Headline</strong></h5> This is a detailed description of a fantastic gadget '
            'with cutting-edge capabilities and premium build quality.</p>'
        )
        summary = clean_plain_summary(rich_content, num_words=6)
        self.assertNotIn('<p>', summary)
        self.assertNotIn('<h5>', summary)
        self.assertNotIn('<strong>', summary)
        self.assertTrue(summary.startswith('Headline This is a detailed description'))
        self.assertTrue(summary.endswith('...'))

    def test_clean_plain_summary_empty_handling(self):
        from product.templatetags.product_tags import clean_plain_summary
        self.assertEqual(clean_plain_summary(''), '')
        self.assertEqual(clean_plain_summary(None), '')


class ProductReviewSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Gadgets', slug='gadgets')
        self.product = Product.objects.create(
            name='Smartphone Pro',
            slug='smartphone-pro',
            category=self.category,
            price=Decimal('799.00'),
            stock=15,
            is_active=True
        )
        self.user = User.objects.create_user(username='customer1', password='Password123!')

    def test_unauthenticated_user_cannot_submit_review(self):
        from django.urls import reverse
        url = reverse('product_add_review', kwargs={'pk': self.product.pk})
        res = self.client.post(url, {
            'rating': '5',
            'comment': 'Amazing product!'
        })
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('account_login'), res.url)
        from product.models import ProductReview
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_authenticated_user_submits_valid_review(self):
        from django.urls import reverse
        self.client.login(username='customer1', password='Password123!')
        url = reverse('product_add_review', kwargs={'pk': self.product.pk})
        res = self.client.post(url, {
            'rating': '4',
            'comment': 'Great quality and fast delivery.'
        })
        self.assertEqual(res.status_code, 302)
        from product.models import ProductReview
        review = ProductReview.objects.filter(product=self.product, user=self.user).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Great quality and fast delivery.')

    def test_rating_boundary_enforcement(self):
        from django.urls import reverse
        self.client.login(username='customer1', password='Password123!')
        url = reverse('product_add_review', kwargs={'pk': self.product.pk})
        # Test rating above 5 is clamped to 5
        self.client.post(url, {
            'rating': '99',
            'comment': 'Awesome!'
        })
        from product.models import ProductReview
        review = ProductReview.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 5)

        # Test rating below 1 is clamped to 1
        from django.utils import timezone
        from datetime import timedelta
        # Fast-forward updated_at in DB directly to bypass throttling in test
        ProductReview.objects.filter(pk=review.pk).update(updated_at=timezone.now() - timedelta(seconds=30))

        self.client.post(url, {
            'rating': '-10',
            'comment': 'Terrible experience!'
        })
        review.refresh_from_db()
        self.assertEqual(review.rating, 1)

    def test_review_comment_xss_sanitization(self):
        from django.urls import reverse
        self.client.login(username='customer1', password='Password123!')
        url = reverse('product_add_review', kwargs={'pk': self.product.pk})
        malicious_comment = '<script>alert("hacked")</script><b>Super cool!</b><img src=x onerror=alert(2)>'
        self.client.post(url, {
            'rating': '5',
            'comment': malicious_comment
        })
        from product.models import ProductReview
        review = ProductReview.objects.get(product=self.product, user=self.user)
        self.assertNotIn('<script>', review.comment)
        self.assertNotIn('alert("hacked")', review.comment)
        self.assertNotIn('onerror', review.comment)
        self.assertIn('Super cool!', review.comment)

    def test_one_review_per_user_per_product(self):
        from django.urls import reverse
        self.client.login(username='customer1', password='Password123!')
        url = reverse('product_add_review', kwargs={'pk': self.product.pk})
        from product.models import ProductReview
        from django.utils import timezone
        from datetime import timedelta

        # First review
        self.client.post(url, {
            'rating': '3',
            'comment': 'First review comment.'
        })
        self.assertEqual(ProductReview.objects.filter(product=self.product, user=self.user).count(), 1)

        # Update review after throttle period (bypass auto_now via queryset update)
        review = ProductReview.objects.get(product=self.product, user=self.user)
        ProductReview.objects.filter(pk=review.pk).update(updated_at=timezone.now() - timedelta(seconds=20))

        self.client.post(url, {
            'rating': '5',
            'comment': 'Updated review: actually amazing!'
        })
        # Should still be 1 review, updated
        self.assertEqual(ProductReview.objects.filter(product=self.product, user=self.user).count(), 1)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Updated review: actually amazing!')


class ImageUploadSecurityTests(TestCase):
    def _create_mock_image(self, format='PNG'):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        buffer = io.BytesIO()
        image = Image.new('RGB', (10, 10), color='blue')
        image.save(buffer, format=format)
        buffer.seek(0)
        return SimpleUploadedFile(f'test.{format.lower()}', buffer.read(), content_type=f'image/{format.lower()}')

    def test_product_form_accepts_valid_image(self):
        from product.forms import ProductForm
        valid_img = self._create_mock_image('PNG')
        form = ProductForm(data={
            'name': 'Test Item',
            'description': 'Detailed product description for testing',
            'price': '19.99',
            'stock': '10',
            'unit': '1 pc',
        }, files={'image': valid_img})
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_form_rejects_svg_file(self):
        from product.forms import ProductForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        svg_file = SimpleUploadedFile('logo.svg', svg_content, content_type='image/svg+xml')
        form = ProductForm(data={
            'name': 'Test Item',
            'description': 'Detailed product description for testing',
            'price': '19.99',
            'stock': '10',
            'unit': '1 pc',
        }, files={'image': svg_file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_product_form_rejects_script_disguised_as_png(self):
        from product.forms import ProductForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_png_content = b'<script>alert("malicious script in png");</script>'
        fake_file = SimpleUploadedFile('fake.png', fake_png_content, content_type='image/png')
        form = ProductForm(data={
            'name': 'Test Item',
            'description': 'Detailed product description for testing',
            'price': '19.99',
            'stock': '10',
            'unit': '1 pc',
        }, files={'image': fake_file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_sitesetting_form_rejects_svg_logo(self):
        from admin_panel.forms import SiteSettingForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'
        svg_file = SimpleUploadedFile('branding.svg', svg_content, content_type='image/svg+xml')
        form = SiteSettingForm(data={'site_name': 'My Shop'}, files={'brand_logo': svg_file})
        self.assertFalse(form.is_valid())
        self.assertIn('brand_logo', form.errors)


class ProductDetailViewUITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Smartphones', slug='smartphones', icon='bi-phone')
        self.brand = Brand.objects.create(name='AcmeTech', slug='acmetech')
        self.product = Product.objects.create(
            name='Flagship Smartphone Ultra',
            slug='flagship-smartphone-ultra',
            sku='SKU-PHONE-001',
            category=self.category,
            brand=self.brand,
            short_description='<p>Compact high performance device with <strong>super camera</strong>.</p>',
            description='<h5>Technical Specifications</h5><p>Experience ultra-fast speed with <strong>Snapdragon 8 Gen 3</strong>.</p><ul><li>12GB RAM</li><li>256GB Storage</li></ul>',
            price=Decimal('899.00'),
            discount_price=Decimal('799.00'),
            stock=12,
            unit='1 box',
            is_active=True
        )

    def test_detail_view_renders_rich_html_without_raw_tags(self):
        res = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        
        # Verify rendered HTML formatting is present
        self.assertIn('<h5>Technical Specifications</h5>', html)
        self.assertIn('<strong>Snapdragon 8 Gen 3</strong>', html)
        self.assertIn('<li>12GB RAM</li>', html)
        
        # Verify raw escaped HTML is NOT rendered
        self.assertNotIn('&lt;h5&gt;Technical Specifications&lt;/h5&gt;', html)
        self.assertNotIn('&lt;p&gt;Experience ultra-fast', html)
        
        # Verify short summary does not leak tags
        self.assertIn('Compact high performance device with super camera.', html)
        self.assertNotIn('&lt;p&gt;Compact', html)

    def test_detail_view_modern_theme_cards_present(self):
        res = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        
        # Verify modern theme cards instead of stark white box
        self.assertIn('product-detail-card', html)
        self.assertIn('product-tabs-card', html)
        self.assertIn('detail-nav-pills', html)
        self.assertIn('spec-feature-box', html)
        self.assertIn('specs-modern-table', html)
        self.assertIn('price-box-detail', html)
        self.assertIn('quantity-stepper', html)

    def test_detail_view_bilingual_english_and_bangla(self):
        # English test
        res_en = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res_en.status_code, 200)
        html_en = res_en.content.decode('utf-8')
        self.assertIn('Detailed Description', html_en)
        self.assertIn('Specifications', html_en)
        self.assertIn('Customer Reviews', html_en)
        self.assertIn('In Stock', html_en)

        # Switch to Bangla
        self.client.get('/set-language/bn/')
        res_bn = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res_bn.status_code, 200)
        html_bn = res_bn.content.decode('utf-8')
        self.assertIn('বিস্তারিত বিবরণ', html_bn)
        self.assertIn('বৈশিষ্ট্য ও স্পেকস', html_bn)
        self.assertIn('গ্রাহক রিভিউ', html_bn)
        self.assertIn('স্টকে আছে', html_bn)

    def test_detail_view_dual_cta_and_trust_widget(self):
        res = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')

        # 1. Dual CTA Button Check
        self.assertIn('name="buy_now"', html)
        self.assertIn('value="1"', html)
        self.assertIn('bi-lightning-charge-fill', html)
        self.assertIn('Order Now', html)
        self.assertIn('Add to Shopping Bag', html)

        # 2. Transparent Delivery & COD Guarantee Box Check
        self.assertIn('delivery-trust-box', html)
        self.assertIn('Inside Dhaka: <span class="text-primary">৳49</span>', html)
        self.assertIn('Outside Dhaka: <span class="text-primary">৳99</span>', html)
        self.assertIn('Free over ৳500', html)
        self.assertIn('Cash on Delivery Available', html)
        self.assertIn('Pay when your order arrives', html)
        self.assertIn('7-Day Return & Replacement Guarantee', html)
        self.assertIn('100% Genuine Guaranteed', html)

    def test_detail_view_frequently_bought_together_bundle(self):
        # Create 2 complementary products in the same category
        p2 = Product.objects.create(
            name='Protective Case for Flagship',
            slug='protective-case-flagship',
            category=self.category,
            brand=self.brand,
            price=Decimal('49.00'),
            stock=25,
            unit='1 pc',
            is_active=True
        )
        p3 = Product.objects.create(
            name='Screen Protector Glass',
            slug='screen-protector-glass',
            category=self.category,
            brand=self.brand,
            price=Decimal('29.00'),
            stock=50,
            unit='1 pc',
            is_active=True
        )

        res = self.client.get(f'/product/{self.product.pk}/')
        self.assertEqual(res.status_code, 200)

        # Context checks
        self.assertIn('bundle_items', res.context)
        self.assertEqual(len(res.context['bundle_items']), 2)
        self.assertEqual(res.context['bundle_discount_percent'], 5)

        expected_total = self.product.effective_price + p2.effective_price + p3.effective_price
        expected_discount_price = round(expected_total * Decimal('0.95'), 2)
        expected_savings = expected_total - expected_discount_price

        self.assertEqual(res.context['bundle_total'], expected_total)
        self.assertEqual(res.context['bundle_discount_price'], expected_discount_price)
        self.assertEqual(res.context['bundle_savings'], expected_savings)

        html = res.content.decode('utf-8')
        # Template checks
        self.assertIn('frequentlyBoughtTogether', html)
        self.assertIn('Frequently Bought Together', html)
        self.assertIn('bundle-checkbox', html)
        self.assertIn('Protective Case for Flagship', html)
        self.assertIn('Screen Protector Glass', html)
        self.assertIn('Add Bundle to Bag', html)
        self.assertIn('addBundleToCart', html)
        self.assertIn('recalculateBundle', html)


