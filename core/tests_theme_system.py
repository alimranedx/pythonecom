from decimal import Decimal
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse

from core.theme_registry import theme_registry, ThemeDefinition
from core.themes import (
    THEMES,
    THEME_CHOICES,
    LEGACY_THEME_CHOICES,
    DEFAULT_THEME_KEY,
    DEFAULT_THEME_ID,
    FLAGSHIP_THEME_KEY,
    get_theme,
    get_theme_data,
)
from core.models import SiteSetting, ThemeCustomization
from core.context_processors import site_settings_processor
from rbac.models import Module, Submodule, Permission, Role, UserRole, RolePermission
from product.models import Category, Product


class ThemeRegistryValidationTests(TestCase):
    """
    Tests for the central Theme Registry system:
    - All 6 canonical themes registered with metadata, schemas, templates.
    - Flagship and default theme discovery.
    - Dict-compatibility for backward compatibility (THEMES, get_theme, get_theme_data).
    """

    def setUp(self):
        self.canonical_ids = [
            'pharmacy-healthcare',
            'marketplace',
            'tech-electronics',
            'beauty-skincare',
            'fashion-lifestyle',
            'organic-grocery',
        ]

    def test_all_six_canonical_themes_registered(self):
        """All 6 canonical industry vertical themes are registered in ThemeRegistry."""
        all_themes = theme_registry.get_all()
        registered_ids = [t.id for t in all_themes]

        for cid in self.canonical_ids:
            self.assertIn(cid, registered_ids, f"Theme '{cid}' must be registered.")

        self.assertGreaterEqual(len(all_themes), 6)

    def test_theme_metadata_and_structure_completeness(self):
        """Every canonical theme definition contains complete metadata, tokens, copy, and schemas."""
        required_tokens = [
            'primary', 'primary_hover', 'primary_light', 'accent',
            'text_on_primary', 'hero_gradient_start', 'hero_gradient_end',
            'dark_primary', 'dark_accent', 'button_radius', 'card_radius', 'badge_radius'
        ]
        required_copy_keys = [
            'hero_headline_en', 'hero_headline_bn',
            'hero_tagline_en', 'hero_tagline_bn',
            'hero_badge_en', 'hero_badge_bn',
            'trust_pillars'
        ]
        required_templates = [
            'layout', 'header', 'footer', 'home',
            'product_card', 'product_list', 'product_detail'
        ]

        for cid in self.canonical_ids:
            theme = theme_registry.get(cid, fallback=False)
            self.assertIsNotNone(theme, f"Theme definition '{cid}' must exist.")
            self.assertEqual(theme.id, cid)
            self.assertTrue(bool(theme.legacy_key), f"Theme '{cid}' must define a legacy_key.")
            self.assertTrue(bool(theme.name), f"Theme '{cid}' must define a name.")
            self.assertTrue(bool(theme.description), f"Theme '{cid}' must define a description.")
            self.assertTrue(bool(theme.industry), f"Theme '{cid}' must define an industry.")
            self.assertTrue(bool(theme.benchmark), f"Theme '{cid}' must define a benchmark.")
            self.assertTrue(bool(theme.preview_image_url), f"Theme '{cid}' must define preview_image_url.")

            # Assets
            self.assertTrue(bool(theme.assets.get('logo_url')), f"Theme '{cid}' missing logo_url")
            self.assertTrue(bool(theme.assets.get('logo_dark_url')), f"Theme '{cid}' missing logo_dark_url")
            self.assertTrue(bool(theme.assets.get('favicon_url')), f"Theme '{cid}' missing favicon_url")

            # Design tokens
            for token in required_tokens:
                self.assertIn(token, theme.design_tokens, f"Theme '{cid}' missing token '{token}'")

            # Copywriting tokens
            for copy_key in required_copy_keys:
                self.assertIn(copy_key, theme.copywriting, f"Theme '{cid}' missing copywriting '{copy_key}'")

            # Trust pillars: exactly 4 items
            pillars = theme.copywriting.get('trust_pillars', [])
            self.assertEqual(len(pillars), 4, f"Theme '{cid}' must have 4 trust pillars")
            for pillar in pillars:
                self.assertIn('icon', pillar)
                self.assertIn('title_en', pillar)
                self.assertIn('title_bn', pillar)
                self.assertIn('desc_en', pillar)
                self.assertIn('desc_bn', pillar)

            # Capabilities: non-empty list
            self.assertTrue(len(theme.supported_capabilities) > 0, f"Theme '{cid}' must declare capabilities")

            # Template mapping
            for tmpl in required_templates:
                self.assertIn(tmpl, theme.template_mapping, f"Theme '{cid}' missing template mapping '{tmpl}'")

            # Customization schema: sections with typed settings
            schema = theme.customization_schema
            self.assertTrue(bool(schema), f"Theme '{cid}' must define customization_schema")
            for sec_name, section in schema.items():
                self.assertIn('title', section, f"Section '{sec_name}' in theme '{cid}' missing title")
                self.assertIn('settings', section, f"Section '{sec_name}' in theme '{cid}' missing settings list")
                for setting in section['settings']:
                    self.assertIn('key', setting)
                    self.assertIn('label', setting)
                    self.assertIn('type', setting)
                    self.assertIn('default', setting)

    def test_flagship_and_default_theme_identification(self):
        """Pharmacy & Healthcare is designated as the flagship and primary default theme."""
        self.assertEqual(theme_registry.flagship_id, 'pharmacy-healthcare')
        self.assertEqual(theme_registry.default_theme_id, 'pharmacy-healthcare')
        self.assertEqual(FLAGSHIP_THEME_KEY, 'pharmacy-healthcare')
        self.assertEqual(DEFAULT_THEME_ID, 'pharmacy-healthcare')

        pharmacy = theme_registry.get('pharmacy-healthcare')
        self.assertTrue(pharmacy.is_flagship)

        for cid in self.canonical_ids:
            if cid != 'pharmacy-healthcare':
                t = theme_registry.get(cid)
                self.assertFalse(t.is_flagship, f"Theme '{cid}' should not be marked as flagship.")

    def test_themes_dict_backward_compatibility(self):
        """THEMES export provides backward compatibility supporting both canonical IDs and legacy keys."""
        self.assertEqual(len(THEMES), len(self.canonical_ids))

        # Can query by canonical ID
        self.assertEqual(THEMES['pharmacy-healthcare'].id, 'pharmacy-healthcare')
        self.assertEqual(THEMES['marketplace'].id, 'marketplace')
        self.assertEqual(THEMES['tech-electronics'].id, 'tech-electronics')

        # Can query by legacy key
        self.assertEqual(THEMES['pharmacy_health'].id, 'pharmacy-healthcare')
        self.assertEqual(THEMES['mega_market'].id, 'marketplace')
        self.assertEqual(THEMES['tech_gadgets'].id, 'tech-electronics')
        self.assertEqual(THEMES['beauty_cosmetics'].id, 'beauty-skincare')
        self.assertEqual(THEMES['fashion_lifestyle'].id, 'fashion-lifestyle')
        self.assertEqual(THEMES['grocery_organic'].id, 'organic-grocery')

        # Membership testing
        self.assertIn('pharmacy-healthcare', THEMES)
        self.assertIn('pharmacy_health', THEMES)
        self.assertIn('marketplace', THEMES)
        self.assertIn('mega_market', THEMES)
        self.assertNotIn('non_existent_theme_key', THEMES)

    def test_get_theme_and_get_theme_data(self):
        """get_theme and get_theme_data function properly across languages and keys."""
        # get_theme
        theme = get_theme('mega_market')
        self.assertEqual(theme['id'], 'marketplace')

        # get_theme_data English
        data_en = get_theme_data('pharmacy-healthcare', is_bangla=False)
        self.assertIn('Certified Genuine Medicines', data_en['hero_headline'])
        self.assertIn('Model Pharmacy', data_en['trust_pillars'][0]['title'])

        # get_theme_data Bangla
        data_bn = get_theme_data('pharmacy-healthcare', is_bangla=True)
        self.assertIn('১০০% আসল ও রেজিস্টার্ড ওষুধ', data_bn['hero_headline'])
        self.assertIn('মডেল ফার্মেসি', data_bn['trust_pillars'][0]['title'])


class ThemeNormalizationAndLegacyKeyTests(TestCase):
    """
    Tests for normalization of theme identifiers and bidirectional legacy key compatibility.
    """

    def test_legacy_key_normalization_all_pairs(self):
        """All 6 legacy keys normalize cleanly to their canonical counterparts."""
        legacy_to_canonical = {
            'pharmacy_health': 'pharmacy-healthcare',
            'mega_market': 'marketplace',
            'tech_gadgets': 'tech-electronics',
            'beauty_cosmetics': 'beauty-skincare',
            'fashion_lifestyle': 'fashion-lifestyle',
            'grocery_organic': 'organic-grocery',
        }
        for legacy, canonical in legacy_to_canonical.items():
            self.assertEqual(
                theme_registry.normalize_id(legacy),
                canonical,
                f"Legacy key '{legacy}' should normalize to '{canonical}'"
            )

    def test_canonical_id_normalization_identity(self):
        """Canonical IDs normalize directly to themselves."""
        canonical_ids = [
            'pharmacy-healthcare',
            'marketplace',
            'tech-electronics',
            'beauty-skincare',
            'fashion-lifestyle',
            'organic-grocery',
        ]
        for cid in canonical_ids:
            self.assertEqual(theme_registry.normalize_id(cid), cid)

    def test_hyphen_and_underscore_variations(self):
        """Registry robustly handles hyphenation and underscore variants."""
        self.assertEqual(theme_registry.normalize_id('pharmacy_healthcare'), 'pharmacy-healthcare')
        self.assertEqual(theme_registry.normalize_id('tech_electronics'), 'tech-electronics')
        self.assertEqual(theme_registry.normalize_id('beauty_skincare'), 'beauty-skincare')
        self.assertEqual(theme_registry.normalize_id('organic_grocery'), 'organic-grocery')
        self.assertEqual(theme_registry.normalize_id('mega-market'), 'marketplace')
        self.assertEqual(theme_registry.normalize_id('tech-gadgets'), 'tech-electronics')

    def test_casing_and_whitespace_insensitivity(self):
        """Registry handles uppercase, mixed case, and surrounding whitespace gracefully."""
        self.assertEqual(theme_registry.normalize_id('  Mega_Market  '), 'marketplace')
        self.assertEqual(theme_registry.normalize_id('PHARMACY-HEALTHCARE'), 'pharmacy-healthcare')
        self.assertEqual(theme_registry.normalize_id('Tech_Gadgets'), 'tech-electronics')

    def test_get_legacy_key(self):
        """get_legacy_key translates canonical theme IDs to their original keys."""
        self.assertEqual(theme_registry.get_legacy_key('marketplace'), 'mega_market')
        self.assertEqual(theme_registry.get_legacy_key('tech-electronics'), 'tech_gadgets')
        self.assertEqual(theme_registry.get_legacy_key('beauty-skincare'), 'beauty_cosmetics')
        self.assertEqual(theme_registry.get_legacy_key('fashion-lifestyle'), 'fashion_lifestyle')
        self.assertEqual(theme_registry.get_legacy_key('organic-grocery'), 'grocery_organic')
        self.assertEqual(theme_registry.get_legacy_key('pharmacy-healthcare'), 'pharmacy_health')

    def test_is_valid(self):
        """is_valid correctly validates canonical IDs and legacy keys, rejecting unknowns."""
        self.assertTrue(theme_registry.is_valid('pharmacy-healthcare'))
        self.assertTrue(theme_registry.is_valid('pharmacy_health'))
        self.assertTrue(theme_registry.is_valid('marketplace'))
        self.assertTrue(theme_registry.is_valid('mega_market'))
        self.assertFalse(theme_registry.is_valid('unknown_theme_123'))
        self.assertFalse(theme_registry.is_valid(''))
        self.assertFalse(theme_registry.is_valid(None))


class ThemeCustomizationModelTests(TestCase):
    """
    Tests for ThemeCustomization model:
    - Creation and persistence per canonical theme_id.
    - get_effective_config(): loading defaults from schema and merging settings_data.
    - reset_to_defaults(): clearing settings_data and custom_css.
    - Isolation between different themes.
    - get_for_theme class method.
    """

    def test_customization_creation_and_defaults(self):
        """Creating a ThemeCustomization loads default schema configuration."""
        cust = ThemeCustomization.objects.create(theme_id='pharmacy-healthcare')
        config = cust.get_effective_config()
        self.assertIsInstance(config, dict)
        # Verify schema default keys exist in effective config
        self.assertIn('show_prescription_cta', config)
        self.assertTrue(config['show_prescription_cta'])
        self.assertIn('show_cold_chain_banner', config)

    def test_effective_config_merges_custom_settings(self):
        """Custom settings in settings_data take precedence over schema defaults."""
        cust = ThemeCustomization.objects.create(
            theme_id='pharmacy-healthcare',
            settings_data={
                'show_prescription_cta': False,
                'custom_badge_text': 'Verified by Doctor',
            }
        )
        config = cust.get_effective_config()
        # Overridden value
        self.assertFalse(config['show_prescription_cta'])
        self.assertEqual(config['custom_badge_text'], 'Verified by Doctor')
        # Preserved schema default
        self.assertIn('show_cold_chain_banner', config)
        self.assertTrue(config['show_cold_chain_banner'])

    def test_reset_to_defaults(self):
        """reset_to_defaults clears settings_data and custom_css and restores defaults."""
        cust = ThemeCustomization.objects.create(
            theme_id='tech-electronics',
            settings_data={'show_emi_calculator_link': False, 'custom_accent': '#ff0000'},
            custom_css='body { background-color: #000; }'
        )
        self.assertEqual(cust.custom_css, 'body { background-color: #000; }')

        restored_config = cust.reset_to_defaults()
        cust.refresh_from_db()

        self.assertEqual(cust.settings_data, {})
        self.assertEqual(cust.custom_css, "")
        # Effective config is restored to schema defaults
        self.assertIn('show_emi_calculator_link', restored_config)
        self.assertTrue(restored_config.get('show_emi_calculator_link'))

    def test_get_for_theme_helper_normalizes_id(self):
        """ThemeCustomization.get_for_theme normalizes legacy keys and retrieves or creates cleanly."""
        cust1 = ThemeCustomization.get_for_theme('mega_market')
        self.assertEqual(cust1.theme_id, 'marketplace')

        cust2 = ThemeCustomization.get_for_theme('marketplace')
        self.assertEqual(cust1.pk, cust2.pk)

    def test_isolation_between_themes(self):
        """Customizing one theme does not alter another theme's configuration."""
        cust_pharma = ThemeCustomization.objects.create(
            theme_id='pharmacy-healthcare',
            settings_data={'show_prescription_uploader': False}
        )
        cust_market = ThemeCustomization.objects.create(
            theme_id='marketplace',
            settings_data={'show_mega_menu': False}
        )

        cust_pharma.reset_to_defaults()
        cust_market.refresh_from_db()

        # Market customization is untouched
        self.assertEqual(cust_market.settings_data, {'show_mega_menu': False})
        self.assertFalse(cust_market.get_effective_config().get('show_mega_menu'))


class ThemeActivationTests(TestCase):
    """
    Tests for theme activation:
    - Persistence in SiteSetting.active_theme.
    - Synchronous updating of ThemeCustomization.is_active status.
    - Transactional safety and invalid theme rejection.
    """

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_theme_tester',
            email='admin_theme@test.com',
            password='Password123'
        )

    def test_sitesetting_active_theme_persistence(self):
        """SiteSetting active_theme updates and persists correctly."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'tech-electronics'
        setting.save()

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, 'tech-electronics')
        self.assertEqual(setting.get_canonical_theme_id(), 'tech-electronics')

    def test_admin_theme_activate_view_transactional(self):
        """Activating a theme via admin panel updates SiteSetting and manages active flags."""
        self.client.force_login(self.superuser)

        # 1. Activate 'tech-electronics'
        res1 = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'tech-electronics'}))
        self.assertEqual(res1.status_code, 302)

        setting = SiteSetting.get_settings()
        self.assertEqual(setting.active_theme, 'tech-electronics')

        tech_cust = ThemeCustomization.objects.filter(theme_id='tech-electronics').first()
        self.assertIsNotNone(tech_cust)
        self.assertTrue(tech_cust.is_active)

        # 2. Activate 'organic-grocery'
        res2 = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'organic-grocery'}))
        self.assertEqual(res2.status_code, 302)

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, 'organic-grocery')

        grocery_cust = ThemeCustomization.objects.filter(theme_id='organic-grocery').first()
        self.assertIsNotNone(grocery_cust)
        self.assertTrue(grocery_cust.is_active)

        # Previous theme customization is now inactive
        tech_cust.refresh_from_db()
        self.assertFalse(tech_cust.is_active)

    def test_admin_theme_activate_via_legacy_key(self):
        """Activating via legacy key normalizes and saves canonical ID."""
        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'mega_market'}))
        self.assertEqual(res.status_code, 302)

        setting = SiteSetting.get_settings()
        self.assertEqual(setting.active_theme, 'marketplace')

    def test_admin_theme_activate_invalid_theme_rejected(self):
        """Attempting to activate an invalid theme ID is rejected without changing active theme."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'pharmacy-healthcare'
        setting.save()

        self.client.force_login(self.superuser)
        res = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'invalid_theme_xyz'}))
        self.assertEqual(res.status_code, 302)

        setting.refresh_from_db()
        self.assertEqual(setting.active_theme, 'pharmacy-healthcare')


class ThemePreviewSystemTests(TestCase):
    """
    Tests for theme preview system:
    - Session-based preview mode for staff users.
    - Strict preview isolation from regular non-staff customers.
    - Exit preview functionality.
    - Visual preview top bar rendering in base.html.
    """

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff_previewer',
            email='staff@test.com',
            password='Password123',
            is_staff=True
        )
        self.customer_user = User.objects.create_user(
            username='customer_previewer',
            email='customer@test.com',
            password='Password123',
            is_staff=False
        )
        # Ensure base active theme is pharmacy-healthcare
        setting = SiteSetting.get_settings()
        setting.active_theme = 'pharmacy-healthcare'
        setting.save()

    def test_staff_session_preview_activation_and_rendering(self):
        """Staff user can start previewing a theme, seeing preview context and banner."""
        self.client.force_login(self.staff_user)

        # Initiate preview for 'fashion-lifestyle'
        preview_url = reverse('admin_theme_preview', kwargs={'theme_id': 'fashion-lifestyle'})
        res = self.client.get(preview_url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.client.session.get('admin_preview_theme'), 'fashion-lifestyle')

        # Load storefront root '/'
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertTrue(res_home.context['IS_THEME_PREVIEW'])
        self.assertEqual(res_home.context['CURRENT_THEME_ID'], 'fashion-lifestyle')

        # Verify preview banner rendered in HTML
        content = res_home.content.decode('utf-8')
        self.assertIn('Previewing Theme:', content)
        self.assertIn('Fashion &amp; Lifestyle', content)
        self.assertIn('Exit Preview', content)
        self.assertIn('Isolated from live customers', content)

    def test_preview_isolation_from_non_staff_users(self):
        """Non-staff customers cannot trigger preview mode or view staff preview sessions."""
        self.client.force_login(self.customer_user)

        # Attempt to access preview endpoint as customer
        preview_url = reverse('admin_theme_preview', kwargs={'theme_id': 'tech-electronics'})
        res = self.client.get(preview_url)
        # Customer should be redirected away without session modification
        self.assertEqual(res.status_code, 302)
        self.assertIsNone(self.client.session.get('admin_preview_theme'))

        # Customer storefront loads live active theme with IS_THEME_PREVIEW False
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertFalse(res_home.context['IS_THEME_PREVIEW'])
        self.assertEqual(res_home.context['CURRENT_THEME_ID'], 'pharmacy-healthcare')
        self.assertNotIn('Previewing Theme:', res_home.content.decode('utf-8'))

    def test_exit_preview(self):
        """Calling admin_theme_exit_preview clears preview session and restores live theme."""
        self.client.force_login(self.staff_user)

        # Start preview
        self.client.get(reverse('admin_theme_preview', kwargs={'theme_id': 'organic-grocery'}))
        self.assertEqual(self.client.session.get('admin_preview_theme'), 'organic-grocery')

        # Exit preview
        res_exit = self.client.get(reverse('admin_theme_exit_preview'))
        self.assertEqual(res_exit.status_code, 302)
        self.assertNotIn('admin_preview_theme', self.client.session)

        # Storefront reverts to live active theme
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertFalse(res_home.context['IS_THEME_PREVIEW'])
        self.assertEqual(res_home.context['CURRENT_THEME_ID'], 'pharmacy-healthcare')

    def test_query_parameter_preview_for_staff(self):
        """Staff user can preview via ?theme= query parameter."""
        self.client.force_login(self.staff_user)
        res = self.client.get('/?theme=beauty-skincare')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['IS_THEME_PREVIEW'])
        self.assertEqual(res.context['CURRENT_THEME_ID'], 'beauty-skincare')


class StoreBrandingPreservationTests(TestCase):
    """
    Tests ensuring store-wide branding (store name, logo, contacts, social links, about copy)
    is cleanly preserved across theme switches, theme customizations, and resets.
    """

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_branding_tester',
            email='branding@test.com',
            password='Password123'
        )
        self.setting = SiteSetting.get_settings()
        self.setting.site_name = "Apex Superstore Bangladesh"
        self.setting.site_tagline = "Premier Online Shopping Destination"
        self.setting.contact_phone = "+880 1711-998877"
        self.setting.contact_email = "support@apexsuperstore.com"
        self.setting.contact_address = "Road 11, Banani, Dhaka-1213"
        self.setting.about_text_en = "Leading national retailer founded in 2020."
        self.setting.social_facebook = "https://facebook.com/apexsuperstore"
        self.setting.save()

    def test_branding_preserved_across_theme_activations(self):
        """Theme activations never overwrite or clear custom store branding fields."""
        self.client.force_login(self.superuser)

        # Switch to marketplace
        self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'marketplace'}))
        # Switch to tech-electronics
        self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'tech-electronics'}))
        # Switch to organic-grocery
        self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'organic-grocery'}))

        self.setting.refresh_from_db()
        self.assertEqual(self.setting.site_name, "Apex Superstore Bangladesh")
        self.assertEqual(self.setting.site_tagline, "Premier Online Shopping Destination")
        self.assertEqual(self.setting.contact_phone, "+880 1711-998877")
        self.assertEqual(self.setting.contact_email, "support@apexsuperstore.com")
        self.assertEqual(self.setting.contact_address, "Road 11, Banani, Dhaka-1213")
        self.assertEqual(self.setting.about_text_en, "Leading national retailer founded in 2020.")
        self.assertEqual(self.setting.social_facebook, "https://facebook.com/apexsuperstore")

    def test_branding_preserved_after_customization_and_reset(self):
        """Resetting a theme customization to defaults does NOT affect store branding."""
        self.client.force_login(self.superuser)

        # Customize organic-grocery
        cust = ThemeCustomization.get_for_theme('organic-grocery')
        cust.settings_data = {'show_slot_time_picker': False}
        cust.custom_css = '/* custom grocery style */'
        cust.save()

        # Reset customization via admin view
        res = self.client.post(reverse('admin_theme_reset_customization', kwargs={'theme_id': 'organic-grocery'}))
        self.assertEqual(res.status_code, 302)

        # Verify branding in SiteSetting is untouched
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.site_name, "Apex Superstore Bangladesh")
        self.assertEqual(self.setting.contact_phone, "+880 1711-998877")
        self.assertEqual(self.setting.contact_email, "support@apexsuperstore.com")

    def test_effective_site_name_and_theme_vector_assets(self):
        """Custom site_name overrides generic theme names, but theme logos resolve per theme."""
        # Custom site_name is returned regardless of theme
        self.assertEqual(self.setting.get_effective_site_name('marketplace'), "Apex Superstore Bangladesh")
        self.assertEqual(self.setting.get_effective_site_name('pharmacy-healthcare'), "Apex Superstore Bangladesh")

        # But dedicated vector logo SVGs are theme-specific
        pharma_logo = self.setting.get_brand_logo_url('pharmacy-healthcare')
        market_logo = self.setting.get_brand_logo_url('marketplace')
        self.assertIn('pharmacy_health', pharma_logo)
        self.assertIn('mega_market', market_logo)
        self.assertNotEqual(pharma_logo, market_logo)


class ThemeRBACAndPermissionsTests(TestCase):
    """
    Tests for RBAC security:
    - Superuser full access.
    - Staff user with 'settings.themes.view' can inspect theme manager.
    - Staff user without 'settings.themes.edit' cannot activate, customize, or reset themes.
    - Non-staff and anonymous users are blocked or redirected.
    """

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='rbac_super_admin',
            email='super@test.com',
            password='Password123'
        )

        # RBAC structure
        self.mod, _ = Module.objects.update_or_create(
            code='settings',
            defaults={'name': 'Settings', 'order': 5}
        )
        self.sub, _ = Submodule.objects.update_or_create(
            code='settings.themes',
            defaults={
                'module': self.mod,
                'name': 'Theme Management',
                'url_name': 'admin_theme_manager',
                'order': 3
            }
        )
        self.p_view, _ = Permission.objects.update_or_create(
            code='settings.themes.view',
            defaults={'submodule': self.sub, 'action': 'view', 'name': 'View Themes'}
        )
        self.p_edit, _ = Permission.objects.update_or_create(
            code='settings.themes.edit',
            defaults={'submodule': self.sub, 'action': 'edit', 'name': 'Edit / Activate Themes'}
        )

        # View-only staff user
        self.staff_viewer = User.objects.create_user(
            username='staff_theme_viewer',
            email='viewer@test.com',
            password='Password123',
            is_staff=True
        )
        self.role_viewer = Role.objects.create(name='Theme Viewer')
        RolePermission.objects.create(role=self.role_viewer, permission=self.p_view)
        UserRole.objects.create(user=self.staff_viewer, role=self.role_viewer)

        # Staff user with no permissions
        self.staff_noperm = User.objects.create_user(
            username='staff_theme_noperm',
            email='noperm@test.com',
            password='Password123',
            is_staff=True
        )

    def test_superuser_has_full_access(self):
        """Superuser has unrestricted access to all theme manager operations."""
        self.client.force_login(self.superuser)

        res_mgr = self.client.get(reverse('admin_theme_manager'))
        self.assertEqual(res_mgr.status_code, 200)

        res_act = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'pharmacy-healthcare'}))
        self.assertEqual(res_act.status_code, 302)

        res_cust = self.client.get(reverse('admin_theme_customize', kwargs={'theme_id': 'pharmacy-healthcare'}))
        self.assertEqual(res_cust.status_code, 200)

    def test_staff_without_view_permission_forbidden(self):
        """Staff member without 'settings.themes.view' is denied access (403 Forbidden)."""
        self.client.force_login(self.staff_noperm)
        res = self.client.get(reverse('admin_theme_manager'))
        self.assertEqual(res.status_code, 403)

    def test_staff_with_view_only_cannot_activate_or_customize(self):
        """Staff with view-only permission can view manager but is blocked from activate/customize."""
        self.client.force_login(self.staff_viewer)

        # Can view
        res_view = self.client.get(reverse('admin_theme_manager'))
        self.assertEqual(res_view.status_code, 200)

        # Cannot activate (403)
        res_act = self.client.post(reverse('admin_theme_activate', kwargs={'theme_id': 'marketplace'}))
        self.assertEqual(res_act.status_code, 403)

        # Cannot customize (403)
        res_cust = self.client.get(reverse('admin_theme_customize', kwargs={'theme_id': 'marketplace'}))
        self.assertEqual(res_cust.status_code, 403)

        # Cannot reset (403)
        res_reset = self.client.post(reverse('admin_theme_reset_customization', kwargs={'theme_id': 'marketplace'}))
        self.assertEqual(res_reset.status_code, 403)

    def test_anonymous_user_redirected_to_admin_login(self):
        """Anonymous user trying to access theme manager is redirected to back-office login."""
        res = self.client.get(reverse('admin_theme_manager'))
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse('admin_login'), res.url)


class ThemeFallbackBehaviorTests(TestCase):
    """
    Tests for graceful fallback behavior:
    - Invalid theme ID passed to theme_registry.get() falls back to flagship theme.
    - SiteSetting with corrupted or unknown active_theme recovers safely.
    - Storefront renders without crash when invalid theme configured.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_registry_fallback_to_flagship(self):
        """Querying an unknown theme key with fallback=True returns the flagship theme."""
        theme = theme_registry.get('non_existent_niche_xyz', fallback=True)
        self.assertIsNotNone(theme)
        self.assertEqual(theme.id, 'pharmacy-healthcare')
        self.assertTrue(theme.is_flagship)

        # With fallback=False, returns None
        theme_none = theme_registry.get('non_existent_niche_xyz', fallback=False)
        self.assertIsNone(theme_none)

    def test_sitesetting_corrupted_theme_fallback(self):
        """If SiteSetting has an unrecognized active_theme string, context processor falls back safely."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'corrupted_theme_key_999'
        setting.save()

        request = self.factory.get('/')
        ctx = site_settings_processor(request)

        # Processor handles it gracefully and resolves flagship data
        self.assertEqual(ctx['CURRENT_THEME_ID'], 'pharmacy-healthcare')
        self.assertIsNotNone(ctx['CURRENT_THEME_DATA'])
        self.assertEqual(ctx['CURRENT_THEME_DATA']['id'], 'pharmacy-healthcare')

    def test_storefront_renders_cleanly_on_fallback(self):
        """Storefront root view '/' responds 200 OK even when database has an invalid theme."""
        setting = SiteSetting.get_settings()
        setting.active_theme = 'obsolete_or_deleted_theme'
        setting.save()

        client = Client()
        res = client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['CURRENT_THEME_ID'], 'pharmacy-healthcare')
