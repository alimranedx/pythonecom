"""
Core Theme Registry System for PythonEcom.

Provides centralized management, metadata discovery, design tokens,
template mappings, capability flags, and typed customization schemas
for all storefront industry vertical themes.

Supported Canonical Themes:
1. pharmacy-healthcare (legacy: pharmacy_health) - FLAGSHIP THEME (Default)
2. marketplace (legacy: mega_market)
3. tech-electronics (legacy: tech_gadgets)
4. beauty-skincare (legacy: beauty_cosmetics)
5. fashion-lifestyle (legacy: fashion_lifestyle)
6. organic-grocery (legacy: grocery_organic)
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import copy


class ThemeDefinition(dict):
    """
    Structured definition of an industry-vertical storefront theme.
    Subclasses dict for 100% transparent backward-compatibility with existing code,
    while providing object-style property access and helper methods.
    """

    def __init__(
        self,
        id: str,
        legacy_key: str,
        name: str,
        description: str,
        industry: str,
        version: str = "2.0.0",
        is_flagship: bool = False,
        benchmark: str = "",
        icon: str = "bi-shop",
        tag: str = "",
        status: str = "available",
        preview_image_url: str = "",
        thumbnail_url: str = "",
        brand_name: str = "",
        brand_sub: str = "",
        subtitle: str = "",
        category_slugs: Optional[List[str]] = None,
        brand_slugs: Optional[List[str]] = None,
        assets: Optional[Dict[str, str]] = None,
        design_tokens: Optional[Dict[str, str]] = None,
        copywriting: Optional[Dict[str, Any]] = None,
        supported_capabilities: Optional[List[str]] = None,
        template_mapping: Optional[Dict[str, str]] = None,
        customization_schema: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__()

        self.id = id
        self.legacy_key = legacy_key
        self.name = name
        self.description = description
        self.industry = industry
        self.version = version
        self.is_flagship = is_flagship
        self.benchmark = benchmark
        self.icon = icon
        self.tag = tag
        self.status = status
        self.preview_image_url = preview_image_url
        self.thumbnail_url = thumbnail_url or preview_image_url

        self.brand_name = brand_name or name
        self.brand_sub = brand_sub
        self.subtitle = subtitle or description
        self.category_slugs = category_slugs
        self.brand_slugs = brand_slugs

        self.assets = assets or {}
        self.design_tokens = design_tokens or {}
        self.copywriting = copywriting or {}
        self.supported_capabilities = supported_capabilities or []
        self.template_mapping = template_mapping or {}
        self.customization_schema = customization_schema or {}

        # Populate underlying dict representation for backward compatibility
        self["id"] = self.id
        self["legacy_key"] = self.legacy_key
        self["key"] = self.legacy_key  # backward-compat alias
        self["name"] = self.name
        self["description"] = self.description
        self["industry"] = self.industry
        self["version"] = self.version
        self["is_flagship"] = self.is_flagship
        self["benchmark"] = self.benchmark
        self["icon"] = self.icon
        self["tag"] = self.tag
        self["status"] = self.status
        self["preview_image_url"] = self.preview_image_url
        self["thumbnail_url"] = self.thumbnail_url
        self["brand_name"] = self.brand_name
        self["brand_sub"] = self.brand_sub
        self["subtitle"] = self.subtitle
        self["category_slugs"] = self.category_slugs
        self["brand_slugs"] = self.brand_slugs

        # Nested dictionaries
        self["assets"] = self.assets
        self["design_tokens"] = self.design_tokens
        self["copywriting"] = self.copywriting
        self["supported_capabilities"] = self.supported_capabilities
        self["template_mapping"] = self.template_mapping
        self["customization_schema"] = self.customization_schema

        # Flattened shortcuts from assets
        for k, v in self.assets.items():
            self[k] = v

        # Flattened shortcuts from design_tokens
        for k, v in self.design_tokens.items():
            self[k] = v

        # Flattened shortcuts from copywriting
        for k, v in self.copywriting.items():
            self[k] = v

        # Additional keyword args
        for k, v in kwargs.items():
            self[k] = v

    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(f"'ThemeDefinition' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        # Keep dict in sync for standard properties
        if hasattr(self, "_initialized") and self._initialized:
            self[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Returns deep copy of theme as standard dictionary."""
        return copy.deepcopy(dict(self))

    def has_capability(self, capability: str) -> bool:
        """Checks if this theme supports a specific domain capability."""
        return capability in self.supported_capabilities

    def get_template(self, slot: str, default: Optional[str] = None) -> Optional[str]:
        """Returns mapped template path for a given slot (e.g. 'header', 'home', 'footer')."""
        return self.template_mapping.get(slot, default)

    def get_default_settings(self) -> Dict[str, Any]:
        """
        Flattens customization_schema sections and returns a dict
        of default setting values: {setting_key: default_value}.
        """
        defaults: Dict[str, Any] = {}
        for section in self.customization_schema.values():
            for item in section.get("settings", []):
                defaults[item["key"]] = item.get("default")
        return defaults


class ThemeRegistryDict(dict):
    """
    Dict-compatible proxy mapping representing THEMES export.
    Supports lookup by BOTH canonical IDs and legacy keys.
    Maintains len() == count of unique registered themes.
    """

    def __init__(self, registry: "ThemeRegistry"):
        super().__init__()
        self._registry = registry

    def __getitem__(self, key: str) -> ThemeDefinition:
        theme = self._registry.get(key, fallback=False)
        if theme is None:
            raise KeyError(key)
        return theme

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self._registry.is_valid(key)

    def get(self, key: str, default: Any = None) -> Any:
        theme = self._registry.get(key, fallback=False)
        return theme if theme is not None else default

    def __len__(self) -> int:
        return len(self._registry._themes)

    def __iter__(self):
        return iter(self._registry._themes)

    def keys(self):
        return self._registry._themes.keys()

    def values(self):
        return self._registry._themes.values()

    def items(self):
        return self._registry._themes.items()

    def copy(self):
        return dict(self._registry._themes)


class ThemeRegistry:
    """
    Central Multi-Niche Theme Registry.
    Maintains registered themes, handles canonical ID normalization,
    legacy key translation, and language-resolved theme data assembly.
    """

    def __init__(self):
        self._themes: Dict[str, ThemeDefinition] = {}
        self._legacy_map: Dict[str, str] = {}
        self._flagship_id: Optional[str] = None
        self._default_id: Optional[str] = None

    @property
    def flagship_id(self) -> str:
        return self._flagship_id or "pharmacy-healthcare"

    @property
    def default_theme_id(self) -> str:
        return self._default_id or self.flagship_id

    def register(self, theme_def: Union[ThemeDefinition, Dict[str, Any]]) -> ThemeDefinition:
        """Registers a theme definition in the central registry."""
        if not isinstance(theme_def, ThemeDefinition):
            theme_def = ThemeDefinition(**theme_def)

        tid = theme_def.id
        self._themes[tid] = theme_def

        if theme_def.legacy_key:
            self._legacy_map[theme_def.legacy_key] = tid
            # Bidirectional normalization
            self._legacy_map[theme_def.legacy_key.replace("_", "-")] = tid
            self._legacy_map[theme_def.legacy_key.replace("-", "_")] = tid

        # Also map tid variations
        self._legacy_map[tid.replace("-", "_")] = tid

        if theme_def.is_flagship or self._flagship_id is None:
            self._flagship_id = tid
            self._default_id = tid

        return theme_def

    def normalize_id(self, theme_id_or_legacy_key: Optional[str]) -> Optional[str]:
        """
        Normalizes any theme ID, legacy key, or variation to canonical theme ID.
        Returns None if not recognized.
        """
        if not theme_id_or_legacy_key:
            return None

        key = str(theme_id_or_legacy_key).strip().lower()

        if key in self._themes:
            return key

        if key in self._legacy_map:
            return self._legacy_map[key]

        hyphenated = key.replace("_", "-")
        if hyphenated in self._themes:
            return hyphenated
        if hyphenated in self._legacy_map:
            return self._legacy_map[hyphenated]

        underscored = key.replace("-", "_")
        if underscored in self._legacy_map:
            return self._legacy_map[underscored]

        return None

    def is_valid(self, theme_id: Optional[str]) -> bool:
        """Returns True if theme_id or legacy key corresponds to a registered theme."""
        return self.normalize_id(theme_id) is not None

    def get_legacy_key(self, theme_id: str) -> str:
        """Returns legacy key for a canonical theme ID."""
        canonical_id = self.normalize_id(theme_id)
        if canonical_id and canonical_id in self._themes:
            return self._themes[canonical_id].legacy_key
        return theme_id

    def get(self, theme_id_or_legacy_key: Optional[str], fallback: bool = True) -> Optional[ThemeDefinition]:
        """
        Retrieves ThemeDefinition by canonical ID or legacy key.
        If not found and fallback is True, returns flagship theme.
        """
        canonical_id = self.normalize_id(theme_id_or_legacy_key)
        if canonical_id and canonical_id in self._themes:
            return self._themes[canonical_id]

        if fallback:
            default_id = self.default_theme_id
            if default_id in self._themes:
                return self._themes[default_id]
            if self._themes:
                return next(iter(self._themes.values()))

        return None

    def get_all(self) -> List[ThemeDefinition]:
        """
        Returns list of all registered ThemeDefinitions,
        with flagship theme sorted first.
        """
        themes = list(self._themes.values())
        return sorted(themes, key=lambda t: (not t.is_flagship, t.id))

    def get_choices(self) -> Tuple[Tuple[str, str], ...]:
        """
        Returns choices tuple for Django CharField models and forms.
        Uses canonical IDs as stored values.
        """
        choices = []
        for theme in self.get_all():
            suffix = " [Flagship]" if theme.is_flagship else ""
            benchmark_str = f" ({theme.benchmark})" if theme.benchmark else ""
            label = f"{theme.name}{benchmark_str}{suffix}"
            choices.append((theme.id, label))
        return tuple(choices)

    def get_theme_data(
        self,
        theme_id: Optional[str],
        is_bangla: bool = False,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assembles a fully resolved, language-aware, customizable theme dictionary.
        Handles bilingual copy, trust pillars resolution, and merges custom config overrides.
        """
        theme = self.get(theme_id, fallback=True)
        if theme is None:
            return {}

        data = theme.to_dict()

        # Language resolution for copywriting tokens
        headline_key = "hero_headline_bn" if is_bangla else "hero_headline_en"
        tagline_key = "hero_tagline_bn" if is_bangla else "hero_tagline_en"
        badge_key = "hero_badge_bn" if is_bangla else "hero_badge_en"

        data["hero_headline"] = theme.get(headline_key, "")
        data["hero_tagline"] = theme.get(tagline_key, "")
        data["hero_badge"] = theme.get(badge_key, "")

        resolved_pillars = []
        for pillar in theme.get("trust_pillars", []):
            p = dict(pillar)
            p["title"] = pillar.get("title_bn" if is_bangla else "title_en", "")
            p["desc"] = pillar.get("desc_bn" if is_bangla else "desc_en", "")
            resolved_pillars.append(p)
        data["trust_pillars"] = resolved_pillars

        # Preserve the queried key if valid, else use legacy_key / id
        normalized = self.normalize_id(theme_id)
        if theme_id and normalized == theme.id:
            data["key"] = theme_id
        else:
            data["key"] = theme.legacy_key or theme.id

        data["canonical_id"] = theme.id
        data["is_flagship"] = theme.is_flagship

        # Apply custom settings / design token overrides if provided
        effective_config = theme.get_default_settings()
        if custom_config and isinstance(custom_config, dict):
            effective_config.update(custom_config)
            # Apply design token overrides if present in custom_config
            for token_key in theme.design_tokens:
                if token_key in custom_config:
                    data[token_key] = custom_config[token_key]
                    if "design_tokens" in data and isinstance(data["design_tokens"], dict):
                        data["design_tokens"][token_key] = custom_config[token_key]

        data["custom_config"] = effective_config

        return data

    def get_theme_dict(self) -> ThemeRegistryDict:
        """Returns the dictionary-compatible proxy for export as THEMES."""
        return ThemeRegistryDict(self)


# ==============================================================================
# DEFAULT CANONICAL THEME DEFINITIONS
# ==============================================================================

def _build_pharmacy_healthcare_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="pharmacy-healthcare",
        legacy_key="pharmacy_health",
        name="Pharmacy & Healthcare",
        description="Licensed prescription medicines, wellness, and medical supplies with DGDA compliance, cold-chain assurance, and prescription audit.",
        industry="Pharmacy, Medicine & Healthcare",
        version="2.0.0",
        is_flagship=True,
        benchmark="Arogga Style",
        icon="bi-heart-pulse",
        tag="Pharmacy",
        status="active",
        preview_image_url="/static/images/themes/previews/pharmacy-healthcare.svg",
        thumbnail_url="/static/images/themes/previews/pharmacy-healthcare.svg",
        brand_name="Arogya Meds",
        brand_sub="Pharmacy & Healthcare",
        subtitle="Licensed Prescription Medicines, Wellness & First Aid",
        category_slugs=["prescriptions", "vitamins", "first-aid", "personal-hygiene"],
        brand_slugs=["square-pharma", "beximco", "dettol", "savlon"],
        assets={
            "logo_url": "/static/images/themes/pharmacy_health/logo.svg",
            "logo_png_url": "/static/images/themes/pharmacy_health/logo.png",
            "logo_dark_url": "/static/images/themes/pharmacy_health/logo_dark.svg",
            "favicon_url": "/static/images/themes/pharmacy_health/favicon.svg",
            "favicon_ico_url": "/static/images/themes/pharmacy_health/favicon.ico",
        },
        design_tokens={
            "primary": "#0d9488",
            "primary_hover": "#0f766e",
            "primary_light": "#f0fdfa",
            "accent": "#0284c7",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#f0fdfa",
            "hero_gradient_end": "#ccfbf1",
            "dark_primary": "#2dd4bf",
            "dark_accent": "#38bdf8",
            "badge_radius": "0.375rem",
            "button_radius": "0.5rem",
            "card_radius": "0.75rem",
            "font_family": 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        copywriting={
            "hero_headline_en": "Certified Genuine Medicines & Comprehensive Healthcare",
            "hero_headline_bn": "১০০% আসল ও রেজিস্টার্ড ওষুধ এবং হেলথকেয়ার সল্যুশন",
            "hero_tagline_en": "Temperature-controlled storage, DGDA licensed pharmacists, and digital prescription review.",
            "hero_tagline_bn": "তাপমাত্রা-নিয়ন্ত্রিত সংরক্ষণ ও রেজিস্টার্ড ফার্মাসিস্টদের তত্ত্বাবধানে নির্ভরযোগ্য সেবা।",
            "hero_badge_en": "Licensed Model Pharmacy",
            "hero_badge_bn": "ডিজিডিএ অনুমোদিত মডেল ফার্মেসি",
            "trust_pillars": [
                {
                    "icon": "bi-hospital",
                    "title_en": "Licensed Model Pharmacy",
                    "title_bn": "ডিজিডিএ অনুমোদিত মডেল ফার্মেসি",
                    "desc_en": "DGDA certified model pharmacy with registered pharmacists",
                    "desc_bn": "সরকারি লাইসেন্সপ্রাপ্ত ও রেজিস্টার্ড ফার্মাসিস্ট পরিচালিত",
                },
                {
                    "icon": "bi-snow2",
                    "title_en": "Cold-Chain Delivery",
                    "title_bn": "কোল্ড-চেইন সংরক্ষণ ব্যবস্থা",
                    "desc_en": "Strict 2-8°C refrigerated storage for insulin & biologics",
                    "desc_bn": "ইনসুলিন ও ভ্যাকসিনের জন্য সুনির্দিষ্ট তাপমাত্রা",
                },
                {
                    "icon": "bi-file-earmark-medical",
                    "title_en": "Prescription Verification",
                    "title_bn": "প্রেসক্রিপশন নিখুঁত যাচাই",
                    "desc_en": "Upload prescription for expert B.Pharm dosage audit",
                    "desc_bn": "অভিজ্ঞ ফার্মাসিস্ট দ্বারা প্রেসক্রিপশন নিরীক্ষা",
                },
                {
                    "icon": "bi-shield-plus",
                    "title_en": "100% Genuine Medicine",
                    "title_bn": "১০০% আসল ওষুধের নিশ্চয়তা",
                    "desc_en": "Directly procured from Square, Beximco, Incepta & Renata",
                    "desc_bn": "শীর্ষ ফার্মাসিউটিক্যালস কোম্পানি থেকে সরাসরি সংগৃহীত",
                },
            ],
        },
        supported_capabilities=[
            "prescription_upload",
            "cold_chain_badge",
            "dosage_calculator",
            "generic_name_display",
            "pharmacist_consultation",
            "refill_reminder",
        ],
        template_mapping={
            "layout": "themes/pharmacy-healthcare/base.html",
            "header": "themes/pharmacy-healthcare/header.html",
            "footer": "themes/pharmacy-healthcare/footer.html",
            "home": "themes/pharmacy-healthcare/home.html",
            "product_card": "themes/pharmacy-healthcare/product_card.html",
            "product_list": "themes/pharmacy-healthcare/product_list.html",
            "product_detail": "themes/pharmacy-healthcare/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Header & Prescription Bar",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_announcement_bar",
                        "label": "Show Announcement Bar",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Toggle top medical delivery announcement bar",
                    },
                    {
                        "key": "show_prescription_cta",
                        "label": "Show Prescription Upload Button in Header",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display quick Upload Prescription button in main navbar",
                    },
                    {
                        "key": "sticky_header",
                        "label": "Sticky Navigation Header",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Keep navbar fixed on top during scroll",
                    },
                ],
            },
            "homepage": {
                "title": "Homepage Sections",
                "icon": "bi-house-door",
                "settings": [
                    {
                        "key": "show_trust_pillars",
                        "label": "Display Healthcare Trust Badges",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show licensed pharmacy, cold chain, and verification pillars",
                    },
                    {
                        "key": "show_cold_chain_banner",
                        "label": "Highlight Cold Chain Medicine Assurance",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show refrigerated temperature banner for insulin and biologics",
                    },
                    {
                        "key": "show_dosage_calc_promo",
                        "label": "Show Dosage Calculator Card",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Promote quick dosage calculator widget on homepage",
                    },
                ],
            },
            "product_display": {
                "title": "Medicine & Product Display",
                "icon": "bi-capsule",
                "settings": [
                    {
                        "key": "show_generic_name",
                        "label": "Show Generic Molecule Name",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display scientific generic name (e.g. Paracetamol) below brand",
                    },
                    {
                        "key": "show_rx_badge",
                        "label": "Show Prescription Required Badge",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display Rx badge on scheduled medicines",
                    },
                    {
                        "key": "card_hover_effect",
                        "label": "Card Hover Style",
                        "type": "select",
                        "default": "lift_shadow",
                        "choices": [
                            ("lift_shadow", "Elevate Card with Shadow"),
                            ("teal_glow", "Teal Border Glow"),
                            ("minimal", "Clean Border Only"),
                        ],
                        "help_text": "Card animation on mouse hover",
                    },
                ],
            },
            "footer": {
                "title": "Footer & Compliance",
                "icon": "bi-shield-check",
                "settings": [
                    {
                        "key": "show_dgda_license",
                        "label": "Show DGDA Model Pharmacy License Badge",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display government DGDA registration notice",
                    },
                    {
                        "key": "show_emergency_hotline",
                        "label": "Show 24/7 Pharmacist Hotline",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display emergency pharmacist contact phone",
                    },
                ],
            },
        },
    )


def _build_marketplace_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="marketplace",
        legacy_key="mega_market",
        name="Mega Market",
        description="High-volume general multi-category marketplace with flash deals, express shipping badges, and multi-vendor variety.",
        industry="General Marketplace",
        version="2.0.0",
        is_flagship=False,
        benchmark="Daraz / Amazon Style",
        icon="bi-cart4",
        tag="Marketplace",
        status="available",
        preview_image_url="/static/images/themes/previews/marketplace.svg",
        thumbnail_url="/static/images/themes/previews/marketplace.svg",
        brand_name="Mega Market",
        brand_sub="Express Superstore",
        subtitle="General Multi-Category Marketplace",
        category_slugs=None,
        brand_slugs=None,
        assets={
            "logo_url": "/static/images/themes/mega_market/logo.svg",
            "logo_png_url": "/static/images/themes/mega_market/logo.png",
            "logo_dark_url": "/static/images/themes/mega_market/logo_dark.svg",
            "favicon_url": "/static/images/themes/mega_market/favicon.svg",
            "favicon_ico_url": "/static/images/themes/mega_market/favicon.ico",
        },
        design_tokens={
            "primary": "#f85606",
            "primary_hover": "#d94400",
            "primary_light": "#fff1ec",
            "accent": "#2563eb",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#fff7ed",
            "hero_gradient_end": "#ffffff",
            "dark_primary": "#fb923c",
            "dark_accent": "#60a5fa",
            "badge_radius": "9999px",
            "button_radius": "0.5rem",
            "card_radius": "0.75rem",
            "font_family": 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        copywriting={
            "hero_headline_en": "Biggest Deals, Endless Variety at Your Doorstep",
            "hero_headline_bn": "সেরা ডিল ও অফুরন্ত পণ্যের সমাহার আপনার দোরগোড়ায়",
            "hero_tagline_en": "Shop millions of products from verified sellers with express nationwide delivery across Bangladesh.",
            "hero_tagline_bn": "সারা বাংলাদেশে দ্রুততম ক্যাশ অন ডেলিভারিতে লাখো পণ্যের বিশাল সংগ্রহ।",
            "hero_badge_en": "Mega Marketplace Savings Festival",
            "hero_badge_bn": "মেগা মার্কেটপ্লেস সেভিংস উৎসব",
            "trust_pillars": [
                {
                    "icon": "bi-truck",
                    "title_en": "Nationwide Delivery",
                    "title_bn": "সারা দেশে ডেলিভারি",
                    "desc_en": "Fast doorstep delivery across all 64 districts",
                    "desc_bn": "৬৪টি জেলায় দ্রুত হোম ডেলিভারি",
                },
                {
                    "icon": "bi-shield-check",
                    "title_en": "100% Secure Checkout",
                    "title_bn": "নিরাপদ পেমেন্ট",
                    "desc_en": "bKash, Nagad, Visa, Mastercard & COD",
                    "desc_bn": "বিকাশ, নগদ, কার্ড ও ক্যাশ অন ডেলিভারি",
                },
                {
                    "icon": "bi-arrow-counterclockwise",
                    "title_en": "7-Day Easy Returns",
                    "title_bn": "৭ দিনে সহজ রিটার্ন",
                    "desc_en": "Hassle-free replacement & refund guarantee",
                    "desc_bn": "পণ্য রিটার্নে সহজ ও নিশ্চিত রিফান্ড",
                },
                {
                    "icon": "bi-tag",
                    "title_en": "Best Price Guarantee",
                    "title_bn": "সেরা মূল্যের নিশ্চয়তা",
                    "desc_en": "Direct factory & wholesaler discounts daily",
                    "desc_bn": "সেরা অফার ও বাজার সেরা দাম প্রতিদিন",
                },
            ],
        },
        supported_capabilities=[
            "mega_menu",
            "flash_deals",
            "multi_vendor_badges",
            "daily_vouchers",
            "category_icons_grid",
            "express_delivery_badge",
        ],
        template_mapping={
            "layout": "themes/marketplace/base.html",
            "header": "themes/marketplace/header.html",
            "footer": "themes/marketplace/footer.html",
            "home": "themes/marketplace/home.html",
            "product_card": "themes/marketplace/product_card.html",
            "product_list": "themes/marketplace/product_list.html",
            "product_detail": "themes/marketplace/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Header & Navigation",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_announcement_bar",
                        "label": "Show Top Announcement Banner",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Toggle festival deals announcement bar",
                    },
                    {
                        "key": "enable_mega_menu",
                        "label": "Enable Multi-Column Mega Menu",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show rich multi-level category navigation dropdown",
                    },
                ],
            },
            "homepage": {
                "title": "Campaign & Flash Deals",
                "icon": "bi-lightning-charge",
                "settings": [
                    {
                        "key": "show_flash_sale_timer",
                        "label": "Show Flash Sale Countdown",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display countdown timer ticker for flash deals",
                    },
                    {
                        "key": "show_category_icons",
                        "label": "Display Quick Category Icon Bar",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show circular category shortcuts below main banner",
                    },
                ],
            },
            "product_display": {
                "title": "Catalog & Discount Pills",
                "icon": "bi-tags",
                "settings": [
                    {
                        "key": "show_discount_percentage",
                        "label": "Show Percentage Savings Pill",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display savings badge e.g. -25%",
                    },
                    {
                        "key": "card_hover_effect",
                        "label": "Product Card Hover Style",
                        "type": "select",
                        "default": "lift_shadow",
                        "choices": [
                            ("lift_shadow", "Elevate Card with Shadow"),
                            ("orange_border", "Orange Accent Border"),
                            ("zoom_image", "Zoom Product Thumbnail"),
                        ],
                        "help_text": "Card interaction on hover",
                    },
                ],
            },
            "footer": {
                "title": "Footer & Payment Badges",
                "icon": "bi-credit-card",
                "settings": [
                    {
                        "key": "show_payment_methods",
                        "label": "Show Accepted Payment Logos",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display bKash, Nagad, Visa, Mastercard in footer",
                    },
                ],
            },
        },
    )


def _build_tech_electronics_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="tech-electronics",
        legacy_key="tech_gadgets",
        name="Tech & Gadgets",
        description="Laptops, smartphones, PC hardware, and premium gadgets with official brand warranties, 0% EMI financing, and express delivery.",
        industry="Consumer Electronics & Hardware",
        version="2.0.0",
        is_flagship=False,
        benchmark="Star Tech / Apple Gadgets Style",
        icon="bi-laptop",
        tag="Electronics",
        status="available",
        preview_image_url="/static/images/themes/previews/tech-electronics.svg",
        thumbnail_url="/static/images/themes/previews/tech-electronics.svg",
        brand_name="TechVerse",
        brand_sub="Gadgets & Pro Gear",
        subtitle="Laptops, Phones & Precision Hardware",
        category_slugs=[
            "laptops",
            "smartphones",
            "pc-hardware",
            "audio-gear",
            "electronics-appliances",
            "tablets",
            "mobile-accessories",
        ],
        brand_slugs=["apple", "samsung", "asus", "dell", "sony", "logitech"],
        assets={
            "logo_url": "/static/images/themes/tech_gadgets/logo.svg",
            "logo_png_url": "/static/images/themes/tech_gadgets/logo.png",
            "logo_dark_url": "/static/images/themes/tech_gadgets/logo_dark.svg",
            "favicon_url": "/static/images/themes/tech_gadgets/favicon.svg",
            "favicon_ico_url": "/static/images/themes/tech_gadgets/favicon.ico",
        },
        design_tokens={
            "primary": "#0284c7",
            "primary_hover": "#0369a1",
            "primary_light": "#f0f9ff",
            "accent": "#38bdf8",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#0f172a",
            "hero_gradient_end": "#1e293b",
            "dark_primary": "#38bdf8",
            "dark_accent": "#818cf8",
            "badge_radius": "0.375rem",
            "button_radius": "0.375rem",
            "card_radius": "0.5rem",
            "font_family": 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        copywriting={
            "hero_headline_en": "Next-Gen Laptops, Flagship Phones & Pro Hardware",
            "hero_headline_bn": "লেটেস্ট ল্যাপটপ, ফ্ল্যাগশিপ স্মার্টফোন ও প্রিমিয়াম গ্যাজেট",
            "hero_tagline_en": "Equip your digital universe with official brand warranties and up to 36 months 0% EMI financing.",
            "hero_tagline_bn": "অফিসিয়াল ব্র্যান্ড ওয়ারেন্টি ও ০% ইএমআই সুবিধায় কেনাকাটা করুন সেরা দামে।",
            "hero_badge_en": "Official Brand Tech 2026",
            "hero_badge_bn": "অফিসিয়াল ব্র্যান্ড টেক ২০২৬",
            "trust_pillars": [
                {
                    "icon": "bi-patch-check-fill",
                    "title_en": "Official Brand Warranty",
                    "title_bn": "অফিসিয়াল ব্র্যান্ড ওয়ারেন্টি",
                    "desc_en": "100% manufacturer warranty claimable in BD",
                    "desc_bn": "বাংলাদেশে সরাসরি ক্লেইমেবল ব্র্যান্ড ওয়ারেন্টি",
                },
                {
                    "icon": "bi-credit-card-2-front",
                    "title_en": "0% EMI Available",
                    "title_bn": "০% সুদে ইএমআই সুবিধা",
                    "desc_en": "Up to 36 months zero-interest installments",
                    "desc_bn": "৩৬ মাস পর্যন্ত সহজ কিস্তি সুবিধা",
                },
                {
                    "icon": "bi-lightning-charge",
                    "title_en": "3-Hour Express Courier",
                    "title_bn": "৩ ঘণ্টায় সুপারফাস্ট ডেলিভারি",
                    "desc_en": "Same-day express dispatch across Dhaka metro",
                    "desc_bn": "ঢাকা সিটির ভেতরে দ্রুততম ডেলিভারি",
                },
                {
                    "icon": "bi-cpu",
                    "title_en": "Verified Genuine Devices",
                    "title_bn": "১০০% আসল অথেনটিক ডিভাইস",
                    "desc_en": "Original boxed products with serial verification",
                    "desc_bn": "সিলযুক্ত প্যাকেট ও অফিশিয়াল সিরিয়াল ভেরিফিকেশন",
                },
            ],
        },
        supported_capabilities=[
            "spec_table",
            "emi_calculator",
            "warranty_badge",
            "serial_lookup",
            "dark_mode_hero",
            "brand_showcase",
        ],
        template_mapping={
            "layout": "themes/tech-electronics/base.html",
            "header": "themes/tech-electronics/header.html",
            "footer": "themes/tech-electronics/footer.html",
            "home": "themes/tech-electronics/home.html",
            "product_card": "themes/tech-electronics/product_card.html",
            "product_list": "themes/tech-electronics/product_list.html",
            "product_detail": "themes/tech-electronics/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Header & Tech Bar",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_emi_calculator_link",
                        "label": "Show EMI Calculator in Header",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Direct link to calculate monthly installment amounts",
                    },
                ],
            },
            "homepage": {
                "title": "Dark Hardware Showcase",
                "icon": "bi-gpu-card",
                "settings": [
                    {
                        "key": "enable_dark_hero_gradient",
                        "label": "Enable Dark High-Tech Hero Background",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Use deep slate gradient for tech look & feel",
                    },
                    {
                        "key": "show_brand_partner_logos",
                        "label": "Display Authorized Brand Logos",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show Apple, Samsung, Asus, Dell official logos",
                    },
                ],
            },
            "product_display": {
                "title": "Hardware Specs & Badges",
                "icon": "bi-cpu",
                "settings": [
                    {
                        "key": "show_warranty_badge",
                        "label": "Display Official Warranty Badge",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show BD claimable warranty seal on cards",
                    },
                    {
                        "key": "show_emi_badge",
                        "label": "Show 0% EMI Available Pill",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Highlight monthly installment availability",
                    },
                ],
            },
            "footer": {
                "title": "Warranty & Service Centers",
                "icon": "bi-wrench-adjustable",
                "settings": [
                    {
                        "key": "show_service_centers",
                        "label": "Show Official Service Points Link",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Direct link for warranty claims and repairs",
                    },
                ],
            },
        },
    )


def _build_beauty_skincare_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="beauty-skincare",
        legacy_key="beauty_cosmetics",
        name="Beauty & Cosmetics",
        description="Skincare, makeup, and imported fragrance boutique featuring Korean formulations, dermatologically certified ingredients, and shade swatches.",
        industry="Beauty, Cosmetics & Personal Care",
        version="2.0.0",
        is_flagship=False,
        benchmark="Shajgoj Style",
        icon="bi-gem",
        tag="Beauty",
        status="available",
        preview_image_url="/static/images/themes/previews/beauty-skincare.svg",
        thumbnail_url="/static/images/themes/previews/beauty-skincare.svg",
        brand_name="Glow & Glam",
        brand_sub="Beauty & Skincare",
        subtitle="Skincare, Makeup & Fragrance Boutique",
        category_slugs=["skin-care", "makeup", "hair-care", "fragrances", "beauty"],
        brand_slugs=["loreal", "the-ordinary", "cerave", "mac", "maybelline", "chanel"],
        assets={
            "logo_url": "/static/images/themes/beauty_cosmetics/logo.svg",
            "logo_png_url": "/static/images/themes/beauty_cosmetics/logo.png",
            "logo_dark_url": "/static/images/themes/beauty_cosmetics/logo_dark.svg",
            "favicon_url": "/static/images/themes/beauty_cosmetics/favicon.svg",
            "favicon_ico_url": "/static/images/themes/beauty_cosmetics/favicon.ico",
        },
        design_tokens={
            "primary": "#db2777",
            "primary_hover": "#be185d",
            "primary_light": "#fdf2f8",
            "accent": "#f43f5e",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#fdf2f8",
            "hero_gradient_end": "#ffe4e6",
            "dark_primary": "#f472b6",
            "dark_accent": "#fda4af",
            "badge_radius": "9999px",
            "button_radius": "9999px",
            "card_radius": "1rem",
            "font_family": 'Poppins, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        copywriting={
            "hero_headline_en": "Glow Authentically with Premium Skincare & Makeup",
            "hero_headline_bn": "১০০% আসল স্কিনকেয়ার ও মেকআপে রূপচর্চার নতুন অভিজ্ঞতা",
            "hero_tagline_en": "Directly imported certified Korean, US, and UK formulations for radiant skin and timeless beauty.",
            "hero_tagline_bn": "কোরিয়ান ও ইউরোপীয় শীর্ষ ব্র্যান্ডের আসল প্রসাধনীর নির্ভরযোগ্য সম্ভার।",
            "hero_badge_en": "100% Authentic Import",
            "hero_badge_bn": "১০০% আসল আমদানিকৃত",
            "trust_pillars": [
                {
                    "icon": "bi-stars",
                    "title_en": "100% Authentic Import",
                    "title_bn": "১০০% আসল আমদানিকৃত",
                    "desc_en": "Directly sourced from authorized brand distributors",
                    "desc_bn": "অনুমোদিত আন্তর্জাতিক ডিস্ট্রিবিউটর থেকে সংগৃহীত",
                },
                {
                    "icon": "bi-heart-pulse",
                    "title_en": "Dermatologically Tested",
                    "title_bn": "ডার্মাটোলজিস্ট পরীক্ষিত",
                    "desc_en": "Certified gentle and safe for all sensitive skin types",
                    "desc_bn": "সব ধরনের ত্বকের জন্য নিরাপদ ও পরীক্ষিত",
                },
                {
                    "icon": "bi-flower1",
                    "title_en": "Cruelty-Free & Safe",
                    "title_bn": "ক্ষতিকারক কেমিক্যালমুক্ত",
                    "desc_en": "Free from parabens, harmful toxins & heavy metals",
                    "desc_bn": "ক্ষতিকারক কেমিক্যাল ও প্যারাবেনমুক্ত ফর্মুলা",
                },
                {
                    "icon": "bi-chat-heart",
                    "title_en": "Personalized Skin Guidance",
                    "title_bn": "ফ্রি স্কিনকেয়ার পরামর্শ",
                    "desc_en": "Certified aesthetic advisors ready to assist",
                    "desc_bn": "বিশেষজ্ঞ বিউটি অ্যাডভাইজারের ফ্রি পরামর্শ",
                },
            ],
        },
        supported_capabilities=[
            "shade_swatches",
            "authenticity_badge",
            "skin_type_filter",
            "ingredient_list",
            "beauty_advisor_chat",
            "routine_builder",
        ],
        template_mapping={
            "layout": "themes/beauty-skincare/base.html",
            "header": "themes/beauty-skincare/header.html",
            "footer": "themes/beauty-skincare/footer.html",
            "home": "themes/beauty-skincare/home.html",
            "product_card": "themes/beauty-skincare/product_card.html",
            "product_list": "themes/beauty-skincare/product_list.html",
            "product_detail": "themes/beauty-skincare/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Beauty Boutique Header",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_consultant_chat_link",
                        "label": "Show Beauty Advisor Chat CTA",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Header CTA for aesthetic advice",
                    },
                ],
            },
            "homepage": {
                "title": "Glow Atmosphere",
                "icon": "bi-flower1",
                "settings": [
                    {
                        "key": "show_authenticity_banner",
                        "label": "Show Authentic Import Guarantee Banner",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Emphasize 100% genuine imported formulations",
                    },
                ],
            },
            "product_display": {
                "title": "Swatches & Skin Types",
                "icon": "bi-palette",
                "settings": [
                    {
                        "key": "show_shade_swatches",
                        "label": "Show Color Shade Circles on Cards",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display foundation and lipstick color dots",
                    },
                    {
                        "key": "show_skin_type_tag",
                        "label": "Display Recommended Skin Type Pill",
                        "type": "boolean",
                        "default": True,
                        "help_text": "E.g. Oily Skin, Dry Skin, Sensitive Skin",
                    },
                ],
            },
            "footer": {
                "title": "Skincare Advisory",
                "icon": "bi-chat-heart",
                "settings": [
                    {
                        "key": "show_routine_guide_link",
                        "label": "Show 10-Step Skincare Guide Link",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Helpful educational guide in footer",
                    },
                ],
            },
        },
    )


def _build_fashion_lifestyle_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="fashion-lifestyle",
        legacy_key="fashion_lifestyle",
        name="Fashion & Lifestyle",
        description="Artisanal apparel, ethnic couture, tailored Panjabis, Jamdani sarees, and modern urban styling with Try & Buy doorstep service.",
        industry="Fashion, Apparel & Lifestyle",
        version="2.0.0",
        is_flagship=False,
        benchmark="Aarong / Sailor Style",
        icon="bi-person-heart",
        tag="Fashion",
        status="available",
        preview_image_url="/static/images/themes/previews/fashion-lifestyle.svg",
        thumbnail_url="/static/images/themes/previews/fashion-lifestyle.svg",
        brand_name="Heritage",
        brand_sub="Fashion & Couture",
        subtitle="Artisanal Apparel, Festive Wear & Modern Styling",
        category_slugs=[
            "mens-panjabi",
            "womens-kurti",
            "formalwear",
            "casual-denim",
            "fashion-apparel",
            "womens-dresses",
            "mens-shirts",
            "mens-shoes",
            "womens-shoes",
        ],
        brand_slugs=["aarong", "sailor", "apex", "bata", "zara"],
        assets={
            "logo_url": "/static/images/themes/fashion_lifestyle/logo.svg",
            "logo_png_url": "/static/images/themes/fashion_lifestyle/logo.png",
            "logo_dark_url": "/static/images/themes/fashion_lifestyle/logo_dark.svg",
            "favicon_url": "/static/images/themes/fashion_lifestyle/favicon.svg",
            "favicon_ico_url": "/static/images/themes/fashion_lifestyle/favicon.ico",
        },
        design_tokens={
            "primary": "#9a3412",
            "primary_hover": "#7c2d12",
            "primary_light": "#fff7ed",
            "accent": "#d97706",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#fefce8",
            "hero_gradient_end": "#ffedd5",
            "dark_primary": "#fb923c",
            "dark_accent": "#fbbf24",
            "badge_radius": "0.25rem",
            "button_radius": "0.375rem",
            "card_radius": "0.75rem",
            "font_family": 'Playfair Display, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, serif',
        },
        copywriting={
            "hero_headline_en": "Handcrafted Elegance, Premium Fabrics & Modern Silhouette",
            "hero_headline_bn": "ঐতিহ্যের ছোঁয়া ও আধুনিক ফ্যাশনের আভিজাত্য",
            "hero_tagline_en": "Discover tailored Panjabis, artisanal Sarees, and contemporary urban ensembles crafted for distinction.",
            "hero_tagline_bn": "আভিজাত পাঞ্জাবি, জামদানি শাড়ি ও ট্রেন্ডি লাইফস্টাইল কালেকশন ঘরে বসেই অর্ডার করুন।",
            "hero_badge_en": "Heritage Festive Collection 2026",
            "hero_badge_bn": "হেরিটেজ ফেস্টিভ কালেকশন ২০২৬",
            "trust_pillars": [
                {
                    "icon": "bi-palette",
                    "title_en": "Handcrafted Artisan Weaves",
                    "title_bn": "হাতে বোনা নিখুঁত কারুকাজ",
                    "desc_en": "Crafted by traditional rural master weavers",
                    "desc_bn": "ঐতিহ্যবাহী তাঁতীদের নিখুঁত হাতের কাজ",
                },
                {
                    "icon": "bi-feather",
                    "title_en": "100% Pure Organic Cotton",
                    "title_bn": "১০০% প্রিমিয়াম সুতি কাপড়",
                    "desc_en": "Breathable, pre-shrunk high-count natural textiles",
                    "desc_bn": "আরামদায়ক ও টেকসই খাঁটি সুতি ফ্যাব্রিক",
                },
                {
                    "icon": "bi-scissors",
                    "title_en": "Perfect Tailored Fit",
                    "title_bn": "পারফেক্ট ফিটিং গ্যারান্টি",
                    "desc_en": "Accurate size charts with easy size replacement",
                    "desc_bn": "সাইজ না মিললে ফ্রি এক্সচেঞ্জ সুবিধা",
                },
                {
                    "icon": "bi-bag-check",
                    "title_en": "Try & Buy Delivery",
                    "title_bn": "ট্রাই অ্যান্ড বাই সুবিধা",
                    "desc_en": "Try apparel at doorstep before confirming purchase",
                    "desc_bn": "পণ্য দেখে ট্রাই করে নিশ্চিত করুন",
                },
            ],
        },
        supported_capabilities=[
            "size_guide_modal",
            "color_swatches",
            "lookbook_grid",
            "try_and_buy_badge",
            "fabric_care_guide",
            "fit_finder",
        ],
        template_mapping={
            "layout": "themes/fashion-lifestyle/base.html",
            "header": "themes/fashion-lifestyle/header.html",
            "footer": "themes/fashion-lifestyle/footer.html",
            "home": "themes/fashion-lifestyle/home.html",
            "product_card": "themes/fashion-lifestyle/product_card.html",
            "product_list": "themes/fashion-lifestyle/product_list.html",
            "product_detail": "themes/fashion-lifestyle/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Couture Header",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_size_guide_header_link",
                        "label": "Show Size Guide Link in Header",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Quick sizing chart access",
                    },
                ],
            },
            "homepage": {
                "title": "Editorial Showcase",
                "icon": "bi-images",
                "settings": [
                    {
                        "key": "show_editorial_lookbook",
                        "label": "Show Seasonal Lookbook Grid",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Editorial collage of styled outfits",
                    },
                ],
            },
            "product_display": {
                "title": "Sizing & Fabric Notes",
                "icon": "bi-rulers",
                "settings": [
                    {
                        "key": "show_size_picker_on_card",
                        "label": "Quick Size Selector on Cards (S, M, L, XL)",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Let customers pick size before adding to bag",
                    },
                    {
                        "key": "show_try_and_buy_badge",
                        "label": "Show Try & Buy Eligible Badge",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Highlight doorstep try-on eligibility",
                    },
                ],
            },
            "footer": {
                "title": "Garment Care & Exchange",
                "icon": "bi-recycle",
                "settings": [
                    {
                        "key": "show_exchange_policy",
                        "label": "Highlight 7-Day Free Size Exchange",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Promote hassle-free fit replacement in footer",
                    },
                ],
            },
        },
    )


def _build_organic_grocery_theme() -> ThemeDefinition:
    return ThemeDefinition(
        id="organic-grocery",
        legacy_key="grocery_organic",
        name="Grocery & Organic Food",
        description="Farm-fresh organic vegetables, pure cold-pressed mustard oil, natural Sundarban honey, and kitchen staples with 1-hour doorstep slot delivery.",
        industry="Organic Food & Daily Groceries",
        version="2.0.0",
        is_flagship=False,
        benchmark="Khaas Food / Ghorer Bazar / Chaldal Style",
        icon="bi-basket2",
        tag="Organic Grocery",
        status="available",
        preview_image_url="/static/images/themes/previews/organic-grocery.svg",
        thumbnail_url="/static/images/themes/previews/organic-grocery.svg",
        brand_name="Pure Harvest",
        brand_sub="Organic & Groceries",
        subtitle="Farm-Fresh Produce, Pure Harvest & Daily Essentials",
        category_slugs=[
            "cold-pressed-mustard-oils",
            "raw-wild-honey",
            "desi-ghee-dairy-butter",
            "whole-ground-spices",
            "aromatic-rice-grains",
            "fresh-farm-vegetables",
        ],
        brand_slugs=["khaas-food", "chaldal-organic", "pran", "aci-pure", "aarong-dairy", "kazi-and-kazi"],
        assets={
            "logo_url": "/static/images/themes/grocery_organic/logo.svg",
            "logo_png_url": "/static/images/themes/grocery_organic/logo.png",
            "logo_dark_url": "/static/images/themes/grocery_organic/logo_dark.svg",
            "favicon_url": "/static/images/themes/grocery_organic/favicon.svg",
            "favicon_ico_url": "/static/images/themes/grocery_organic/favicon.ico",
        },
        design_tokens={
            "primary": "#1e7a32",
            "primary_hover": "#165e26",
            "primary_light": "#edf6ea",
            "accent": "#f6c431",
            "text_on_primary": "#ffffff",
            "hero_gradient_start": "#faf9f3",
            "hero_gradient_end": "#f2f5eb",
            "dark_primary": "#34d399",
            "dark_accent": "#fbbf24",
            "badge_radius": "9999px",
            "button_radius": "9999px",
            "card_radius": "1.125rem",
            "font_family": 'Plus Jakarta Sans, Hind Siliguri, -apple-system, BlinkMacSystemFont, sans-serif',
        },
        copywriting={
            "hero_headline_en": "Farm-Fresh Organic Food & Daily Groceries in 1 Hour",
            "hero_headline_bn": "খাঁটি অর্গানিক খাদ্য ও নিত্যপ্রয়োজনীয় বাজার ১ ঘণ্টায়",
            "hero_tagline_en": "Direct farm harvest, cold-pressed oils, natural Sundarban honey & daily cooking essentials.",
            "hero_tagline_bn": "ফরমালিনমুক্ত তাজা শাকসবজি, খাঁটি মধু ও সরিষার তেল ঘরে বসেই অর্ডার করুন।",
            "hero_badge_en": "100% Organic & Chemical-Free",
            "hero_badge_bn": "১০০% প্রাকৃতিক ও রাসায়নিকমুক্ত",
            "trust_pillars": [
                {
                    "icon": "bi-shield-check",
                    "title_en": "100% Organic & Chemical-Free",
                    "title_bn": "১০০% খাঁটি ও রাসায়নিকমুক্ত",
                    "desc_en": "Strictly zero preservatives, formalin or adulteration",
                    "desc_bn": "ফরমালিন ও প্রিজারভেটিভমুক্ত নিরাপদ খাদ্য",
                },
                {
                    "icon": "bi-stopwatch",
                    "title_en": "1-Hour Express Delivery",
                    "title_bn": "১ ঘণ্টায় দ্রুততম ডেলিভারি",
                    "desc_en": "Temperature-controlled slot delivery to your kitchen",
                    "desc_bn": "নির্ধারিত সময়ে টাটকা বাজার আপনার দরজায়",
                },
                {
                    "icon": "bi-tree",
                    "title_en": "Fresh Daily Harvest",
                    "title_bn": "সরাসরি খামার থেকে সংগৃহীত",
                    "desc_en": "Harvested at dawn and delivered crisp daily",
                    "desc_bn": "ভোরের তাজা শাকসবজি ও দেশি ফলমূল",
                },
                {
                    "icon": "bi-arrow-repeat",
                    "title_en": "Doorstep Return if Unsatisfied",
                    "title_bn": "পছন্দ না হলে সাথে সাথে ফেরত",
                    "desc_en": "Not fresh? Hand it right back with zero questions",
                    "desc_bn": "পছন্দ না হলে কোনো চার্জ ছাড়াই ফেরত দিন",
                },
            ],
        },
        supported_capabilities=[
            "slot_delivery_selector",
            "organic_certification_badge",
            "weight_unit_selector",
            "express_1hr_badge",
            "freshness_guarantee",
            "recurring_basket",
        ],
        template_mapping={
            "layout": "themes/organic-grocery/base.html",
            "header": "themes/organic-grocery/header.html",
            "footer": "themes/organic-grocery/footer.html",
            "home": "themes/organic-grocery/home.html",
            "product_card": "themes/organic-grocery/product_card.html",
            "product_list": "themes/organic-grocery/product_list.html",
            "product_detail": "themes/organic-grocery/product_detail.html",
        },
        customization_schema={
            "header": {
                "title": "Pantry Header",
                "icon": "bi-layout-navbar",
                "settings": [
                    {
                        "key": "show_slot_time_picker",
                        "label": "Show Next Delivery Slot in Header",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Display next available delivery window e.g. 'Delivering in 60 mins'",
                    },
                ],
            },
            "homepage": {
                "title": "Harvest Freshness",
                "icon": "bi-tree",
                "settings": [
                    {
                        "key": "show_freshness_pledge",
                        "label": "Show Zero Formalin Harvest Pledge",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Highlight laboratory testing & organic authenticity",
                    },
                ],
            },
            "product_display": {
                "title": "Weight & Freshness Badges",
                "icon": "bi-basket",
                "settings": [
                    {
                        "key": "show_weight_unit",
                        "label": "Display Unit / Weight on Card (e.g. per 1 kg / 500 gm)",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Show unit volume / weight clearly",
                    },
                    {
                        "key": "show_doorstep_return_badge",
                        "label": "Show Doorstep Return Guarantee Pill",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Immediate return if produce is not fresh",
                    },
                ],
            },
            "footer": {
                "title": "Freshness Assurance",
                "icon": "bi-patch-check",
                "settings": [
                    {
                        "key": "show_farm_origin_notes",
                        "label": "Show Partner Farm Geographic Origins",
                        "type": "boolean",
                        "default": True,
                        "help_text": "Direct farm sourcing locations list",
                    },
                ],
            },
        },
    )


# ==============================================================================
# GLOBAL SINGLETON INSTANCE & BOOTSTRAP
# ==============================================================================

theme_registry = ThemeRegistry()

# Register the 6 canonical themes (flagship registered first as primary default)
theme_registry.register(_build_pharmacy_healthcare_theme())
theme_registry.register(_build_marketplace_theme())
theme_registry.register(_build_tech_electronics_theme())
theme_registry.register(_build_beauty_skincare_theme())
theme_registry.register(_build_fashion_lifestyle_theme())
theme_registry.register(_build_organic_grocery_theme())
