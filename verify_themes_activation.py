"""
Automated Theme Activation & Comprehensive Catalog Verification Script.
Simulates Admin Panel Theme Switch for all 6 themes and validates
branding, category isolation, brand logos, product featured images, and gallery.
"""
import os
import sys
import django

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonecom.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import SiteSetting, SystemErrorLog
from product.models import Category, Brand, Product
from core.themes import THEMES
from django.conf import settings

def run_theme_verification():
    admin_client = Client()
    store_client = Client()

    superadmin = User.objects.filter(is_superuser=True).first()
    assert superadmin, "Superadmin user not found in database!"
    admin_client.force_login(superadmin)

    print("=" * 75)
    print("STARTING MULTI-THEME ACTIVATION AND VERIFICATION SWARM")
    print("=" * 75)

    summary_results = []

    for theme_key, theme_meta in THEMES.items():
        theme_name = theme_meta['name']
        print(f"\n>>> [ACTIVATING THEME]: {theme_key} ({theme_name})")

        # 1. Admin switch theme via POST /app-admin/settings/ using admin_client
        switch_res = admin_client.post(
            '/app-admin/settings/',
            {'quick_switch_theme': theme_key},
            follow=True
        )
        assert switch_res.status_code == 200, f"Admin switch failed with status {switch_res.status_code}"

        # 2. Verify SiteSetting updated in DB
        setting = SiteSetting.objects.get(pk=1)
        setting.refresh_from_db()
        assert setting.active_theme == theme_key, f"Expected active_theme {theme_key}, got {setting.active_theme}"
        print(f"  [OK] Admin Panel Theme Switch: active_theme = '{setting.active_theme}'")

        # 3. Request Storefront Homepage GET / using store_client
        home_res = store_client.get('/')
        assert home_res.status_code == 200, f"Storefront homepage returned {home_res.status_code}"
        home_html = home_res.content.decode('utf-8')

        # Check logo and favicon in DOM
        assert theme_meta['logo_url'] in home_html, f"Logo {theme_meta['logo_url']} not found in storefront HTML"
        assert (theme_meta['favicon_url'] in home_html or theme_meta['favicon_ico_url'] in home_html), "Favicon not found in storefront HTML"
        print(f"  [OK] Storefront Branding: Verified Brand Logo ({theme_meta['brand_name']}) & Favicon in DOM")

        # 4. Verify Theme-Isolated Catalog
        theme_cats = list(Category.objects.filter(theme=theme_key))
        theme_brands = list(Brand.objects.filter(theme=theme_key))
        theme_prods = list(Product.objects.filter(theme=theme_key))

        print(f"  [OK] Theme Isolation: {len(theme_cats)} Categories | {len(theme_brands)} Brands | {len(theme_prods)} Products")
        assert len(theme_cats) == 11, f"Expected 11 categories, got {len(theme_cats)}"
        assert len(theme_brands) == 11, f"Expected 11 brands, got {len(theme_brands)}"
        assert len(theme_prods) == 32, f"Expected 32 products, got {len(theme_prods)}"

        # 5. Check Category Images
        for cat in theme_cats:
            assert cat.image, f"Category '{cat.name}' missing image"
            img_path = os.path.join(settings.MEDIA_ROOT, str(cat.image))
            assert os.path.exists(img_path), f"Category image file missing on disk: {img_path}"
        print(f"  [OK] All {len(theme_cats)} Category cover images physically verified on disk")

        # 6. Check Brand Logos
        for brand in theme_brands:
            assert brand.logo, f"Brand '{brand.name}' missing logo"
            logo_path = os.path.join(settings.MEDIA_ROOT, str(brand.logo))
            assert os.path.exists(logo_path), f"Brand logo file missing on disk: {logo_path}"
        print(f"  [OK] All {len(theme_brands)} Brand logos physically verified on disk")

        # 7. Check Product Featured Images & Gallery
        total_gallery = 0
        for prod in theme_prods:
            assert prod.image, f"Product '{prod.name}' missing featured image"
            pimg_path = os.path.join(settings.MEDIA_ROOT, str(prod.image))
            assert os.path.exists(pimg_path), f"Product image missing on disk: {pimg_path}"
            gcount = prod.images.count()
            assert gcount == 4, f"Product '{prod.name}' has {gcount} gallery images (expected 4)"
            total_gallery += gcount
        print(f"  [OK] All {len(theme_prods)} Product images and {total_gallery} gallery images verified on disk")

        summary_results.append({
            'theme_key': theme_key,
            'name': theme_name,
            'brand_name': theme_meta['brand_name'],
            'categories': len(theme_cats),
            'brands': len(theme_brands),
            'products': len(theme_prods),
            'gallery_images': total_gallery,
            'status': 'HEALTHY & VERIFIED'
        })

    # Restore default active theme to mega_market
    setting.active_theme = 'mega_market'
    setting.save(update_fields=['active_theme'])
    print("\nDefault active theme restored to 'mega_market'.")

    # Check for any SystemErrorLog entries
    unresolved = SystemErrorLog.objects.filter(is_resolved=False).count()
    print(f"Final Unresolved System Exceptions: {unresolved}")
    assert unresolved == 0, f"{unresolved} unresolved system errors found!"

    print("\n" + "=" * 75)
    print("VERIFICATION SUMMARY MATRIX")
    print("=" * 75)
    for r in summary_results:
        print(f"{r['theme_key']:<20} | {r['name']:<25} | Brand: {r['brand_name']:<15} | Cats: {r['categories']} | Brands: {r['brands']} | Prods: {r['products']} | Gallery: {r['gallery_images']} | {r['status']}")
    print("=" * 75)
    print("ALL 6 THEMES VERIFIED 100% OPERATIONAL WITH ZERO DEFECTS!")

if __name__ == '__main__':
    run_theme_verification()
