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


class BaseMarketplaceThemeTestCase(TestCase):
    """
    Base test case setting up common marketplace categories, brands, products,
    and customer users for thorough testing.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Site Settings initialized for Marketplace theme
        cls.setting = SiteSetting.get_settings()
        cls.setting.site_name = "Mega Marketplace Test Store"
        cls.setting.active_theme = "marketplace"
        cls.setting.contact_phone = "+880 1700-123456"
        cls.setting.contact_email = "support@megamarket.test"
        cls.setting.contact_address = "Tejgaon Industrial Area, Dhaka-1208"
        cls.setting.save()

        # 2. Categories
        cls.cat_electronics = Category.objects.create(
            name="Electronics & Gadgets",
            slug="electronics-gadgets",
            icon="bi-laptop",
            theme="marketplace",
            is_featured=True,
            order=1,
        )
        cls.cat_fashion = Category.objects.create(
            name="Fashion & Lifestyle",
            slug="fashion-lifestyle",
            icon="bi-bag",
            theme="marketplace",
            is_featured=True,
            order=2,
        )
        cls.cat_home = Category.objects.create(
            name="Home & Living",
            slug="home-living",
            icon="bi-house",
            theme="marketplace",
            is_featured=True,
            order=3,
        )
        cls.cat_pharmacy = Category.objects.create(
            name="Prescription Medicines",
            slug="prescription-medicines",
            icon="bi-capsule",
            theme="pharmacy_health",
            is_featured=False,
            order=10,
        )

        # 3. Brands
        cls.brand_sony = Brand.objects.create(
            name="Sony Electronics",
            slug="sony-electronics",
            theme="marketplace",
        )
        cls.brand_samsung = Brand.objects.create(
            name="Samsung Official",
            slug="samsung-official",
            theme="marketplace",
        )
        cls.brand_pharma = Brand.objects.create(
            name="Square Pharma",
            slug="square-pharma",
            theme="pharmacy_health",
        )

        # 4. Products for Marketplace Theme
        cls.product_flagship = Product.objects.create(
            name="Sony WH-1000XM5 Wireless Headphones",
            slug="sony-wh-1000xm5-wireless-headphones",
            sku="MKT-SONY-001",
            category=cls.cat_electronics,
            brand=cls.brand_sony,
            theme="marketplace",
            short_description="Industry-leading noise canceling headphones with superior sound.",
            description="Sony WH-1000XM5 Wireless Noise-Canceling Headphones with Auto NC Optimizer, 30-hour battery life, and crystal-clear hands-free calling.",
            price=Decimal("38000.00"),
            discount_price=Decimal("34500.00"),
            stock=15,
            unit="1 unit",
            is_active=True,
            is_featured=True,
            is_flash_sale=True,
        )

        cls.product_phone = Product.objects.create(
            name="Samsung Galaxy S24 Ultra 5G",
            slug="samsung-galaxy-s24-ultra-5g",
            sku="MKT-SAM-002",
            category=cls.cat_electronics,
            brand=cls.brand_samsung,
            theme="marketplace",
            short_description="Flagship AI smartphone with 200MP camera and S-Pen.",
            description="Samsung Galaxy S24 Ultra featuring Titanium frame, Snapdragon 8 Gen 3, Dynamic AMOLED 2X, and revolutionary Galaxy AI tools.",
            price=Decimal("155000.00"),
            discount_price=Decimal("142000.00"),
            stock=8,
            unit="1 unit",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_fashion = Product.objects.create(
            name="Premium Linen Casual Shirt",
            slug="premium-linen-casual-shirt",
            sku="MKT-FAS-003",
            category=cls.cat_fashion,
            brand=cls.brand_sony,
            theme="marketplace",
            short_description="Breathable 100% pure organic linen summer shirt.",
            description="Breathable, relaxed-fit linen shirt tailored for supreme daily comfort and timeless elegance.",
            price=Decimal("2800.00"),
            discount_price=None,
            stock=30,
            unit="1 piece",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        cls.product_out_of_stock = Product.objects.create(
            name="Rare Collector Vintage Watch",
            slug="rare-collector-vintage-watch",
            sku="MKT-VNT-004",
            category=cls.cat_fashion,
            brand=cls.brand_sony,
            theme="marketplace",
            short_description="Limited edition collectible timepiece.",
            description="Rare vintage chronograph, currently completely out of stock.",
            price=Decimal("50000.00"),
            stock=0,
            unit="1 piece",
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

        # 5. Customer, Staff, & Superuser Users
        cls.customer_user = User.objects.create_user(
            username="marketplace_buyer",
            email="buyer@test.com",
            password="Password123",
            first_name="Rahim",
            last_name="Uddin",
        )

        cls.staff_user = User.objects.create_user(
            username="marketplace_staff",
            email="staff@test.com",
            password="Password123",
            is_staff=True,
        )

        cls.superuser = User.objects.create_superuser(
            username="marketplace_admin",
            email="admin@megamarket.test",
            password="Password123",
        )

        # 6. Reviews for Rating tests
        ProductReview.objects.create(
            product=cls.product_flagship,
            user=cls.customer_user,
            rating=5,
            comment="Outstanding noise cancellation and sound quality! Highly recommended.",
        )
        ProductReview.objects.create(
            product=cls.product_phone,
            user=cls.customer_user,
            rating=4,
            comment="Excellent display and camera performance.",
        )

    def setUp(self):
        self.client = Client()


class MarketplaceThemeActivationAndResolutionTests(BaseMarketplaceThemeTestCase):
    """
    1. Tests for Theme Registry, Activation, Normalization, Preview, and Context Processors.
    """

    def test_marketplace_theme_registry_definition(self):
        """ThemeRegistry holds 'marketplace' with legacy key 'mega_market' and all mappings."""
        theme = theme_registry.get("marketplace", fallback=False)
        self.assertIsNotNone(theme)
        self.assertEqual(theme.id, "marketplace")
        self.assertEqual(theme.legacy_key, "mega_market")
        self.assertEqual(theme_registry.normalize_id("mega_market"), "marketplace")
        self.assertEqual(theme_registry.normalize_id("marketplace"), "marketplace")

        # Template mapping verification
        mapping = theme.template_mapping
        self.assertEqual(mapping.get("header"), "themes/marketplace/header.html")
        self.assertEqual(mapping.get("footer"), "themes/marketplace/footer.html")
        self.assertEqual(mapping.get("home"), "themes/marketplace/home.html")
        self.assertEqual(mapping.get("product_card"), "themes/marketplace/product_card.html")
        self.assertEqual(mapping.get("product_list"), "themes/marketplace/product_list.html")
        self.assertEqual(mapping.get("product_detail"), "themes/marketplace/product_detail.html")

    def test_sitesetting_active_theme_activation(self):
        """SiteSetting active_theme='marketplace' updates and persists correctly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "marketplace"
        setting.save()

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, "marketplace")
        self.assertEqual(setting.get_canonical_theme_id(), "marketplace")

        # Admin activation route sets active flag on ThemeCustomization
        self.client.force_login(self.superuser)
        res = self.client.post(reverse("admin_theme_activate", kwargs={"theme_id": "marketplace"}))
        self.assertEqual(res.status_code, 302)

        cust = ThemeCustomization.get_for_theme("marketplace")
        self.assertIsNotNone(cust)
        self.assertTrue(cust.is_active)

    def test_context_processor_populates_marketplace_theme_variables(self):
        """site_settings_processor accurately injects all marketplace theme variables."""
        factory = RequestFactory()
        req = factory.get("/")
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "marketplace")
        self.assertIn(ctx["CURRENT_THEME_KEY"], ["marketplace", "mega_market"])
        self.assertIsNotNone(ctx["CURRENT_THEME_DATA"])
        self.assertEqual(ctx["CURRENT_THEME_DATA"]["id"], "marketplace")
        self.assertFalse(ctx["IS_THEME_PREVIEW"])

    def test_session_based_theme_preview_for_staff(self):
        """Staff session previewing 'marketplace' isolates context without altering site setting."""
        factory = RequestFactory()
        req = factory.get("/")
        req.user = self.staff_user
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session["admin_preview_theme"] = "marketplace"
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "marketplace")
        self.assertTrue(ctx["IS_THEME_PREVIEW"])

    def test_query_param_preview_isolation(self):
        """Query parameter ?theme=marketplace activates theme preview cleanly."""
        res = self.client.get("/?theme=marketplace")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_theme_id"], "marketplace")


class MarketplaceHeaderAndFooterRenderingTests(BaseMarketplaceThemeTestCase):
    """
    2. Tests for Marketplace Header, Navigation Sub-bar, and Multi-column Footer.
    """

    def test_marketplace_header_announcement_strip_and_branding(self):
        """Header renders top announcement strip, order tracking link, helpline, and branding."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Marketplace Header Container
        self.assertIn("marketplace-header", html)
        self.assertIn("mkt-top-strip", html)

        # Track order link and Helpline
        self.assertIn(reverse("customer_orders"), html)
        self.assertIn("+880 1700-123456", html)

        # Language Switcher
        self.assertIn(reverse("set_language", args=["en"]), html)
        self.assertIn(reverse("set_language", args=["bn"]), html)

    def test_marketplace_search_bar_structure(self):
        """Header renders marketplace search form with category selector prefix and action button."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Search Form, category prefix select, and input
        self.assertIn('action="/product/"', html)
        self.assertIn('name="category"', html)
        self.assertIn('name="q"', html)
        self.assertIn("bi-search", html)

        # Category options in search select
        self.assertIn("electronics-gadgets", html)
        self.assertIn("Electronics &amp; Gadgets", html)

    def test_marketplace_header_account_wishlist_cart_controls(self):
        """Header includes user account dropdown, live wishlist badge, and cart trigger."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Guest auth links / modal triggers
        self.assertIn("bi-person-fill", html)
        self.assertIn("navWishlistBadge", html)
        self.assertIn("navCartBadge", html)
        self.assertIn("cartOffcanvas", html)

    def test_marketplace_navigation_sub_bar_and_links(self):
        """Marketplace navigation sub-bar renders All Categories flyout, Flash Deals, and Best Sellers."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("#flash-deals", html)
        self.assertIn("#official-brands", html)
        self.assertIn("sellerCenterModal", html)
        self.assertIn("downloadAppModal", html)

    def test_marketplace_footer_pillars_and_columns(self):
        """Footer renders 4 trust assurance pillars, multi-columns, payment badges, and copyright."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Marketplace Footer container
        self.assertIn("marketplace-footer", html)

        # 4 Assurance Pillars
        self.assertIn("Nationwide Delivery", html)
        self.assertIn("100% Authentic Products", html)
        self.assertIn("7-Day Easy Returns", html)
        self.assertIn("100% Secure Checkout", html)

        # Contact information & Payment badges
        self.assertIn("support@megamarket.test", html)
        self.assertIn("Tejgaon", html)
        self.assertIn("bKash", html)
        self.assertIn("Cash on Delivery", html)
        self.assertIn("MEGA100", html)


class MarketplaceHomepageLayoutTests(BaseMarketplaceThemeTestCase):
    """
    3. Tests for Marketplace Homepage Layout and Commercial Section Composition.
    """

    def test_homepage_renders_marketplace_home_template(self):
        """Home view loads themes/marketplace/home.html when marketplace theme is active."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/home.html")
        self.assertEqual(res.context["current_theme_id"], "marketplace")

    def test_homepage_hero_split_banner_and_deal_boxes(self):
        """Homepage renders split hero banner carousel and deal of the day highlight boxes."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("marketplaceHeroCarousel", html)
        self.assertIn("Deal of the Day", html)
        self.assertIn("MEGA50", html)

    def test_homepage_category_quick_access_strip(self):
        """Homepage renders quick-access category shortcuts strip."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("mkt-category-strip-card", html)
        self.assertIn("Electronics", html)

    def test_homepage_flash_deals_section_with_countdown(self):
        """Homepage renders flash deals section with ticking countdown elements."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn('id="flash-deals"', html)
        self.assertIn("flashTimerH", html)
        self.assertIn("flashTimerM", html)
        self.assertIn("flashTimerS", html)
        self.assertIn("Sony WH-1000XM5 Wireless Headphones", html)

    def test_homepage_featured_categories_and_brand_storefronts(self):
        """Homepage displays visual category grid and official brand storefronts."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Category tiles & product count
        self.assertIn("mkt-cat-tile", html)

        # Official Brand Stores
        self.assertIn('id="official-brands"', html)
        self.assertIn("Official Store", html)

    def test_homepage_just_for_you_and_trust_pillars(self):
        """Homepage displays multi-tab discovery and bottom trust assurance pillars."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("just-for-you", html)
        self.assertIn("mkt-trust-card", html)


class MarketplaceProductCardAndCatalogTests(BaseMarketplaceThemeTestCase):
    """
    4. Tests for Marketplace Product Card, Product List Layout, Filtering, and Sorting.
    """

    def test_marketplace_product_card_elements(self):
        """Product card renders discount badge, brand tag, title clamp, ratings, and price."""
        res = self.client.get("/product/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Card container & elements
        self.assertIn("marketplace-product-card", html)
        self.assertIn("marketplace-wishlist-btn", html)
        self.assertIn("toggleWishlist", html)
        self.assertIn("marketplace-title", html)
        self.assertIn("Sony WH-1000XM5 Wireless Headphones", html)

        # Pricing and discount
        self.assertIn("34500.00", html)
        self.assertIn("38000.00", html)

        # Quick Add-to-Cart
        self.assertIn("Add to Cart", html)

    def test_product_list_renders_marketplace_catalog_template(self):
        """Product list view dynamically loads themes/marketplace/product_list.html."""
        res = self.client.get("/product/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/product_list.html")
        html = res.content.decode("utf-8")

        # Marketplace catalog header & layout toggle buttons
        self.assertIn("marketplace-catalog-header", html)
        self.assertIn("btnGridView", html)
        self.assertIn("btnListView", html)

        # Filter Sidebar
        self.assertIn("filter-sidebar-card", html)
        self.assertIn("catalogFilterOffcanvas", html)

    def test_catalog_keyword_search_query(self):
        """Search query ?q=Sony returns Sony products and excludes others."""
        res = self.client.get("/product/?q=Sony")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/product_list.html")
        products = list(res.context["products"])

        product_names = [p.name for p in products]
        self.assertIn(self.product_flagship.name, product_names)
        self.assertNotIn(self.product_phone.name, product_names)

        html = res.content.decode("utf-8")
        self.assertIn('Search: "Sony"', html)

    def test_catalog_category_filtering(self):
        """Filtering by category slug narrows product list to that category."""
        res = self.client.get(f"/product/?category={self.cat_electronics.slug}")
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])

        for p in products:
            self.assertEqual(p.category, self.cat_electronics)

        # Direct path /product/category/<slug>/
        res_path = self.client.get(f"/product/category/{self.cat_electronics.slug}/")
        self.assertEqual(res_path.status_code, 200)
        self.assertTemplateUsed(res_path, "themes/marketplace/product_list.html")

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

        # Rating sorting
        res_rating = self.client.get("/product/?sort=rating")
        self.assertEqual(res_rating.status_code, 200)
        products_rating = list(res_rating.context["products"])
        self.assertEqual(products_rating[0].pk, self.product_flagship.pk)

    def test_catalog_in_stock_and_price_range_filter(self):
        """Filters in_stock=1 and min_price/max_price return appropriate items."""
        # in_stock=1 excludes out of stock
        res_stock = self.client.get("/product/?in_stock=1")
        self.assertEqual(res_stock.status_code, 200)
        for p in res_stock.context["products"]:
            self.assertGreater(p.stock, 0)
        p_ids = [p.pk for p in res_stock.context["products"]]
        self.assertNotIn(self.product_out_of_stock.pk, p_ids)

        # price range 30000 - 40000
        res_price = self.client.get("/product/?min_price=30000&max_price=40000")
        self.assertEqual(res_price.status_code, 200)
        p_ids = [p.pk for p in res_price.context["products"]]
        self.assertIn(self.product_flagship.pk, p_ids)
        self.assertNotIn(self.product_fashion.pk, p_ids)


class MarketplaceProductDetailTests(BaseMarketplaceThemeTestCase):
    """
    5. Tests for Marketplace Product Detail View, Image Gallery, Delivery & Services Box, and Tabs.
    """

    def test_product_detail_renders_marketplace_detail_template(self):
        """Product detail dynamically loads themes/marketplace/product_detail.html."""
        res = self.client.get(f"/product/{self.product_flagship.pk}/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/product_detail.html")
        html = res.content.decode("utf-8")

        # Marketplace detail card
        self.assertIn("marketplace-detail-card", html)
        self.assertIn("product-detail-card", html)

    def test_product_detail_image_gallery_and_actions(self):
        """Detail page renders main gallery, thumbnail strip, quantity stepper, and action buttons."""
        res = self.client.get(f"/product/{self.product_flagship.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("mainGalleryBox", html)
        self.assertIn("mkt-thumb-strip", html)
        self.assertIn('name="quantity"', html)
        self.assertIn("toggleWishlist", html)

    def test_marketplace_delivery_assurance_box(self):
        """Detail page renders marketplace Delivery & Services box with rates and guarantees."""
        res = self.client.get(f"/product/{self.product_flagship.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Delivery & Services Box
        self.assertIn("delivery-trust-box", html)
        self.assertIn("Delivery & Services", html)
        self.assertIn("Standard Delivery", html)
        self.assertIn("Inside Dhaka", html)
        self.assertIn("Outside Dhaka", html)
        self.assertIn("Cash on Delivery Available", html)
        self.assertIn("7-Day Easy Return Policy", html)

    def test_product_detail_specifications_and_customer_reviews(self):
        """Detail page renders Specifications table, 5-star review breakdown, and reviews."""
        res = self.client.get(f"/product/{self.product_flagship.pk}/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tabs
        self.assertIn("marketplaceDetailTabs", html)
        self.assertIn("rating-bar-progress", html)
        self.assertIn("Outstanding noise cancellation", html)
        self.assertIn("Rahim", html)


class MarketplaceCartAndWishlistTests(BaseMarketplaceThemeTestCase):
    """
    6. Tests for Cart Functionality and Wishlist Toggle Integration with Marketplace Theme.
    """

    def test_add_to_cart_standard_and_ajax(self):
        """Add to cart works via both standard form submission and AJAX JSON request."""
        # Standard POST
        add_url = reverse("add_to_cart", args=[self.product_flagship.pk])
        res = self.client.post(add_url, {"quantity": 2}, follow=True)
        self.assertEqual(res.status_code, 200)

        # Inspect Cart Detail
        cart_res = self.client.get(reverse("cart_detail"))
        self.assertEqual(cart_res.status_code, 200)
        cart = cart_res.context["cart"]
        self.assertEqual(cart.total_items, 2)

        # AJAX POST
        ajax_res = self.client.post(
            reverse("add_to_cart", args=[self.product_phone.pk]),
            {"quantity": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data.get("success"))

    def test_cart_drawer_endpoint_rendering(self):
        """Cart drawer endpoint returns valid HTML drawer with updated item count."""
        # Add item
        self.client.post(reverse("add_to_cart", args=[self.product_flagship.pk]), {"quantity": 1})

        drawer_res = self.client.get(reverse("cart_drawer"))
        self.assertEqual(drawer_res.status_code, 200)
        drawer_html = drawer_res.content.decode("utf-8")
        self.assertIn("Sony WH-1000XM5 Wireless Headphones", drawer_html)

    def test_wishlist_toggle_authenticated_buyer(self):
        """Customer can toggle item in and out of wishlist via AJAX."""
        self.client.force_login(self.customer_user)
        wishlist_url = reverse("wishlist_toggle", args=[self.product_flagship.pk])

        # 1st toggle: adds to wishlist
        res1 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user=self.customer_user, product=self.product_flagship).exists())

        # 2nd toggle: removes from wishlist
        res2 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(Wishlist.objects.filter(user=self.customer_user, product=self.product_flagship).exists())

    def test_wishlist_unauthenticated_requires_login(self):
        """Anonymous user trying to toggle wishlist receives 401 login_required."""
        wishlist_url = reverse("wishlist_toggle", args=[self.product_flagship.pk])
        res = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertTrue(data.get("login_required"))


class NonMarketplaceThemesFallbackRegressionTests(BaseMarketplaceThemeTestCase):
    """
    7. Tests verifying non-marketplace themes fall back gracefully without regression or leakage.
    """

    def test_pharmacy_theme_activation_and_template_rendering(self):
        """When pharmacy theme is active, it renders its flagship pharmacy templates cleanly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Homepage renders pharmacy home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/pharmacy-healthcare/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("rxUploadModal", html)
        self.assertIn("pharmacy-hero-card", html)

        # Header renders pharmacy header
        self.assertIn("pharmacy-header", html)

        # Product list falls back cleanly to default product/list.html
        res_list = self.client.get("/product/")
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "product/list.html")
        list_html = res_list.content.decode("utf-8")
        # Ensure marketplace catalog header is NOT leaked
        self.assertNotIn("marketplace-catalog-header", list_html)

        # Product detail falls back cleanly to default product/detail.html
        res_detail = self.client.get(f"/product/{self.product_pharma.pk}/")
        self.assertEqual(res_detail.status_code, 200)
        self.assertTemplateUsed(res_detail, "product/detail.html")
        detail_html = res_detail.content.decode("utf-8")
        self.assertNotIn("marketplace-detail-card", detail_html)

    def test_other_canonical_themes_fallback_cleanly(self):
        """Themes without dedicated templates fall back to default templates without 500 errors."""
        themes_to_test = [
            "beauty-skincare",
            "fashion-lifestyle",
            "organic-grocery",
        ]

        setting = SiteSetting.get_settings()
        for th in themes_to_test:
            setting.active_theme = th
            setting.save()

            # Home view
            res_home = self.client.get("/")
            self.assertEqual(res_home.status_code, 200, f"Theme {th} failed on home")
            expected_home = f"themes/{th}/home.html"
            try:
                from django.template.loader import get_template
                get_template(expected_home)
                self.assertTemplateUsed(res_home, expected_home)
            except Exception:
                self.assertTemplateUsed(res_home, "home/index.html")

            # Catalog view
            res_list = self.client.get("/product/")
            self.assertEqual(res_list.status_code, 200, f"Theme {th} failed on catalog")
            expected_list = f"themes/{th}/product_list.html"
            try:
                from django.template.loader import get_template
                get_template(expected_list)
                self.assertTemplateUsed(res_list, expected_list)
            except Exception:
                self.assertTemplateUsed(res_list, "product/list.html")
