"""
Comprehensive Test Suite for Organic Food & Daily Grocery Storefront Theme (organic-grocery / grocery_organic).

Tests:
1. Grocery Theme Registry, Activation, Normalization, Preview, and Context Processors.
2. Grocery Header, Announcement Ribbon, Delivery Slot Modal, Navigation Aisles, Mobile Drawer, and 4 Assurance Pillars Footer.
3. Grocery Homepage Layout, Hero Carousel, 2 Side Spotlights, Trust Pillars, Harvest Category Discovery, Pantry Essentials, Bestsellers, Artisanal Origin Story, Harvest Box Subscription Modal, and Newsletter.
4. Grocery Product Card, Net Weight / Volume Badge, Unit Price Breakdown, Catalog Listing, Shortcuts Bar, Grocery Filter Sidebar, Search, and Sorting.
5. Grocery Product Detail View, Produce Gallery, Purity Badges, Package Size Chips, Harvest Assurance & Delivery Box, Structured Tabs (Nutritional Facts Table), and Pantry Bundle Module.
6. Cart Functionality (Standard + AJAX Stepper), Offcanvas Basket Drawer, and Wishlist Toggle Integration.
7. Cross-Theme Isolation & Fallback Regression (Marketplace, Tech & Electronics, Beauty & Skincare, Pharmacy & Healthcare).
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
from product.templatetags.product_tags import (
    grocery_package_size,
    grocery_unit_price,
    grocery_nutrition_table,
)
from accounts.models import Wishlist

User = get_user_model()


class BaseGroceryThemeTestCase(TestCase):
    """
    Base test case establishing categories, brands, products, customer & admin users,
    and SiteSetting configured for Organic Food & Daily Grocery storefront theme.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Site Settings initialized for Organic Grocery theme
        cls.setting = SiteSetting.get_settings()
        cls.setting.site_name = "Pure Harvest Organic Store"
        cls.setting.active_theme = "organic-grocery"
        cls.setting.contact_phone = "+880 1711-223344"
        cls.setting.contact_email = "harvest@pureharvest.test"
        cls.setting.contact_address = "Farmgate Agro Center, Dhaka"
        cls.setting.save()

        # 2. Grocery categories
        cls.cat_oils = Category.objects.create(
            name="Cold-Pressed Oils & Ghee",
            slug="cold-pressed-mustard-oils",
            icon="bi-droplet-half",
            theme="organic-grocery",
            is_featured=True,
            order=1,
        )
        cls.cat_honey = Category.objects.create(
            name="Sundarbans Raw Wild Honey",
            slug="raw-wild-honey",
            icon="bi-flower2",
            theme="organic-grocery",
            is_featured=True,
            order=2,
        )
        cls.cat_spices = Category.objects.create(
            name="Hand-Pounded Pure Spices",
            slug="whole-ground-spices",
            icon="bi-fire",
            theme="organic-grocery",
            is_featured=True,
            order=3,
        )
        cls.cat_rice = Category.objects.create(
            name="Aromatic Rice & Daal",
            slug="aromatic-rice-grains",
            icon="bi-basket2",
            theme="organic-grocery",
            is_featured=True,
            order=4,
        )

        # Cross-theme categories
        cls.cat_beauty = Category.objects.create(
            name="Skincare & Serums",
            slug="skin-care",
            icon="bi-droplet-half",
            theme="beauty-skincare",
            is_featured=False,
            order=10,
        )
        cls.cat_tech = Category.objects.create(
            name="Laptops & Ultrabooks",
            slug="laptops",
            icon="bi-laptop",
            theme="tech-electronics",
            is_featured=False,
            order=11,
        )
        cls.cat_pharmacy = Category.objects.create(
            name="Prescription Medicines",
            slug="prescription-medicines",
            icon="bi-capsule",
            theme="pharmacy_health",
            is_featured=False,
            order=12,
        )
        cls.cat_marketplace = Category.objects.create(
            name="Fashion & Lifestyle",
            slug="fashion-lifestyle",
            icon="bi-bag",
            theme="marketplace",
            is_featured=False,
            order=13,
        )

        # 3. Brands
        cls.brand_khaas = Brand.objects.create(
            name="Khaas Food",
            slug="khaas-food",
            theme="organic-grocery",
        )
        cls.brand_chaldal = Brand.objects.create(
            name="Chaldal Organic",
            slug="chaldal-organic",
            theme="organic-grocery",
        )
        cls.brand_pran = Brand.objects.create(
            name="PRAN Natural",
            slug="pran-natural",
            theme="organic-grocery",
        )
        cls.brand_beauty = Brand.objects.create(
            name="The Ordinary",
            slug="the-ordinary",
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

        # 4. Grocery Products
        cls.product_mustard = Product.objects.create(
            name="Pure Wood-Ghani Cold Pressed Mustard Oil 1 Litre",
            slug="pure-wood-ghani-cold-pressed-mustard-oil-1-litre",
            category=cls.cat_oils,
            brand=cls.brand_khaas,
            theme="organic-grocery",
            short_description="100% natural cold pressed yellow mustard seed oil from Sirajganj.",
            description="<p>Traditional wood ghani cold-pressed mustard oil with authentic pungent aroma and high natural antioxidants.</p>",
            price=Decimal("280.00"),
            discount_price=Decimal("250.00"),
            stock=50,
            unit="1 Litre",
            is_active=True,
            is_featured=True,
            is_flash_sale=True,
        )

        cls.product_honey = Product.objects.create(
            name="Sundarbans Raw Wild Natural Honey 500 gm",
            slug="sundarbans-raw-wild-natural-honey-500gm",
            category=cls.cat_honey,
            brand=cls.brand_chaldal,
            theme="organic-grocery",
            short_description="Unprocessed raw forest honey gathered by traditional Mouals.",
            description="<p>Natural raw nectar from Sundarbans mangrove forest. Lab tested 100% pure with zero added sugar.</p>",
            price=Decimal("650.00"),
            discount_price=Decimal("590.00"),
            stock=35,
            unit="500 gm",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_rice = Product.objects.create(
            name="Premium Nazirshail Non-Sticky Aromatic Rice 5 Kg",
            slug="premium-nazirshail-non-sticky-aromatic-rice-5kg",
            category=cls.cat_rice,
            brand=cls.brand_pran,
            theme="organic-grocery",
            short_description="Naturally matured Dinajpur aromatic long grain rice.",
            description="<p>High quality aged aromatic rice perfect for daily dining and wholesome deshi recipes.</p>",
            price=Decimal("480.00"),
            discount_price=None,
            stock=40,
            unit="5 Kg",
            is_active=True,
            is_featured=True,
            is_flash_sale=False,
        )

        cls.product_turmeric = Product.objects.create(
            name="Organic Hand-Pounded Sun-Dried Turmeric Powder 250 gm",
            slug="organic-hand-pounded-turmeric-powder-250gm",
            category=cls.cat_spices,
            brand=cls.brand_khaas,
            theme="organic-grocery",
            short_description="Rich in natural curcumin with zero artificial lead chromate color.",
            description="<p>Pure sun-dried organic turmeric rhizomes pulverized using stone mortar.</p>",
            price=Decimal("120.00"),
            discount_price=None,
            stock=60,
            unit="250 gm",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        cls.product_out_of_stock = Product.objects.create(
            name="Organic Grass-Fed Deshi Cow Ghee 500 gm",
            slug="organic-grass-fed-deshi-cow-ghee-500gm",
            category=cls.cat_oils,
            brand=cls.brand_khaas,
            theme="organic-grocery",
            short_description="Pure bilona churned artisanal cow ghee.",
            description="<p>Traditional cultured bilona ghee from indigenous desi cows. Temporarily out of stock.</p>",
            price=Decimal("950.00"),
            stock=0,
            unit="500 gm",
            is_active=True,
            is_featured=False,
            is_flash_sale=False,
        )

        # Cross-theme isolated products
        cls.product_beauty = Product.objects.create(
            name="The Ordinary Niacinamide 10% + Zinc 1% 30ml",
            slug="the-ordinary-niacinamide-10-zinc-1-30ml",
            category=cls.cat_beauty,
            brand=cls.brand_beauty,
            theme="beauty-skincare",
            short_description="High-strength vitamin and mineral blemish formula.",
            description="Purifying facial serum.",
            price=Decimal("1250.00"),
            stock=30,
            unit="30ml",
            is_active=True,
            is_featured=True,
        )

        cls.product_tech = Product.objects.create(
            name="Apple MacBook Pro 16 M3 Max",
            slug="apple-macbook-pro-16-m3-max",
            category=cls.cat_tech,
            brand=cls.brand_tech,
            theme="tech-electronics",
            short_description="Flagship workstation laptop.",
            description="Liquid Retina XDR display.",
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
            username="grocerycustomer",
            email="customer@grocery.test",
            password="Password123!",
            first_name="Rafiq",
            last_name="Islam",
        )
        cls.staff_user = User.objects.create_user(
            username="grocerystaff",
            email="staff@grocery.test",
            password="Password123!",
            is_staff=True,
        )
        cls.superuser = User.objects.create_superuser(
            username="groceryadmin",
            email="admin@grocery.test",
            password="Password123!",
        )

        # 6. Customer Review
        cls.review = ProductReview.objects.create(
            product=cls.product_mustard,
            user=cls.customer_user,
            rating=5,
            comment="Authentic wood-pressed mustard oil! Pungent aroma and rich taste. Excellent quality.",
        )


class GroceryThemeRegistryAndContextTests(BaseGroceryThemeTestCase):
    """
    1. Tests for Theme Registry, Activation, Normalization, Preview, and Context Processors.
    """

    def test_theme_registry_registration_and_mappings(self):
        """Theme registry properly defines organic-grocery and maps all grocery templates."""
        theme = theme_registry.get("organic-grocery")
        self.assertIsNotNone(theme)
        self.assertEqual(theme.id, "organic-grocery")
        self.assertEqual(theme.legacy_key, "grocery_organic")
        self.assertEqual(theme.industry, "Organic Food & Daily Groceries")

        # Template mappings verification
        mapping = theme.template_mapping
        self.assertEqual(mapping.get("layout"), "themes/organic-grocery/base.html")
        self.assertEqual(mapping.get("header"), "themes/organic-grocery/header.html")
        self.assertEqual(mapping.get("footer"), "themes/organic-grocery/footer.html")
        self.assertEqual(mapping.get("home"), "themes/organic-grocery/home.html")
        self.assertEqual(mapping.get("product_card"), "themes/organic-grocery/product_card.html")
        self.assertEqual(mapping.get("product_list"), "themes/organic-grocery/product_list.html")
        self.assertEqual(mapping.get("product_detail"), "themes/organic-grocery/product_detail.html")

        # Capabilities verification
        capabilities = theme.supported_capabilities
        self.assertIn("slot_delivery_selector", capabilities)
        self.assertIn("weight_unit_selector", capabilities)
        self.assertIn("express_1hr_badge", capabilities)
        self.assertIn("freshness_guarantee", capabilities)

    def test_normalization_canonical_and_legacy_keys(self):
        """theme_registry normalizes both 'organic-grocery' and 'grocery_organic' to 'organic-grocery'."""
        self.assertEqual(theme_registry.normalize_id("organic-grocery"), "organic-grocery")
        self.assertEqual(theme_registry.normalize_id("grocery_organic"), "organic-grocery")

    def test_sitesetting_active_theme_activation(self):
        """SiteSetting active_theme='organic-grocery' updates and persists correctly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "organic-grocery"
        setting.save()

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, "organic-grocery")
        self.assertEqual(setting.get_canonical_theme_id(), "organic-grocery")

        # Admin activation route sets active flag on ThemeCustomization
        self.client.force_login(self.superuser)
        res = self.client.post(reverse("admin_theme_activate", kwargs={"theme_id": "organic-grocery"}))
        self.assertEqual(res.status_code, 302)

        cust = ThemeCustomization.get_for_theme("organic-grocery")
        self.assertIsNotNone(cust)
        self.assertTrue(cust.is_active)

    def test_context_processor_populates_grocery_theme_variables(self):
        """site_settings_processor accurately injects all grocery theme variables."""
        factory = RequestFactory()
        req = factory.get("/")
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "organic-grocery")
        self.assertIn(ctx["CURRENT_THEME_KEY"], ["organic-grocery", "grocery_organic"])
        self.assertIsNotNone(ctx["CURRENT_THEME_DATA"])
        self.assertEqual(ctx["CURRENT_THEME_DATA"]["id"], "organic-grocery")
        self.assertFalse(ctx["IS_THEME_PREVIEW"])

    def test_session_based_theme_preview_for_staff(self):
        """Staff session previewing 'organic-grocery' isolates context without altering site setting."""
        factory = RequestFactory()
        req = factory.get("/")
        req.user = self.staff_user
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session["admin_preview_theme"] = "organic-grocery"
        req.session.save()

        ctx = site_settings_processor(req)
        self.assertEqual(ctx["CURRENT_THEME_ID"], "organic-grocery")
        self.assertTrue(ctx["IS_THEME_PREVIEW"])

    def test_query_param_preview_isolation(self):
        """Query parameter ?theme=organic-grocery activates theme preview cleanly."""
        res = self.client.get("/?theme=organic-grocery")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["current_theme_id"], "organic-grocery")


class GroceryHeaderAndFooterRenderingTests(BaseGroceryThemeTestCase):
    """
    2. Tests for Grocery Header, Announcement Ribbon, Navigation Aisles, Delivery Slot Modal, and 4 Assurance Pillars Footer.
    """

    def test_grocery_header_announcement_ribbon(self):
        """Header renders same-day delivery announcement, delivery slot teaser, and customer care hotline."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue(
            "Free Same-Day Delivery" in html or "750" in html
        )
        self.assertTrue("Delivering to" in html or "Select Slot" in html or "deliverySlotModal" in html)
        self.assertIn("+880 1711-223344", html)

        # Language Switcher
        self.assertIn(reverse("set_language", args=["en"]), html)
        self.assertIn(reverse("set_language", args=["bn"]), html)

    def test_grocery_header_search_bar_structure(self):
        """Header includes grocery search bar with category prefix and placeholder."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn('action="/product/"', html)
        self.assertIn('name="q"', html)
        self.assertTrue("mustard oil" in html.lower() or "search" in html.lower())
        self.assertIn("grocery-search-btn", html)

    def test_grocery_header_account_wishlist_cart_controls(self):
        """Header contains user controls, badges, and offcanvas basket drawer triggers."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("navWishlistBadge", html)
        self.assertIn("navCartBadge", html)
        self.assertIn("navCartSubtotal", html)
        self.assertTrue("cartOffcanvas" in html or "cartDrawer" in html)

    def test_grocery_header_navigation_and_aisles(self):
        """Header renders specialized grocery aisles and Delivery Slots trigger."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Browse All Aisles", html)
        self.assertTrue("deliverySlotModal" in html or "Delivery Slots" in html)

    def test_mobile_grocery_drawer(self):
        """Header includes dedicated mobile grocery drawer #mobileGroceryOffcanvas."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("mobileGroceryOffcanvas", html)
        self.assertIn("grocery-mobile-header", html)

    def test_delivery_slot_modal_elements(self):
        """Delivery slot modal renders neighborhood options, date choices, and time slots."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("deliverySlotModal", html)
        self.assertTrue("Dhanmondi" in html or "Gulshan" in html or "Banani" in html or "Uttara" in html)
        self.assertTrue("Today" in html and "Tomorrow" in html)
        self.assertTrue("Morning" in html or "Afternoon" in html or "Evening" in html or "8-11" in html)

    def test_grocery_footer_assurance_pillars(self):
        """Footer displays the 4 fresh food assurance pillars."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("100% Pure" in html and ("Adulteration-Free" in html or "Chemical-Free" in html or "Pure" in html))
        self.assertTrue("Farm-to-Door" in html or "Express" in html or "24h" in html)
        self.assertTrue("Cold-Pressed" in html or "Wood-Milled" in html)
        self.assertTrue("Replacement Guarantee" in html or "Doorstep Replacement" in html)

    def test_grocery_footer_columns_and_newsletter(self):
        """Footer displays multi-column layout, contact info, harvest voucher HARVEST100, and payment chips."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("harvest@pureharvest.test", html)
        self.assertIn("Farmgate", html)
        self.assertIn("HARVEST100", html)
        self.assertIn("bKash", html)
        self.assertIn("Cash on Delivery", html)
        self.assertIn("Nagad", html)
        self.assertTrue("Back to Top" in html or "window.scrollTo" in html)

    def test_bangla_localization(self):
        """Grocery header and footer render proper Bangla copy when requested."""
        session = self.client.session
        session["django_language"] = "bn"
        session.save()

        res = self.client.get("/set-language/bn/", follow=True)
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue(
            "৭৫০" in html or "খাঁটি" in html or "সরিষার তেল" in html or "বাং" in html
        )


class GroceryHomepageLayoutTests(BaseGroceryThemeTestCase):
    """
    3. Tests for Grocery Homepage Layout, Hero Carousel, 2 Side Spotlights, Trust Pillars,
    Harvest Category Discovery, Daily Pantry Essentials, Bestselling Organic Harvest,
    Artisanal Origin Story, Harvest Box Subscription Modal, and Newsletter.
    """

    def test_homepage_renders_grocery_home_template(self):
        """Home view loads themes/organic-grocery/home.html when organic-grocery theme is active."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/organic-grocery/home.html")
        self.assertEqual(res.context["current_theme_id"], "organic-grocery")

    def test_homepage_hero_carousel_and_ctas(self):
        """Homepage renders farm-fresh hero carousel with CTAs."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("groceryHeroCarousel", html)
        self.assertTrue("Farm" in html and "Table" in html)
        self.assertTrue("Shop Farm Harvest" in html or "Shop" in html)
        self.assertTrue("Schedule Delivery" in html or "deliverySlotModal" in html)

    def test_homepage_side_spotlights(self):
        """Homepage renders Daily Farm Fresh Pick and Delivery Slot spotlight cards."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("Daily Farm" in html or "DAILY FARM PICK" in html)
        self.assertTrue("Delivery Slot" in html or "deliverySlotModal" in html)

    def test_homepage_trust_pillars(self):
        """Homepage displays the 4 organic trust pillars."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("100% Pure" in html or "Adulteration-Free" in html)
        self.assertTrue("Cold-Pressed" in html or "Wood-Milled" in html)
        self.assertTrue("Farm-to-Door" in html or "Express" in html)

    def test_homepage_category_discovery_tiles(self):
        """Homepage displays curated harvest category discovery tiles."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("Shop by Harvest" in html or "Category" in html)
        self.assertTrue(
            "Mustard Oil" in html or "Honey" in html or "Spices" in html or "Rice" in html
        )

    def test_homepage_pantry_essentials_and_bestsellers(self):
        """Homepage displays Daily Pantry Essentials and Bestselling Organic Harvest sections."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Daily Pantry Essentials", html)
        self.assertIn("Bestselling Organic Harvest", html)
        self.assertIn("Pure Wood-Ghani Cold Pressed Mustard Oil", html)

    def test_homepage_artisanal_origin_story(self):
        """Homepage renders rural origin narrative and impact stats."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("From Mindful Farmers to Your Table" in html or "Origin Story" in html or "Artisanal" in html)
        self.assertTrue("Sirajganj" in html or "Sundarbans" in html or "Dinajpur" in html)

    def test_homepage_brand_showcases(self):
        """Homepage displays verified organic brand showcases."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("Khaas Food" in html or "Chaldal Organic" in html or "PRAN" in html)

    def test_homepage_harvest_box_subscription_modal(self):
        """Homepage features Fresh Harvest Box Subscription Teaser and modal."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("harvestBoxModal", html)
        self.assertTrue("Harvest Box" in html or "Weekly" in html)

    def test_homepage_newsletter_and_voucher(self):
        """Homepage renders newsletter capture with HARVEST100 promo code."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("HARVEST100", html)


class GroceryProductCardAndCatalogTests(BaseGroceryThemeTestCase):
    """
    4. Tests for Grocery Product Card, Net Weight / Volume Badge, Unit Price Breakdown,
    Product List Layout, Subcategory Shortcuts, Filter Sidebar, Search, and Sorting.
    """

    def test_grocery_product_card_elements(self):
        """Grocery product card renders natural cream canvas, brand, package size, unit price, and stepper."""
        res = self.client.get(reverse("product_list"))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("grocery-product-card", html)
        self.assertIn("grocery-card-img-wrapper", html)
        self.assertIn("KHAAS FOOD", html)
        self.assertIn("Pure Wood-Ghani Cold Pressed Mustard Oil", html)
        self.assertIn("Cold Pressed", html)
        self.assertIn("In Stock - Fresh Batch", html)
        self.assertIn("toggleWishlist", html)
        self.assertIn("grocery-add-basket-form", html)
        self.assertIn("grocery-card-stepper", html)
        self.assertIn("grocery-basket-btn", html)

    def test_product_list_renders_grocery_catalog_template(self):
        """Product list view dynamically loads themes/organic-grocery/product_list.html."""
        res = self.client.get(reverse("product_list"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/organic-grocery/product_list.html")
        html = res.content.decode("utf-8")

        # Harvest Category Header & Shortcuts
        self.assertIn("grocery-shortcuts-bar", html)

        # Filters
        self.assertIn("Package Weight / Size", html)
        self.assertTrue("Organic &amp; Chemical-Free" in html or "Chemical-Free" in html)
        self.assertIn("In Stock Ready to Dispatch", html)

        # Offcanvas & Layout Switchers
        self.assertIn("groceryFilterOffcanvas", html)
        self.assertIn("groceryTableViewBtn", html)

    def test_catalog_keyword_search_query(self):
        """Search query ?q=Mustard returns mustard oil and excludes honey."""
        res = self.client.get(f"{reverse('product_list')}?q=Mustard")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/organic-grocery/product_list.html")
        products = list(res.context["products"])
        product_names = [p.name for p in products]

        self.assertIn(self.product_mustard.name, product_names)
        self.assertNotIn(self.product_honey.name, product_names)

    def test_catalog_category_filtering(self):
        """Filtering by category slug narrows product list strictly to that grocery category."""
        res = self.client.get(f"{reverse('product_list')}?category={self.cat_honey.slug}")
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])

        for p in products:
            self.assertEqual(p.category, self.cat_honey)

        # Direct path /product/category/<slug>/
        res_path = self.client.get(f"/product/category/{self.cat_honey.slug}/")
        self.assertEqual(res_path.status_code, 200)
        self.assertTemplateUsed(res_path, "themes/organic-grocery/product_list.html")

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
        """Filters in_stock=1 and min_price/max_price return appropriate grocery products."""
        # in_stock=1 excludes out of stock ghee
        res_stock = self.client.get(f"{reverse('product_list')}?in_stock=1")
        self.assertEqual(res_stock.status_code, 200)
        for p in res_stock.context["products"]:
            self.assertGreater(p.stock, 0)
        p_ids = [p.pk for p in res_stock.context["products"]]
        self.assertNotIn(self.product_out_of_stock.pk, p_ids)

        # price range 200 - 300 returns mustard oil (280) but excludes honey (650)
        res_price = self.client.get(f"{reverse('product_list')}?min_price=200&max_price=300")
        self.assertEqual(res_price.status_code, 200)
        p_ids = [p.pk for p in res_price.context["products"]]
        self.assertIn(self.product_mustard.pk, p_ids)
        self.assertNotIn(self.product_honey.pk, p_ids)

    def test_dynamic_template_resolution_grocery_organic_legacy_key(self):
        """Both list and detail resolve correctly when using legacy theme key grocery_organic."""
        res_list = self.client.get(f"{reverse('product_list')}?theme=grocery_organic")
        self.assertEqual(res_list.status_code, 200)
        html_list = res_list.content.decode("utf-8")
        self.assertIn("grocery-shortcuts-bar", html_list)

        res_detail = self.client.get(f"{reverse('product_detail', kwargs={'pk': self.product_mustard.pk})}?theme=grocery_organic")
        self.assertEqual(res_detail.status_code, 200)
        html_detail = res_detail.content.decode("utf-8")
        self.assertIn("Organic Harvest Assurance", html_detail)


class GroceryProductDetailTests(BaseGroceryThemeTestCase):
    """
    5. Tests for Grocery Product Detail View, Produce Gallery, Purity Badges,
    Organic Harvest Assurance & Delivery Box, Structured Tabs, Nutrition Table, and Pantry Bundle.
    """

    def test_product_detail_renders_grocery_detail_template(self):
        """Product detail dynamically loads themes/organic-grocery/product_detail.html."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/organic-grocery/product_detail.html")
        html = res.content.decode("utf-8")

        self.assertIn("Pure Wood-Ghani Cold Pressed Mustard Oil", html)
        self.assertIn("Khaas Food", html)

    def test_product_detail_gallery_and_purity_badges(self):
        """Product detail displays produce gallery and the purity verification badges."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("groceryGalleryContainer", html)
        self.assertIn("grocery-gallery-main", html)
        self.assertTrue("100% Adulteration Free" in html or "Adulteration Free" in html)
        self.assertTrue("Lab Tested Purity" in html or "Lab Tested" in html)
        self.assertTrue("Hygienically Packed" in html or "Traditional" in html)

    def test_product_detail_package_size_chips_and_pricing(self):
        """Product detail renders package size/weight selector chips, pricing, and unit breakdown."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertTrue("1 Litre" in html or "1L" in html or "1 Kg" in html)
        self.assertTrue("250" in html)
        self.assertTrue("280" in html)
        self.assertTrue("Add to Grocery Basket" in html)
        self.assertTrue("Express Delivery Checkout" in html or "Express Checkout" in html or "Buy Now" in html)

    def test_product_detail_harvest_assurance_box(self):
        """Product detail renders Organic Harvest Assurance & Delivery Box with origin and slot advisory."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Organic Harvest Assurance", html)
        self.assertTrue("Sirajganj" in html or "Origin" in html or "Verified" in html)
        self.assertTrue("Traditional" in html or "Cold-Pressed" in html or "Wood-Ghani" in html)
        self.assertTrue("100% Purity Guarantee" in html or "Replacement" in html)
        self.assertTrue("Delivery Slot Advisory" in html or "Today" in html or "Slot" in html)

    def test_product_detail_structured_tabs_and_nutrition_table(self):
        """Product detail renders structured tabs for Overview, Nutrition Facts, Storage, and Customer Reviews."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        # Tabs
        self.assertTrue("Nutritional Facts" in html and "Purity Standards" in html)
        self.assertTrue("Storage" in html and "Freshness Guidelines" in html)
        self.assertIn("Customer Reviews", html)

        # Review content from setup
        self.assertIn("Rafiq", html)
        self.assertIn("Authentic wood-pressed mustard oil", html)

    def test_product_detail_frequently_cooked_together_bundle(self):
        """Product detail renders 'Frequently Cooked Together' Kitchen Pantry Bundle."""
        res = self.client.get(reverse("product_detail", kwargs={"pk": self.product_mustard.pk}))
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn("Frequently Cooked Together", html)
        self.assertTrue("Add Pantry Bundle to Basket" in html or "Add Bundle" in html)

    def test_grocery_template_filters(self):
        """Unit test the 3 grocery template filters: package size, unit price, and nutrition table."""
        # 1. grocery_package_size
        size_mustard = grocery_package_size(self.product_mustard)
        self.assertEqual(size_mustard, "1 Litre")

        size_honey = grocery_package_size(self.product_honey)
        self.assertEqual(size_honey, "500 gm")

        size_rice = grocery_package_size(self.product_rice)
        self.assertEqual(size_rice, "5 Kg")

        size_turmeric = grocery_package_size(self.product_turmeric)
        self.assertEqual(size_turmeric, "250 gm")

        # 2. grocery_unit_price
        unit_mustard = grocery_unit_price(self.product_mustard)
        self.assertEqual(unit_mustard, "(৳250/Litre)")

        unit_honey = grocery_unit_price(self.product_honey)
        self.assertEqual(unit_honey, "(৳1180/Kg)")

        unit_rice = grocery_unit_price(self.product_rice)
        self.assertEqual(unit_rice, "(৳96/Kg)")

        # 3. grocery_nutrition_table
        table_html = str(grocery_nutrition_table(self.product_mustard))
        self.assertIn("Nutritional Facts", table_html)
        self.assertIn("Purity & Standard Verification", table_html)
        self.assertIn("Cold Pressed", table_html)
        self.assertIn("Argemone", table_html)


class GroceryCartAndWishlistTests(BaseGroceryThemeTestCase):
    """
    6. Tests for Cart Functionality and Wishlist Toggle Integration with Grocery Theme.
    """

    def test_add_to_basket_standard_and_ajax(self):
        """Add to basket works via both standard form submission and AJAX JSON request."""
        # Standard POST
        add_url = reverse("add_to_cart", args=[self.product_mustard.pk])
        res = self.client.post(add_url, {"quantity": 2}, follow=True)
        self.assertEqual(res.status_code, 200)

        # Inspect Cart Detail
        cart_res = self.client.get(reverse("cart_detail"))
        self.assertEqual(cart_res.status_code, 200)
        cart = cart_res.context["cart"]
        self.assertEqual(cart.total_items, 2)

        # AJAX POST
        ajax_res = self.client.post(
            reverse("add_to_cart", args=[self.product_honey.pk]),
            {"quantity": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(ajax_res.status_code, 200)
        data = ajax_res.json()
        self.assertTrue(data.get("success"))

    def test_cart_drawer_rendering_with_grocery_products(self):
        """Cart drawer endpoint returns valid HTML drawer with updated grocery item."""
        self.client.post(reverse("add_to_cart", args=[self.product_mustard.pk]), {"quantity": 1})

        drawer_res = self.client.get(reverse("cart_drawer"))
        self.assertEqual(drawer_res.status_code, 200)
        drawer_html = drawer_res.content.decode("utf-8")
        self.assertIn("Pure Wood-Ghani Cold Pressed Mustard Oil", drawer_html)

    def test_wishlist_toggle_authenticated_customer(self):
        """Customer can toggle grocery product in and out of wishlist via AJAX."""
        self.client.force_login(self.customer_user)
        wishlist_url = reverse("wishlist_toggle", args=[self.product_mustard.pk])

        # 1st toggle: adds to wishlist
        res1 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(Wishlist.objects.filter(user=self.customer_user, product=self.product_mustard).exists())

        # 2nd toggle: removes from wishlist
        res2 = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(Wishlist.objects.filter(user=self.customer_user, product=self.product_mustard).exists())

    def test_wishlist_unauthenticated_requires_login(self):
        """Anonymous user trying to toggle wishlist receives 401 login_required."""
        wishlist_url = reverse("wishlist_toggle", args=[self.product_mustard.pk])
        res = self.client.get(wishlist_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertTrue(data.get("login_required"))


class CrossThemeIsolationAndFallbackRegressionTests(BaseGroceryThemeTestCase):
    """
    7. Tests verifying marketplace, tech-electronics, beauty-skincare, and pharmacy-healthcare continue to render cleanly,
    and cross-theme catalog isolation is strictly enforced.
    """

    def test_marketplace_theme_isolation_from_grocery(self):
        """When marketplace theme is active, it renders its marketplace storefront cleanly without grocery elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "marketplace"
        setting.save()

        # Homepage renders marketplace home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/marketplace/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("marketplaceHeroCarousel", html)
        self.assertNotIn("groceryHeroCarousel", html)
        self.assertNotIn("deliverySlotModal", html)

        # Header renders marketplace header
        self.assertIn("marketplace-header", html)

        # Product list renders marketplace product list
        res_list = self.client.get(reverse("product_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/marketplace/product_list.html")

    def test_tech_theme_isolation_from_grocery(self):
        """When tech-electronics theme is active, it renders its tech storefront cleanly without grocery elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "tech-electronics"
        setting.save()

        # Homepage renders tech home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/tech-electronics/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("techHeroCarousel", html)
        self.assertNotIn("groceryHeroCarousel", html)
        self.assertNotIn("deliverySlotModal", html)

        # Header renders tech header
        self.assertIn("tech-header", html)

        # Product list renders tech product list
        res_list = self.client.get(reverse("product_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/tech-electronics/product_list.html")

    def test_beauty_theme_isolation_from_grocery(self):
        """When beauty-skincare theme is active, it renders its beauty storefront cleanly without grocery elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "beauty-skincare"
        setting.save()

        # Homepage renders beauty home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/beauty-skincare/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("beautyHeroCarousel", html)
        self.assertNotIn("groceryHeroCarousel", html)
        self.assertNotIn("deliverySlotModal", html)

        # Header renders beauty header
        self.assertIn("beauty-header", html)

        # Product list renders beauty product list
        res_list = self.client.get(reverse("product_list"))
        self.assertEqual(res_list.status_code, 200)
        self.assertTemplateUsed(res_list, "themes/beauty-skincare/product_list.html")

    def test_pharmacy_theme_isolation_from_grocery(self):
        """When pharmacy theme is active, it renders its pharmacy storefront cleanly without grocery elements."""
        setting = SiteSetting.get_settings()
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Homepage renders pharmacy home
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "themes/pharmacy-healthcare/home.html")
        html = res.content.decode("utf-8")
        self.assertIn("rxUploadModal", html)
        self.assertNotIn("groceryHeroCarousel", html)
        self.assertNotIn("deliverySlotModal", html)

        # Header renders pharmacy header
        self.assertIn("pharmacy-header", html)

    def test_strict_theme_isolation_cross_theme_404(self):
        """
        Product belonging strictly to other themes raises 404 when grocery theme is active.
        Product belonging strictly to grocery raises 404 when other themes are active.
        """
        # Active theme is organic-grocery
        setting = SiteSetting.get_settings()
        setting.active_theme = "organic-grocery"
        setting.save()

        # Beauty product in grocery theme raises 404
        res_beauty = self.client.get(f"/product/{self.product_beauty.pk}/")
        self.assertEqual(res_beauty.status_code, 404)

        # Pharmacy product in grocery theme raises 404
        res_pharma = self.client.get(f"/product/{self.product_pharma.pk}/")
        self.assertEqual(res_pharma.status_code, 404)

        # Tech product in grocery theme raises 404
        res_tech = self.client.get(f"/product/{self.product_tech.pk}/")
        self.assertEqual(res_tech.status_code, 404)

        # Marketplace product in grocery theme raises 404
        res_mkt = self.client.get(f"/product/{self.product_mkt.pk}/")
        self.assertEqual(res_mkt.status_code, 404)

        # Grocery product in grocery theme is 200 OK
        res_grocery = self.client.get(f"/product/{self.product_mustard.pk}/")
        self.assertEqual(res_grocery.status_code, 200)

        # Now switch active theme to pharmacy-healthcare
        setting.active_theme = "pharmacy-healthcare"
        setting.save()

        # Grocery product in pharmacy theme raises 404
        res_grocery_under_pharma = self.client.get(f"/product/{self.product_mustard.pk}/")
        self.assertEqual(res_grocery_under_pharma.status_code, 404)

        # Now switch active theme to beauty-skincare
        setting.active_theme = "beauty-skincare"
        setting.save()

        # Grocery product in beauty theme raises 404
        res_grocery_under_beauty = self.client.get(f"/product/{self.product_mustard.pk}/")
        self.assertEqual(res_grocery_under_beauty.status_code, 404)

        # Now switch active theme to tech-electronics
        setting.active_theme = "tech-electronics"
        setting.save()

        # Grocery product in tech theme raises 404
        res_grocery_under_tech = self.client.get(f"/product/{self.product_mustard.pk}/")
        self.assertEqual(res_grocery_under_tech.status_code, 404)


class OrganicPaletteAndBackgroundTests(BaseGroceryThemeTestCase):
    """
    8. Tests verifying the sunlit Natura-inspired organic background and color combination
    tokens across base layout, homepage hero, floating badges, trust strip, and dark mode.
    """

    def test_organic_theme_registry_tokens(self):
        """Organic theme registry exposes sunlit cream, leaf green, and honey gold tokens."""
        theme = theme_registry.get("organic-grocery")
        tokens = theme.design_tokens
        self.assertEqual(tokens.get("primary"), "#1e7a32")
        self.assertEqual(tokens.get("primary_hover"), "#165e26")
        self.assertEqual(tokens.get("primary_light"), "#edf6ea")
        self.assertEqual(tokens.get("accent"), "#f6c431")
        self.assertEqual(tokens.get("hero_gradient_start"), "#faf9f3")
        self.assertEqual(tokens.get("hero_gradient_end"), "#f2f5eb")

    def test_organic_storefront_background_and_natura_layout_markers(self):
        """Base layout and homepage apply warm cream background, forest green/gold CTAs, floating cards, and trust strip."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.content.decode("utf-8")

        self.assertIn('data-store-theme="organic-grocery"', html)
        self.assertIn("#faf9f3", html)
        self.assertIn("#f2f6ee", html)
        self.assertIn("#1e7a32", html)
        self.assertIn("#f6c431", html)
        self.assertIn("#0c160f", html)
        self.assertIn("natura-hero-wrapper", html)
        self.assertIn("natura-float-card", html)
        self.assertIn("natura-trust-strip", html)
        self.assertIn("btn-og-solid", html)
        self.assertIn("btn-og-gold", html)

