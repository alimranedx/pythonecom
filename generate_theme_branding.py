"""
Generate bespoke, production-ready Brand Logos and Browser Favicons (SVG, PNG, ICO)
for all 6 Multi-Niche Storefront Themes in PythonEcom.
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\python\django\pythonecom"
STATIC_THEMES_DIR = os.path.join(BASE_DIR, "static", "images", "themes")
MEDIA_BRANDING_DIR = os.path.join(BASE_DIR, "media", "branding")

os.makedirs(STATIC_THEMES_DIR, exist_ok=True)
os.makedirs(MEDIA_BRANDING_DIR, exist_ok=True)

THEME_CONFIGS = {
    'mega_market': {
        'name': 'MEGA MARKET',
        'sub': 'EXPRESS SUPERSTORE',
        'primary': '#f85606',
        'accent': '#2563eb',
        'dark_text': '#0f172a',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'cart',
    },
    'tech_gadgets': {
        'name': 'TECHVERSE',
        'sub': 'GADGETS &amp; PRO GEAR',
        'primary': '#0284c7',
        'accent': '#38bdf8',
        'dark_text': '#0f172a',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'chip',
    },
    'beauty_cosmetics': {
        'name': 'GLOW &amp; GLAM',
        'sub': 'BEAUTY &amp; SKINCARE',
        'primary': '#db2777',
        'accent': '#f43f5e',
        'dark_text': '#4c0519',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'lotus',
    },
    'fashion_lifestyle': {
        'name': 'HERITAGE',
        'sub': 'FASHION &amp; COUTURE',
        'primary': '#9a3412',
        'accent': '#d97706',
        'dark_text': '#451a03',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'weave',
    },
    'grocery_organic': {
        'name': 'PURE HARVEST',
        'sub': 'ORGANIC &amp; GROCERIES',
        'primary': '#16a34a',
        'accent': '#eab308',
        'dark_text': '#14532d',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'leaf',
    },
    'pharmacy_health': {
        'name': 'AROGYA MEDS',
        'sub': 'PHARMACY &amp; HEALTHCARE',
        'primary': '#0d9488',
        'accent': '#0284c7',
        'dark_text': '#134e4a',
        'light_text': '#ffffff',
        'bg_light': '#ffffff',
        'symbol_type': 'cross',
    },
}

def get_svg_symbol(symbol_type, primary, accent, size=40):
    if symbol_type == 'cart':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <path d="M12 14h3l3.5 12h12l3-9h-18" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="19" cy="30" r="2" fill="#ffffff"/>
            <circle cx="28" cy="30" r="2" fill="#ffffff"/>
            <path d="M26 12l4-4m0 0l-4-4m4 4h-8" fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round"/>
        </g>
        '''
    elif symbol_type == 'chip':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <rect x="12" y="12" width="20" height="20" rx="4" fill="#0f172a" stroke="{accent}" stroke-width="2"/>
            <path d="M8 17h4M8 22h4M8 27h4M32 17h4M32 22h4M32 27h4M17 8v4M22 8v4M27 8v4M17 32v4M22 32v4M27 32v4" stroke="{accent}" stroke-width="1.8" stroke-linecap="round"/>
            <circle cx="22" cy="22" r="3.5" fill="{accent}"/>
        </g>
        '''
    elif symbol_type == 'lotus':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <path d="M22 10c0 6-5 12-8 15 4 0 9-3 10-6 1 3 6 6 10 6-3-3-8-9-8-15" fill="#ffffff"/>
            <path d="M22 14c0 6-3 10-5 12 3 0 6-2 7-4 1 2 4 4 7 4-2-2-5-6-5-12" fill="{accent}" opacity="0.9"/>
            <circle cx="22" cy="30" r="2.5" fill="#ffffff"/>
        </g>
        '''
    elif symbol_type == 'weave':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <path d="M14 14l16 16M14 30l16-16" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
            <rect x="16" y="16" width="12" height="12" rx="2" fill="none" stroke="{accent}" stroke-width="2.5"/>
            <circle cx="22" cy="22" r="2" fill="#ffffff"/>
        </g>
        '''
    elif symbol_type == 'leaf':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <path d="M14 28c0-8 6-14 14-14 0 8-6 14-14 14z" fill="#ffffff"/>
            <path d="M14 28c4-4 8-6 14-14" stroke="{primary}" stroke-width="2" stroke-linecap="round"/>
            <circle cx="28" cy="14" r="3" fill="{accent}"/>
        </g>
        '''
    elif symbol_type == 'cross':
        return f'''
        <g transform="translate(6, 6) scale({size/44})">
            <rect x="2" y="2" width="40" height="40" rx="10" fill="{primary}"/>
            <path d="M22 12v20M12 22h20" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
            <path d="M15 28c2-3 5-4 7-4s5 1 7 4" fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round"/>
        </g>
        '''
    return ''

def generate_theme_logos_and_favicons():
    print("Starting generation of theme Brand Logos and Favicons...")
    for theme_key, cfg in THEME_CONFIGS.items():
        theme_dir = os.path.join(STATIC_THEMES_DIR, theme_key)
        os.makedirs(theme_dir, exist_ok=True)
        
        # 1. Light Logo SVG
        symbol_svg = get_svg_symbol(cfg['symbol_type'], cfg['primary'], cfg['accent'], size=42)
        logo_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 54" width="280" height="54">
            <defs>
                <style>
                    .brand-title {{ font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; font-weight: 800; font-size: 20px; letter-spacing: -0.5px; fill: {cfg['dark_text']}; }}
                    .brand-sub {{ font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; font-weight: 700; font-size: 9px; letter-spacing: 2px; fill: {cfg['primary']}; text-transform: uppercase; }}
                </style>
            </defs>
            {symbol_svg}
            <text x="60" y="27" class="brand-title">{cfg['name']}</text>
            <text x="60" y="42" class="brand-sub">{cfg['sub']}</text>
        </svg>'''
        
        # 2. Dark Logo SVG
        logo_dark_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 54" width="280" height="54">
            <defs>
                <style>
                    .brand-title-dark {{ font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; font-weight: 800; font-size: 20px; letter-spacing: -0.5px; fill: {cfg['light_text']}; }}
                    .brand-sub-dark {{ font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; font-weight: 700; font-size: 9px; letter-spacing: 2px; fill: {cfg['accent']}; text-transform: uppercase; }}
                </style>
            </defs>
            {symbol_svg}
            <text x="60" y="27" class="brand-title-dark">{cfg['name']}</text>
            <text x="60" y="42" class="brand-sub-dark">{cfg['sub']}</text>
        </svg>'''
        
        # 3. Favicon SVG
        favicon_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
            <rect width="64" height="64" rx="16" fill="{cfg['primary']}"/>
            <g transform="translate(10, 10) scale(1)">
                {get_svg_symbol(cfg['symbol_type'], cfg['primary'], cfg['accent'], size=44)}
            </g>
        </svg>'''
        
        # Write SVGs
        with open(os.path.join(theme_dir, "logo.svg"), "w", encoding="utf-8") as f:
            f.write(logo_svg)
        with open(os.path.join(theme_dir, "logo_dark.svg"), "w", encoding="utf-8") as f:
            f.write(logo_dark_svg)
        with open(os.path.join(theme_dir, "favicon.svg"), "w", encoding="utf-8") as f:
            f.write(favicon_svg)
            
        # Copy to media/branding
        with open(os.path.join(MEDIA_BRANDING_DIR, f"{theme_key}_logo.svg"), "w", encoding="utf-8") as f:
            f.write(logo_svg)
        with open(os.path.join(MEDIA_BRANDING_DIR, f"{theme_key}_favicon.svg"), "w", encoding="utf-8") as f:
            f.write(favicon_svg)
            
        # 4. Generate Raster PNGs using Pillow
        # Favicon PNG (64x64) and Favicon ICO
        fav_img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        fav_draw = ImageDraw.Draw(fav_img)
        fav_draw.rounded_rectangle([2, 2, 62, 62], radius=16, fill=cfg['primary'])
        fav_draw.rounded_rectangle([14, 14, 50, 50], radius=8, outline="white", width=3)
        fav_draw.ellipse([26, 26, 38, 38], fill="white")
        fav_img.save(os.path.join(theme_dir, "favicon.png"), "PNG")
        fav_img.save(os.path.join(MEDIA_BRANDING_DIR, f"{theme_key}_favicon.png"), "PNG")
        
        # Save multi-size .ico
        fav_img.save(os.path.join(theme_dir, "favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        fav_img.save(os.path.join(MEDIA_BRANDING_DIR, f"{theme_key}_favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        
        # Logo PNG (300x60)
        logo_img = Image.new("RGBA", (320, 64), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_img)
        # Symbol badge
        logo_draw.rounded_rectangle([6, 8, 54, 56], radius=12, fill=cfg['primary'])
        logo_draw.rounded_rectangle([18, 20, 42, 44], radius=6, outline="white", width=2)
        logo_draw.ellipse([26, 28, 34, 36], fill="white")
        
        # Text
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 20)
            font_sub = ImageFont.truetype("arial.ttf", 10)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()
            
        logo_draw.text((68, 12), cfg['name'], font=font_title, fill=cfg['dark_text'])
        logo_draw.text((68, 38), cfg['sub'], font=font_sub, fill=cfg['primary'])
        logo_img.save(os.path.join(theme_dir, "logo.png"), "PNG")
        logo_img.save(os.path.join(MEDIA_BRANDING_DIR, f"{theme_key}_logo.png"), "PNG")
        
        # Dark Logo PNG
        logo_dark_img = Image.new("RGBA", (320, 64), (0, 0, 0, 0))
        logo_dark_draw = ImageDraw.Draw(logo_dark_img)
        logo_dark_draw.rounded_rectangle([6, 8, 54, 56], radius=12, fill=cfg['primary'])
        logo_dark_draw.rounded_rectangle([18, 20, 42, 44], radius=6, outline="white", width=2)
        logo_dark_draw.ellipse([26, 28, 34, 36], fill="white")
        logo_dark_draw.text((68, 12), cfg['name'], font=font_title, fill="#ffffff")
        logo_dark_draw.text((68, 38), cfg['sub'], font=font_sub, fill=cfg['accent'])
        logo_dark_img.save(os.path.join(theme_dir, "logo_dark.png"), "PNG")
        
        print(f"Generated brand logo and favicon assets for: {theme_key}")

    print("All theme branding assets generated successfully!")

if __name__ == '__main__':
    generate_theme_logos_and_favicons()
