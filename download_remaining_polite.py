import os
import sys
import io
import time
import urllib.request
from PIL import Image, ImageOps

sys.path.insert(0, r'd:\python\django\pythonecom')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pythonecom.settings')

import django
django.setup()

from django.conf import settings
from product.models import Product, ProductImage

MEDIA_ROOT = settings.MEDIA_ROOT
PROD_DIR = os.path.join(MEDIA_ROOT, 'products')
PROD_REAL_DIR = os.path.join(PROD_DIR, 'real')
GALLERY_DIR = os.path.join(PROD_DIR, 'gallery')
GALLERY_REAL_DIR = os.path.join(GALLERY_DIR, 'real')

HEADERS = {
    'User-Agent': 'PythonEcom/2.0 (https://ecommerce.shopbusket.com; admin@shopbusket.com)'
}

ITEMS = {
    'walton-split-air-conditioner-1-5-ton': 'https://upload.wikimedia.org/wikipedia/commons/e/eb/Panasonic_AIR_CONDITIONER_INDOOR_UNIT_CS-C10KJ2_%282%29.jpg',
    'walton-inverter-refrigerator-365l': 'https://upload.wikimedia.org/wikipedia/commons/6/61/Panasonic_HOME_REFRIGERATOR_NR-C320WP-N.jpg',
    'gazi-automatic-water-pump-1-hp': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Centrifugal_Pump.jpg',
    'haier-frost-free-bottom-mount-fridge-328l': 'https://upload.wikimedia.org/wikipedia/commons/8/85/LG_refrigerator_interior.jpg',
    'panasonic-inverter-flatbed-microwave-27l': 'https://upload.wikimedia.org/wikipedia/commons/0/08/Panasonic_NN-SD69LS_20220410.jpg',
    'singer-convection-microwave-oven-30l': 'https://upload.wikimedia.org/wikipedia/commons/f/f9/California_Kitchen_Microwave_Oven.jpg',
    'haier-twin-tub-washing-machine-9kg': 'https://upload.wikimedia.org/wikipedia/commons/9/95/A_collection_of_washing_machines_in_a_laundry_shop.jpg',
    'philips-series-3000-wet-dry-electric-shaver': 'https://upload.wikimedia.org/wikipedia/commons/3/3f/2023_Golarka_Philips.jpg',
    'gazi-anti-bacterial-food-grade-water-tank-1000l': 'https://upload.wikimedia.org/wikipedia/commons/5/5c/EFTA00001994_-_Basement_storage_area_with_red_tile_flooring_white_walls_and_wooden_shelving_holding_black_plastic_bins_A_large_grey_water_tank_sits_on_the_left_surrounded_by_pipes_and_fixtures.jpg',
    'rfl-easy-twist-pedal-spin-mop-bucket': 'https://upload.wikimedia.org/wikipedia/commons/a/a8/-2022-01-14_Cleaning_brushes_and_buckets%2C_Morrisons%2C_Cromer.JPG',
    'vision-infrared-electric-cooker-2200w': 'https://upload.wikimedia.org/wikipedia/commons/7/79/Eupa_TSI-IH1880.jpg',
}

def process_and_save(img_bytes, slug):
    raw_img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    master = ImageOps.fit(raw_img, (800, 800), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    p1 = os.path.join(PROD_REAL_DIR, f"{slug}.webp")
    p2 = os.path.join(PROD_DIR, f"{slug}.webp")
    master.save(p1, 'WEBP', quality=85)
    master.save(p2, 'WEBP', quality=85)

    # 4 distinct angles
    a1 = master.copy()
    w, h = master.size
    crop_w, crop_h = int(w / 1.3), int(h / 1.3)
    a2 = master.crop(((w - crop_w) // 2, (h - crop_h) // 2, (w + crop_w) // 2, (h + crop_h) // 2)).resize((800, 800), Image.Resampling.LANCZOS)
    a3 = master.transpose(Image.FLIP_LEFT_RIGHT)
    crop_w4, crop_h4 = int(w / 1.6), int(h / 1.6)
    a4 = master.crop(((w - crop_w4) // 2, int((h - crop_h4) * 0.3), (w + crop_w4) // 2, int((h - crop_h4) * 0.3) + crop_h4)).resize((800, 800), Image.Resampling.LANCZOS)

    for idx, ang in enumerate([a1, a2, a3, a4], start=1):
        gp1 = os.path.join(GALLERY_REAL_DIR, f"{slug}-angle-{idx}.webp")
        gp2 = os.path.join(GALLERY_DIR, f"{slug}-angle-{idx}.webp")
        ang.save(gp1, 'WEBP', quality=85)
        ang.save(gp2, 'WEBP', quality=85)

for slug, url in ITEMS.items():
    time.sleep(2)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            process_and_save(data, slug)
            
            p = Product.objects.filter(slug=slug).first()
            if p:
                p.image = f"products/real/{slug}.webp"
                p.save(update_fields=['image'])
                gallery_imgs = list(ProductImage.objects.filter(product=p).order_by('id'))
                for idx in range(1, 5):
                    img_path = f"products/gallery/real/{slug}-angle-{idx}.webp"
                    if idx - 1 < len(gallery_imgs):
                        g = gallery_imgs[idx - 1]
                        g.image = img_path
                        g.save(update_fields=['image'])
                    else:
                        ProductImage.objects.create(product=p, image=img_path)
            print(f"DONE -> {slug} ({len(data)} bytes)")
    except Exception as e:
        print(f"FAILED -> {slug}: {e}")
