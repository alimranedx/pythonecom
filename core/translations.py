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
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'theme': 'Theme',
        'toggle_theme': 'Toggle Dark/Light Mode',
        'menu': 'Menu',
        'apply_filters': 'Apply Filters',
        'filter_and_sort': 'Filter & Sort',
        'explore': 'Explore',

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

        # Catalog & Filter
        'show': 'Show:',
        'sort': 'Sort:',
        'newest_arrivals': 'Newest Arrivals',
        'price_low_high': 'Price: Low to High',
        'price_high_low': 'Price: High to Low',
        'name_a_z': 'Name: A to Z',
        'active_filters': 'Active Filters:',
        'in_stock_only': 'In Stock Only',
        'clear_all': 'Clear All',
        'filters': 'Filters',
        'reset_all': 'Reset All',
        'brands': 'Brands',
        'all_brands': 'All Brands',
        'price_range': 'Price Range (৳)',
        'apply_price': 'Apply Price',
        'availability': 'Availability',
        'prev': 'Prev',
        'next': 'Next',
        'per_page': 'per page',

        # Product Detail
        'low_stock': 'Low Stock',
        'tax_included_notice': 'Tax included. Free Express delivery on orders over ৳500.',
        'quantity': 'Quantity:',
        'add_to_bag_btn': 'Add to Shopping Bag',
        'fast_shipping_highlight': 'Fast Shipping within 24-48h',
        'genuine_product_highlight': '100% Genuine Brand Product',
        'detailed_description': 'Detailed Description',
        'specifications': 'Specifications',
        'customer_reviews': 'Customer Reviews',
        'product_sku': 'Product SKU',
        'stock_availability': 'Stock Availability',

        # Cart Drawer & Cart Detail Page
        'shopping_bag_empty': 'Your shopping bag is empty',
        'shopping_bag_empty_sub': 'Start exploring fresh daily essentials and grocery items.',
        'start_shopping': 'Start Shopping',
        'continue_shopping': 'Continue Shopping',
        'subtotal': 'Subtotal',
        'delivery_fee': 'Delivery Fee',
        'free': 'FREE',
        'grand_total': 'Grand Total',
        'proceed_to_checkout': 'Proceed to Checkout',
        'view_full_bag': 'View Full Bag Details',
        'unlocked_free_delivery': 'Congratulations! You have unlocked Free Express Delivery!',
        'add_more_prefix': 'Add',
        'for_free_delivery': 'more for FREE Delivery!',
        'items_count': 'Items',
        'single_item': 'Item',
        'order_summary': 'Order Summary',
        'cart_review_sub': 'Review your items before proceeding to checkout',
        'secure_checkout_badge': '256-bit Secure Encrypted Checkout',
        'threshold_500': '৳500 Threshold',

        # Checkout
        'express_checkout': 'Express Checkout',
        'checkout_sub': 'Select your delivery area, schedule your convenient time slot, and confirm payment',
        'delivery_location': 'Delivery Location & Contact',
        'delivery_zone': 'Select Delivery Zone:',
        'inside_dhaka': 'Inside Dhaka City',
        'inside_dhaka_sub': 'Gulshan, Banani, Dhanmondi, Uttara, Mirpur (৳49)',
        'outside_dhaka': 'Outside Dhaka / Nationwide',
        'outside_dhaka_sub': 'All 64 Districts Courier Delivery (৳99)',
        'full_name': 'Full Name',
        'phone_number': 'Phone Number',
        'email_address': 'Email Address',
        'city_district': 'City / District',
        'delivery_address': 'Delivery Address (House, Road, Area)',
        'postal_code': 'Postal Code',
        'country': 'Country',
        'delivery_notes': 'Delivery Instructions / Landmarks (Optional)',
        'schedule_slot': 'Schedule Delivery Slot',
        'preferred_date': 'Preferred Delivery Date:',
        'preferred_time': 'Select Preferred Time Window:',
        'payment_method': 'Payment Method',
        'cod': 'Cash On Delivery (COD)',
        'cod_sub': 'Pay in cash when order arrives at your door',
        'mfs': 'Mobile Banking (MFS)',
        'mfs_sub': 'bKash, Nagad, Rocket instant settlement',
        'card': 'Credit / Debit Card',
        'card_sub': 'Visa, Mastercard, Amex secured gateway',
        'total_payable': 'Total Payable',
        'confirm_order': 'Confirm Order',

        # Customer Account & Dashboard
        'customer_signin': 'Customer Sign In',
        'customer_signin_sub': 'Access your order history and saved addresses',
        'username_or_email': 'Username or Email',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'no_account_yet': "Don't have an account yet?",
        'already_registered': 'Already registered?',
        'join_offers_sub': 'Join PythonEcom for fast checkout and exclusive offers',
        'dashboard_overview': 'Dashboard Overview',
        'change_password': 'Change Password',
        'total_orders': 'Total Orders',
        'cart_items': 'Cart Items',
        'wishlist_items': 'Wishlist Items',
        'recent_orders': 'Recent Orders',
        'order_reference': 'Order Reference',
        'date': 'Date',
        'order_status': 'Order Status',
        'payment': 'Payment',
        'action': 'Action',
        'back_to_dashboard': 'Back to Dashboard',
        'orders_track_sub': 'Track and view your past purchases',
        'wishlist_saved_sub': 'Items you have saved for later',
        'move_to_cart': 'Move to Cart',

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
        'dark_mode': 'ডার্ক মোড',
        'light_mode': 'লাইট মোড',
        'theme': 'থিম',
        'toggle_theme': 'ডার্ক/লাইট থিম পরিবর্তন',
        'menu': 'মেনু',
        'apply_filters': 'ফিল্টার প্রয়োগ করুন',
        'filter_and_sort': 'ফিল্টার ও সাজান',
        'explore': 'এক্সপ্লোর',

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

        # Catalog & Filter
        'show': 'দেখান:',
        'sort': 'সাজান:',
        'newest_arrivals': 'নতুন পণ্য',
        'price_low_high': 'মূল্য: কম থেকে বেশি',
        'price_high_low': 'মূল্য: বেশি থেকে কম',
        'name_a_z': 'নাম: ক থেকে য়',
        'active_filters': 'ফিল্টারসমূহ:',
        'in_stock_only': 'শুধুমাত্র স্টকে আছে',
        'clear_all': 'সব মুছুন',
        'filters': 'ফিল্টার',
        'reset_all': 'রিসেট করুন',
        'brands': 'ব্র্যান্ডসমূহ',
        'all_brands': 'সকল ব্র্যান্ড',
        'price_range': 'মূল্যের সীমা (৳)',
        'apply_price': 'ফিল্টার করুন',
        'availability': 'লভ্যতা',
        'prev': 'পূর্ববর্তী',
        'next': 'পরবর্তী',
        'per_page': 'প্রতি পেজে',

        # Product Detail
        'low_stock': 'সীমিত স্টক',
        'tax_included_notice': 'ভ্যাট অন্তর্ভুক্ত। ৳৫০০ এর বেশি অর্ডারে ফ্রি এক্সপ্রেস ডেলিভারি।',
        'quantity': 'পরিমাণ:',
        'add_to_bag_btn': 'শপিং ব্যাগে যোগ করুন',
        'fast_shipping_highlight': '২৪-৪৮ ঘণ্টার মধ্যে দ্রুত ডেলিভারি',
        'genuine_product_highlight': '১০০% আসল ব্র্যান্ড পণ্য',
        'detailed_description': 'বিস্তারিত বিবরণ',
        'specifications': 'বৈশিষ্ট্য ও স্পেকস',
        'customer_reviews': 'গ্রাহক রিভিউ',
        'product_sku': 'পণ্য এসকেইউ (SKU)',
        'stock_availability': 'স্টক লভ্যতা',

        # Cart Drawer & Cart Detail Page
        'shopping_bag_empty': 'আপনার শপিং ব্যাগটি খালি',
        'shopping_bag_empty_sub': 'নিত্যপ্রয়োজনীয় গ্রোসারি ও সেরা পণ্যগুলো কেনাকাটা শুরু করুন।',
        'start_shopping': 'কেনাকাটা শুরু করুন',
        'continue_shopping': 'আরও কেনাকাটা করুন',
        'subtotal': 'মোট মূল্য',
        'delivery_fee': 'ডেলিভারি চার্জ',
        'free': 'ফ্রি',
        'grand_total': 'সর্বমোট',
        'proceed_to_checkout': 'অর্ডার সম্পন্ন করুন',
        'view_full_bag': 'সম্পূর্ণ ব্যাগ দেখুন',
        'unlocked_free_delivery': 'অভিনন্দন! আপনি ফ্রি ডেলিভারি পেয়েছেন!',
        'add_more_prefix': 'আরও',
        'for_free_delivery': 'যোগ করলেই ফ্রি ডেলিভারি!',
        'items_count': 'টি পণ্য',
        'single_item': 'টি পণ্য',
        'order_summary': 'অর্ডার বিবরণী',
        'cart_review_sub': 'চেকআউট করার পূর্বে আপনার পণ্যগুলো যাচাই করুন',
        'secure_checkout_badge': 'নিরাপদ ও এনক্রিপ্টেড চেকআউট',
        'threshold_500': '৳৫০০ এর লিমিট',

        # Checkout
        'express_checkout': 'এক্সপ্রেস চেকআউট',
        'checkout_sub': 'ডেলিভারি এরিয়া ও সুবিধাজনক সময় নির্বাচন করে অর্ডার সম্পন্ন করুন',
        'delivery_location': 'ডেলিভারির ঠিকানা ও তথ্য',
        'delivery_zone': 'ডেলিভারি জোন নির্বাচন করুন:',
        'inside_dhaka': 'ঢাকা শহরের ভেতর',
        'inside_dhaka_sub': 'গুলশান, বনানী, ধানমন্ডি, উত্তরা, মিরপুর (৳৪৯)',
        'outside_dhaka': 'ঢাকার বাইরে / সারাদেশে',
        'outside_dhaka_sub': 'সারাদেশের ৬৪ জেলায় কুরিয়ার ডেলিভারি (৳৯৯)',
        'full_name': 'পুরো নাম',
        'phone_number': 'মোবাইল নম্বর',
        'email_address': 'ইমেইল ঠিকানা',
        'city_district': 'শহর / জেলা',
        'delivery_address': 'ডেলিভারি ঠিকানা (বাসা, রোড, এলাকা)',
        'postal_code': 'পোস্টাল কোড',
        'country': 'দেশ',
        'delivery_notes': 'ডেলিভারি সংক্রান্ত নির্দেশনা (ঐচ্ছিক)',
        'schedule_slot': 'ডেলিভারি সময়সূচি',
        'preferred_date': 'ডেলিভারির তারিখ:',
        'preferred_time': 'সুবিধাজনক সময় নির্বাচন করুন:',
        'payment_method': 'পেমেন্ট পদ্ধতি',
        'cod': 'ক্যাশ অন ডেলিভারি (COD)',
        'cod_sub': 'পণ্য হাতে পেয়ে মূল্য পরিশোধ করুন',
        'mfs': 'মোবাইল ব্যাংকিং (বিকাশ / নগদ / রকেট)',
        'mfs_sub': 'বিকাশ, নগদ ও রকেটের মাধ্যমে পেমেন্ট',
        'card': 'ক্রেডিট / ডেবিট কার্ড',
        'card_sub': 'ভিসা, মাস্টারকার্ড ও অ্যামেক্স কার্ড পেমেন্ট',
        'total_payable': 'সর্বমোট প্রদেয়',
        'confirm_order': 'অর্ডার কনফার্ম করুন',

        # Customer Account & Dashboard
        'customer_signin': 'কাস্টমার লগইন',
        'customer_signin_sub': 'আপনার অর্ডার ও সংরক্ষিত ঠিকানা দেখতে লগইন করুন',
        'username_or_email': 'ইউজারনেম অথবা ইমেইল',
        'password': 'পাসওয়ার্ড',
        'confirm_password': 'পাসওয়ার্ড নিশ্চিত করুন',
        'first_name': 'নামের প্রথম অংশ',
        'last_name': 'নামের শেষ অংশ',
        'no_account_yet': 'এখনও অ্যাকাউন্ট নেই?',
        'already_registered': 'ইতিমধ্যে অ্যাকাউন্ট আছে?',
        'join_offers_sub': 'দ্রুত চেকআউট ও স্পেশাল অফার পেতে অ্যাকাউন্ট তৈরি করুন',
        'dashboard_overview': 'ড্যাশবোর্ড ওভারভিউ',
        'change_password': 'পাসওয়ার্ড পরিবর্তন',
        'total_orders': 'মোট অর্ডার',
        'cart_items': 'কার্ট পণ্য',
        'wishlist_items': 'উইশলিস্ট পণ্য',
        'recent_orders': 'সাম্প্রতিক অর্ডারসমূহ',
        'order_reference': 'অর্ডার নম্বর',
        'date': 'তারিখ',
        'order_status': 'অর্ডার স্ট্যাটাস',
        'payment': 'পেমেন্ট',
        'action': 'অ্যাকশন',
        'back_to_dashboard': 'ড্যাশবোর্ডে ফিরুন',
        'orders_track_sub': 'আপনার পূর্ববর্তী সকল কেনাকাটা ও ডেলিভারি স্ট্যাটাস দেখুন',
        'wishlist_saved_sub': 'পরবর্তীতে কেনার জন্য আপনার সংরক্ষিত পণ্যসমূহ',
        'move_to_cart': 'ব্যাগে যোগ করুন',

        # Footer
        'footer_desc': 'বাংলাদেশের আধুনিকতম ও সুরক্ষিত ই-কমার্স প্ল্যাটফর্ম, বিশ্বমানের শপিং অভিজ্ঞতা এবং দ্রুততম ডেলিভারি সেবা।',
        'quick_links': 'প্রয়োজনীয় লিংক',
        'track_orders': 'অর্ডার ট্র্যাক করুন',
        'shop_catalog': 'পণ্য ক্যাটালগ',
        'order_history': 'অর্ডারের হিস্ট্রি',
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
