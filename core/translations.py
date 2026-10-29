"""
Storefront Bilingual Translation Catalog (English & Bangla)
Provides translations for the public customer storefront while preserving
strict English-only operation for administrative back-office portals.
"""

TRANSLATIONS = {
    'en': {
        # Navigation & Topbar
        'home': 'Home',
        'all_products': 'All Products',
        'categories': 'Categories',
        'flash_deals': 'Flash Deals',
        'featured': 'Featured Deals',
        'search_placeholder': 'Search products, brands, or categories...',
        'search_btn': 'Search',
        'all_categories': 'All Categories',
        'account': 'Account',
        'wishlist': 'Wishlist',
        'cart': 'Bag',
        'shopping_bag': 'Shopping Bag',
        'sign_in': 'Sign In',
        'create_account': 'Create Account',
        'dashboard': 'Dashboard',
        'my_orders': 'My Orders',
        'edit_profile': 'Edit Profile',
        'address_book': 'Address Book',
        'logout': 'Logout',
        'signed_in_as': 'Signed in as',

        # Announcement Bar
        'free_shipping_bar': 'Free Express Shipping on orders over ৳500!',
        'customer_care': '24/7 Customer Care',

        # Sub-Navigation Shortcuts
        'laptops': 'Laptops',
        'smartphones': 'Smartphones',
        'fashion': 'Fashion',
        'audio': 'Audio',
        'watches': 'Watches',
        'flash_sale_active': 'Flash Sale Active',

        # Value Propositions (Root Route / Home)
        'free_shipping': 'Free Shipping',
        'orders_over_500': 'On orders over ৳500',
        'authentic': '100% Authentic',
        'brand_warranty': 'Direct brand warranty',
        'days_return': '30 Days Return',
        'hassle_free_returns': 'Easy hassle-free returns',
        'vip_support': '24/7 VIP Support',
        'dedicated_team': 'Dedicated expert team',

        # Home Sections
        'shop_by_category': 'Shop by Category',
        'shop_by_category_sub': 'Explore our extensive curated catalog',
        'view_all': 'View All',
        'ends_soon': 'Ends Soon!',
        'flash_deals_sub': 'Limited time special promotional prices',
        'trending_products': 'Trending Products',
        'trending_products_sub': 'Top rated customer picks',
        'shop_all': 'Shop All',
        'official_store': 'Official Store',
        'official_brand': 'Official',

        # Product Cards & Actions
        'in_stock': 'In Stock',
        'out_of_stock': 'Out of Stock',
        'add_to_cart': 'Add to Cart',
        'quick_add': 'Quick Add',
        'save': 'Save',
        'off': 'OFF',
        'shop_deal_now': 'Shop Deal Now',
        'view_details': 'View Details',
        'save_to_wishlist': 'Save to Wishlist',
        'authentic_guarantee': 'Authentic Guarantee',
        'free_express_delivery': 'Free Express Delivery',
        'returns_guarantee': '30-Day Hassle-Free Returns',

        # Cart Drawer & Mini-Bag
        'shopping_bag_empty': 'Your shopping bag is empty',
        'shopping_bag_empty_sub': 'Start exploring fresh daily essentials and grocery items.',
        'start_shopping': 'Start Shopping',
        'subtotal': 'Subtotal',
        'delivery_fee': 'Delivery Fee',
        'free': 'FREE',
        'grand_total': 'Grand Total',
        'proceed_to_checkout': 'Proceed to Checkout',
        'view_full_bag': 'View Full Bag Details',
        'unlocked_free_delivery': 'You unlocked FREE Delivery!',
        'add_more_prefix': 'Add',
        'for_free_delivery': 'for FREE Delivery!',
        'items_count': 'Items',
        'single_item': 'Item',

        # Footer
        'footer_desc': 'Enterprise-ready multi-category e-commerce platform built on Django, featuring role-based back-office security and high-converting storefront design.',
        'quick_links': 'Quick Links',
        'track_orders': 'Track Orders',
        'shop_catalog': 'Shop Catalog',
        'order_history': 'Order History',
        'cart_checkout': 'Cart & Checkout',
        'all_rights_reserved': 'All rights reserved.',
        'help_support': 'Help & Support',
    },
    'bn': {
        # Navigation & Topbar
        'home': 'হোম',
        'all_products': 'সকল পণ্য',
        'categories': 'ক্যাটাগরি',
        'flash_deals': 'ফ্ল্যাশ ডিল',
        'featured': 'সেরা অফার',
        'search_placeholder': 'পণ্য, ব্র্যান্ড বা ক্যাটাগরি খুঁজুন...',
        'search_btn': 'অনুসন্ধান',
        'all_categories': 'সকল ক্যাটাগরি',
        'account': 'অ্যাকাউন্ট',
        'wishlist': 'উইশলিস্ট',
        'cart': 'ব্যাগ',
        'shopping_bag': 'শপিং ব্যাগ',
        'sign_in': 'লগইন',
        'create_account': 'রেজিস্টার',
        'dashboard': 'ড্যাশবোর্ড',
        'my_orders': 'আমার অর্ডারসমূহ',
        'edit_profile': 'প্রোফাইল পরিবর্তন',
        'address_book': 'ঠিকানা বই',
        'logout': 'লগআউট',
        'signed_in_as': 'লগইন আছেন',

        # Announcement Bar
        'free_shipping_bar': '৳৫০০ এর বেশি অর্ডারে ফ্রি এক্সপ্রেস ডেলিভারি!',
        'customer_care': '২৪/৭ কাস্টমার কেয়ার',

        # Sub-Navigation Shortcuts
        'laptops': 'ল্যাপটপ',
        'smartphones': 'স্মার্টফোন',
        'fashion': 'ফ্যাশন',
        'audio': 'অডিও ও সাউন্ড',
        'watches': 'ঘড়ি',
        'flash_sale_active': 'ফ্ল্যাশ সেল চলছে',

        # Value Propositions (Root Route / Home)
        'free_shipping': 'ফ্রি ডেলিভারি',
        'orders_over_500': '৳৫০০ এর বেশি অর্ডারে',
        'authentic': '১০০% আসল পণ্য',
        'brand_warranty': 'অফিসিয়াল ব্র্যান্ড ওয়ারেন্টি',
        'days_return': '৩০ দিনের রিটার্ন',
        'hassle_free_returns': 'সহজ ও ঝামেলামুক্ত রিটার্ন',
        'vip_support': '২৪/৭ ভিআইপি সাপোর্ট',
        'dedicated_team': 'দক্ষ বিশেষজ্ঞ টিম',

        # Home Sections
        'shop_by_category': 'ক্যাটাগরি অনুযায়ী কিনুন',
        'shop_by_category_sub': 'আমাদের বিশাল পণ্য কালেকশন থেকে বেছে নিন',
        'view_all': 'সব দেখুন',
        'ends_soon': 'দ্রুত শেষ হচ্ছে!',
        'flash_deals_sub': 'সীমিত সময়ের বিশেষ মূল্যছাড় ও অফার',
        'trending_products': 'জনপ্রিয় পণ্যসমূহ',
        'trending_products_sub': 'ক্রেতাদের পছন্দের সেরা পণ্য',
        'shop_all': 'সব কিনুন',
        'official_store': 'অফিসিয়াল স্টোর',
        'official_brand': 'অফিসিয়াল',

        # Product Cards & Actions
        'in_stock': 'স্টকে আছে',
        'out_of_stock': 'স্টক শেষ',
        'add_to_cart': 'ব্যাগে যোগ করুন',
        'quick_add': 'দ্রুত যোগ',
        'save': 'বাঁচবে',
        'off': 'ছাড়',
        'shop_deal_now': 'অফারটি কিনুন',
        'view_details': 'বিস্তারিত দেখুন',
        'save_to_wishlist': 'উইশলিস্টে রাখুন',
        'authentic_guarantee': 'আসল পণ্যের গ্যারান্টি',
        'free_express_delivery': 'ফ্রি এক্সপ্রেস ডেলিভারি',
        'returns_guarantee': '৩০ দিনের সহজ রিটার্ন',

        # Cart Drawer & Mini-Bag
        'shopping_bag_empty': 'আপনার শপিং ব্যাগটি খালি',
        'shopping_bag_empty_sub': 'নিত্যপ্রয়োজনীয় গ্রোসারি ও সেরা পণ্যগুলো কেনাকাটা শুরু করুন।',
        'start_shopping': 'কেনাকাটা শুরু করুন',
        'subtotal': 'মোট মূল্য',
        'delivery_fee': 'ডেলিভারি চার্জ',
        'free': 'ফ্রি',
        'grand_total': 'সর্বমোট',
        'proceed_to_checkout': 'অর্ডার সম্পন্ন করুন',
        'view_full_bag': 'সম্পূর্ণ ব্যাগ দেখুন',
        'unlocked_free_delivery': 'আপনি ফ্রি ডেলিভারি পেয়েছেন!',
        'add_more_prefix': 'আরও',
        'for_free_delivery': 'যোগ করলেই ফ্রি ডেলিভারি!',
        'items_count': 'টি পণ্য',
        'single_item': 'টি পণ্য',

        # Footer
        'footer_desc': 'বাংলাদেশের আধুনিকতম ও সুরক্ষিত ই-কমার্স প্ল্যাটফর্ম, বিশ্বমানের শপিং অভিজ্ঞতা এবং দ্রুততম ডেলিভারি সেবা।',
        'quick_links': 'প্রয়োজনীয় লিংক',
        'track_orders': 'অর্ডার ট্র্যাক করুন',
        'shop_catalog': 'পণ্য ক্যাটালগ',
        'order_history': 'অর্ডারের ইতিহাস',
        'cart_checkout': 'কার্ট ও চেকআউট',
        'all_rights_reserved': 'সর্বস্বত্ব সংরক্ষিত।',
        'help_support': 'সাহায্য ও সাপোর্ট',
    }
}

STRING_TO_KEY = {
    'home': 'home',
    'all products': 'all_products',
    'categories': 'categories',
    'flash deals': 'flash_deals',
    'featured': 'featured',
    'search': 'search_btn',
    'all categories': 'all_categories',
    'account': 'account',
    'wishlist': 'wishlist',
    'cart': 'cart',
    'shopping bag': 'shopping_bag',
    'sign in': 'sign_in',
    'login': 'sign_in',
    'create account': 'create_account',
    'register': 'create_account',
    'dashboard': 'dashboard',
    'my orders': 'my_orders',
    'edit profile': 'edit_profile',
    'address book': 'address_book',
    'logout': 'logout',
    'free shipping': 'free_shipping',
    '100% authentic': 'authentic',
    '30 days return': 'days_return',
    '24/7 vip support': 'vip_support',
    'shop by category': 'shop_by_category',
    'view all': 'view_all',
    'ends soon!': 'ends_soon',
    'trending products': 'trending_products',
    'shop all': 'shop_all',
    'add to cart': 'add_to_cart',
    'in stock': 'in_stock',
    'out of stock': 'out_of_stock',
    'quick add': 'quick_add',
    'save': 'save',
    'off': 'off',
    'shop deal now': 'shop_deal_now',
    'subtotal': 'subtotal',
    'delivery fee': 'delivery_fee',
    'free': 'free',
    'grand total': 'grand_total',
    'proceed to checkout': 'proceed_to_checkout',
    'view full bag details': 'view_full_bag',
    'quick links': 'quick_links',
    'customer care': 'customer_care',
    'track orders': 'track_orders',
}


def to_bn_number(number_val):
    """Convert western numerals 0-9 to Bengali numerals ০-৯."""
    bn_digits = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    return ''.join(bn_digits.get(ch, ch) for ch in str(number_val))


class TranslationProxy:
    """Helper wrapper for effortless dictionary and attribute access in Django templates."""
    def __init__(self, lang='en'):
        self.lang = lang if lang in ('en', 'bn') else 'en'
        self._dict = TRANSLATIONS.get(self.lang, TRANSLATIONS['en'])
        self._fallback = TRANSLATIONS['en']

    def __getattr__(self, name):
        return self._dict.get(name, self._fallback.get(name, name))

    def __getitem__(self, name):
        return self._dict.get(name, self._fallback.get(name, name))

    def get(self, name, default=None):
        return self._dict.get(name, self._fallback.get(name, default if default is not None else name))


def get_translation(text_or_key, lang='en'):
    """Resolve translation by key or by common English string."""
    if lang not in ('en', 'bn'):
        lang = 'en'
    lang_dict = TRANSLATIONS[lang]
    fallback_dict = TRANSLATIONS['en']

    # Direct key lookup
    if text_or_key in lang_dict:
        return lang_dict[text_or_key]

    # Normalized text lookup
    normalized = str(text_or_key).strip().lower()
    key = STRING_TO_KEY.get(normalized)
    if key and key in lang_dict:
        return lang_dict[key]

    return text_or_key
