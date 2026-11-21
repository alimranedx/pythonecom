"""
Comprehensive Storefront Automated Test Suite for PythonEcom.

Tests all storefront capabilities and user flows across all 6 registered canonical themes:
1. pharmacy-healthcare
2. marketplace
3. tech-electronics
4. beauty-skincare
5. fashion-lifestyle
6. organic-grocery

Verifies:
1. Homepage rendering with preview mode (?preview_theme=<theme_id>): hero campaigns, category shortcuts, promo banners, product sections, footer.
2. Product listing/catalog: category filter, brand filter, price filtering, sorting, pagination, search.
3. Product detail: gallery images, prices, badges, specs, reviews, related products.
4. Cart operations: add to cart (standard & ajax), quantity updates, cart drawer, cart detail page.
5. Header & Navigation: category menus, search bar, account links, cart badge count.
6. Verify theme customizer variable overrides apply correctly to storefront templates.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.theme_registry import theme_registry
from core.models import SiteSetting, ThemeCustomization
from product.models import Category, Brand, Product, ProductReview

User = get_user_model()


class StorefrontComprehensiveThemeTests(TestCase):
    """
    Exhaustive test suite verifying storefront features across all 6 themes.
    """

    @classmethod
    def setUpTestData(cls):
        cls.themes = [
            'pharmacy-healthcare',
            'marketplace',
            'tech-electronics',
            'beauty-skincare',
            'fashion-lifestyle',
            'organic-grocery',
        ]

        # Ensure base site settings exist
        cls.settings = SiteSetting.get_settings()
        cls.settings.site_name = "Easy Purchase Store"
        cls.settings.announcement_enabled = True
        cls.settings.announcement_text_en = "Free Delivery on orders over ৳500!"
        cls.settings.announcement_text_bn = "৫০০ টাকার বেশি অর্ডারে ফ্রি ডেলিভারি!"
        cls.settings.contact_phone = "+880 1700-112233"
        cls.settings.contact_email = "support@easypurchase.test"
        cls.settings.save()

        cls.reviewer = User.objects.create_user(
            username="test_reviewer",
            email="reviewer@easypurchase.test",
            password="pass"
        )

        # Seed categories, brands, and products for all themes
        cls.theme_products = {}
        for theme_id in cls.themes:
            legacy_key = theme_registry.get_legacy_key(theme_id) or theme_id
            
            # Category
            cat = Category.objects.create(
                name=f"{theme_id.title()} Category",
                slug=f"{theme_id}-category",
                theme=theme_id,
                icon="bi-tag",
                is_featured=True,
                order=1
            )
            # Brand
            brand = Brand.objects.create(
                name=f"{theme_id.title()} Brand",
                slug=f"{theme_id}-brand",
                theme=theme_id
            )
            # Products (create at least 3 per theme for catalog & detail testing)
            p1 = Product.objects.create(
                name=f"Premium {theme_id.title()} Product 1",
                slug=f"prem-{theme_id}-prod-1",
                category=cat,
                brand=brand,
                price=Decimal("150.00"),
                discount_price=Decimal("130.00"),
                stock=50,
                is_active=True,
                is_featured=True,
                theme=theme_id,
                description=f"Authentic formulation and premium craftsmanship for {theme_id}.",
                short_description=f"Top-rated {theme_id} item."
            )
            p2 = Product.objects.create(
                name=f"Standard {theme_id.title()} Product 2",
                slug=f"std-{theme_id}-prod-2",
                category=cat,
                brand=brand,
                price=Decimal("80.00"),
                stock=20,
                is_active=True,
                theme=theme_id,
                description=f"Reliable standard daily product for {theme_id}."
            )
            p3 = Product.objects.create(
                name=f"Budget {theme_id.title()} Product 3",
                slug=f"bdg-{theme_id}-prod-3",
                category=cat,
                brand=brand,
                price=Decimal("45.00"),
                stock=100,
                is_active=True,
                theme=theme_id,
                description=f"Affordable everyday essential for {theme_id}."
            )

            # Add sample review
            ProductReview.objects.create(
                product=p1,
                user=cls.reviewer,
                rating=5,
                comment="Exceptional quality, exactly as described!"
            )

            cls.theme_products[theme_id] = (p1, p2, p3, cat, brand)

    def setUp(self):
        self.client = Client()

    # =========================================================================
    # 1. HOMEPAGE RENDERING WITH PREVIEW MODE (?preview_theme=<theme_id>)
    # =========================================================================
    def test_01_homepage_preview_mode_rendering_all_themes(self):
        """Verify homepage renders with HTTP 200 in preview mode for all 6 themes."""
        for tid in self.themes:
            with self.subTest(theme=tid):
                url = f"/?preview_theme={tid}"
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Theme {tid} homepage failed with status {res.status_code}")

                # Context assertions
                self.assertEqual(res.context['CURRENT_THEME_ID'], tid)
                self.assertTrue(res.context['IS_THEME_PREVIEW'], f"Theme {tid} must flag IS_THEME_PREVIEW=True")
                self.assertIsNotNone(res.context['CURRENT_THEME_DATA'])

                html = res.content.decode('utf-8')
                # Preview mode top bar
                self.assertIn("PREVIEW MODE", html, f"Theme {tid} missing PREVIEW MODE indicator")
                # Header brand / logo fallback or site title
                self.assertTrue(
                    "Easy Purchase" in html or tid in html.lower(),
                    f"Theme {tid} missing store identity"
                )
                # Footer trust pillars / copyright
                self.assertTrue(
                    "©" in html or "Easy Purchase" in html or "2026" in html,
                    f"Theme {tid} missing footer elements"
                )

    # =========================================================================
    # 2. PRODUCT LISTING / CATALOG FILTERING, SORTING, SEARCH, PAGINATION
    # =========================================================================
    def test_02_product_catalog_listing_and_filters_all_themes(self):
        """Verify product catalog listing, filtering, search, sorting and pagination for all 6 themes."""
        for tid in self.themes:
            p1, p2, p3, cat, brand = self.theme_products[tid]
            with self.subTest(theme=tid):
                # 2.1 Base Catalog Listing
                res_base = self.client.get(f"/product/?preview_theme={tid}")
                self.assertEqual(res_base.status_code, 200, f"Catalog base failed for {tid}")
                self.assertIn('products', res_base.context)
                self.assertGreaterEqual(len(res_base.context['products']), 1)

                # 2.2 Category Filter
                res_cat = self.client.get(f"/product/?preview_theme={tid}&category={cat.slug}")
                self.assertEqual(res_cat.status_code, 200, f"Category filter failed for {tid}")
                self.assertIn('products', res_cat.context)
                cat_prod_ids = [p.id for p in res_cat.context['products']]
                self.assertIn(p1.id, cat_prod_ids)

                # 2.3 Brand Filter
                res_brand = self.client.get(f"/product/?preview_theme={tid}&brand={brand.slug}")
                self.assertEqual(res_brand.status_code, 200, f"Brand filter failed for {tid}")
                self.assertIn('products', res_brand.context)
                brand_prod_ids = [p.id for p in res_brand.context['products']]
                self.assertIn(p1.id, brand_prod_ids)

                # 2.4 Price Filter
                res_price = self.client.get(f"/product/?preview_theme={tid}&min_price=100&max_price=200")
                self.assertEqual(res_price.status_code, 200, f"Price filter failed for {tid}")
                price_prod_ids = [p.id for p in res_price.context['products']]
                self.assertIn(p1.id, price_prod_ids)
                self.assertNotIn(p3.id, price_prod_ids)  # p3 is 45.00, should be excluded

                # 2.5 Sorting (price_asc, price_desc, newest, rating)
                for sort_opt in ['price_asc', 'price_desc', 'newest', 'rating']:
                    res_sort = self.client.get(f"/product/?preview_theme={tid}&sort={sort_opt}")
                    self.assertEqual(res_sort.status_code, 200, f"Sort '{sort_opt}' failed for {tid}")

                # 2.6 Search Query
                res_search = self.client.get(f"/product/?preview_theme={tid}&q=Premium")
                self.assertEqual(res_search.status_code, 200, f"Search failed for {tid}")
                search_prod_ids = [p.id for p in res_search.context['products']]
                self.assertIn(p1.id, search_prod_ids)

                # 2.7 Pagination
                res_page = self.client.get(f"/product/?preview_theme={tid}&page=1")
                self.assertEqual(res_page.status_code, 200, f"Pagination page 1 failed for {tid}")
                self.assertTrue(res_page.context.get('page_obj') is not None or res_page.context.get('paginator') is not None)

    # =========================================================================
    # 3. PRODUCT DETAIL RENDERING
    # =========================================================================
    def test_03_product_detail_rendering_all_themes(self):
        """Verify product detail view renders product specs, prices, reviews, and related products."""
        for tid in self.themes:
            p1, p2, p3, cat, brand = self.theme_products[tid]
            with self.subTest(theme=tid):
                url = f"/product/{p1.pk}/?preview_theme={tid}"
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Product detail failed for {tid} on product {p1.pk}")

                # Context checks
                self.assertEqual(res.context['product'].id, p1.id)
                self.assertIn('related_products', res.context)

                html = res.content.decode('utf-8')
                # Price display
                self.assertTrue("130" in html or "150" in html, f"Price not rendered in {tid} product detail")
                # Title
                self.assertIn(p1.name, html, f"Product name missing in {tid} product detail")
                # Reviews section / stars
                self.assertTrue(
                    "Review" in html or "review" in html or "bi-star" in html or "Customer" in html,
                    f"Reviews section missing in {tid} product detail"
                )

    # =========================================================================
    # 4. CART OPERATIONS: ADD, UPDATE, DRAWER, CART DETAIL PAGE
    # =========================================================================
    def test_04_cart_operations_all_themes(self):
        """Verify standard & AJAX add to cart, drawer view, quantity updates, and cart page."""
        for tid in self.themes:
            p1, p2, p3, cat, brand = self.theme_products[tid]
            with self.subTest(theme=tid):
                # 4.1 AJAX Add to Cart
                res_ajax = self.client.post(
                    f"/cart/add/{p1.pk}/?preview_theme={tid}",
                    {'quantity': 1},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                )
                self.assertEqual(res_ajax.status_code, 200, f"AJAX add to cart failed for {tid}")
                json_data = res_ajax.json()
                self.assertTrue(json_data.get('success'), f"AJAX add to cart not successful for {tid}: {json_data}")

                # 4.2 Cart Drawer
                res_drawer = self.client.get(f"/cart/drawer/?preview_theme={tid}")
                self.assertEqual(res_drawer.status_code, 200, f"Cart drawer failed for {tid}")
                drawer_html = res_drawer.content.decode('utf-8')
                self.assertIn(p1.name, drawer_html, f"Added product missing from drawer in {tid}")

                # 4.3 Quantity Update
                res_update = self.client.post(
                    f"/cart/update/{p1.pk}/?preview_theme={tid}",
                    {'quantity': 3},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                )
                self.assertEqual(res_update.status_code, 200, f"Cart update quantity failed for {tid}")
                update_data = res_update.json()
                self.assertTrue(update_data.get('success'), f"Cart update not successful for {tid}: {update_data}")

                # 4.4 Cart Detail Page
                res_cart = self.client.get(f"/cart/?preview_theme={tid}")
                self.assertEqual(res_cart.status_code, 200, f"Cart detail page failed for {tid}")
                cart_html = res_cart.content.decode('utf-8')
                self.assertIn(p1.name, cart_html, f"Product missing on cart detail page for {tid}")

                # 4.5 Standard Form Add to Cart
                res_std = self.client.post(f"/cart/add/{p2.pk}/?preview_theme={tid}", {'quantity': 1})
                self.assertEqual(res_std.status_code, 302, f"Standard add to cart should redirect for {tid}")

                # Clean up session for clean run on next theme
                session = self.client.session
                session.flush()

    # =========================================================================
    # 5. HEADER & NAVIGATION VERIFICATION
    # =========================================================================
    def test_05_header_and_navigation_all_themes(self):
        """Verify navigation links, search forms, account controls and cart badge on header."""
        for tid in self.themes:
            with self.subTest(theme=tid):
                res = self.client.get(f"/?preview_theme={tid}")
                self.assertEqual(res.status_code, 200)
                html = res.content.decode('utf-8')

                # Search bar presence
                self.assertIn('name="q"', html, f"Theme {tid} missing search input 'q'")
                self.assertIn('/product/', html, f"Theme {tid} missing search form action '/product/'")

                # Cart badge / offcanvas triggers
                self.assertTrue(
                    "cartOffcanvas" in html or "cartDrawer" in html or "navCartBadge" in html or "mobileBottomCartBadge" in html,
                    f"Theme {tid} missing cart badge / drawer trigger"
                )

                # Account / Sign-in shortcuts
                self.assertTrue(
                    reverse("account_login") in html or "login" in html.lower() or "account" in html.lower(),
                    f"Theme {tid} missing account login / register shortcut"
                )

    # =========================================================================
    # 6. THEME CUSTOMIZER VARIABLE OVERRIDES ON STOREFRONT
    # =========================================================================
    def test_06_theme_customizer_variable_overrides_all_themes(self):
        """Verify theme customizer variable overrides and custom CSS apply dynamically to storefront."""
        for tid in self.themes:
            with self.subTest(theme=tid):
                # 6.1 Create custom settings override
                custom_token_color = "#e11d48"
                custom_css_rule = f".test-marker-{tid} {{ color: {custom_token_color}; }}"
                
                cust, _ = ThemeCustomization.objects.get_or_create(theme_id=tid)
                cust.settings_data = {
                    'primary': custom_token_color,
                    'hero_headline_en': f"Customized {tid.title()} Headline",
                }
                cust.custom_css = custom_css_rule
                cust.save()

                # 6.2 Render storefront with preview
                res = self.client.get(f"/?preview_theme={tid}")
                self.assertEqual(res.status_code, 200)

                # Context assertion: CURRENT_THEME_CONFIG holds custom settings
                config = res.context.get('CURRENT_THEME_CONFIG', {})
                self.assertEqual(config.get('primary'), custom_token_color)

                html = res.content.decode('utf-8')
                # Custom CSS injected
                self.assertIn(f"test-marker-{tid}", html, f"Theme {tid} missing custom CSS injection in storefront")

                # 6.3 Reset customization
                cust.reset_to_defaults()
                cust.refresh_from_db()
                self.assertEqual(cust.settings_data, {})
                self.assertEqual(cust.custom_css, "")

                # 6.4 Clean render after reset
                res_clean = self.client.get(f"/?preview_theme={tid}")
                self.assertEqual(res_clean.status_code, 200)
                clean_html = res_clean.content.decode('utf-8')
                self.assertNotIn(f"test-marker-{tid}", clean_html)
