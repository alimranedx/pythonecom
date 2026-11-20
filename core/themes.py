"""
Multi-Niche Dynamic Theme Engine Registry for PythonEcom.
Provides centralized design tokens, color palettes, hero copy, and trust pillars
for 6 distinct e-commerce industry verticals benchmarked against leading Bangladeshi
and global platforms:
1. mega_market: Daraz / Amazon Style (General Marketplace)
2. tech_gadgets: Star Tech / Apple Gadgets Style (Laptops, Phones & Tech)
3. beauty_cosmetics: Shajgoj Style (Beauty, Skincare & Makeup)
4. fashion_lifestyle: Aarong / Sailor Style (Fashion, Apparel & Lifestyle)
5. grocery_organic: Chaldal / Khaas Food Style (Organic Food & Daily Groceries)
6. pharmacy_health: Arogga Style (Pharmacy, Medicine & Healthcare)
"""

THEME_CHOICES = (
    ('mega_market', 'General Marketplace (Daraz / Amazon Style)'),
    ('tech_gadgets', 'Laptops, Phones & Tech (Star Tech / Apple Gadgets Style)'),
    ('beauty_cosmetics', 'Beauty, Skincare & Makeup (Shajgoj Style)'),
    ('fashion_lifestyle', 'Fashion, Apparel & Lifestyle (Aarong / Sailor Style)'),
    ('grocery_organic', 'Organic Food & Daily Groceries (Chaldal / Khaas Food Style)'),
    ('pharmacy_health', 'Pharmacy, Medicine & Healthcare (Arogga Style)'),
)

THEMES = {
    'mega_market': {
        'key': 'mega_market',
        'name': 'Mega Market',
        'brand_name': 'Mega Market',
        'brand_sub': 'Express Superstore',
        'subtitle': 'General Multi-Category Marketplace',
        'benchmark': 'Daraz / Amazon Style',
        'icon': 'bi-cart4',
        'tag': 'Marketplace',
        'logo_url': '/static/images/themes/mega_market/logo.svg',
        'logo_png_url': '/static/images/themes/mega_market/logo.png',
        'logo_dark_url': '/static/images/themes/mega_market/logo_dark.svg',
        'favicon_url': '/static/images/themes/mega_market/favicon.svg',
        'favicon_ico_url': '/static/images/themes/mega_market/favicon.ico',
        # Vertical Filtering Slugs (None = All categories & brands)
        'category_slugs': None,
        'brand_slugs': None,
        # Color Tokens
        'primary': '#f85606',
        'primary_hover': '#d94400',
        'primary_light': '#fff1ec',
        'accent': '#2563eb',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#fff7ed',
        'hero_gradient_end': '#ffffff',
        'dark_primary': '#fb923c',
        'dark_accent': '#60a5fa',
        # Geometry Tokens
        'badge_radius': '9999px',
        'button_radius': '0.5rem',
        'card_radius': '0.75rem',
        # Copywriting Tokens
        'hero_headline_en': 'Biggest Deals, Endless Variety at Your Doorstep',
        'hero_headline_bn': 'সেরা ডিল ও অফুরন্ত পণ্যের সমাহার আপনার দোরগোড়ায়',
        'hero_tagline_en': 'Shop millions of products from verified sellers with express nationwide delivery across Bangladesh.',
        'hero_tagline_bn': 'সারা বাংলাদেশে দ্রুততম ক্যাশ অন ডেলিভারিতে লাখো পণ্যের বিশাল সংগ্রহ।',
        'hero_badge_en': 'Mega Marketplace Savings Festival',
        'hero_badge_bn': 'মেগা মার্কেটপ্লেস সেভিংস উৎসব',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-truck',
                'title_en': 'Nationwide Delivery',
                'title_bn': 'সারা দেশে ডেলিভারি',
                'desc_en': 'Fast doorstep delivery across all 64 districts',
                'desc_bn': '৬৪টি জেলায় দ্রুত হোম ডেলিভারি',
            },
            {
                'icon': 'bi-shield-check',
                'title_en': '100% Secure Checkout',
                'title_bn': 'নিরাপদ পেমেন্ট',
                'desc_en': 'bKash, Nagad, Visa, Mastercard & COD',
                'desc_bn': 'বিকাশ, নগদ, কার্ড ও ক্যাশ অন ডেলিভারি',
            },
            {
                'icon': 'bi-arrow-counterclockwise',
                'title_en': '7-Day Easy Returns',
                'title_bn': '৭ দিনে সহজ রিটার্ন',
                'desc_en': 'Hassle-free replacement & refund guarantee',
                'desc_bn': 'পণ্য রিটার্নে সহজ ও নিশ্চিত রিফান্ড',
            },
            {
                'icon': 'bi-tag',
                'title_en': 'Best Price Guarantee',
                'title_bn': 'সেরা মূল্যের নিশ্চয়তা',
                'desc_en': 'Direct factory & wholesaler discounts daily',
                'desc_bn': 'সেরা অফার ও বাজার সেরা দাম প্রতিদিন',
            },
        ],
    },

    'tech_gadgets': {
        'key': 'tech_gadgets',
        'name': 'Tech & Gadgets',
        'brand_name': 'TechVerse',
        'brand_sub': 'Gadgets & Pro Gear',
        'subtitle': 'Laptops, Phones & Precision Hardware',
        'benchmark': 'Star Tech / Apple Gadgets Style',
        'icon': 'bi-laptop',
        'tag': 'Electronics',
        'logo_url': '/static/images/themes/tech_gadgets/logo.svg',
        'logo_png_url': '/static/images/themes/tech_gadgets/logo.png',
        'logo_dark_url': '/static/images/themes/tech_gadgets/logo_dark.svg',
        'favicon_url': '/static/images/themes/tech_gadgets/favicon.svg',
        'favicon_ico_url': '/static/images/themes/tech_gadgets/favicon.ico',
        # Vertical Filtering Slugs
        'category_slugs': ['laptops', 'smartphones', 'pc-hardware', 'audio-gear', 'electronics-appliances', 'tablets', 'mobile-accessories'],
        'brand_slugs': ['apple', 'samsung', 'asus', 'dell', 'sony', 'logitech'],
        # Color Tokens
        'primary': '#0284c7',
        'primary_hover': '#0369a1',
        'primary_light': '#f0f9ff',
        'accent': '#38bdf8',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#0f172a',
        'hero_gradient_end': '#1e293b',
        'dark_primary': '#38bdf8',
        'dark_accent': '#818cf8',
        # Geometry Tokens
        'badge_radius': '0.375rem',
        'button_radius': '0.375rem',
        'card_radius': '0.5rem',
        # Copywriting Tokens
        'hero_headline_en': 'Next-Gen Laptops, Flagship Phones & Pro Hardware',
        'hero_headline_bn': 'লেটেস্ট ল্যাপটপ, ফ্ল্যাগশিপ স্মার্টফোন ও প্রিমিয়াম গ্যাজেট',
        'hero_tagline_en': 'Equip your digital universe with official brand warranties and up to 36 months 0% EMI financing.',
        'hero_tagline_bn': 'অফিসিয়াল ব্র্যান্ড ওয়ারেন্টি ও ০% ইএমআই সুবিধায় কেনাকাটা করুন সেরা দামে।',
        'hero_badge_en': 'Official Brand Tech 2026',
        'hero_badge_bn': 'অফিসিয়াল ব্র্যান্ড টেক ২০২৬',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-patch-check-fill',
                'title_en': 'Official Brand Warranty',
                'title_bn': 'অফিসিয়াল ব্র্যান্ড ওয়ারেন্টি',
                'desc_en': '100% manufacturer warranty claimable in BD',
                'desc_bn': 'বাংলাদেশে সরাসরি ক্লেইমেবল ব্র্যান্ড ওয়ারেন্টি',
            },
            {
                'icon': 'bi-credit-card-2-front',
                'title_en': '0% EMI Available',
                'title_bn': '০% সুদে ইএমআই সুবিধা',
                'desc_en': 'Up to 36 months zero-interest installments',
                'desc_bn': '৩৬ মাস পর্যন্ত সহজ কিস্তি সুবিধা',
            },
            {
                'icon': 'bi-lightning-charge',
                'title_en': '3-Hour Express Courier',
                'title_bn': '৩ ঘণ্টায় সুপারফাস্ট ডেলিভারি',
                'desc_en': 'Same-day express dispatch across Dhaka metro',
                'desc_bn': 'ঢাকা সিটির ভেতরে দ্রুততম ডেলিভারি',
            },
            {
                'icon': 'bi-cpu',
                'title_en': 'Verified Genuine Devices',
                'title_bn': '১০০% আসল অথেনটিক ডিভাইস',
                'desc_en': 'Original boxed products with serial verification',
                'desc_bn': 'সিলযুক্ত প্যাকেট ও অফিশিয়াল সিরিয়াল ভেরিফিকেশন',
            },
        ],
    },

    'beauty_cosmetics': {
        'key': 'beauty_cosmetics',
        'name': 'Beauty & Cosmetics',
        'brand_name': 'Glow & Glam',
        'brand_sub': 'Beauty & Skincare',
        'subtitle': 'Skincare, Makeup & Fragrance Boutique',
        'benchmark': 'Shajgoj Style',
        'icon': 'bi-gem',
        'tag': 'Beauty',
        'logo_url': '/static/images/themes/beauty_cosmetics/logo.svg',
        'logo_png_url': '/static/images/themes/beauty_cosmetics/logo.png',
        'logo_dark_url': '/static/images/themes/beauty_cosmetics/logo_dark.svg',
        'favicon_url': '/static/images/themes/beauty_cosmetics/favicon.svg',
        'favicon_ico_url': '/static/images/themes/beauty_cosmetics/favicon.ico',
        # Vertical Filtering Slugs
        'category_slugs': ['skin-care', 'makeup', 'hair-care', 'fragrances', 'beauty'],
        'brand_slugs': ['loreal', 'the-ordinary', 'cerave', 'mac', 'maybelline', 'chanel'],
        # Color Tokens
        'primary': '#db2777',
        'primary_hover': '#be185d',
        'primary_light': '#fdf2f8',
        'accent': '#f43f5e',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#fdf2f8',
        'hero_gradient_end': '#ffe4e6',
        'dark_primary': '#f472b6',
        'dark_accent': '#fda4af',
        # Geometry Tokens
        'badge_radius': '9999px',
        'button_radius': '9999px',
        'card_radius': '1rem',
        # Copywriting Tokens
        'hero_headline_en': 'Glow Authentically with Premium Skincare & Makeup',
        'hero_headline_bn': '১০০% আসল স্কিনকেয়ার ও মেকআপে রূপচর্চার নতুন অভিজ্ঞতা',
        'hero_tagline_en': 'Directly imported certified Korean, US, and UK formulations for radiant skin and timeless beauty.',
        'hero_tagline_bn': 'কোরিয়ান ও ইউরোপীয় শীর্ষ ব্র্যান্ডের আসল প্রসাধনীর নির্ভরযোগ্য সম্ভার।',
        'hero_badge_en': '100% Authentic Import',
        'hero_badge_bn': '১০০% আসল আমদানিকৃত',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-stars',
                'title_en': '100% Authentic Import',
                'title_bn': '১০০% আসল আমদানিকৃত',
                'desc_en': 'Directly sourced from authorized brand distributors',
                'desc_bn': 'অনুমোদিত আন্তর্জাতিক ডিস্ট্রিবিউটর থেকে সংগৃহীত',
            },
            {
                'icon': 'bi-heart-pulse',
                'title_en': 'Dermatologically Tested',
                'title_bn': 'ডার্মাটোলজিস্ট পরীক্ষিত',
                'desc_en': 'Certified gentle and safe for all sensitive skin types',
                'desc_bn': 'সব ধরনের ত্বকের জন্য নিরাপদ ও পরীক্ষিত',
            },
            {
                'icon': 'bi-flower1',
                'title_en': 'Cruelty-Free & Safe',
                'title_bn': 'ক্ষতিকারক কেমিক্যালমুক্ত',
                'desc_en': 'Free from parabens, harmful toxins & heavy metals',
                'desc_bn': 'ক্ষতিকারক কেমিক্যাল ও প্যারাবেনমুক্ত ফর্মুলা',
            },
            {
                'icon': 'bi-chat-heart',
                'title_en': 'Personalized Skin Guidance',
                'title_bn': 'ফ্রি স্কিনকেয়ার পরামর্শ',
                'desc_en': 'Certified aesthetic advisors ready to assist',
                'desc_bn': 'বিশেষজ্ঞ বিউটি অ্যাডভাইজারের ফ্রি পরামর্শ',
            },
        ],
    },

    'fashion_lifestyle': {
        'key': 'fashion_lifestyle',
        'name': 'Fashion & Lifestyle',
        'brand_name': 'Heritage',
        'brand_sub': 'Fashion & Couture',
        'subtitle': 'Artisanal Apparel, Festive Wear & Modern Styling',
        'benchmark': 'Aarong / Sailor Style',
        'icon': 'bi-person-heart',
        'tag': 'Fashion',
        'logo_url': '/static/images/themes/fashion_lifestyle/logo.svg',
        'logo_png_url': '/static/images/themes/fashion_lifestyle/logo.png',
        'logo_dark_url': '/static/images/themes/fashion_lifestyle/logo_dark.svg',
        'favicon_url': '/static/images/themes/fashion_lifestyle/favicon.svg',
        'favicon_ico_url': '/static/images/themes/fashion_lifestyle/favicon.ico',
        # Vertical Filtering Slugs
        'category_slugs': ['mens-panjabi', 'womens-kurti', 'formalwear', 'casual-denim', 'fashion-apparel', 'womens-dresses', 'mens-shirts', 'mens-shoes', 'womens-shoes'],
        'brand_slugs': ['aarong', 'sailor', 'apex', 'bata', 'zara'],
        # Color Tokens
        'primary': '#9a3412',
        'primary_hover': '#7c2d12',
        'primary_light': '#fff7ed',
        'accent': '#d97706',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#fefce8',
        'hero_gradient_end': '#ffedd5',
        'dark_primary': '#fb923c',
        'dark_accent': '#fbbf24',
        # Geometry Tokens
        'badge_radius': '0.25rem',
        'button_radius': '0.375rem',
        'card_radius': '0.75rem',
        # Copywriting Tokens
        'hero_headline_en': 'Handcrafted Elegance, Premium Fabrics & Modern Silhouette',
        'hero_headline_bn': 'ঐতিহ্যের ছোঁয়া ও আধুনিক ফ্যাশনের আভিজাত্য',
        'hero_tagline_en': 'Discover tailored Panjabis, artisanal Sarees, and contemporary urban ensembles crafted for distinction.',
        'hero_tagline_bn': 'আভিজাত পাঞ্জাবি, জামদানি শাড়ি ও ট্রেন্ডি লাইফস্টাইল কালেকশন ঘরে বসেই অর্ডার করুন।',
        'hero_badge_en': 'Heritage Festive Collection 2026',
        'hero_badge_bn': 'হেরিটেজ ফেস্টিভ কালেকশন ২০২৬',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-palette',
                'title_en': 'Handcrafted Artisan Weaves',
                'title_bn': 'হাতে বোনা নিখুঁত কারুকাজ',
                'desc_en': 'Crafted by traditional rural master weavers',
                'desc_bn': 'ঐতিহ্যবাহী তাঁতীদের নিখুঁত হাতের কাজ',
            },
            {
                'icon': 'bi-feather',
                'title_en': '100% Pure Organic Cotton',
                'title_bn': '১০০% প্রিমিয়াম সুতি কাপড়',
                'desc_en': 'Breathable, pre-shrunk high-count natural textiles',
                'desc_bn': 'আরামদায়ক ও টেকসই খাঁটি সুতি ফ্যাব্রিক',
            },
            {
                'icon': 'bi-scissors',
                'title_en': 'Perfect Tailored Fit',
                'title_bn': 'পারফেক্ট ফিটিং গ্যারান্টি',
                'desc_en': 'Accurate size charts with easy size replacement',
                'desc_bn': 'সাইজ না মিললে ফ্রি এক্সচেঞ্জ সুবিধা',
            },
            {
                'icon': 'bi-bag-check',
                'title_en': 'Try & Buy Delivery',
                'title_bn': 'ট্রাই অ্যান্ড বাই সুবিধা',
                'desc_en': 'Try apparel at doorstep before confirming purchase',
                'desc_bn': 'পণ্য দেখে ট্রাই করে নিশ্চিত করুন',
            },
        ],
    },

    'grocery_organic': {
        'key': 'grocery_organic',
        'name': 'Grocery & Organic Food',
        'brand_name': 'Pure Harvest',
        'brand_sub': 'Organic & Groceries',
        'subtitle': 'Farm-Fresh Produce, Pure Harvest & Daily Essentials',
        'benchmark': 'Chaldal / Khaas Food Style',
        'icon': 'bi-basket2',
        'tag': 'Organic Grocery',
        'logo_url': '/static/images/themes/grocery_organic/logo.svg',
        'logo_png_url': '/static/images/themes/grocery_organic/logo.png',
        'logo_dark_url': '/static/images/themes/grocery_organic/logo_dark.svg',
        'favicon_url': '/static/images/themes/grocery_organic/favicon.svg',
        'favicon_ico_url': '/static/images/themes/grocery_organic/favicon.ico',
        # Vertical Filtering Slugs
        'category_slugs': ['rice-grains', 'pure-oils', 'honey-dry-fruits', 'fresh-agro', 'groceries'],
        'brand_slugs': ['khaas-food', 'chaldal-organic', 'pran', 'aci', 'nestle', 'unilever'],
        # Color Tokens
        'primary': '#16a34a',
        'primary_hover': '#15803d',
        'primary_light': '#f0fdf4',
        'accent': '#eab308',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#f0fdf4',
        'hero_gradient_end': '#dcfce7',
        'dark_primary': '#4ade80',
        'dark_accent': '#facc15',
        # Geometry Tokens
        'badge_radius': '9999px',
        'button_radius': '0.75rem',
        'card_radius': '1rem',
        # Copywriting Tokens
        'hero_headline_en': 'Farm-Fresh Organic Food & Daily Groceries in 1 Hour',
        'hero_headline_bn': 'খাঁটি অর্গানিক খাদ্য ও নিত্যপ্রয়োজনীয় বাজার ১ ঘণ্টায়',
        'hero_tagline_en': 'Direct farm harvest, cold-pressed oils, natural Sundarban honey & daily cooking essentials.',
        'hero_tagline_bn': 'ফরমালিনমুক্ত তাজা শাকসবজি, খাঁটি মধু ও সরিষার তেল ঘরে বসেই অর্ডার করুন।',
        'hero_badge_en': '100% Organic & Chemical-Free',
        'hero_badge_bn': '১০০% প্রাকৃতিক ও রাসায়নিকমুক্ত',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-shield-check',
                'title_en': '100% Organic & Chemical-Free',
                'title_bn': '১০০% খাঁটি ও রাসায়নিকমুক্ত',
                'desc_en': 'Strictly zero preservatives, formalin or adulteration',
                'desc_bn': 'ফরমালিন ও প্রিজারভেটিভমুক্ত নিরাপদ খাদ্য',
            },
            {
                'icon': 'bi-stopwatch',
                'title_en': '1-Hour Express Delivery',
                'title_bn': '১ ঘণ্টায় দ্রুততম ডেলিভারি',
                'desc_en': 'Temperature-controlled slot delivery to your kitchen',
                'desc_bn': 'নির্ধারিত সময়ে টাটকা বাজার আপনার দরজায়',
            },
            {
                'icon': 'bi-tree',
                'title_en': 'Fresh Daily Harvest',
                'title_bn': 'সরাসরি খামার থেকে সংগৃহীত',
                'desc_en': 'Harvested at dawn and delivered crisp daily',
                'desc_bn': 'ভোরের তাজা শাকসবজি ও দেশি ফলমূল',
            },
            {
                'icon': 'bi-arrow-repeat',
                'title_en': 'Doorstep Return if Unsatisfied',
                'title_bn': 'পছন্দ না হলে সাথে সাথে ফেরত',
                'desc_en': 'Not fresh? Hand it right back with zero questions',
                'desc_bn': 'পছন্দ না হলে কোনো চার্জ ছাড়াই ফেরত দিন',
            },
        ],
    },

    'pharmacy_health': {
        'key': 'pharmacy_health',
        'name': 'Pharmacy & Healthcare',
        'brand_name': 'Arogya Meds',
        'brand_sub': 'Pharmacy & Healthcare',
        'subtitle': 'Licensed Prescription Medicines, Wellness & First Aid',
        'benchmark': 'Arogga Style',
        'icon': 'bi-heart-pulse',
        'tag': 'Pharmacy',
        'logo_url': '/static/images/themes/pharmacy_health/logo.svg',
        'logo_png_url': '/static/images/themes/pharmacy_health/logo.png',
        'logo_dark_url': '/static/images/themes/pharmacy_health/logo_dark.svg',
        'favicon_url': '/static/images/themes/pharmacy_health/favicon.svg',
        'favicon_ico_url': '/static/images/themes/pharmacy_health/favicon.ico',
        # Vertical Filtering Slugs
        'category_slugs': ['prescriptions', 'vitamins', 'first-aid', 'personal-hygiene'],
        'brand_slugs': ['square-pharma', 'beximco', 'dettol', 'savlon'],
        # Color Tokens
        'primary': '#0d9488',
        'primary_hover': '#0f766e',
        'primary_light': '#f0fdfa',
        'accent': '#0284c7',
        'text_on_primary': '#ffffff',
        'hero_gradient_start': '#f0fdfa',
        'hero_gradient_end': '#ccfbf1',
        'dark_primary': '#2dd4bf',
        'dark_accent': '#38bdf8',
        # Geometry Tokens
        'badge_radius': '0.375rem',
        'button_radius': '0.5rem',
        'card_radius': '0.75rem',
        # Copywriting Tokens
        'hero_headline_en': 'Certified Genuine Medicines & Comprehensive Healthcare',
        'hero_headline_bn': '১০০% আসল ও রেজিস্টার্ড ওষুধ এবং হেলথকেয়ার সল্যুশন',
        'hero_tagline_en': 'Temperature-controlled storage, DGDA licensed pharmacists, and digital prescription review.',
        'hero_tagline_bn': 'তাপমাত্রা-নিয়ন্ত্রিত সংরক্ষণ ও রেজিস্টার্ড ফার্মাসিস্টদের তত্ত্বাবধানে নির্ভরযোগ্য সেবা।',
        'hero_badge_en': 'Licensed Model Pharmacy',
        'hero_badge_bn': 'ডিজিডিএ অনুমোদিত মডেল ফার্মেসি',
        # Trust Pillars (4 items)
        'trust_pillars': [
            {
                'icon': 'bi-hospital',
                'title_en': 'Licensed Model Pharmacy',
                'title_bn': 'ডিজিডিএ অনুমোদিত মডেল ফার্মেসি',
                'desc_en': 'DGDA certified model pharmacy with registered pharmacists',
                'desc_bn': 'সরকারি লাইসেন্সপ্রাপ্ত ও রেজিস্টার্ড ফার্মাসিস্ট পরিচালিত',
            },
            {
                'icon': 'bi-snow2',
                'title_en': 'Cold-Chain Delivery',
                'title_bn': 'কোল্ড-চেইন সংরক্ষণ ব্যবস্থা',
                'desc_en': 'Strict 2-8°C refrigerated storage for insulin & biologics',
                'desc_bn': 'ইনসুলিন ও ভ্যাকসিনের জন্য সুনির্দিষ্ট তাপমাত্রা',
            },
            {
                'icon': 'bi-file-earmark-medical',
                'title_en': 'Prescription Verification',
                'title_bn': 'প্রেসক্রিপশন নিখুঁত যাচাই',
                'desc_en': 'Upload prescription for expert B.Pharm dosage audit',
                'desc_bn': 'অভিজ্ঞ ফার্মাসিস্ট দ্বারা প্রেসক্রিপশন নিরীক্ষা',
            },
            {
                'icon': 'bi-shield-plus',
                'title_en': '100% Genuine Medicine',
                'title_bn': '১০০% আসল ওষুধের নিশ্চয়তা',
                'desc_en': 'Directly procured from Square, Beximco, Incepta & Renata',
                'desc_bn': 'শীর্ষ ফার্মাসিউটিক্যালস কোম্পানি থেকে সরাসরি সংগৃহীত',
            },
        ],
    },
}

DEFAULT_THEME_KEY = 'mega_market'


def get_theme(theme_key):
    """
    Returns base theme configuration dictionary for theme_key.
    Falls back to 'mega_market' if theme_key is invalid or not registered.
    """
    if theme_key in THEMES:
        return THEMES[theme_key]
    return THEMES[DEFAULT_THEME_KEY]


def get_theme_data(theme_key, is_bangla=False):
    """
    Returns a language-resolved copy of the theme dict.
    Provides resolved shortcut properties:
    - hero_headline: bangla or english according to is_bangla
    - hero_tagline: bangla or english according to is_bangla
    - hero_badge: bangla or english according to is_bangla
    - trust_pillars: list of pillars with resolved 'title' and 'desc' keys
    """
    base = get_theme(theme_key)
    data = dict(base)
    data['hero_headline'] = base['hero_headline_bn'] if is_bangla else base['hero_headline_en']
    data['hero_tagline'] = base['hero_tagline_bn'] if is_bangla else base['hero_tagline_en']
    data['hero_badge'] = base['hero_badge_bn'] if is_bangla else base['hero_badge_en']

    resolved_pillars = []
    for p in base.get('trust_pillars', []):
        p_resolved = dict(p)
        p_resolved['title'] = p['title_bn'] if is_bangla else p['title_en']
        p_resolved['desc'] = p['desc_bn'] if is_bangla else p['desc_en']
        resolved_pillars.append(p_resolved)
    data['trust_pillars'] = resolved_pillars
    data['key'] = theme_key if theme_key in THEMES else DEFAULT_THEME_KEY
    return data
