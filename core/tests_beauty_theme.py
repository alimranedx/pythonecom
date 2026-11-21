"""
Comprehensive Test Suite for Beauty & Skincare Storefront Theme (beauty-skincare / beauty_cosmetics).

Tests:
1. Beauty Theme Registry, Activation, Normalization, Preview, and Context Processors.
2. Beauty Header, Announcement Bar, Concierge Hotline, Navigation, Mobile Drawer, Modals, and Clean Beauty Footer.
3. Beauty Homepage Layout, Hero Showcase, 4 Clean Beauty Trust Pillars, Category Discovery, Bestsellers, Regimen Builder, and VIP Newsletter.
4. Beauty Product Card, Catalog Listing, Shortcuts Bar, Beauty Filter Sidebar, Keyword Search, and Sorting.
5. Beauty Product Detail View, Studio Gallery, Authenticity Badges, Volume Chips, Clean Beauty Box, Routine Step Indicator, Structured Tabs, and Bundle Module.
6. Cart Functionality (Standard + AJAX), Offcanvas Drawer, and Wishlist Toggle Integration.
7. Cross-Theme Isolation & Fallback Regression (Marketplace, Tech & Electronics, Pharmacy & Healthcare).
"""

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


class BaseBeautyThemeTestCase(TestCase):
    """
    Base test case establishing categories, brands, products, customer & admin users,
    and SiteSetting configured for Beauty & Skincare storefront theme.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Site Settings initialized for Beauty & Skincare theme
        cls.setting = SiteSetting.get_settings()
        cls.setting.site_name = "L'Éclat Beauté Studio"
        cls.setting.active_theme = "beauty-skincare"
        cls.setting.contact_phone = "+880 1711-223344"
        cls.setting.contact_email = "concierge@leclat.test"
        cls.setting.contact_address = "Gulshan Avenue, Road 11, Banani, Dhaka"
        cls.setting.save()

        # 2. Beauty categories
        cls.cat_skincare = Category.objects.create(
            name="Skincare",
            slug="skin-care",
            icon="bi-droplet-half",
            theme="beauty-skincare",
            is_featured=True,
            order=1,
        )
        cls.cat_cleansers = Category.objects.create(
            name="Gentle Cleansers",
            slug="cleansers",
            icon="bi-water",
            theme="beauty-skincare",
            is_featured=True,
            order=2,
        )
        cls.cat_makeup = Category.objects.create(
            name="Makeup & Lips",
            slug="makeup",
            icon="bi-brush",
            theme="beauty-skincare",
            is_featured=True,
            order=3,
        )
        cls.cat_haircare = Category.objects.create(
            name="Haircare",
            slug="hair-care",
            icon="bi-scissors",
            theme="beauty-skincare",
            is_featured=True,
            order=4,
        )

        # Cross-theme categories
        cls.cat_tech = Category.objects.create(
            name="Laptops & Ultrabooks",
            slug="laptops",
            icon="bi-laptop",
            theme="tech-electronics",
            is_featured=False,
            order=10,
        )
        cls.cat_pharmacy = Category.objects.create(
            name="Prescription Medicines",
            slug="prescription-medicines",
            icon="bi-capsule",
            theme="pharmacy_health",
            is_featured=False,
            order=11,
        )
        cls.cat_marketplace = Category.objects.create(
            name="Fashion & Lifestyle",
            slug="fashion-lifestyle",
            icon="bi-bag",
            theme="marketplace",
            is_featured=False,
            order=12,
        )

        # 3. Brands
        cls.brand_ordinary = Brand.objects.create(
            name="The Ordinary",
            slug="the-ordinary",
            theme="beauty-skincare",
        )
        cls.brand_cosrx = Brand.objects.create(
            name="COSRX",
            slug="cosrx",
            theme="beauty-skincare",
        )
        cls.brand_cerave = Brand.objects.create(
            name="CeraVe",
            slug="cerave",
            theme="beauty-skincare",
        )
        cls.brand_tech = Brand.objects.create(
            name="Apple",
            slug="apple",
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

        # 4. Beauty Products
        cls.product_serum = Product.objects.create(
            name="The Ordinary Niacinamide 10% + Zinc 1% Oil Control Serum 30ml",
            slug="the-ordinary-niacinamide-10-zinc-1-serum-30ml",
            category=cls.cat_skincare,
            brand=cls.brand_ordinary,
            theme="beauty-skincare",
            short_description="High-strength vitamin and mineral blemish formula with 10% pure Niacinamide.",
            description="<p>Niacinamide (Vitamin B3) is indicated to reduce the appearance of skin blemishes and congestion. Formulated for all skin types, especially oily and blemish-prone skin.</p>",
            price=Decimal("1250.00"),
            discount_price=Decimal("1050.00"),
            stock=45,
            unit="30ml",
            is_active=True,
            is_featured=True,
            is_flash_sale=True,
        )

        cls.product_toner = Product.objects.create(
            name="COSRX Centella Water Alcohol-Free Soothing Facial Toner 150ml",
            slug="cosrx-centella-water-alcohol-free-toner-150ml",
            category=cls.cat_skincare,
            brand=cls.brand_cosrx,
            theme="beauty-skincare",
            short_description="Gentle calming daily mist toner formulated with Jeju Centella Asiatica leaf water.",
            description="<p>Centella Asiatica leaf water provides calming relief for irritated and redness-prone skin while replenishing moisture levels.</p>",
            price=Decimal("1650.00"),
            discount_price=Decimal("1450.00"),
            stock=30,
            unit="150ml",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_cleanser = Product.objects.create(
            name="CeraVe Hydrating Facial Cleanser with Ceramides 236ml",
            slug="cerave-hydrating-facial-cleanser-236ml",
            category=cls.cat_cleansers,
            brand=cls.brand_cerave,
            theme="beauty-skincare",
            short_description="Gentle hydrating lotion cleanser developed with dermatologists.",
            description="<p>Formulated with 3 essential ceramides and hyaluronic acid to cleanse and hydrate without disrupting the skin barrier.</p>",
            price=Decimal("1850.00"),
            discount_price=None,
            stock=20,
            unit="236ml",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_out_of_stock = Product.objects.create(
            name="Limited Botanical Rosehip Overnight Elixir 50ml",
            slug="limited-botanical-rosehip-overnight-elixir-50ml",
            category=cls.cat_skincare,
            brand=cls.brand_ordinary,
            theme="beauty-skincare",
            short_description="Cold-pressed organic rosehip seed oil for overnight nourishment.",
            description="<p>Rich in linoleic acid and pro-vitamin A. Currently out of stock.</p>",
            price=Decimal("3200.00"),
            stock=0,
            unit="50ml",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        # Cross-theme isolated products
        cls.product_tech = Product.objects.create(
            name="Apple MacBook Pro 16 M3 Max",
            slug="apple-macbook-pro-16-m3-max",
            category=cls.cat_tech,
            brand=cls.brand_tech,
            theme="tech-electronics",
            short_description="Flagship workstation laptop.",
            description="Liquid Retina XDR display with 36GB unified RAM.",
            price=Decimal("399000.00"),
            stock=10,
            unit="1 unit",
            is_active=True,
            is_featured=True,
        )

        cls.product_pharma = Product.objects.create(
            name="Napa Extra 500mg/65mg Paracetamol",
            slug="napa-extra-500mg-paracetamol",
            category=cls.cat_pharmacy,
            brand=cls.brand_pharma,
            theme="pharmacy_health",
            short_description="Fast relief for fever and pain.",
            description="Standard paracetamol by Square Pharmaceuticals.",
            price=Decimal("35.00"),
            stock=500,
            unit="1 strip",
            is_active=True,
            is_featured=True,
        )

        cls.product_mkt = Product.objects.create(
            name="Casual Denim Jacket",
            slug="casual-denim-jacket",
            category=cls.cat_marketplace,
            brand=cls.brand_mkt,
            theme="marketplace",
            short_description="100% Cotton denim jacket.",
            description="Classic blue wash denim jacket.",
            price=Decimal("3500.00"),
            stock=25,
            unit="1 piece",
            is_active=True,
            is_featured=True,
        )

        # 5. Users
        cls.customer_user = User.objects.create_user(
            username="glowqueen",
            email="glow@example.com",
            password="Password123!",
            first_name="Farzana",
            last_name="Karim",
        )
        cls.staff_user = User.objects.create_user(
            username="beauty_staff",
            email="staff@beautystudio.test",
            password="Password123!",
            is_staff=True,
        )
        cls.superuser = User.objects.create_superuser(
            username="beauty_admin",
            email="admin@beautystudio.test",
            password="AdminPassword123!",
        )

        # 6. Product Reviews
        ProductReview.objects.create(
            product=cls.product_serum,
            user=cls.customer_user,
            rating=5,
            comment="Transformed my oily skin within two weeks. My pores look much smaller and smoother!",
        )

    def setUp(self):
        self.client = Client()


class BeautyThemeActivationAndResolutionTests(BaseBeautyThemeTestCase):
    """
    1. Tests for Beauty Theme Registry, Activation, Normalization, Preview, and Context Processors.
    """

    def test_beauty_theme_registry_definition(self):
        """ThemeRegistry holds 'beauty-skincare' with legacy key 'beauty_cosmetics' and template mappings."""
        theme = theme_registry.get("beauty-skincare", fallback=False)
        self.assertIsNotNone(theme)
        self.assertEqual(theme.id, "beauty-skincare")
        self.assertEqual(theme.legacy_key, "beauty_cosmetics")
        self.assertEqual(theme_registry.normalize_id("beauty_cosmetics"), "beauty-skincare")
        self.assertEqual(theme_registry.normalize_id("beauty-skincare"), "beauty-skincare")

        # Template mapping verification
        mapping = theme.template_mapping
        self.assertEqual(mapping.get("header"), "themes/beauty-skincare/header.html")
        self.assertEqual(mapping.get("footer"), "themes/beauty-skincare/footer.html")
        self.assertEqual(mapping.get("home"), "themes/beauty-skincare/home.html")
        self.assertEqual(mapping.get("product_card"), "themes/beauty-skincare/product_card.html")
        self.assertEqual(mapping.get("product_list"), "themes/beauty-skincare/product_list.html")
        self.assertEqual(mapping.get("product_detail"), "themes/beauty-skincare/product_detail.html")

        # Capabilities verification
        capabilities = theme.supported_capabilities
        self.assertIn("shade_swatches", capabilities)
        self.assertIn("skin_type_filter", capabilities)
        self.assertIn("ingredient_list", capabilities)
        self.assertIn("routine_builder", capabilities)

    def test_sitesetting_active_theme_activation(self):
        """SiteSetting active_theme='beauty-skincare' updates and persists correctly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "beauty-skincare"
        setting.save()

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, "beauty-skincare")
        self.assertEqual(setting.get_canonical_theme_id(), "beauty-skincare")

        # Admin activation route sets active flag on ThemeCustomization
        self.client.force_login(self.superuser)
        res = self.client.post(reverse("admin_theme_activate", kwargs={"theme_id": "beauty-skincare"}))
        self.assertEqual(res.status_code, 302)

        cust = ThemeCustomization.get_for_theme("beauty-skincare")
        self.assertIsNotNone(cust)
        self.assertTrue(cust.is_active)

    def test_context_processor_populates_beauty_theme_variables(self):
        """site_settings_processor accurately injects all beauty theme variables."""
        factory = RequestFactory()
        req = factory.get("/")
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "beauty-skincare")
        self.assertIn(ctx["CURRENT_THEME_KEY"], ["beauty-skincare", "beauty_cosmetics"])
        self.assertIsNotNone(ctx["CURRENT_THEME_DATA"])
        self.assertEqual(ctx["CURRENT_THEME_DATA"]["id"], "beauty-skincare")
        self.assertFalse(ctx["IS_THEME_PREVIEW"])

    def test_session_based_theme_preview_for_staff(self):
        """Staff session previewing 'beauty-skincare' isolates context without altering site setting."""
        factory = RequestFactory()
        req = factory.get("/")
        req.user = self.staff_user
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session["admin_preview_theme"] = "beauty-skincare"
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "beauty-skincare")
        self.assertTrue(ctx["IS_THEME_PREVIEW"])

    def test_query_param_preview_isolation(self):
        """Query parameter ?theme=beauty-skincare activates theme preview cleanly."""
        res = self.client.get("/?theme=beauty-skincare")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_theme_id"], "beauty-skincare")


class BeautyHeaderAndFooterRenderingTests(BaseBeautyThemeTestCase):
    """
    2. Tests for Beauty Header, Top Bar, Navigation, Mobile Drawer, Consultation Modal, and 4 Clean Beauty Pillars Footer.
    """

    def test_beauty_header_announcement_and_concierge_bar(self):
        """Header renders luxury samples announcement, consultation hotline, and language switcher."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue(
            "Complimentary Luxury Beauty Samples" in html or "1,500" in html
        )
        self.assertIn("100% Authentic Direct from Brands", html)
        self.assertIn("+880 1711-223344", html)

        # Language Switcher
        self.assertIn(reverse("set_language", args=["en"]), html)
        self.assertIn(reverse("set_language", args=["bn"]), html)

    def test_beauty_header_search_bar_structure(self):
        """Header includes beauty search bar with category prefix and placeholder."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn('action="/product/"', html)
        self.assertIn('name="q"', html)
        self.assertIn("Search serums, sunscreens, moisturizers, lipsticks", html)
        self.assertIn("beauty-btn-pill", html)

    def test_beauty_header_account_wishlist_cart_controls(self):
        """Header contains user controls, badges, and offcanvas cart drawer triggers."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("navWishlistBadge", html)
        self.assertIn("navCartBadge", html)
        self.assertIn("navCartSubtotal", html)
        self.assertTrue("cartOffcanvas" in html or "cartDrawer" in html)

    def test_beauty_header_navigation_and_routine_trigger(self):
        """Header renders specialized beauty departments and Find Your Routine trigger."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("skin-care", html)
        self.assertIn("makeup", html)
        self.assertIn("hair-care", html)
        self.assertIn("Find Your Routine", html)
        self.assertIn("skinConsultationModal", html)

    def test_mobile_beauty_drawer(self):
        """Header includes dedicated mobile beauty drawer #mobileBeautyOffcanvas."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("mobileBeautyOffcanvas", html)
        self.assertIn("beauty-mobile-header", html)

    def test_skin_consultation_modal_elements(self):
        """Skin consultation modal renders skin types, concerns, and routine recommendations."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("skinConsultationModal", html)
        self.assertIn("Dry / Dehydrated", html)
        self.assertIn("Oily / Acne-Prone", html)
        self.assertIn("Combination", html)
        self.assertIn("Sensitive &amp; Red", html)
        self.assertIn("concernHydration", html)
        self.assertIn("routineResultBox", html)

    def test_beauty_footer_assurance_pillars(self):
        """Footer displays the 4 clean beauty assurance pillars."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("100% Authentic &amp; Direct", html)
        self.assertIn("Dermatologically Tested", html)
        self.assertIn("Fresh Batch Guarantee", html)
        self.assertIn("Complimentary Samples", html)

    def test_beauty_footer_columns_and_newsletter(self):
        """Footer displays multi-column layout, contact info, newsletter, and payment chips."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("concierge@leclat.test", html)
        self.assertIn("Gulshan Avenue", html)
        self.assertIn("Inner Glow Circle", html)
        self.assertIn("bKash", html)
        self.assertIn("Cash on Delivery", html)
        self.assertIn("Nagad", html)
        self.assertIn("256-Bit", html)
        self.assertIn("beauty-back-to-top", html)

    def test_bangla_localization(self):
        """Beauty header and footer render proper Bangla copy when requested."""
        session = self.client.session
        session["django_language"] = "bn"
        session.save()

        res = self.client.get("/set-language/bn/", follow=True)
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue(
            "১৫০০" in html or "স্কিনকেয়ার" in html or "ইনার গ্লো সার্কেল" in html
        )


class BeautyHomepageLayoutTests(BaseBeautyThemeTestCase):
    """
    3. Tests for Beauty Homepage Layout, Hero Carousel, 4 Clean Beauty Trust Pillars,
    Category Discovery, Bestsellers, Regimen Builder, and VIP Newsletter.
    """

    def test_homepage_renders_beauty_home_template(self):
        """Home view loads themes/beauty-skincare/home.html when beauty-skincare theme is active."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/beauty-skincare/home.html")
        self.assertEqual(res.context["current_theme_id"], "beauty-skincare")

    def test_homepage_hero_carousel_and_ctas(self):
        """Homepage renders serene editorial beauty hero carousel with CTAs."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("beautyHeroCarousel", html)
        self.assertIn("Radiant Skin, Naturally Yours", html)
        self.assertIn("Explore Collection", html)
        self.assertIn("Build Your Skincare Routine", html)

    def test_homepage_editorial_spotlights(self):
        """Homepage renders Daily Glow Highlight and Complimentary Luxury Sample spotlight cards."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Daily Glow Highlight", html)
        self.assertIn("Complimentary Luxury Sample", html)

    def test_homepage_clean_beauty_trust_pillars(self):
        """Homepage displays the 4 clean beauty trust pillars."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("100% Authentic" in html and ("Certified" in html or "Brand" in html))
        self.assertIn("Dermatologically Approved", html)
        self.assertIn("Fresh Batch Guarantee", html)
        self.assertTrue("Cruelty-Free" in html and "Conscious" in html)

    def test_homepage_category_discovery_tiles(self):
        """Homepage displays curated visual rituals & category discovery tiles."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Curated Rituals", html)
        self.assertTrue(
            "Hydrating Serums" in html or "Gentle Cleansers" in html or "Daily Moisturizers" in html
        )

    def test_homepage_bestsellers_and_fresh_glow(self):
        """Homepage displays Just In Fresh Glow Essentials and Bestsellers & Community Favorites grids."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Fresh Glow Essentials", html)
        self.assertIn("Just In", html)
        self.assertTrue("Bestsellers & Community Favorites" in html or "Bestsellers &amp; Community Favorites" in html)
        self.assertIn("The Ordinary Niacinamide 10% + Zinc 1%", html)

    def test_homepage_editorial_story_block(self):
        """Homepage renders the 'Beauty in Simplicity' editorial conscious skincare block."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Beauty in Simplicity", html)
        self.assertIn("Botanical Bio-Availability", html)
        self.assertTrue("100% Free From Harsh Additives" in html or "Zero Toxic" in html)
        self.assertTrue("Sustainable" in html or "Mindfully Crafted" in html)

    def test_homepage_brand_showcases(self):
        """Homepage displays official beauty brand partner showcases."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("The Ordinary", html)
        self.assertIn("COSRX", html)
        self.assertIn("CeraVe", html)

    def test_homepage_routine_regimen_builder(self):
        """Homepage features the 5-step skincare regimen builder flow."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("routineSection", html)
        self.assertIn("Step 1 Cleanse", html)
        self.assertIn("Step 2 Tone", html)
        self.assertIn("Step 3 Serum", html)
        self.assertIn("Step 4 Moisturize", html)
        self.assertIn("Step 5 Protect", html)

    def test_homepage_vip_newsletter_and_coupon(self):
        """Homepage renders Inner Glow Circle newsletter capture with GLOW10 promo code."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("GLOW10", html)
        self.assertIn("copyBeautyCoupon", html)
        self.assertIn("beautyNewsletterForm", html)


class BeautyProductCardAndCatalogTests(BaseBeautyThemeTestCase):
    """
    4. Tests for Beauty Product Card, Product List Layout, Subcategory Shortcuts, Filter Sidebar, Search, and Sorting.
    """

    def test_beauty_product_card_elements(self):
        """Beauty product card renders refined LUNA aesthetic, brand, title clamp, volume, badges, and bag button."""
        res = self.client.get(reverse("product_list"))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("beauty-product-card", html)
        self.assertIn("beauty-card-img-wrapper", html)
        self.assertIn("THE ORDINARY", html)
        self.assertIn("Niacinamide 10% + Zinc 1%", html)
        self.assertIn("30ml", html)
        self.assertIn("Clean Beauty", html)
        self.assertIn("Derm Tested", html)
        self.assertIn("Add to Bag", html)
        self.assertIn("toggleWishlist", html)

    def test_product_list_renders_beauty_catalog_template(self):
        """Product list view dynamically loads themes/beauty-skincare/product_list.html."""
        res = self.client.get(reverse("product_list"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/beauty-skincare/product_list.html")
        html = res.content.decode("utf-8")

        # Editorial Header & Shortcuts
        self.assertIn("The Skincare & Beauty Atelier", html)
        self.assertIn("beauty-shortcuts-bar", html)
        self.assertIn("All Formulas", html)

        # Filters
        self.assertIn("Skincare Filters", html)
        self.assertIn("Regimen Categories", html)
        self.assertIn("Curated Brands", html)
        self.assertIn("Price Range", html)
        self.assertIn("In Stock Ready to Dispatch", html)
        self.assertIn("Client Ratings", html)

        # Sort & Offcanvas
        self.assertIn("beautySortSelect", html)
        self.assertIn("beautyFilterOffcanvas", html)

    def test_catalog_keyword_search_query(self):
        """Search query ?q=Niacinamide returns Niacinamide serum and excludes toner."""
        res = self.client.get(f"{reverse('product_list')}?q=Niacinamide")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/beauty-skincare/product_list.html")
        products = list(res.context["products"])
        product_names = [p.name for p in products]

        self.assertIn(self.product_serum.name, product_names)
        self.assertNotIn(self.product_toner.name, product_names)

    def test_catalog_category_filtering(self):
        """Filtering by category slug narrows product list strictly to that category."""
        res = self.client.get(f"{reverse('product_list')}?category={self.cat_cleansers.slug}")
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])

        for p in products:
            self.assertEqual(p.category, self.cat_cleansers)

        # Direct path /product/category/<slug>/
        res_path = self.client.get(f"/product/category/{self.cat_cleansers.slug}/")
        self.assertEqual(res_path.status_code, 200)
        self.assertTemplateUsed(res_path, "themes/beauty-skincare/product_list.html")

    def test_catalog_sorting_options(self):
        """Catalog sorting works correctly for price_asc and price_desc."""
        # Price Ascending
        res_asc = self.client.get(f"{reverse('product_list')}?sort=price_asc")
        self.assertEqual(res_asc.status_code, 200)
        prices_asc = [p.price for p in res_asc.context["products"]]
        self.assertEqual(prices_asc, sorted(prices_asc))

        # Price Descending
        res_desc = self.client.get(f"{reverse('product_list')}?sort=price_desc")
        self.assertEqual(res_desc.status_code, 200)
        prices_desc = [p.price for p in res_desc.context["products"]]
        self.assertEqual(prices_desc, sorted(prices_desc, reverse=True))

    def test_catalog_in_stock_and_price_range_filter(self):
        """Filters in_stock=1 and min_price/max_price return appropriate beauty formulas."""
        # in_stock=1 excludes out of stock
        res_stock = self.client.get(f"{reverse('product_list')}?in_stock=1")
        self.assertEqual(res_stock.status_code, 200)
        for p in res_stock.context["products"]:
            self.assertGreater(p.stock, 0)
        p_ids = [p.pk for p in res_stock.context["products"]]
        self.assertNotIn(self.product_out_of_stock.pk, p_ids)

        # price range 1000 - 1500 returns serum (1250) but excludes cleanser (1850)
        res_price = self.client.get(f"{reverse('product_list')}?min_price=1000&max_price=1500")
        self.assertEqual(res_price.status_code, 200)
        p_ids = [p.pk for p in res_price.context["products"]]
        self.assertIn(self.product_serum.pk, p_ids)
        self.assertNotIn(self.product_cleanser.pk, p_ids)

    def test_dynamic_template_resolution_beauty_cosmetics_legacy_key(self):
        """Both list and detail resolve correctly when using legacy theme key beauty_cosmetics."""
        res_list = self.client.get(f"{reverse('product_list')}?theme=beauty_cosmetics")
        self.assertEqual(res_list.status_code, 200)
        html_list = res_list.content.decode("utf-8")
        self.assertIn("The Skincare & Beauty Atelier", html_list)

        res_detail = self.client.get(f"{reverse('product_detail', kwargs={'pk': self.product_serum.pk})}?theme=beauty_cosmetics")
        self.assertEqual(res_detail.status_code, 200)
        html_detail = res_detail.content.decode("utf-8")
        self.assertIn("Clean Beauty Assurance", html_detail)


class BeautyProductDetailTests(BaseBeautyThemeTestCase):
    """
    5. Tests for Beauty Product Detail View, Studio Gallery, Authenticity Badges,
    Clean Beauty Assurance Box, Routine Step Indicator, Structured Tabs, and Routine Bundle Module.
    """

    def test_product_detail_renders_beauty_detail_template(self):
        """Product detail dynamically loads themes/beauty-skincare/product_detail.html."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/beauty-skincare/product_detail.html")
        html = res.content.decode("utf-8")

        self.assertIn("The Ordinary Niacinamide 10% + Zinc 1%", html)
        self.assertIn("The Ordinary", html)

    def test_product_detail_gallery_and_authenticity_badges(self):
        """Product detail displays studio gallery and the 3 authenticity badges."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("beautyGalleryContainer", html)
        self.assertIn("beautyMainImg", html)
        self.assertIn("100% Authentic Direct Import", html)
        self.assertIn("Dermatologically Tested", html)
        self.assertIn("Fresh Batch Guaranteed", html)

    def test_product_detail_volume_chips_and_pricing(self):
        """Product detail renders volume/size chips, pricing, and skin compatibility badge."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("30ml", html)
        self.assertTrue("1050" in html or "1,050" in html)
        self.assertTrue("1250" in html or "1,250" in html)
        self.assertTrue("SAVINGS" in html or "SAVE" in html or "discount" in html.lower())
        self.assertTrue("Skin Compatibility" in html or "Derm Approved" in html or "Sensitive" in html or "All Skin Types" in html)

    def test_product_detail_clean_beauty_assurance_box(self):
        """Product detail renders Clean Beauty Assurance & Client Services Box with advisories."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Clean Beauty Assurance", html)
        self.assertIn("Patch Test Advisory", html)
        self.assertIn("7-Day Return Guarantee", html)
        self.assertIn("Complimentary Deluxe Sample", html)
        self.assertIn("Free Express Shipping", html)

    def test_product_detail_daily_ritual_step_indicator(self):
        """Product detail displays the 5-step Daily Ritual Architecture indicator."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("DAILY RITUAL ARCHITECTURE", html)
        self.assertIn("Step 1", html)
        self.assertIn("Step 2", html)
        self.assertIn("Step 3", html)
        self.assertIn("Step 4", html)
        self.assertIn("Step 5", html)

    def test_product_detail_structured_tabs(self):
        """Product detail renders structured tabs for Formula, Active Ingredients, How to Apply, and Reviews."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tabs
        self.assertTrue("Formula" in html and "Clinical Benefits" in html)
        self.assertIn("Key Active Ingredients", html)
        self.assertTrue("How to Apply" in html and "AM/PM Ritual" in html)
        self.assertIn("Customer Reviews", html)
        self.assertIn("5 Star", html)

        # Review content from setup
        self.assertIn("Farzana", html)
        self.assertIn("Transformed my oily skin", html)

    def test_product_detail_routine_bundle_module(self):
        """Product detail renders 'Complete Your Daily Skincare Routine' bundle module."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_serum.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Complete Your Daily Skincare Routine", html)
        self.assertIn("Add Routine Bundle to Bag", html)


class BeautyCartAndWishlistTests(BaseBeautyThemeTestCase):
    """
    6. Tests for Cart Functionality and Wishlist Toggle Integration with Beauty Theme.
    """

    def test_add_to_cart_standard_and_ajax(self):
        """Add to cart works via both standard form submission and AJAX JSON request."""
        # Standard POST
        add_url = reverse("add_to_cart", args=[self.product_serum.pk])
        res = self.client.post(add_url, {"quantity": 1}, follow=True)
        self.assertEqual(res.status_code, 200)

        # Inspect Cart Detail
        cart_res = self.client.get(reverse("cart_detail"))
        self.assertEqual(cart_res.status_code, 200)
        cart = cart_res.context["cart"]
        self.assertEqual(cart.total_items, 1)

        # AJAX POST
        ajax_res = self.client.post(
            reverse("add_to_cart", args=[self.product_toner.pk]),
            {"quantity": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data.get("success"))

    def test_cart_drawer_rendering_with_beauty_products(self):
        """Cart drawer endpoint returns valid HTML drawer with updated beauty item."""
        self.client.post(reverse("add_to_cart", args=[self.product_serum.pk]), {"quantity": 1})

        drawer_res = self.client.get(reverse("cart_drawer"))
        self.assertEqual(drawer_res.status_code, 200)
        drawer_html = drawer_res.content.decode("utf-8")
        self.assertIn("The Ordinary Niacinamide 10% + Zinc 1%", drawer_html)

    def test_wishlist_toggle_authenticated_customer(self):
        """Customer can toggle beauty product in and out of wishlist via AJAX."""
        self.client.force_login(self.customer_user)
        wishlist_url = reverse("wishlist_toggle", args=[self.product_serum.pk])

        # 1st toggle: adds to wishlist
        res1 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user=self.customer_user, product=self.product_serum).exists())

        # 2nd toggle: removes from wishlist
        res2 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(Wishlist.objects.filter(user=self.customer_user, product=self.product_serum).exists())

    def test_wishlist_unauthenticated_requires_login(self):
        """Anonymous user trying to toggle wishlist receives 401 login_required."""
        wishlist_url = reverse("wishlist_toggle", args=[self.product_serum.pk])
        res = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertTrue(data.get("login_required"))


class CrossThemeIsolationAndFallbackRegressionTests(BaseBeautyThemeTestCase):
    """
    7. Tests verifying marketplace, tech-electronics, and pharmacy-healthcare continue to render cleanly,
    and cross-theme catalog isolation is strictly enforced.
    """

    def test_marketplace_theme_isolation_from_beauty(self):
        """When marketplace theme is active, it renders its marketplace storefront cleanly without beauty elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "marketplace"
        setting.save()

        # Homepage renders marketplace home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("marketplaceHeroCarousel", html)
        self.assertNotIn("beautyHeroCarousel", html)
        self.assertNotIn("skinConsultationModal", html)

        # Header renders marketplace header
        self.assertIn("marketplace-header", html)

        # Product list renders marketplace product list
        res_list = self.client.get(reverse("product_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/marketplace/product_list.html")

    def test_tech_theme_isolation_from_beauty(self):
        """When tech-electronics theme is active, it renders its tech storefront cleanly without beauty elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "tech-electronics"
        setting.save()

        # Homepage renders tech home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("techHeroCarousel", html)
        self.assertNotIn("beautyHeroCarousel", html)
        self.assertNotIn("skinConsultationModal", html)

        # Header renders tech header
        self.assertIn("tech-header", html)

        # Product list renders tech product list
        res_list = self.client.get(reverse("product_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/tech-electronics/product_list.html")

    def test_pharmacy_theme_isolation_from_beauty(self):
        """When pharmacy theme is active, it renders its pharmacy storefront cleanly without beauty elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Homepage renders pharmacy home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/pharmacy-healthcare/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("rxUploadModal", html)
        self.assertNotIn("beautyHeroCarousel", html)
        self.assertNotIn("skinConsultationModal", html)

        # Header renders pharmacy header
        self.assertIn("pharmacy-header", html)

    def test_strict_theme_isolation_cross_theme_404(self):
        """
        Product belonging strictly to pharmacy or tech raises 404 when beauty theme is active.
        Product belonging strictly to beauty raises 404 when pharmacy or tech theme is active.
        """
        # Active theme is beauty-skincare
        setting = SiteSetting.get_settings()
        setting.active_theme = "beauty-skincare"
        setting.save()

        # Pharmacy product in beauty theme raises 404
        res_pharma = self.client.get(f"/product/{self.product_pharma.pk}/")
        self.assertEqual(res_pharma.status_code, 404)

        # Tech product in beauty theme raises 404
        res_tech = self.client.get(f"/product/{self.product_tech.pk}/")
        self.assertEqual(res_tech.status_code, 404)

        # Marketplace product in beauty theme raises 404
        res_mkt = self.client.get(f"/product/{self.product_mkt.pk}/")
        self.assertEqual(res_mkt.status_code, 404)

        # Beauty product in beauty theme is 200 OK
        res_beauty = self.client.get(f"/product/{self.product_serum.pk}/")
        self.assertEqual(res_beauty.status_code, 200)

        # Now switch active theme to pharmacy-healthcare
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Beauty product in pharmacy theme raises 404
        res_beauty_under_pharma = self.client.get(f"/product/{self.product_serum.pk}/")
        self.assertEqual(res_beauty_under_pharma.status_code, 404)

        # Now switch active theme to tech-electronics
        setting.active_theme = "tech-electronics"
        setting.save()

        # Beauty product in tech theme raises 404
        res_beauty_under_tech = self.client.get(f"/product/{self.product_serum.pk}/")
        self.assertEqual(res_beauty_under_tech.status_code, 404)
