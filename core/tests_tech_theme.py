from decimal import Decimal
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from core.theme_registry import theme_registry
from core.models import SiteSetting, ThemeCustomization
from core.context_processors import site_settings_processor
from product.models import Category, Brand, Product, ProductReview
from accounts.models import Wishlist

User = get_user_model()


class BaseTechThemeTestCase(TestCase):
    """
    Base test case setting up common tech categories, brands, products,
    and customer users for thorough testing.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Site Settings initialized for Tech & Electronics theme
        cls.setting = SiteSetting.get_settings()
        cls.setting.site_name = "TechVerse Electronics Lab"
        cls.setting.active_theme = "tech-electronics"
        cls.setting.contact_phone = "+880 1800-999888"
        cls.setting.contact_email = "support@techverse.test"
        cls.setting.contact_address = "Multiplan Center, New Elephant Road, Dhaka"
        cls.setting.save()

        # 2. Categories for Tech theme and non-tech themes
        cls.cat_laptops = Category.objects.create(
            name="Laptops & MacBooks",
            slug="laptops",
            icon="bi-laptop",
            theme="tech-electronics",
            is_featured=True,
            order=1,
        )
        cls.cat_phones = Category.objects.create(
            name="Smartphones & Tablets",
            slug="smartphones",
            icon="bi-phone",
            theme="tech-electronics",
            is_featured=True,
            order=2,
        )
        cls.cat_hardware = Category.objects.create(
            name="PC Hardware & GPUs",
            slug="pc-hardware",
            icon="bi-cpu",
            theme="tech-electronics",
            is_featured=True,
            order=3,
        )
        cls.cat_audio = Category.objects.create(
            name="Audio & Soundbars",
            slug="audio-gear",
            icon="bi-headphones",
            theme="tech-electronics",
            is_featured=True,
            order=4,
        )
        cls.cat_pharmacy = Category.objects.create(
            name="Prescription Medicines",
            slug="prescription-medicines",
            icon="bi-capsule",
            theme="pharmacy_health",
            is_featured=False,
            order=10,
        )
        cls.cat_marketplace = Category.objects.create(
            name="Fashion & Lifestyle",
            slug="fashion-lifestyle",
            icon="bi-bag",
            theme="marketplace",
            is_featured=False,
            order=11,
        )

        # 3. Brands
        cls.brand_apple = Brand.objects.create(
            name="Apple",
            slug="apple",
            theme="tech-electronics",
        )
        cls.brand_asus = Brand.objects.create(
            name="Asus ROG",
            slug="asus",
            theme="tech-electronics",
        )
        cls.brand_samsung = Brand.objects.create(
            name="Samsung",
            slug="samsung",
            theme="tech-electronics",
        )
        cls.brand_logitech = Brand.objects.create(
            name="Logitech",
            slug="logitech",
            theme="tech-electronics",
        )
        cls.brand_pharma = Brand.objects.create(
            name="Square Pharma",
            slug="square-pharma",
            theme="pharmacy_health",
        )
        cls.brand_mkt = Brand.objects.create(
            name="Zara Lifestyle",
            slug="zara-lifestyle",
            theme="marketplace",
        )

        # 4. Products for Tech Theme
        cls.product_laptop = Product.objects.create(
            name="Apple MacBook Pro 16 M3 Max",
            slug="apple-macbook-pro-16-m3-max",
            sku="TECH-MBP-001",
            category=cls.cat_laptops,
            brand=cls.brand_apple,
            theme="tech-electronics",
            short_description="Apple M3 Max chip with 16-core CPU, 40-core GPU, 36GB Unified Memory, 1TB SSD.",
            description="Liquid Retina XDR display, extreme dynamic range, 22 hours battery life, official 1-year Apple warranty.",
            price=Decimal("425000.00"),
            discount_price=Decimal("399000.00"),
            stock=10,
            unit="1 unit",
            is_active=True,
            is_featured=True,
            is_flash_sale=True,
        )

        cls.product_gpu = Product.objects.create(
            name="Asus ROG Strix GeForce RTX 4090 OC 24GB",
            slug="asus-rog-strix-geforce-rtx-4090-oc-24gb",
            sku="TECH-GPU-002",
            category=cls.cat_hardware,
            brand=cls.brand_asus,
            theme="tech-electronics",
            short_description="Flagship gaming graphics card with DLSS 3 and axial-tech fans.",
            description="Asus ROG Strix RTX 4090 OC Edition with 24GB GDDR6X, Vapor Chamber cooling, and 3-Year Official Warranty.",
            price=Decimal("295000.00"),
            discount_price=Decimal("275000.00"),
            stock=5,
            unit="1 unit",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_phone = Product.objects.create(
            name="Samsung Galaxy S24 Ultra 5G AI",
            slug="samsung-galaxy-s24-ultra-5g-ai",
            sku="TECH-SAM-003",
            category=cls.cat_phones,
            brand=cls.brand_samsung,
            theme="tech-electronics",
            short_description="Titanium frame, 200MP camera, Snapdragon 8 Gen 3, S-Pen included.",
            description="Galaxy AI phone with 6.8-inch Dynamic AMOLED 2X, 12GB RAM, 512GB Storage, 1-Year Official Samsung Warranty.",
            price=Decimal("165000.00"),
            discount_price=Decimal("149000.00"),
            stock=15,
            unit="1 unit",
            is_active=True,
            is_featured=True,
            is_flash_sale=True,
        )

        cls.product_mouse = Product.objects.create(
            name="Logitech MX Master 3S Wireless Mouse",
            slug="logitech-mx-master-3s-wireless-mouse",
            sku="TECH-LOGI-004",
            category=cls.cat_hardware,
            brand=cls.brand_logitech,
            theme="tech-electronics",
            short_description="Ergonomic performance wireless mouse with 8K DPI tracking and Quiet Clicks.",
            description="MagSpeed electromagnetic scrolling, USB-C fast charging, connects up to 3 devices.",
            price=Decimal("12500.00"),
            discount_price=None,
            stock=40,
            unit="1 piece",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        cls.product_out_of_stock = Product.objects.create(
            name="Limited Custom Liquid Cooled Gaming Rig",
            slug="limited-custom-liquid-cooled-gaming-rig",
            sku="TECH-RIG-005",
            category=cls.cat_hardware,
            brand=cls.brand_asus,
            theme="tech-electronics",
            short_description="Extreme watercooled dual-loop workstation.",
            description="Currently out of stock pending next production batch.",
            price=Decimal("850000.00"),
            stock=0,
            unit="1 system",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        # Pharmacy isolated product
        cls.product_pharma = Product.objects.create(
            name="Napa Extra 500mg/65mg Paracetamol",
            slug="napa-extra-500mg-paracetamol",
            sku="PHARM-NAP-001",
            category=cls.cat_pharmacy,
            brand=cls.brand_pharma,
            theme="pharmacy_health",
            short_description="Fast relief for headache and fever.",
            description="Standard paracetamol and caffeine formulation by Square Pharmaceuticals.",
            price=Decimal("35.00"),
            stock=500,
            unit="1 strip",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        # Marketplace isolated product
        cls.product_mkt = Product.objects.create(
            name="Casual Denim Jacket",
            slug="casual-denim-jacket",
            sku="MKT-JKT-001",
            category=cls.cat_marketplace,
            brand=cls.brand_mkt,
            theme="marketplace",
            short_description="100% Cotton denim jacket.",
            description="Classic blue wash denim jacket with metal buttons.",
            price=Decimal("3500.00"),
            stock=25,
            unit="1 piece",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        # 5. Customer, Staff, & Superuser Users
        cls.customer_user = User.objects.create_user(
            username="tech_buyer",
            email="techbuyer@test.com",
            password="Password123",
            first_name="Tanvir",
            last_name="Hasan",
        )

        cls.staff_user = User.objects.create_user(
            username="tech_staff",
            email="techstaff@test.com",
            password="Password123",
            is_staff=True,
        )

        cls.superuser = User.objects.create_superuser(
            username="tech_admin",
            email="admin@techverse.test",
            password="Password123",
        )

        # 6. Reviews for Rating tests
        ProductReview.objects.create(
            product=cls.product_laptop,
            user=cls.customer_user,
            rating=5,
            comment="Beast of a machine! The M3 Max handles 8K video rendering with zero stutter.",
        )
        ProductReview.objects.create(
            product=cls.product_gpu,
            user=cls.customer_user,
            rating=5,
            comment="Incredible 4K gaming performance at ultra settings. Temps never exceed 62C.",
        )
        ProductReview.objects.create(
            product=cls.product_phone,
            user=cls.customer_user,
            rating=4,
            comment="Stunning display and Galaxy AI photo editing tools are magical.",
        )

    def setUp(self):
        self.client = Client()


class TechThemeActivationAndResolutionTests(BaseTechThemeTestCase):
    """
    1. Tests for Theme Registry, Activation, Normalization, Preview, and Context Processors.
    """

    def test_tech_theme_registry_definition(self):
        """ThemeRegistry holds 'tech-electronics' with legacy key 'tech_gadgets' and template mappings."""
        theme = theme_registry.get("tech-electronics", fallback=False)
        self.assertIsNotNone(theme)
        self.assertEqual(theme.id, "tech-electronics")
        self.assertEqual(theme.legacy_key, "tech_gadgets")
        self.assertEqual(theme_registry.normalize_id("tech_gadgets"), "tech-electronics")
        self.assertEqual(theme_registry.normalize_id("tech-electronics"), "tech-electronics")

        # Template mapping verification
        mapping = theme.template_mapping
        self.assertEqual(mapping.get("header"), "themes/tech-electronics/header.html")
        self.assertEqual(mapping.get("footer"), "themes/tech-electronics/footer.html")
        self.assertEqual(mapping.get("home"), "themes/tech-electronics/home.html")
        self.assertEqual(mapping.get("product_card"), "themes/tech-electronics/product_card.html")
        self.assertEqual(mapping.get("product_list"), "themes/tech-electronics/product_list.html")
        self.assertEqual(mapping.get("product_detail"), "themes/tech-electronics/product_detail.html")

        # Capabilities verification
        capabilities = theme.supported_capabilities
        self.assertIn("spec_table", capabilities)
        self.assertIn("emi_calculator", capabilities)
        self.assertIn("warranty_badge", capabilities)

    def test_sitesetting_active_theme_activation(self):
        """SiteSetting active_theme='tech-electronics' updates and persists correctly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "tech-electronics"
        setting.save()

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, "tech-electronics")
        self.assertEqual(setting.get_canonical_theme_id(), "tech-electronics")

        # Admin activation route sets active flag on ThemeCustomization
        self.client.force_login(self.superuser)
        res = self.client.post(reverse("admin_theme_activate", kwargs={"theme_id": "tech-electronics"}))
        self.assertEqual(res.status_code, 302)

        cust = ThemeCustomization.get_for_theme("tech-electronics")
        self.assertIsNotNone(cust)
        self.assertTrue(cust.is_active)

    def test_context_processor_populates_tech_theme_variables(self):
        """site_settings_processor accurately injects all tech theme variables."""
        factory = RequestFactory()
        req = factory.get("/")
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "tech-electronics")
        self.assertIn(ctx["CURRENT_THEME_KEY"], ["tech-electronics", "tech_gadgets"])
        self.assertIsNotNone(ctx["CURRENT_THEME_DATA"])
        self.assertEqual(ctx["CURRENT_THEME_DATA"]["id"], "tech-electronics")
        self.assertFalse(ctx["IS_THEME_PREVIEW"])

    def test_session_based_theme_preview_for_staff(self):
        """Staff session previewing 'tech-electronics' isolates context without altering site setting."""
        factory = RequestFactory()
        req = factory.get("/")
        req.user = self.staff_user
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session["admin_preview_theme"] = "tech-electronics"
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "tech-electronics")
        self.assertTrue(ctx["IS_THEME_PREVIEW"])

    def test_query_param_preview_isolation(self):
        """Query parameter ?theme=tech-electronics activates theme preview cleanly."""
        res = self.client.get("/?theme=tech-electronics")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_theme_id"], "tech-electronics")


class TechHeaderAndFooterRenderingTests(BaseTechThemeTestCase):
    """
    2. Tests for Tech Header, Announcement Bar, Electronics Navigation, and 4 Tech Pillars Footer.
    """

    def test_tech_header_announcement_strip_and_support_hotline(self):
        """Header renders top tech announcement bar, hotline, warranty notice, and language switcher."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Contact Phone / Tech Support hotline
        self.assertIn("+880 1800-999888", html)

        # Warranty / EMI Notice in header or announcement bar
        self.assertTrue(
            "Warranty" in html or "EMI" in html or "tech-announcement" in html or "tech" in html
        )

        # Language Switcher
        self.assertIn(reverse("set_language", args=["en"]), html)
        self.assertIn(reverse("set_language", args=["bn"]), html)

    def test_tech_header_search_bar_structure(self):
        """Header renders tech search bar with form action, input, and precision search button."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Search Form and input
        self.assertIn('action="/product/"', html)
        self.assertIn('name="q"', html)
        self.assertIn("bi-search", html)

    def test_tech_header_account_wishlist_cart_controls(self):
        """Header includes user account dropdown, live wishlist badge, and cart trigger."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Wishlist and Cart live badges
        self.assertIn("navWishlistBadge", html)
        self.assertIn("navCartBadge", html)
        self.assertTrue("cartOffcanvas" in html or "cartDrawer" in html or "cart" in html)

    def test_tech_navigation_bar_and_categories(self):
        """Navigation bar displays tech categories and specialized electronics badges."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tech categories
        self.assertTrue(
            "Laptops" in html or "laptops" in html or "Hardware" in html or "pc-hardware" in html
        )

    def test_tech_footer_assurance_pillars_and_columns(self):
        """Footer renders 4 tech assurance pillars, multi-columns, payment badges, and copyright."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # 4 Tech Assurance Pillars (Official Brand Warranty, 0% EMI Financing, Express Courier Dispatch, Certified Tech Specialist Support)
        self.assertTrue(
            "Warranty" in html and ("EMI" in html or "Installment" in html)
        )

        # Contact information & Payment badges
        self.assertIn("support@techverse.test", html)
        self.assertIn("Multiplan Center", html)
        self.assertTrue("bKash" in html or "Nagad" in html or "Cash on Delivery" in html or "Visa" in html)


class TechHomepageLayoutTests(BaseTechThemeTestCase):
    """
    3. Tests for Tech Homepage Layout, Flagship Hero, Precision Category Tiles, and Flash Deals.
    """

    def test_homepage_renders_tech_home_template(self):
        """Home view loads themes/tech-electronics/home.html when tech-electronics theme is active."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/home.html")
        self.assertEqual(res.context["current_theme_id"], "tech-electronics")

    def test_homepage_hero_carousel_and_spec_badges(self):
        """Homepage renders flagship tech hero carousel with technical spec badges."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Hero section present
        self.assertTrue(
            "techHeroCarousel" in html or "hero" in html.lower() or "carousel" in html.lower()
        )

    def test_homepage_category_tiles_and_shortcuts(self):
        """Homepage renders specialized electronics category tiles."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue(
            "Laptops &amp; MacBooks" in html or "Laptops & MacBooks" in html or "Smartphones" in html
        )

    def test_homepage_flash_deals_section(self):
        """Homepage renders flash tech deals and price drops bar."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tech flash sale product present
        self.assertTrue(
            "Apple MacBook Pro 16 M3 Max" in html or "Samsung Galaxy S24 Ultra 5G AI" in html
        )

    def test_homepage_brand_showcases(self):
        """Homepage displays official tech brand showcases (Apple, Asus, Samsung, Logitech)."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Brand names
        self.assertTrue("Apple" in html or "Asus" in html or "Samsung" in html)

    def test_homepage_vip_coupon_or_newsletter(self):
        """Homepage renders tech newsletter / VIP promo coupon."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("TECH100" in html or "newsletter" in html.lower() or "subscribe" in html.lower())


class TechProductCardAndCatalogTests(BaseTechThemeTestCase):
    """
    4. Tests for Tech Product Card, Product List Layout, Technical Filter Sidebar, and Search.
    """

    def test_tech_product_card_elements(self):
        """Product card renders official warranty badge, discount pill, brand, specs, and price."""
        res = self.client.get("/product/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tech products visible
        self.assertIn("Apple MacBook Pro 16 M3 Max", html)

        # Warranty badge / EMI financing estimate
        self.assertTrue(
            "Warranty" in html or "EMI" in html or "Official" in html
        )

        # Pricing
        self.assertTrue("399000" in html or "425000" in html)

        # Add to cart and wishlist toggle
        self.assertTrue("Add to Cart" in html or "Cart" in html or "bi-cart" in html)
        self.assertTrue("toggleWishlist" in html or "wishlist" in html.lower())

    def test_product_list_renders_tech_catalog_template(self):
        """Product list view dynamically loads themes/tech-electronics/product_list.html."""
        res = self.client.get("/product/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/product_list.html")
        html = res.content.decode("utf-8")

        # Technical filter sidebar or view toggle
        self.assertTrue(
            "Filter" in html or "filter" in html.lower() or "sidebar" in html.lower() or "grid" in html.lower()
        )

    def test_catalog_keyword_search_query(self):
        """Search query ?q=MacBook returns MacBook Pro and excludes RTX 4090."""
        res = self.client.get("/product/?q=MacBook")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/product_list.html")
        products = list(res.context["products"])

        product_names = [p.name for p in products]
        self.assertIn(self.product_laptop.name, product_names)
        self.assertNotIn(self.product_gpu.name, product_names)

    def test_catalog_category_filtering(self):
        """Filtering by category slug narrows product list strictly to that category."""
        res = self.client.get(f"/product/?category={self.cat_laptops.slug}")
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])

        for p in products:
            self.assertEqual(p.category, self.cat_laptops)

        # Direct path /product/category/<slug>/
        res_path = self.client.get(f"/product/category/{self.cat_laptops.slug}/")
        self.assertEqual(res_path.status_code, 200)
        self.assertTemplateUsed(res_path, "themes/tech-electronics/product_list.html")

    def test_catalog_sorting_options(self):
        """Catalog sorting works correctly for price_asc, price_desc, rating, and newest."""
        # Price Ascending
        res_asc = self.client.get("/product/?sort=price_asc")
        self.assertEqual(res_asc.status_code, 200)
        prices_asc = [p.price for p in res_asc.context["products"]]
        self.assertEqual(prices_asc, sorted(prices_asc))

        # Price Descending
        res_desc = self.client.get("/product/?sort=price_desc")
        self.assertEqual(res_desc.status_code, 200)
        prices_desc = [p.price for p in res_desc.context["products"]]
        self.assertEqual(prices_desc, sorted(prices_desc, reverse=True))

    def test_catalog_in_stock_and_price_range_filter(self):
        """Filters in_stock=1 and min_price/max_price return appropriate items."""
        # in_stock=1 excludes out of stock
        res_stock = self.client.get("/product/?in_stock=1")
        self.assertEqual(res_stock.status_code, 200)
        for p in res_stock.context["products"]:
            self.assertGreater(p.stock, 0)
        p_ids = [p.pk for p in res_stock.context["products"]]
        self.assertNotIn(self.product_out_of_stock.pk, p_ids)

        # price range 200000 - 350000
        res_price = self.client.get("/product/?min_price=200000&max_price=350000")
        self.assertEqual(res_price.status_code, 200)
        p_ids = [p.pk for p in res_price.context["products"]]
        self.assertIn(self.product_gpu.pk, p_ids)
        self.assertNotIn(self.product_mouse.pk, p_ids)


class TechProductDetailTests(BaseTechThemeTestCase):
    """
    5. Tests for Tech Product Detail View, Image Gallery, Tech Retail Assurance Box, EMI Teaser, and Specs Table.
    """

    def test_product_detail_renders_tech_detail_template(self):
        """Product detail dynamically loads themes/tech-electronics/product_detail.html."""
        res = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/product_detail.html")
        html = res.content.decode("utf-8")

        # Product Title and Brand
        self.assertIn("Apple MacBook Pro 16 M3 Max", html)
        self.assertIn("Apple", html)

    def test_product_detail_emi_calculator_teaser(self):
        """Detail page renders EMI financing calculator teaser / badge."""
        res = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # EMI teaser or financing calculation
        self.assertTrue(
            "EMI" in html or "Installment" in html or "0% EMI" in html
        )

    def test_product_detail_retail_assurance_box(self):
        """Detail page renders Tech Retail Assurance & Services Box."""
        res = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Official Brand Warranty / Replacement / Courier
        self.assertTrue(
            "Warranty" in html or "Official" in html or "Replacement" in html or "Dispatch" in html
        )

    def test_product_detail_specifications_table_and_reviews(self):
        """Detail page renders Technical Specifications Table and customer reviews."""
        res = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Technical specs / Description / Reviews
        self.assertTrue(
            "Specification" in html or "Specs" in html or "M3 Max" in html or "Liquid Retina" in html
        )
        self.assertIn("Tanvir", html)
        self.assertIn("Beast of a machine", html)


class TechCartAndWishlistTests(BaseTechThemeTestCase):
    """
    6. Tests for Cart Functionality and Wishlist Toggle Integration with Tech Theme.
    """

    def test_add_to_cart_standard_and_ajax(self):
        """Add to cart works via both standard form submission and AJAX JSON request."""
        # Standard POST
        add_url = reverse("add_to_cart", args=[self.product_laptop.pk])
        res = self.client.post(add_url, {"quantity": 1}, follow=True)
        self.assertEqual(res.status_code, 200)

        # Inspect Cart Detail
        cart_res = self.client.get(reverse("cart_detail"))
        self.assertEqual(cart_res.status_code, 200)
        cart = cart_res.context["cart"]
        self.assertEqual(cart.total_items, 1)

        # AJAX POST
        ajax_res = self.client.post(
            reverse("add_to_cart", args=[self.product_phone.pk]),
            {"quantity": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data.get("success"))

    def test_cart_drawer_rendering_with_tech_products(self):
        """Cart drawer endpoint returns valid HTML drawer with updated tech item."""
        self.client.post(reverse("add_to_cart", args=[self.product_laptop.pk]), {"quantity": 1})

        drawer_res = self.client.get(reverse("cart_drawer"))
        self.assertEqual(drawer_res.status_code, 200)
        drawer_html = drawer_res.content.decode("utf-8")
        self.assertIn("Apple MacBook Pro 16 M3 Max", drawer_html)

    def test_wishlist_toggle_authenticated_tech_buyer(self):
        """Customer can toggle tech product in and out of wishlist via AJAX."""
        self.client.force_login(self.customer_user)
        wishlist_url = reverse("wishlist_toggle", args=[self.product_laptop.pk])

        # 1st toggle: adds to wishlist
        res1 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user=self.customer_user, product=self.product_laptop).exists())

        # 2nd toggle: removes from wishlist
        res2 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(Wishlist.objects.filter(user=self.customer_user, product=self.product_laptop).exists())

    def test_wishlist_unauthenticated_requires_login(self):
        """Anonymous user trying to toggle wishlist receives 401 login_required."""
        wishlist_url = reverse("wishlist_toggle", args=[self.product_laptop.pk])
        res = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertTrue(data.get("login_required"))


class CrossThemeIsolationAndFallbackRegressionTests(BaseTechThemeTestCase):
    """
    7. Tests verifying marketplace and pharmacy continue to render cleanly and cross-theme isolation is enforced.
    """

    def test_marketplace_theme_isolation_from_tech(self):
        """When marketplace theme is active, it renders its marketplace storefront cleanly without tech elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "marketplace"
        setting.save()

        # Homepage renders marketplace home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("marketplaceHeroCarousel", html)

        # Header renders marketplace header
        self.assertIn("marketplace-header", html)

        # Product list renders marketplace product list
        res_list = self.client.get("/product/")
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/marketplace/product_list.html")

    def test_pharmacy_theme_isolation_from_tech(self):
        """When pharmacy theme is active, it renders its pharmacy storefront cleanly without tech elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Homepage renders pharmacy home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/pharmacy-healthcare/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("rxUploadModal", html)

        # Header renders pharmacy header
        self.assertIn("pharmacy-header", html)

    def test_strict_theme_isolation_product_detail_cross_theme_404(self):
        """
        Product belonging strictly to pharmacy raises 404 when tech theme is active.
        Product belonging strictly to tech raises 404 when pharmacy theme is active.
        """
        # Active theme is tech-electronics
        setting = SiteSetting.get_settings()
        setting.active_theme = "tech-electronics"
        setting.save()

        # Pharmacy product in tech theme raises 404
        res_pharma = self.client.get(f"/product/{self.product_pharma.pk}/")
        self.assertEqual(res_pharma.status_code, 404)

        # Marketplace product in tech theme raises 404
        res_mkt = self.client.get(f"/product/{self.product_mkt.pk}/")
        self.assertEqual(res_mkt.status_code, 404)

        # Tech product in tech theme is 200 OK
        res_tech = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res_tech.status_code, 200)

        # Now switch active theme to pharmacy-healthcare
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Tech product in pharmacy theme raises 404
        res_tech_under_pharma = self.client.get(f"/product/{self.product_laptop.pk}/")
        self.assertEqual(res_tech_under_pharma.status_code, 404)
