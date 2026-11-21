"""
Multi-Niche Dynamic Theme Engine Registry for PythonEcom.

Provides centralized design tokens, color palettes, hero copy, and trust pillars
for 6 distinct e-commerce industry verticals benchmarked against leading Bangladeshi
and global platforms:
1. pharmacy-healthcare: Arogga Style (Pharmacy, Medicine & Healthcare) [FLAGSHIP THEME]
2. marketplace: Daraz / Amazon Style (General Marketplace)
3. tech-electronics: Star Tech / Apple Gadgets Style (Laptops, Phones & Tech)
4. beauty-skincare: Shajgoj Style (Beauty, Skincare & Makeup)
5. fashion-lifestyle: Aarong / Sailor Style (Fashion, Apparel & Lifestyle)
6. organic-grocery: Chaldal / Khaas Food Style (Organic Food & Daily Groceries)

This module provides 100% backward compatibility by forwarding to core.theme_registry.
"""

from typing import Dict, Any, Optional
from core.theme_registry import (
    theme_registry,
    ThemeDefinition,
    ThemeRegistryDict,
)

# Canonical Choices for Django model & form fields
THEME_CHOICES = theme_registry.get_choices()

# Legacy choices tuple kept for full backward compatibility
LEGACY_THEME_CHOICES = (
    ('pharmacy_health', 'Pharmacy, Medicine & Healthcare (Arogga Style)'),
    ('mega_market', 'General Marketplace (Daraz / Amazon Style)'),
    ('tech_gadgets', 'Laptops, Phones & Tech (Star Tech / Apple Gadgets Style)'),
    ('beauty_cosmetics', 'Beauty, Skincare & Makeup (Shajgoj Style)'),
    ('fashion_lifestyle', 'Fashion, Apparel & Lifestyle (Aarong / Sailor Style)'),
    ('grocery_organic', 'Organic Food & Daily Groceries (Chaldal / Khaas Food Style)'),
)

# Exported THEMES mapping supporting lookup by both canonical IDs and legacy keys
THEMES: ThemeRegistryDict = theme_registry.get_theme_dict()

# Flagship default theme is Pharmacy & Healthcare
DEFAULT_THEME_KEY = theme_registry.default_theme_id
DEFAULT_THEME_ID = theme_registry.default_theme_id
FLAGSHIP_THEME_KEY = theme_registry.flagship_id
LEGACY_DEFAULT_THEME_KEY = 'mega_market'


def get_theme(theme_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns base theme configuration dictionary for theme_key.
    Supports canonical IDs (e.g. 'pharmacy-healthcare', 'marketplace')
    and legacy keys (e.g. 'pharmacy_health', 'mega_market').
    Falls back to flagship default theme if theme_key is invalid or not registered.
    """
    theme = theme_registry.get(theme_key, fallback=True)
    if theme is None:
        return {}

    # If queried by a specific registered key or legacy key, preserve it under 'key'
    normalized = theme_registry.normalize_id(theme_key)
    if theme_key and normalized == theme.id:
        theme_copy = dict(theme)
        theme_copy['key'] = theme_key
        return theme_copy

    return theme


def get_theme_data(
    theme_key: Optional[str] = None,
    is_bangla: bool = False,
    custom_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Returns a language-resolved copy of the theme dict.
    Provides resolved shortcut properties:
    - hero_headline: bangla or english according to is_bangla
    - hero_tagline: bangla or english according to is_bangla
    - hero_badge: bangla or english according to is_bangla
    - trust_pillars: list of pillars with resolved 'title' and 'desc' keys
    - custom_config: applied dynamic settings and design token overrides
    """
    return theme_registry.get_theme_data(
        theme_id=theme_key,
        is_bangla=is_bangla,
        custom_config=custom_config,
    )
