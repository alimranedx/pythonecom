import os
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify

from core.models import SiteSetting
from rbac.models import Module, Submodule, Permission, Role, RolePermission, UserRole
from accounts.models import CustomerProfile, Address
from product.models import Category, Brand, Product, ProductImage, ProductReview
from orders.models import Order, OrderItem, DeliverySlot, Coupon


class Command(BaseCommand):
    help = (
        "Seeds complete marketplace database: Brand settings, RBAC modules/roles, "
        "test accounts, categories, brands, products with specs/images, reviews, coupons, and orders."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            '--dump',
            action='store_true',
            help='Export current live database records into core/fixtures/initial_seed_data.json',
        )

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'core', 'fixtures', 'initial_seed_data.json')

        # 1. Export mode
        if options.get('export'):
            self._export_fixtures(fixture_path)
            return

        # 2. Seed from Fixture if available (using resilient idempotent loader)
        if os.path.exists(fixture_path):
            self.stdout.write(self.style.NOTICE(f"==> Loading complete database fixture from {fixture_path}..."))
            count = self._load_fixture_data(fixture_path)
            self.stdout.write(self.style.SUCCESS(f"[OK] Successfully synchronized {count} database objects from fixture."))
        else:
            self.stdout.write(self.style.WARNING("==> Fixture file not found; running programmatic fallback..."))
            self._seed_rbac()
            self._seed_users()

        # 3. Always synchronize Multi-Niche Theme Catalog (Categories, Brands, Flagship Products & Multiple Gallery Images)
        self.stdout.write(self.style.NOTICE("==> Synchronizing Multi-Niche Theme Catalog & Multi-Angle Product Gallery..."))
        self._seed_catalog()

        # 4. Always synchronize RBAC modules, permissions & superuser roles
        self.stdout.write(self.style.NOTICE("==> Synchronizing RBAC Modules & Permissions..."))
        self._seed_rbac()

        # 5. Synchronize demo accounts & passwords
        self.stdout.write(self.style.NOTICE("==> Verifying Demo Accounts & Passwords..."))
        self._seed_users()

        # 6. Synchronize Store & Brand Settings
        self.stdout.write(self.style.NOTICE("==> Verifying Store & Brand Settings..."))
        self._seed_site_settings()

        # 7. Synchronize Media Assets (Images, Logos, Gallery)
        self.stdout.write(self.style.NOTICE("==> Verifying & Generating Local Media Assets (Images, Logos, Gallery)..."))
        self._ensure_media_assets()

        # 8. Print summary
        self._print_summary()

    def _export_fixtures(self, fixture_path):
        """Export all current database records into initial_seed_data.json with UTF-8 encoding."""
        self.stdout.write(self.style.NOTICE("==> Exporting current database models to fixture..."))
        os.makedirs(os.path.dirname(fixture_path), exist_ok=True)

        models_to_export = [
            User,
            CustomerProfile,
            Address,
            SiteSetting,
            Module,
            Submodule,
            Permission,
            Role,
            RolePermission,
            UserRole,
            Category,
            Brand,
            Product,
            ProductImage,
            ProductReview,
            DeliverySlot,
            Coupon,
            Order,
            OrderItem,
        ]

        all_objects = []
        for model in models_to_export:
            objs = list(model.objects.all())
            all_objects.extend(objs)

        serialized = serializers.serialize('json', all_objects, indent=2)
        with open(fixture_path, 'w', encoding='utf-8') as f:
            f.write(serialized)

        self.stdout.write(self.style.SUCCESS(
            f"[SUCCESS] Exported {len(all_objects)} database objects across {len(models_to_export)} models to {fixture_path}!"
        ))

    def _load_fixture_data(self, fixture_path):
        """
        Idempotent fixture loader that updates-or-creates objects matching on natural unique keys.
        Prevents IntegrityError duplicate key conflicts across diverse database setups.
        """
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        records = {}
        for item in data:
            records.setdefault(item['model'], []).append(item)

        user_map = {}
        for item in records.get('auth.user', []):
            f = dict(item['fields'])
            user, _ = User.objects.update_or_create(
                username=f['username'],
                defaults={
                    'email': f.get('email', ''),
                    'is_staff': f.get('is_staff', False),
                    'is_superuser': f.get('is_superuser', False),
                    'is_active': f.get('is_active', True),
                    'first_name': f.get('first_name', ''),
                    'last_name': f.get('last_name', ''),
                }
            )
            user.password = f['password']
            user.save()
            user_map[item['pk']] = user

        for item in records.get('core.sitesetting', []):
            f = dict(item['fields'])
            SiteSetting.objects.update_or_create(id=1, defaults=f)

        for item in records.get('accounts.customerprofile', []):
            f = dict(item['fields'])
            user = user_map.get(f['user']) or User.objects.filter(id=f['user']).first()
            if user:
                f['user'] = user
                CustomerProfile.objects.update_or_create(user=user, defaults=f)

        for item in records.get('accounts.address', []):
            f = dict(item['fields'])
            user = user_map.get(f['user']) or User.objects.filter(id=f['user']).first()
            if user:
                f['user'] = user
                Address.objects.update_or_create(user=user, full_name=f['full_name'], street_address=f['street_address'], defaults=f)

        module_map = {}
        for item in records.get('rbac.module', []):
            f = dict(item['fields'])
            mod, _ = Module.objects.update_or_create(code=f['code'], defaults=f)
            module_map[item['pk']] = mod

        submodule_map = {}
        for item in records.get('rbac.submodule', []):
            f = dict(item['fields'])
            mod = module_map.get(f['module']) or Module.objects.filter(id=f['module']).first()
            f['module'] = mod
            sub, _ = Submodule.objects.update_or_create(code=f['code'], defaults=f)
            submodule_map[item['pk']] = sub

        perm_map = {}
        for item in records.get('rbac.permission', []):
            f = dict(item['fields'])
            sub = submodule_map.get(f['submodule']) or Submodule.objects.filter(id=f['submodule']).first()
            f['submodule'] = sub
            perm, _ = Permission.objects.update_or_create(code=f['code'], defaults=f)
            perm_map[item['pk']] = perm

        role_map = {}
        for item in records.get('rbac.role', []):
            f = dict(item['fields'])
            role, _ = Role.objects.update_or_create(name=f['name'], defaults=f)
            role_map[item['pk']] = role

        for item in records.get('rbac.rolepermission', []):
            f = dict(item['fields'])
            role = role_map.get(f['role']) or Role.objects.filter(id=f['role']).first()
            perm = perm_map.get(f['permission']) or Permission.objects.filter(id=f['permission']).first()
            if role and perm:
                RolePermission.objects.get_or_create(role=role, permission=perm)

        for item in records.get('rbac.userrole', []):
            f = dict(item['fields'])
            user = user_map.get(f['user']) or User.objects.filter(id=f['user']).first()
            role = role_map.get(f['role']) or Role.objects.filter(id=f['role']).first()
            if user and role:
                UserRole.objects.get_or_create(user=user, role=role)

        cat_map = {}
        for item in records.get('product.category', []):
            f = dict(item['fields'])
            cat, _ = Category.objects.update_or_create(slug=f['slug'], defaults=f)
            cat_map[item['pk']] = cat

        brand_map = {}
        for item in records.get('product.brand', []):
            f = dict(item['fields'])
            brand, _ = Brand.objects.update_or_create(slug=f['slug'], defaults=f)
            brand_map[item['pk']] = brand

        prod_map = {}
        for item in records.get('product.product', []):
            f = dict(item['fields'])
            f['category'] = cat_map.get(f['category']) or Category.objects.filter(id=f['category']).first() if f.get('category') else None
            f['brand'] = brand_map.get(f['brand']) or Brand.objects.filter(id=f['brand']).first() if f.get('brand') else None
            prod, _ = Product.objects.update_or_create(slug=f['slug'], defaults=f)
            prod_map[item['pk']] = prod

        for item in records.get('product.productimage', []):
            f = dict(item['fields'])
            prod = prod_map.get(f['product']) or Product.objects.filter(id=f['product']).first()
            if prod:
                f['product'] = prod
                ProductImage.objects.update_or_create(id=item['pk'], defaults=f)

        for item in records.get('product.productreview', []):
            f = dict(item['fields'])
            prod = prod_map.get(f['product']) or Product.objects.filter(id=f['product']).first()
            user = user_map.get(f['user']) or User.objects.filter(id=f['user']).first()
            if prod and user:
                f['product'] = prod
                f['user'] = user
                ProductReview.objects.update_or_create(id=item['pk'], defaults=f)

        for item in records.get('orders.deliveryslot', []):
            f = dict(item['fields'])
            DeliverySlot.objects.update_or_create(id=item['pk'], defaults=f)

        for item in records.get('orders.coupon', []):
            f = dict(item['fields'])
            Coupon.objects.update_or_create(code=f['code'], defaults=f)

        order_map = {}
        for item in records.get('orders.order', []):
            f = dict(item['fields'])
            f['user'] = user_map.get(f['user']) or User.objects.filter(id=f['user']).first() if f.get('user') else None
            f['delivery_slot'] = DeliverySlot.objects.filter(id=f['delivery_slot']).first() if f.get('delivery_slot') else None
            f['coupon'] = Coupon.objects.filter(id=f['coupon']).first() if f.get('coupon') else None
            order, _ = Order.objects.update_or_create(id=item['pk'], defaults=f)
            order_map[item['pk']] = order

        for item in records.get('orders.orderitem', []):
            f = dict(item['fields'])
            f['order'] = order_map.get(f['order']) or Order.objects.filter(id=f['order']).first()
            f['product'] = prod_map.get(f['product']) or Product.objects.filter(id=f['product']).first() if f.get('product') else None
            if f['order']:
                OrderItem.objects.update_or_create(id=item['pk'], defaults=f)

        return len(data)

    def _seed_site_settings(self):
        """Ensure singleton SiteSetting exists with complete branding and bilingual notices."""
        setting = SiteSetting.get_settings()
        if not setting.site_name:
            setting.site_name = "Easy Purchase"
            setting.save()

    def _seed_rbac(self):
        modules_data = [
            {
                'name': 'Catalog',
                'code': 'catalog',
                'icon': 'bi-boxes',
                'order': 1,
                'submodules': [
                    {'name': 'Products', 'code': 'catalog.products', 'url_name': 'admin_product_list', 'order': 1},
                    {'name': 'Categories', 'code': 'catalog.categories', 'url_name': 'admin_category_list', 'order': 2},
                    {'name': 'Brands', 'code': 'catalog.brands', 'url_name': 'admin_brand_list', 'order': 3},
                    {'name': 'Customer Reviews', 'code': 'catalog.reviews', 'url_name': 'admin_review_list', 'order': 4},
                ]
            },
            {
                'name': 'Orders',
                'code': 'orders',
                'icon': 'bi-cart-check',
                'order': 2,
                'submodules': [
                    {'name': 'All Orders', 'code': 'orders.orders', 'url_name': 'admin_order_list', 'order': 1},
                ]
            },
            {
                'name': 'Customers',
                'code': 'customers',
                'icon': 'bi-people',
                'order': 3,
                'submodules': [
                    {'name': 'Customer Accounts', 'code': 'customers.customers', 'url_name': 'admin_customer_list', 'order': 1},
                ]
            },
            {
                'name': 'User & Role Management',
                'code': 'rbac',
                'icon': 'bi-shield-lock-fill',
                'order': 4,
                'submodules': [
                    {'name': 'User Management', 'code': 'rbac.staff', 'url_name': 'admin_staff_list', 'order': 1},
                    {'name': 'Role & Permission Management', 'code': 'rbac.roles', 'url_name': 'admin_role_list', 'order': 2},
                ]
            },
            {
                'name': 'Settings',
                'code': 'settings',
                'icon': 'bi-gear-fill',
                'order': 5,
                'submodules': [
                    {'name': 'Store & Brand Settings', 'code': 'settings.site_settings', 'url_name': 'admin_site_settings', 'order': 1},
                    {'name': 'System Error Logs', 'code': 'settings.system_errors', 'url_name': 'admin_system_errors', 'order': 2},
                ]
            },
        ]

        actions = ['view', 'create', 'edit', 'delete']

        for m_data in modules_data:
            module, _ = Module.objects.update_or_create(
                code=m_data['code'],
                defaults={'name': m_data['name'], 'icon': m_data['icon'], 'order': m_data['order']}
            )
            for s_data in m_data['submodules']:
                submodule, _ = Submodule.objects.update_or_create(
                    code=s_data['code'],
                    defaults={
                        'module': module,
                        'name': s_data['name'],
                        'url_name': s_data['url_name'],
                        'order': s_data['order']
                    }
                )
                for action in actions:
                    perm_code = f"{submodule.code}.{action}"
                    Permission.objects.update_or_create(
                        code=perm_code,
                        defaults={
                            'submodule': submodule,
                            'action': action,
                            'name': f"{action.capitalize()} {submodule.name}",
                        }
                    )

        # Setup standard roles
        roles_config = [
            {
                'name': 'Super Admin',
                'description': 'Full unrestricted back-office access to all modules and configurations.',
                'is_system_role': True,
                'perm_filter': None,  # all permissions
            },
            {
                'name': 'Catalog Manager',
                'description': 'Full management access for products, categories, and inventory.',
                'is_system_role': False,
                'perm_filter': lambda p: p.code.startswith('catalog.'),
            },
            {
                'name': 'Order Dispatcher',
                'description': 'Manages order processing, shipments, customer details.',
                'is_system_role': False,
                'perm_filter': lambda p: p.code.startswith('orders.') or p.code in ['customers.customers.view', 'catalog.products.view'],
            },
            {
                'name': 'Customer Support',
                'description': 'Read-only access to customer orders and contact details.',
                'is_system_role': False,
                'perm_filter': lambda p: p.action == 'view' and not p.code.startswith('rbac.'),
            },
        ]

        all_perms = list(Permission.objects.all())
        for r_cfg in roles_config:
            role, _ = Role.objects.update_or_create(
                name=r_cfg['name'],
                defaults={
                    'description': r_cfg['description'],
                    'is_system_role': r_cfg['is_system_role']
                }
            )
            if r_cfg['perm_filter'] is None:
                assigned_perms = all_perms
            else:
                assigned_perms = [p for p in all_perms if r_cfg['perm_filter'](p)]

            RolePermission.objects.filter(role=role).delete()
            RolePermission.objects.bulk_create([
                RolePermission(role=role, permission=p) for p in assigned_perms
            ])

    def _seed_users(self):
        users_data = [
            {
                'username': 'superadmin',
                'email': 'superadmin@pythonecom.local',
                'password': 'Admin@12345',
                'is_staff': True,
                'is_superuser': True,
                'role': 'Super Admin',
            },
            {
                'username': 'catalog_admin',
                'email': 'catalog@pythonecom.local',
                'password': 'Manager@12345',
                'is_staff': True,
                'is_superuser': False,
                'role': 'Catalog Manager',
            },
            {
                'username': 'orders_staff',
                'email': 'orders@pythonecom.local',
                'password': 'Staff@12345',
                'is_staff': True,
                'is_superuser': False,
                'role': 'Order Dispatcher',
            },
            {
                'username': 'customer_user',
                'email': 'customer@pythonecom.local',
                'password': 'User@12345',
                'is_staff': False,
                'is_superuser': False,
                'role': None,
            },
        ]

        for u_data in users_data:
            user, created = User.objects.get_or_create(username=u_data['username'])
            user.email = u_data['email']
            user.is_staff = u_data['is_staff']
            user.is_superuser = u_data['is_superuser']
            user.set_password(u_data['password'])
            user.save()

            CustomerProfile.objects.get_or_create(
                user=user,
                defaults={'phone': '+880 1712-345678'}
            )

            if u_data['role']:
                role = Role.objects.get(name=u_data['role'])
                UserRole.objects.get_or_create(user=user, role=role)

        # Create demo shipping address for customer
        customer = User.objects.get(username='customer_user')
        Address.objects.get_or_create(
            user=customer,
            street_address='House 42, Road 11, Banani',
            defaults={
                'full_name': 'John Customer',
                'phone': '+880 1819-001122',
                'apartment': 'Suite 4B',
                'city': 'Dhaka',
                'postal_code': '1213',
                'country': 'Bangladesh',
                'is_default': True,
            }
        )

    def _seed_catalog(self):
        """
        Seeds complete multi-niche taxonomy, top brands, and flagship products across all 6 themes:
        1. Mega Market (Electronics, Fashion, Grocery, Home Living)
        2. Tech & Gadgets (Laptops, Smartphones, PC Hardware, Audio Gear)
        3. Beauty & Cosmetics (Skincare, Makeup, Haircare, Fragrance)
        4. Fashion & Lifestyle (Men's Panjabi, Women's Kurti, Formalwear, Casual Denim)
        5. Organic Grocery (Rice & Grains, Pure Oils, Honey & Dry Fruits, Fresh Agro)
        6. Pharmacy & Health (Prescriptions, Vitamins, First Aid, Personal Hygiene)

        Guarantees realistic BDT prices, discount percentages, stock quantities,
        and multiple ProductImage gallery entries for every flagship product.
        """
        categories_data = [
            # Mega Market / General
            {'name': 'Electronics & Appliances', 'slug': 'electronics-appliances', 'icon': 'bi-tv', 'is_featured': True, 'order': 1},
            {'name': 'Fashion & Apparel', 'slug': 'fashion-apparel', 'icon': 'bi-bag-heart', 'is_featured': True, 'order': 2},
            {'name': 'Daily Groceries & Essentials', 'slug': 'groceries', 'icon': 'bi-basket2', 'is_featured': True, 'order': 3},
            {'name': 'Home & Living Furniture', 'slug': 'furniture', 'icon': 'bi-lamp', 'is_featured': True, 'order': 4},

            # Tech & Gadgets
            {'name': 'Laptops & Ultrabooks', 'slug': 'laptops', 'icon': 'bi-laptop', 'is_featured': True, 'order': 10},
            {'name': 'Smartphones & Mobiles', 'slug': 'smartphones', 'icon': 'bi-phone', 'is_featured': True, 'order': 11},
            {'name': 'PC Hardware & Components', 'slug': 'pc-hardware', 'icon': 'bi-cpu', 'is_featured': True, 'order': 12},
            {'name': 'Audio Gear & Headphones', 'slug': 'audio-gear', 'icon': 'bi-headphones', 'is_featured': True, 'order': 13},
            {'name': 'Tablets & E-Readers', 'slug': 'tablets', 'icon': 'bi-tablet', 'is_featured': True, 'order': 14},
            {'name': 'Mobile Accessories & Gadgets', 'slug': 'mobile-accessories', 'icon': 'bi-smartwatch', 'is_featured': True, 'order': 15},

            # Beauty & Cosmetics
            {'name': 'Skincare & Dermatological Serums', 'slug': 'skin-care', 'icon': 'bi-flower1', 'is_featured': True, 'order': 20},
            {'name': 'Makeup & Color Cosmetics', 'slug': 'makeup', 'icon': 'bi-palette', 'is_featured': True, 'order': 21},
            {'name': 'Hair Care & Deep Conditioning', 'slug': 'hair-care', 'icon': 'bi-droplet-half', 'is_featured': True, 'order': 22},
            {'name': 'Fragrances & Luxury Perfumes', 'slug': 'fragrances', 'icon': 'bi-droplet', 'is_featured': True, 'order': 23},
            {'name': 'Beauty & Personal Care', 'slug': 'beauty', 'icon': 'bi-sparkles', 'is_featured': True, 'order': 24},

            # Fashion & Lifestyle
            {'name': "Men's Panjabi & Festive Wear", 'slug': 'mens-panjabi', 'icon': 'bi-person-badge', 'is_featured': True, 'order': 30},
            {'name': "Women's Kurti & Salwar Kameez", 'slug': 'womens-kurti', 'icon': 'bi-person-hearts', 'is_featured': True, 'order': 31},
            {'name': 'Formalwear, Blazers & Suits', 'slug': 'formalwear', 'icon': 'bi-briefcase', 'is_featured': True, 'order': 32},
            {'name': 'Casual Denim, Chinos & Jeans', 'slug': 'casual-denim', 'icon': 'bi-tag', 'is_featured': True, 'order': 33},
            {'name': "Women's Fashion & Dresses", 'slug': 'womens-dresses', 'icon': 'bi-gender-female', 'is_featured': True, 'order': 34},
            {'name': "Men's Shirts & Casuals", 'slug': 'mens-shirts', 'icon': 'bi-person', 'is_featured': True, 'order': 35},
            {'name': "Men's Footwear & Shoes", 'slug': 'mens-shoes', 'icon': 'bi-shoe', 'is_featured': True, 'order': 36},
            {'name': "Women's Footwear & Heels", 'slug': 'womens-shoes', 'icon': 'bi-handbag', 'is_featured': True, 'order': 37},

            # Organic Grocery
            {'name': 'Rice & Organic Ancient Grains', 'slug': 'rice-grains', 'icon': 'bi-box-seam', 'is_featured': True, 'order': 40},
            {'name': 'Pure Cold-Pressed Oils & Desi Ghee', 'slug': 'pure-oils', 'icon': 'bi-droplet-fill', 'is_featured': True, 'order': 41},
            {'name': 'Honey, Nuts & Premium Dry Fruits', 'slug': 'honey-dry-fruits', 'icon': 'bi-sun', 'is_featured': True, 'order': 42},
            {'name': 'Fresh Organic Agro & Harvest Produce', 'slug': 'fresh-agro', 'icon': 'bi-flower2', 'is_featured': True, 'order': 43},

            # Pharmacy & Health
            {'name': 'Prescriptions & OTC Medicines', 'slug': 'prescriptions', 'icon': 'bi-capsule', 'is_featured': True, 'order': 50},
            {'name': 'Vitamins & Dietary Supplements', 'slug': 'vitamins', 'icon': 'bi-heart-pulse', 'is_featured': True, 'order': 51},
            {'name': 'First Aid & Medical Devices', 'slug': 'first-aid', 'icon': 'bi-bandaid', 'is_featured': True, 'order': 52},
            {'name': 'Personal Hygiene & Antiseptics', 'slug': 'personal-hygiene', 'icon': 'bi-shield-check', 'is_featured': True, 'order': 53},
        ]

        cat_map = {}
        for c in categories_data:
            obj, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'icon': c['icon'],
                    'is_featured': c['is_featured'],
                    'order': c['order'],
                    'image': f"categories/{c['slug']}.png"
                }
            )
            cat_map[c['slug']] = obj

        brands_data = [
            # Tech & Gadgets
            {'name': 'Apple', 'slug': 'apple'},
            {'name': 'Samsung', 'slug': 'samsung'},
            {'name': 'Asus', 'slug': 'asus'},
            {'name': 'Dell', 'slug': 'dell'},
            {'name': 'Sony', 'slug': 'sony'},
            {'name': 'Logitech', 'slug': 'logitech'},

            # Beauty & Cosmetics
            {'name': "L'Oreal", 'slug': 'loreal'},
            {'name': 'The Ordinary', 'slug': 'the-ordinary'},
            {'name': 'Cerave', 'slug': 'cerave'},
            {'name': 'MAC', 'slug': 'mac'},
            {'name': 'Maybelline', 'slug': 'maybelline'},
            {'name': 'Chanel', 'slug': 'chanel'},

            # Fashion & Lifestyle
            {'name': 'Aarong', 'slug': 'aarong'},
            {'name': 'Sailor', 'slug': 'sailor'},
            {'name': 'Apex', 'slug': 'apex'},
            {'name': 'Bata', 'slug': 'bata'},
            {'name': 'Zara', 'slug': 'zara'},

            # Organic Grocery
            {'name': 'Khaas Food', 'slug': 'khaas-food'},
            {'name': 'Chaldal Organic', 'slug': 'chaldal-organic'},
            {'name': 'Pran', 'slug': 'pran'},
            {'name': 'ACI', 'slug': 'aci'},

            # Pharmacy & Health
            {'name': 'Square Pharma', 'slug': 'square-pharma'},
            {'name': 'Beximco', 'slug': 'beximco'},
            {'name': 'Dettol', 'slug': 'dettol'},
            {'name': 'Savlon', 'slug': 'savlon'},

            # Mega Market / General
            {'name': 'Unilever', 'slug': 'unilever'},
            {'name': 'Nestle', 'slug': 'nestle'},
        ]

        brand_map = {}
        for b in brands_data:
            obj, _ = Brand.objects.update_or_create(
                slug=b['slug'],
                defaults={
                    'name': b['name'],
                    'logo': f"brands/{b['slug']}.png"
                }
            )
            brand_map[b['slug']] = obj

        products_data = [
            # ==================== TECH & GADGETS ====================
            {
                'slug': 'macbook-pro-16-m3-max',
                'name': 'MacBook Pro 16" Liquid Retina XDR (M3 Max / 36GB / 1TB SSD)',
                'category': 'laptops',
                'brand': 'apple',
                'short_description': 'Supercharged by Apple M3 Max with 16-core CPU, 40-core GPU, and up to 22 hours battery life.',
                'description': 'The Apple MacBook Pro 16" with M3 Max is engineered for extreme professional workflows: 3D rendering, machine learning modeling, and 8K ProRes video editing. Features a Liquid Retina XDR display with 1600 nits peak brightness, 3 Thunderbolt 4 ports, HDMI, SDXC slot, MagSafe 3 charging, and six-speaker sound system with Spatial Audio.',
                'price': Decimal('365000.00'),
                'discount_price': Decimal('345000.00'),
                'stock': 14,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/macbook-pro-16-m3-max-angle-1.webp', 'MacBook Pro 16" Front Hero Angled View', 1),
                    ('products/gallery/macbook-pro-16-m3-max-angle-2.webp', 'MacBook Pro 16" Liquid Retina XDR Screen and Backlit Magic Keyboard', 2),
                    ('products/gallery/macbook-pro-16-m3-max-angle-3.webp', 'MacBook Pro 16" MagSafe 3 and Thunderbolt 4 Side Ports', 3),
                    ('products/gallery/macbook-pro-16-m3-max-angle-4.webp', 'MacBook Pro 16" Space Black Anodized Aluminum Lid and Official Packaging', 4),
                ]
            },
            {
                'slug': 'asus-rog-zephyrus-g16-oled',
                'name': 'ASUS ROG Zephyrus G16 OLED Gaming Laptop (Intel Core Ultra 9 / RTX 4080)',
                'category': 'laptops',
                'brand': 'asus',
                'short_description': 'Ultra-thin AI gaming powerhouse with 2.5K OLED 240Hz Nebula Display and Slash Lighting lid.',
                'description': 'The ROG Zephyrus G16 precision CNC aluminum chassis packs an Intel Core Ultra 9 processor with dedicated NPU AI acceleration and NVIDIA GeForce RTX 4080 laptop graphics. Features ROG Intelligent Cooling with vapor chamber and tri-fan technology, 32GB LPDDR5X RAM, and 1TB PCIe 4.0 NVMe SSD.',
                'price': Decimal('265000.00'),
                'discount_price': Decimal('248000.00'),
                'stock': 8,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/asus-rog-zephyrus-g16-oled-angle-1.webp', 'ASUS ROG Zephyrus G16 Slash Lighting Lid Angle', 1),
                    ('products/gallery/asus-rog-zephyrus-g16-oled-angle-2.webp', 'ROG 2.5K OLED 240Hz Display and RGB Keyboard', 2),
                    ('products/gallery/asus-rog-zephyrus-g16-oled-angle-3.webp', 'ROG Vapor Chamber Dual Vents and Exhaust Profile', 3),
                    ('products/gallery/asus-rog-zephyrus-g16-oled-angle-4.webp', 'ASUS Republic of Gamers Collector Gift Box & Charger', 4),
                ]
            },
            {
                'slug': 'dell-xps-15-oled-touch',
                'name': 'Dell XPS 15 9530 3.5K OLED InfinityEdge Touchscreen Laptop (Core i9 / 32GB)',
                'category': 'laptops',
                'brand': 'dell',
                'short_description': 'Premium CNC aluminum and carbon fiber chassis with 15.6" 3.5K OLED touch display.',
                'description': 'Engineered for creators and executives, the Dell XPS 15 features an Intel Core i9-13900H processor, 32GB dual-channel DDR5 memory, 1TB NVMe SSD, and NVIDIA RTX 4070 studio graphics. Diamond-cut sidewalls, massive glass trackpad, and quad-speaker design with Waves Nx 3D audio.',
                'price': Decimal('280000.00'),
                'discount_price': Decimal('265000.00'),
                'stock': 10,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/dell-xps-15-oled-touch-angle-1.webp', 'Dell XPS 15 Platinum Silver Front View', 1),
                    ('products/gallery/dell-xps-15-oled-touch-angle-2.webp', 'InfinityEdge OLED Display & Carbon Fiber Palmrest', 2),
                    ('products/gallery/dell-xps-15-oled-touch-angle-3.webp', 'Precision Diamond-Cut Side Edge & Thunderbolt Ports', 3),
                    ('products/gallery/dell-xps-15-oled-touch-angle-4.webp', 'Dell XPS Retail Packaging and 130W USB-C Adapter', 4),
                ]
            },
            {
                'slug': 'iphone-15-pro-max-natural-titanium',
                'name': 'Apple iPhone 15 Pro Max 256GB Natural Titanium (A17 Pro)',
                'category': 'smartphones',
                'brand': 'apple',
                'short_description': 'Aerospace-grade titanium design with A17 Pro chip, Action Button, and 5x optical telephoto lens.',
                'description': 'iPhone 15 Pro Max is the first iPhone with an aerospace-grade titanium design. Powered by the groundbreaking A17 Pro chip for next-level mobile gaming and graphics performance. Includes a 48MP main camera with 5x telephoto optical zoom, Dynamic Island, Always-On Super Retina XDR display, and USB-C connectivity.',
                'price': Decimal('175000.00'),
                'discount_price': Decimal('162000.00'),
                'stock': 24,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/iphone-15-pro-max-natural-titanium-angle-1.webp', 'iPhone 15 Pro Max Natural Titanium Rear Island', 1),
                    ('products/gallery/iphone-15-pro-max-natural-titanium-angle-2.webp', 'Dynamic Island Super Retina XDR Screen', 2),
                    ('products/gallery/iphone-15-pro-max-natural-titanium-angle-3.webp', 'Custom Action Button and Contoured Brushed Edge', 3),
                    ('products/gallery/iphone-15-pro-max-natural-titanium-angle-4.webp', 'Sealed Apple Box with USB-C Braided Cable', 4),
                ]
            },
            {
                'slug': 'samsung-galaxy-s24-ultra-5g',
                'name': 'Samsung Galaxy S24 Ultra 5G AI 12GB/512GB Titanium Gray with S Pen',
                'category': 'smartphones',
                'brand': 'samsung',
                'short_description': 'Galaxy AI smartphone with flat 6.8" 120Hz Dynamic AMOLED 2X, embedded S Pen, and 200MP camera.',
                'description': 'Meet Galaxy S24 Ultra with Galaxy AI: Circle to Search, Live Translate, and Note Assist. Constructed with a titanium frame, Corning Gorilla Armor glass with reduced reflections, Snapdragon 8 Gen 3 for Galaxy, vapor chamber cooling, and 5000mAh all-day battery.',
                'price': Decimal('185000.00'),
                'discount_price': Decimal('169000.00'),
                'stock': 18,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/samsung-galaxy-s24-ultra-5g-angle-1.webp', 'Samsung Galaxy S24 Ultra Front & S Pen Detached', 1),
                    ('products/gallery/samsung-galaxy-s24-ultra-5g-angle-2.webp', 'Quad Telephoto 200MP Rear Camera Lenses', 2),
                    ('products/gallery/samsung-galaxy-s24-ultra-5g-angle-3.webp', 'Flat Armor Glass Display and Titanium Matte Bezel', 3),
                    ('products/gallery/samsung-galaxy-s24-ultra-5g-angle-4.webp', 'Official Samsung Retail Packaging & S Pen Ejection', 4),
                ]
            },
            {
                'slug': 'asus-tuf-gaming-geforce-rtx-4070-ti-super',
                'name': 'ASUS TUF Gaming GeForce RTX 4070 Ti SUPER 16GB GDDR6X OC Graphics Card',
                'category': 'pc-hardware',
                'brand': 'asus',
                'short_description': 'Military-grade endurance, dual ball bearing axial fans, and Ada Lovelace DLSS 3 architecture.',
                'description': 'The ASUS TUF Gaming RTX 4070 Ti SUPER features auto-extreme manufacturing, military-grade capacitors rated for 20,000 hours at 105C, and a protective vented metal exoskeleton. Equipped with 16GB GDDR6X VRAM, dual BIOS switch, and Aura Sync ARGB lighting.',
                'price': Decimal('125000.00'),
                'discount_price': Decimal('118000.00'),
                'stock': 15,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/asus-tuf-gaming-geforce-rtx-4070-ti-super-angle-1.webp', 'ASUS TUF RTX 4070 Ti SUPER Triple Fan Shroud', 1),
                    ('products/gallery/asus-tuf-gaming-geforce-rtx-4070-ti-super-angle-2.webp', 'Vented Aluminum Backplate & Military Logos', 2),
                    ('products/gallery/asus-tuf-gaming-geforce-rtx-4070-ti-super-angle-3.webp', '3x DisplayPort 1.4a and HDMI 2.1a Gold Bracket', 3),
                    ('products/gallery/asus-tuf-gaming-geforce-rtx-4070-ti-super-angle-4.webp', 'Official TUF Retail Package with Anti-Sag GPU Holder', 4),
                ]
            },
            {
                'slug': 'sony-wh-1000xm5-wireless-anc-headphones',
                'name': 'Sony WH-1000XM5 Wireless Industry-Leading Noise-Canceling Headphones',
                'category': 'audio-gear',
                'brand': 'sony',
                'short_description': 'Auto NC Optimizer with two processors, 8 microphones, 30-hour battery, and LDAC High-Res Audio.',
                'description': 'The Sony WH-1000XM5 rewrites the rules for distraction-free listening. Equipped with two processors controlling 8 microphones for unparalleled noise canceling. Specially designed 30mm carbon fiber composite driver unit delivers clear sound with natural bass, while soft-fit leather headband ensures all-day comfort.',
                'price': Decimal('42000.00'),
                'discount_price': Decimal('38500.00'),
                'stock': 30,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/sony-wh-1000xm5-wireless-anc-headphones-angle-1.webp', 'Sony WH-1000XM5 Silver Over-Ear Earcups Profile', 1),
                    ('products/gallery/sony-wh-1000xm5-wireless-anc-headphones-angle-2.webp', 'Soft-Fit Synthetic Leather Headband & Swivel Fold', 2),
                    ('products/gallery/sony-wh-1000xm5-wireless-anc-headphones-angle-3.webp', 'Capacitive Gesture Touch Sensor & Noise Sensor Ports', 3),
                    ('products/gallery/sony-wh-1000xm5-wireless-anc-headphones-angle-4.webp', 'Collapsible Magnetic Travel Case with Cables', 4),
                ]
            },
            {
                'slug': 'logitech-mx-master-3s-wireless-mouse',
                'name': 'Logitech MX Master 3S Quiet Click Ergonomic Wireless Mouse 8K DPI',
                'category': 'pc-hardware',
                'brand': 'logitech',
                'short_description': 'Electromagnetic MagSpeed scroll wheel, 8000 DPI track-on-glass sensor, and 90% quieter clicks.',
                'description': 'Logitech MX Master 3S is an iconic precision mouse remastered for ultimate feel and tactile feedback. Features Quiet Clicks delivering 90% less noise with satisfying tactile feel. Tracks on virtually any surface including glass with 8K DPI optical sensor, customizable gestures, and Bluetooth / Logi Bolt wireless connectivity.',
                'price': Decimal('14500.00'),
                'discount_price': Decimal('12800.00'),
                'stock': 40,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/logitech-mx-master-3s-wireless-mouse-angle-1.webp', 'Logitech MX Master 3S Ergonomic Thumb Rest Profile', 1),
                    ('products/gallery/logitech-mx-master-3s-wireless-mouse-angle-2.webp', 'MagSpeed Steel Scroll Wheel & Gesture Buttons', 2),
                    ('products/gallery/logitech-mx-master-3s-wireless-mouse-angle-3.webp', 'Dark Graphite Base with Easy-Switch Multi-Device Button', 3),
                    ('products/gallery/logitech-mx-master-3s-wireless-mouse-angle-4.webp', 'FSC-Certified Retail Box with Logi Bolt Receiver', 4),
                ]
            },

            # ==================== BEAUTY & COSMETICS ====================
            {
                'slug': 'the-ordinary-niacinamide-10-zinc-1',
                'name': 'The Ordinary Niacinamide 10% + Zinc 1% Oil Control Serum 60ml',
                'category': 'skin-care',
                'brand': 'the-ordinary',
                'short_description': 'High-strength vitamin and mineral blemish formula that refines skin texture and minimizes pores.',
                'description': 'A clinically proven, water-based serum that boosts skin brightness, improves skin smoothness, and reinforces skin barrier integrity over time. Niacinamide (Vitamin B3) targets visible blemishes and signs of congestion, while Zinc PCA balances sebum activity.',
                'price': Decimal('1450.00'),
                'discount_price': Decimal('1250.00'),
                'stock': 65,
                'unit': '60 ml',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/the-ordinary-niacinamide-10-zinc-1-angle-1.webp', 'The Ordinary 60ml Dropper Bottle Front View', 1),
                    ('products/gallery/the-ordinary-niacinamide-10-zinc-1-angle-2.webp', 'Glass Pipette Dispensing Clear Serum Droplet', 2),
                    ('products/gallery/the-ordinary-niacinamide-10-zinc-1-angle-3.webp', 'Serum Swatch on Skin Showing Hydrated Finish', 3),
                    ('products/gallery/the-ordinary-niacinamide-10-zinc-1-angle-4.webp', 'Authentic Deciem Canada Box Packaging & Batch Code', 4),
                ]
            },
            {
                'slug': 'cerave-moisturizing-cream-454g',
                'name': 'CeraVe Moisturizing Cream with 3 Essential Ceramides & Hyaluronic Acid 454g',
                'category': 'skin-care',
                'brand': 'cerave',
                'short_description': 'Dermatologist-developed barrier-restoring rich cream with 24-hour hydration release.',
                'description': 'Developed with dermatologists, CeraVe Moisturizing Cream has a unique formula that provides 24-hour hydration and helps restore the protective skin barrier with three essential ceramides (1, 3, 6-II). Utilizes patented MVE delivery technology for sustained release of nourishing hydration. Fragrance-free and non-comedogenic.',
                'price': Decimal('2850.00'),
                'discount_price': Decimal('2490.00'),
                'stock': 45,
                'unit': '454 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/cerave-moisturizing-cream-454g-angle-1.webp', 'CeraVe Moisturizing Cream 454g Large Tub Front', 1),
                    ('products/gallery/cerave-moisturizing-cream-454g-angle-2.webp', 'Open Tub Showing Thick Velvet Cream Texture', 2),
                    ('products/gallery/cerave-moisturizing-cream-454g-angle-3.webp', 'Pump Dispenser Lid and Usage Directions', 3),
                    ('products/gallery/cerave-moisturizing-cream-454g-angle-4.webp', 'National Eczema Association Acceptance Seal & Barcode', 4),
                ]
            },
            {
                'slug': 'mac-retro-matte-ruby-woo',
                'name': 'MAC Retro Matte Lipstick - Ruby Woo (Iconic Long-Wearing Vivid Red)',
                'category': 'makeup',
                'brand': 'mac',
                'short_description': 'The world-famous long-wearing vivid blue-red lipstick with completely zero-shine matte finish.',
                'description': 'MAC Ruby Woo is the iconic best-selling red lipstick celebrated by celebrity makeup artists worldwide. Formulated to shade, define, and showcase the lips with high color payoff and up to 12 hours of fade-resistant wear without feathering.',
                'price': Decimal('3200.00'),
                'discount_price': Decimal('2850.00'),
                'stock': 50,
                'unit': '3 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/mac-retro-matte-ruby-woo-angle-1.webp', 'MAC Ruby Woo Iconic Matte Black Bullet Extended', 1),
                    ('products/gallery/mac-retro-matte-ruby-woo-angle-2.webp', 'Close-Up of Vivid Blue-Red Teardrop Bullet Tip', 2),
                    ('products/gallery/mac-retro-matte-ruby-woo-angle-3.webp', 'Bold Red Matte Swatch Application on Lips', 3),
                    ('products/gallery/mac-retro-matte-ruby-woo-angle-4.webp', 'Official MAC Retail Cardboard Box and Shade Label', 4),
                ]
            },
            {
                'slug': 'maybelline-lash-sensational-sky-high',
                'name': 'Maybelline Lash Sensational Sky High Waterproof Mascara - Very Black',
                'category': 'makeup',
                'brand': 'maybelline',
                'short_description': 'Flex Tower silicone brush delivers full volume and limitless lash length from root to tip.',
                'description': 'Sky High mascara provides limitless lash impact from every angle! Infused with bamboo extract and fibers for long, full lashes that feel lightweight and never flake. Waterproof formula tested by ophthalmologists and safe for sensitive eyes.',
                'price': Decimal('1750.00'),
                'discount_price': Decimal('1490.00'),
                'stock': 60,
                'unit': '7.2 ml',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/maybelline-lash-sensational-sky-high-angle-1.webp', 'Maybelline Sky High Metallic Rose-Gold Tube', 1),
                    ('products/gallery/maybelline-lash-sensational-sky-high-angle-2.webp', 'Flex Tower Silicone Wand Bristles Showing Black Coating', 2),
                    ('products/gallery/maybelline-lash-sensational-sky-high-angle-3.webp', 'Dramatic Lash Extension Before and After Visual', 3),
                    ('products/gallery/maybelline-lash-sensational-sky-high-angle-4.webp', 'Sealed Blister Retail Card with Holographic Authentic Seal', 4),
                ]
            },
            {
                'slug': 'cerave-hydrating-cleanser-473ml',
                'name': 'CeraVe Hydrating Facial Cleanser with Ceramides & Hyaluronic Acid 473ml',
                'category': 'skin-care',
                'brand': 'cerave',
                'short_description': 'Dermatologist-developed gentle non-foaming lotion cleanser that hydrates and cleanses without stripping skin barrier.',
                'description': 'Formulated with 3 essential ceramides and hyaluronic acid, CeraVe Hydrating Cleanser effectively cleanses away dirt, oil, and makeup while locking in moisture with MVE delivery technology. Non-comedogenic, fragrance-free, and accepted by the National Eczema Association.',
                'price': Decimal('2250.00'),
                'discount_price': Decimal('1950.00'),
                'stock': 55,
                'unit': '473 ml',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/cerave-hydrating-cleanser-473ml-angle-1.webp', 'CeraVe Hydrating Cleanser 473ml Pump Bottle Front', 1),
                    ('products/gallery/cerave-hydrating-cleanser-473ml-angle-2.webp', 'Locking Pump Dispenser Nozzle and Lotion Texture', 2),
                    ('products/gallery/cerave-hydrating-cleanser-473ml-angle-3.webp', 'Gentle Foamless Cleansing Demonstration on Skin', 3),
                    ('products/gallery/cerave-hydrating-cleanser-473ml-angle-4.webp', 'Dermatologist Recommended Packaging & Ingredients', 4),
                ]
            },
            {
                'slug': 'loreal-paris-revitalift-hyaluronic-acid-serum',
                'name': 'L\'Oreal Paris Hyaluron Expert 1.5% Pure Hyaluronic Acid Plumping Serum 30ml',
                'category': 'skin-care',
                'brand': 'loreal',
                'short_description': 'Dermatologist-validated anti-aging serum that visibly replumps skin and reduces wrinkles.',
                'description': 'L\'Oreal Paris Hyaluron Expert 1.5% Pure Hyaluronic Acid Serum absorbs quickly without sticky residue to visibly plump skin in 1 hour and reduce wrinkles in 4 weeks. Contains 0.5% High Molecular Weight Hyaluronic Acid to intensely rehydrate skin surface, and 1% Micro Molecular Weight Hyaluronic Acid to deeply penetrate.',
                'price': Decimal('2450.00'),
                'discount_price': Decimal('2150.00'),
                'stock': 40,
                'unit': '30 ml',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/loreal-paris-revitalift-hyaluronic-acid-serum-angle-1.webp', 'L\'Oreal Hyaluron Expert Purple Glass Bottle Front View', 1),
                    ('products/gallery/loreal-paris-revitalift-hyaluronic-acid-serum-angle-2.webp', 'Curved Precision Dropper with Anti-Wrinkle Solution', 2),
                    ('products/gallery/loreal-paris-revitalift-hyaluronic-acid-serum-angle-3.webp', 'Clinical Plumpness and Hydration Chart Demonstration', 3),
                    ('products/gallery/loreal-paris-revitalift-hyaluronic-acid-serum-angle-4.webp', 'French Retail Carton Packaging with Safety Seal', 4),
                ]
            },
            {
                'slug': 'loreal-extraordinary-oil-hair-serum',
                'name': 'L\'Oreal Paris Extraordinary Oil Multi-Use Nourishing Hair Serum 100ml',
                'category': 'hair-care',
                'brand': 'loreal',
                'short_description': 'Enriched with 6 rare precious floral extracts for luminous shine and supreme frizz control.',
                'description': 'Transform dry, unruly tresses into silky perfection with L\'Oreal Paris Extraordinary Oil. Infused with lotus, chamomile, tiare, lotus, rose, and flax flower oils to provide deep hydration, heat protection up to 230C, and 98% less frizz.',
                'price': Decimal('1850.00'),
                'discount_price': Decimal('1590.00'),
                'stock': 55,
                'unit': '100 ml',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/loreal-extraordinary-oil-hair-serum-angle-1.webp', 'L\'Oreal Extraordinary Oil Amber Glass Pump Bottle', 1),
                    ('products/gallery/loreal-extraordinary-oil-hair-serum-angle-2.webp', 'Nozzle Dispensing Golden Gloss Hair Droplet', 2),
                    ('products/gallery/loreal-extraordinary-oil-hair-serum-angle-3.webp', 'Silk Shine Smooth Hair Transformation View', 3),
                    ('products/gallery/loreal-extraordinary-oil-hair-serum-angle-4.webp', 'Rear Ingredients and Heat Protection Label', 4),
                ]
            },
            {
                'slug': 'chanel-coco-mademoiselle-edp-100ml',
                'name': 'Chanel Coco Mademoiselle Eau De Parfum Vaporisateur Spray 100ml',
                'category': 'fragrances',
                'brand': 'chanel',
                'short_description': 'Amber floral women\'s perfume with vibrant orange, clear jasmine, and refined patchouli.',
                'description': 'The essence of a bold, free woman. An airy, sensual amber-floral accord that opens with sparks of fresh orange and bergamot, clears into transparent accords of Grasse jasmine and May rose, and settles into pure accents of patchouli and Haitian vetiver.',
                'price': Decimal('19500.00'),
                'discount_price': Decimal('17800.00'),
                'stock': 20,
                'unit': '100 ml',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/chanel-coco-mademoiselle-edp-100ml-angle-1.webp', 'Chanel Coco Mademoiselle Frosted Glass Flacon Front', 1),
                    ('products/gallery/chanel-coco-mademoiselle-edp-100ml-angle-2.webp', 'Engraved Golden Collar & Faceted Stopper Close-Up', 2),
                    ('products/gallery/chanel-coco-mademoiselle-edp-100ml-angle-3.webp', 'Atmospheric Perfume Mist Spray Demonstration', 3),
                    ('products/gallery/chanel-coco-mademoiselle-edp-100ml-angle-4.webp', 'Embossed White and Gold Signature Gift Packaging', 4),
                ]
            },

            # ==================== FASHION & LIFESTYLE ====================
            {
                'slug': 'aarong-hand-embroidered-royal-panjabi',
                'name': 'Aarong Royal Silk & Hand-Embroidered Festive Panjabi - Off-White & Gold',
                'category': 'mens-panjabi',
                'brand': 'aarong',
                'short_description': 'Heritage Nakshi Kantha hand-stitched collar and placket on breathable pure silk and combed cotton blend.',
                'description': 'Exclusively hand-crafted by rural master artisans of Bangladesh, this Aarong Royal Silk Panjabi pairs time-honored Nakshi needlecraft with contemporary tailored silhouette. Cut from premium breathable combed silk-cotton blend with mother-of-pearl buttons and discreet side pockets.',
                'price': Decimal('4850.00'),
                'discount_price': Decimal('4250.00'),
                'stock': 35,
                'unit': '1 piece',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/aarong-hand-embroidered-royal-panjabi-angle-1.webp', 'Aarong Royal Panjabi Mannequin Full Front View', 1),
                    ('products/gallery/aarong-hand-embroidered-royal-panjabi-angle-2.webp', 'Nakshi Kantha Hand Embroidery on Mandarin Collar', 2),
                    ('products/gallery/aarong-hand-embroidered-royal-panjabi-angle-3.webp', 'Handmade Metallic Buttons and Pocket Detail', 3),
                    ('products/gallery/aarong-hand-embroidered-royal-panjabi-angle-4.webp', 'Aarong Signature Cardboard Presentation Box', 4),
                ]
            },
            {
                'slug': 'aarong-dhakai-jamdani-handloom-saree',
                'name': 'Aarong Heritage Dhakai Jamdani Handloom Silk Saree - Midnight Blue & Silver',
                'category': 'womens-kurti',
                'brand': 'aarong',
                'short_description': 'UNESCO-recognized authentic handloom Dhakai Jamdani woven with pure mulberry silk and silver zari.',
                'description': 'Each Aarong Dhakai Jamdani saree takes over six weeks of painstaking handloom weaving by generational master weavers in Rupganj. Intricate floral jhalar patterns adorn the midnight blue sheer body, finished with a heavy ornamental aanchal.',
                'price': Decimal('18500.00'),
                'discount_price': Decimal('16200.00'),
                'stock': 15,
                'unit': '1 piece',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/aarong-dhakai-jamdani-handloom-saree-angle-1.webp', 'Aarong Dhakai Jamdani Saree Full Drape on Model', 1),
                    ('products/gallery/aarong-dhakai-jamdani-handloom-saree-angle-2.webp', 'Intricate Silver Zari Aanchal Weave Close-Up', 2),
                    ('products/gallery/aarong-dhakai-jamdani-handloom-saree-angle-3.webp', 'Delicate Geometric Border and Sheer Silk Texture', 3),
                    ('products/gallery/aarong-dhakai-jamdani-handloom-saree-angle-4.webp', 'Silk Mark Verified Wooden Aarong Gift Box', 4),
                ]
            },
            {
                'slug': 'sailor-heritage-motif-viscose-kurti',
                'name': 'Sailor Heritage Geometric Motif Fine Viscose Long Kurti',
                'category': 'womens-kurti',
                'brand': 'sailor',
                'short_description': 'Contemporary A-line long silhouette with folk-inspired yoke print and delicate bell sleeves.',
                'description': 'Designed for festive elegance and everyday breathability, the Sailor Heritage Kurti combines ultra-soft flowy viscose fabric with refined geometric digital motifs. Embellished with tassel tie cord at neckline and subtle side slits.',
                'price': Decimal('2850.00'),
                'discount_price': Decimal('2450.00'),
                'stock': 40,
                'unit': '1 piece',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/sailor-heritage-motif-viscose-kurti-angle-1.webp', 'Sailor Heritage Kurti Front Studio Model Shot', 1),
                    ('products/gallery/sailor-heritage-motif-viscose-kurti-angle-2.webp', 'Embroidered Yoke & Tassel Tie Neckline Detail', 2),
                    ('products/gallery/sailor-heritage-motif-viscose-kurti-angle-3.webp', 'Flowy Bell Sleeve Cuffs with Lace Trimming', 3),
                    ('products/gallery/sailor-heritage-motif-viscose-kurti-angle-4.webp', 'Breathable Viscose Textile Swatch & Care Tag', 4),
                ]
            },
            {
                'slug': 'zara-tailored-slim-fit-formal-blazer',
                'name': 'Zara Man Structured Slim-Fit Wool-Blend Formal Blazer - Charcoal Gray',
                'category': 'formalwear',
                'brand': 'zara',
                'short_description': 'Modern structured European cut with notch lapels, flap pockets, and silky interior lining.',
                'description': 'Sharp tailoring meets contemporary sophistication in this Zara charcoal blazer. Spun from high-twist wool blend that resists wrinkling during travel. Features contrast kissing horn buttons, double back vents for freedom of movement, and structured padded shoulders.',
                'price': Decimal('14500.00'),
                'discount_price': Decimal('12900.00'),
                'stock': 22,
                'unit': '1 piece',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/zara-tailored-slim-fit-formal-blazer-angle-1.webp', 'Zara Man Charcoal Blazer Front Buttoned View', 1),
                    ('products/gallery/zara-tailored-slim-fit-formal-blazer-angle-2.webp', 'Crisp Notch Lapel and Welt Chest Pocket', 2),
                    ('products/gallery/zara-tailored-slim-fit-formal-blazer-angle-3.webp', 'Silky Interior Lining with Passport Pocket', 3),
                    ('products/gallery/zara-tailored-slim-fit-formal-blazer-angle-4.webp', 'Garment Travel Cover Bag and Zara Brand Hanger', 4),
                ]
            },
            {
                'slug': 'zara-premium-selvedge-tapered-denim',
                'name': 'Zara Authentic Selvedge Tapered Denim Jeans - Dark Indigo Wash',
                'category': 'casual-denim',
                'brand': 'zara',
                'short_description': 'Shuttle-loom selvedge denim with red ID line, copper rivets, and genuine leather waistband patch.',
                'description': 'Woven on vintage shuttle looms from 13.5oz ring-spun cotton denim, these Zara selvedge jeans offer unmatched longevity and develop personalized fades with wear. Finished with antiqued brass button fly and reinforced bar-tack stitching.',
                'price': Decimal('5500.00'),
                'discount_price': Decimal('4800.00'),
                'stock': 48,
                'unit': '1 piece',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/zara-premium-selvedge-tapered-denim-angle-1.webp', 'Zara Selvedge Denim Full Tapered Front View', 1),
                    ('products/gallery/zara-premium-selvedge-tapered-denim-angle-2.webp', 'Rolled Cuff Displaying Red Selvedge ID Line', 2),
                    ('products/gallery/zara-premium-selvedge-tapered-denim-angle-3.webp', 'Heavy Stitched Back Pockets & Leather Patch', 3),
                    ('products/gallery/zara-premium-selvedge-tapered-denim-angle-4.webp', 'Solid Copper Shank Button Fly Close-Up', 4),
                ]
            },
            {
                'slug': 'apex-venturini-handcrafted-leather-oxfords',
                'name': 'Apex Venturini Handcrafted Italian Leather Formal Oxford Shoes',
                'category': 'formalwear',
                'brand': 'apex',
                'short_description': 'Full-grain Italian calfskin with hand-burnished toe cap and channeled anti-slip leather sole.',
                'description': 'Handcrafted for distinguished executives, the Venturini Oxford by Apex exemplifies sartorial excellence. Cut from full-grain vegetable-tanned calfskin leather with a cushioned leather-lined insole and Goodyear-welted channeled sole.',
                'price': Decimal('9990.00'),
                'discount_price': Decimal('8750.00'),
                'stock': 28,
                'unit': '1 pair',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/apex-venturini-handcrafted-leather-oxfords-angle-1.webp', 'Apex Venturini Hand-Burnished Calfskin Profile', 1),
                    ('products/gallery/apex-venturini-handcrafted-leather-oxfords-angle-2.webp', 'Closed Lacing Oxford V-Shaped Throat View', 2),
                    ('products/gallery/apex-venturini-handcrafted-leather-oxfords-angle-3.webp', 'Channeled Anti-Slip Welted Leather Outsole', 3),
                    ('products/gallery/apex-venturini-handcrafted-leather-oxfords-angle-4.webp', 'Flannel Shoe Dust Bags and Wooden Shoe Trees Box', 4),
                ]
            },
            {
                'slug': 'bata-comfit-memory-foam-walkers',
                'name': 'Bata Comfit Ergonomic Air-Cooled Memory Foam Walking Loafers',
                'category': 'casual-denim',
                'brand': 'bata',
                'short_description': 'Ultra-lightweight walking loafers with dual-density memory foam and slip-resistant grip.',
                'description': 'Enjoy effortless cloud-like walking comfort with the Bata Comfit walkers. Engineered with breathable engineered mesh uppers, antimicrobial arch support, and shock-absorbing EVA outsoles that cradle your feet all day long.',
                'price': Decimal('3490.00'),
                'discount_price': Decimal('2990.00'),
                'stock': 50,
                'unit': '1 pair',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/bata-comfit-memory-foam-walkers-angle-1.webp', 'Bata Comfit Loafer Ergonomic Side View', 1),
                    ('products/gallery/bata-comfit-memory-foam-walkers-angle-2.webp', 'Removable Air-Cooled Memory Foam Insole', 2),
                    ('products/gallery/bata-comfit-memory-foam-walkers-angle-3.webp', 'High-Traction Flex-Groove EVA Outsole', 3),
                    ('products/gallery/bata-comfit-memory-foam-walkers-angle-4.webp', 'Official Bata Comfit Red Box Packaging', 4),
                ]
            },

            # ==================== ORGANIC GROCERY ====================
            {
                'slug': 'khaas-food-kalijeera-polao-rice-5kg',
                'name': 'Khaas Food Premium Kalijeera Aromatic Polao Rice 5kg',
                'category': 'rice-grains',
                'brand': 'khaas-food',
                'short_description': 'Native ancient aromatic slender rice sourced directly from Dinajpur growers without chemical polish.',
                'description': 'Khaas Food Kalijeera Rice is famous for its natural floral aroma, slender grains, and exquisite taste. Cultivated naturally and aged properly for superior elongation upon cooking. Ideal for festive Polao, Biryani, and traditional Payesh.',
                'price': Decimal('850.00'),
                'discount_price': Decimal('780.00'),
                'stock': 80,
                'unit': '5 kg',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/khaas-food-kalijeera-polao-rice-5kg-angle-1.webp', 'Khaas Food Burlap Jute Sack Packaging Front', 1),
                    ('products/gallery/khaas-food-kalijeera-polao-rice-5kg-angle-2.webp', 'Raw Uncooked Aromatic Slender Rice Grains', 2),
                    ('products/gallery/khaas-food-kalijeera-polao-rice-5kg-angle-3.webp', 'Steaming Hot Festive Mutton Polao Serving', 3),
                    ('products/gallery/khaas-food-kalijeera-polao-rice-5kg-angle-4.webp', 'Pesticide-Free Chemical Testing Certificate Tag', 4),
                ]
            },
            {
                'slug': 'khaas-food-cold-pressed-mustard-oil-1l',
                'name': 'Khaas Food Ghani-Bhanga Cold-Pressed Extra Virgin Mustard Oil 1L',
                'category': 'pure-oils',
                'brand': 'khaas-food',
                'short_description': '100% pure first-press mustard oil extracted via traditional wooden ghani without heat treatment.',
                'description': 'Pure cold-pressed mustard oil with its signature pungent aroma and deep golden color. Rich in Omega-3 and natural antioxidants, perfect for traditional Bangladeshi bhorta, pickles, and hearty curries.',
                'price': Decimal('390.00'),
                'discount_price': Decimal('350.00'),
                'stock': 100,
                'unit': '1 ltr',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/khaas-food-cold-pressed-mustard-oil-1l-angle-1.webp', 'Khaas Food 1 Liter Glass Bottle Front Angle', 1),
                    ('products/gallery/khaas-food-cold-pressed-mustard-oil-1l-angle-2.webp', 'Pungent Golden Mustard Oil Pouring into Ceramic Bowl', 2),
                    ('products/gallery/khaas-food-cold-pressed-mustard-oil-1l-angle-3.webp', 'Traditional Wooden Ghani Extraction Diagram', 3),
                    ('products/gallery/khaas-food-cold-pressed-mustard-oil-1l-angle-4.webp', 'Tamper-Evident Safety Foil Seal & Bottle Cap', 4),
                ]
            },
            {
                'slug': 'khaas-food-sundarban-wild-natural-honey-500g',
                'name': 'Khaas Food Raw Sundarban Wild Flower Natural Honey 500g',
                'category': 'honey-dry-fruits',
                'brand': 'khaas-food',
                'short_description': 'Unprocessed raw forest honey gathered by traditional Mouvals from mangrove blossoms.',
                'description': 'Harvested directly from wild beehives deep within the Sundarban mangrove forest. Never pasteurized or adulterated with sugar syrup. Packed with natural enzymes, propolis, and medicinal pollen.',
                'price': Decimal('950.00'),
                'discount_price': Decimal('850.00'),
                'stock': 65,
                'unit': '500 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/khaas-food-sundarban-wild-natural-honey-500g-angle-1.webp', 'Hexagonal Glass Jar of Amber Forest Honey', 1),
                    ('products/gallery/khaas-food-sundarban-wild-natural-honey-500g-angle-2.webp', 'Wooden Dipper Drizzling Pure Thick Honey', 2),
                    ('products/gallery/khaas-food-sundarban-wild-natural-honey-500g-angle-3.webp', 'Slice of Raw Honeycomb Floating in Jar', 3),
                    ('products/gallery/khaas-food-sundarban-wild-natural-honey-500g-angle-4.webp', 'Lab Purity & Pollen Analysis Certificate', 4),
                ]
            },
            {
                'slug': 'chaldal-organic-royal-afghani-medjool-dates-1kg',
                'name': 'Chaldal Organic Royal Afghani Premium Jumbo Medjool Dates 1kg',
                'category': 'honey-dry-fruits',
                'brand': 'chaldal-organic',
                'short_description': 'Large, juicy caramel-sweet Medjool dates with thin skin and succulent melt-in-mouth pulp.',
                'description': 'Known as the King of Dates, these premium Medjool dates are handpicked at peak ripeness. Naturally sweet with notes of rich caramel and wild honey. Free from added preservatives and packaged under strict hygienic conditions.',
                'price': Decimal('1450.00'),
                'discount_price': Decimal('1250.00'),
                'stock': 75,
                'unit': '1 kg',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/chaldal-organic-royal-afghani-medjool-dates-1kg-angle-1.webp', 'Royal Gold Gift Box Packaging of Medjool Dates', 1),
                    ('products/gallery/chaldal-organic-royal-afghani-medjool-dates-1kg-angle-2.webp', 'Halved Jumbo Date Showing Succulent Caramel Flesh', 2),
                    ('products/gallery/chaldal-organic-royal-afghani-medjool-dates-1kg-angle-3.webp', 'Traditional Brass Plate Arrangement of Whole Dates', 3),
                    ('products/gallery/chaldal-organic-royal-afghani-medjool-dates-1kg-angle-4.webp', 'Airtight Vacuum Inner Tray & Nutritional Panel', 4),
                ]
            },
            {
                'slug': 'chaldal-organic-california-almonds-cashews-mix-500g',
                'name': 'Chaldal Organic Roasted Jumbo California Almonds & Cashew Mix 500g',
                'category': 'honey-dry-fruits',
                'brand': 'chaldal-organic',
                'short_description': 'Crunchy slow-roasted California almonds and whole buttery cashews in resealable zip pouch.',
                'description': 'Hand-selected premium tree nuts slow-roasted without excessive salt or oil to preserve heart-healthy nutrients. Packed with healthy fats, magnesium, and dietary fiber for quick energy and sustained vitality.',
                'price': Decimal('1150.00'),
                'discount_price': Decimal('980.00'),
                'stock': 70,
                'unit': '500 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/chaldal-organic-california-almonds-cashews-mix-500g-angle-1.webp', 'Kraft Zipper Pouch with Transparent Nut Window', 1),
                    ('products/gallery/chaldal-organic-california-almonds-cashews-mix-500g-angle-2.webp', 'Acacia Wood Bowl Filled with Roasted Mixed Nuts', 2),
                    ('products/gallery/chaldal-organic-california-almonds-cashews-mix-500g-angle-3.webp', 'Macro Shot of Golden Roasted Whole Cashews', 3),
                    ('products/gallery/chaldal-organic-california-almonds-cashews-mix-500g-angle-4.webp', 'Resealable Zip Lock & Certified Organic Seal', 4),
                ]
            },
            {
                'slug': 'pran-premium-pure-organic-ghee-900g',
                'name': 'Pran Premium Organic Cow Milk Desi Danadar Ghee 900g Tin',
                'category': 'pure-oils',
                'brand': 'pran',
                'short_description': 'Authentic traditional clarified butter made from pasture-raised cow milk with granular danadar aroma.',
                'description': 'Simmered slowly to achieve a rich golden hue and delightful granular texture. Imparts unbeatable richness to biryanis, parathas, and sweets. Zero trans fats or added artificial coloring.',
                'price': Decimal('1650.00'),
                'discount_price': Decimal('1480.00'),
                'stock': 55,
                'unit': '900 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/pran-premium-pure-organic-ghee-900g-angle-1.webp', 'Pran Premium 900g Gold Metal Tin Container', 1),
                    ('products/gallery/pran-premium-pure-organic-ghee-900g-angle-2.webp', 'Granular Golden Danadar Spoonful Scoop', 2),
                    ('products/gallery/pran-premium-pure-organic-ghee-900g-angle-3.webp', 'Aromatic Ghee Drizzling on Hot Basmati Khichuri', 3),
                    ('products/gallery/pran-premium-pure-organic-ghee-900g-angle-4.webp', 'BSTI Certified Seal & Nutritional Guarantee', 4),
                ]
            },
            {
                'slug': 'aci-pure-aromatic-chinigura-rice-5kg',
                'name': 'ACI Pure Premium Aromatic Dinajpur Chinigura Rice 5kg Pack',
                'category': 'rice-grains',
                'brand': 'aci',
                'short_description': 'Fine small-grain Chinigura rice with unmatched fragrance, perfect for Kacchi Biryani & Firni.',
                'description': 'Selected from the renowned agricultural belt of Dinajpur. Triple-destoned, sortex-cleaned, and vacuum-sealed to preserve natural aroma and tender grain fluffiness upon cooking.',
                'price': Decimal('750.00'),
                'discount_price': Decimal('690.00'),
                'stock': 90,
                'unit': '5 kg',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/aci-pure-aromatic-chinigura-rice-5kg-angle-1.webp', 'ACI Pure 5kg Airtight Nitrogen Vacuum Poly Pack', 1),
                    ('products/gallery/aci-pure-aromatic-chinigura-rice-5kg-angle-2.webp', 'Pristine White Unbroken Short Grain Chinigura Macro', 2),
                    ('products/gallery/aci-pure-aromatic-chinigura-rice-5kg-angle-3.webp', 'Steaming Royal Kacchi Biryani Serving Plate', 3),
                    ('products/gallery/aci-pure-aromatic-chinigura-rice-5kg-angle-4.webp', 'Laser Sortex Cleaning & Purity Certification Mark', 4),
                ]
            },
            {
                'slug': 'chaldal-organic-chia-seeds-500g',
                'name': 'Chaldal Organic Raw Superfood Black Chia Seeds 500g',
                'category': 'fresh-agro',
                'brand': 'chaldal-organic',
                'short_description': 'Pesticide-free 100% natural raw black chia seeds rich in Omega-3, plant protein, and dietary fiber.',
                'description': 'Chaldal Organic Chia Seeds are harvested from sustainable farms and triple-cleaned to deliver pure nutrition. Soak in water, yogurt, or smoothies to form a gelatinous superfood pudding that aids digestive health, controls appetite, and boosts endurance.',
                'price': Decimal('520.00'),
                'discount_price': Decimal('460.00'),
                'stock': 85,
                'unit': '500 gm',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/chaldal-organic-chia-seeds-500g-angle-1.webp', 'Chaldal Organic 500g Matte Zipper Pouch Front', 1),
                    ('products/gallery/chaldal-organic-chia-seeds-500g-angle-2.webp', 'Macro View of Whole Glossy Black Chia Seeds in Spoon', 2),
                    ('products/gallery/chaldal-organic-chia-seeds-500g-angle-3.webp', 'Hydrated Chia Seed Pudding Cup with Berries', 3),
                    ('products/gallery/chaldal-organic-chia-seeds-500g-angle-4.webp', 'Resealable Top Seal and Certified Organic Nutrition Facts', 4),
                ]
            },
            {
                'slug': 'aci-pure-premium-danadar-ghee-900g',
                'name': 'ACI Pure Premium Cow Milk Danadar Desi Ghee 900g Tin',
                'category': 'pure-oils',
                'brand': 'aci',
                'short_description': 'Pure traditional clarified butter made from fresh dairy milk with distinct golden granular aroma.',
                'description': 'ACI Pure Ghee is processed through advanced hygienic dairy technology preserving traditional rural taste and aroma. Rich in fat-soluble vitamins A, D, E, and K with zero adulteration or artificial fragrance.',
                'price': Decimal('1580.00'),
                'discount_price': Decimal('1420.00'),
                'stock': 60,
                'unit': '900 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/aci-pure-premium-danadar-ghee-900g-angle-1.webp', 'ACI Pure 900g Golden Metal Tin Container Front', 1),
                    ('products/gallery/aci-pure-premium-danadar-ghee-900g-angle-2.webp', 'Spoonful of Granular Golden Aromatic Desi Ghee', 2),
                    ('products/gallery/aci-pure-premium-danadar-ghee-900g-angle-3.webp', 'Rich Ghee Melted Over Traditional Shahi Polao', 3),
                    ('products/gallery/aci-pure-premium-danadar-ghee-900g-angle-4.webp', 'Hermetic Easy-Open Tin Ring Lid and BSTI Purity Mark', 4),
                ]
            },

            # ==================== PHARMACY & HEALTH ====================
            {
                'slug': 'square-pharma-napa-extra-paracetamol-box',
                'name': 'Square Pharma Napa Extra 500mg/65mg Rapid Pain Relief (Box of 200 Tablets)',
                'category': 'prescriptions',
                'brand': 'square-pharma',
                'short_description': 'Paracetamol and Caffeine formulation for fast relief from severe headache, fever, and body aches.',
                'description': 'Napa Extra combines Paracetamol BP 500mg with Caffeine 65mg to provide rapid, potent pain and fever relief. Certified by DGDA with rigorous quality assurance from Square Pharmaceuticals PLC.',
                'price': Decimal('500.00'),
                'discount_price': Decimal('460.00'),
                'stock': 150,
                'unit': 'Box of 200 tabs',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/square-pharma-napa-extra-paracetamol-box-angle-1.webp', 'Square Pharma Napa Extra Official Box Front', 1),
                    ('products/gallery/square-pharma-napa-extra-paracetamol-box-angle-2.webp', 'Foil Blister Strip of Red Coated Tablets', 2),
                    ('products/gallery/square-pharma-napa-extra-paracetamol-box-angle-3.webp', 'DGDA Drug Administration QR Code and Expiry Batch', 3),
                    ('products/gallery/square-pharma-napa-extra-paracetamol-box-angle-4.webp', 'Patient Dosage Guidelines & Safety Leaflet', 4),
                ]
            },
            {
                'slug': 'square-pharma-seclo-20mg-delayed-release',
                'name': 'Square Pharma Seclo 20mg Omeprazole Delayed-Release (Box of 100 Capsules)',
                'category': 'prescriptions',
                'brand': 'square-pharma',
                'short_description': 'Proton pump inhibitor for hyperacidity, gastric ulcer, and gastroesophageal reflux relief.',
                'description': 'Seclo 20 contains enteric-coated omeprazole pellets that resist gastric acid and dissolve specifically in the small intestine for sustained 24-hour acid suppression. Manufactured under WHO cGMP standards.',
                'price': Decimal('700.00'),
                'discount_price': Decimal('640.00'),
                'stock': 120,
                'unit': 'Box of 100 caps',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/square-pharma-seclo-20mg-delayed-release-angle-1.webp', 'Seclo 20mg Blue-and-White Outer Box Front', 1),
                    ('products/gallery/square-pharma-seclo-20mg-delayed-release-angle-2.webp', 'Alu-Alu Blister Strip of Blue & Pink Capsules', 2),
                    ('products/gallery/square-pharma-seclo-20mg-delayed-release-angle-3.webp', 'Single Capsule Macro Showing Enteric Coated Pellets', 3),
                    ('products/gallery/square-pharma-seclo-20mg-delayed-release-angle-4.webp', 'Reverse Blister Foil with Expiration Date', 4),
                ]
            },
            {
                'slug': 'beximco-bextram-gold-multivitamin-30s',
                'name': 'Beximco Bextram Gold Complete 32-in-1 Daily Multivitamin & Minerals (30 Tablets)',
                'category': 'vitamins',
                'brand': 'beximco',
                'short_description': 'Comprehensive nutritional support enriched with Lutein, Lycopene, and essential trace minerals.',
                'description': 'Bextram Gold is scientifically formulated to meet daily micronutrient requirements for energy, immune defense, eye health, and cardiovascular wellness. Produced by Beximco Pharmaceuticals with premium imported USP-grade ingredients.',
                'price': Decimal('380.00'),
                'discount_price': Decimal('340.00'),
                'stock': 110,
                'unit': '30 tabs bottle',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/beximco-bextram-gold-multivitamin-30s-angle-1.webp', 'Bextram Gold Amber Prescription Bottle Front', 1),
                    ('products/gallery/beximco-bextram-gold-multivitamin-30s-angle-2.webp', 'Golden Oval Coated Tablets in Bottle Cap', 2),
                    ('products/gallery/beximco-bextram-gold-multivitamin-30s-angle-3.webp', 'Complete 32 Vitamin and Mineral RDA Table', 3),
                    ('products/gallery/beximco-bextram-gold-multivitamin-30s-angle-4.webp', 'Child-Resistant Safety Push-and-Turn Cap', 4),
                ]
            },
            {
                'slug': 'beximco-maxpro-20mg-esomeprazole-mups',
                'name': 'Beximco Maxpro 20mg Esomeprazole Magnesium MUPS (Box of 100 Tablets)',
                'category': 'prescriptions',
                'brand': 'beximco',
                'short_description': 'Multiple-Unit Pellet System (MUPS) tablet for consistent heartburn and GERD control.',
                'description': 'Maxpro 20 MUPS offers advanced pharmacokinetic consistency over conventional PPIs. Rapidly disperses into hundreds of micro-pellets in the stomach, ensuring reliable gastric emptying and round-the-clock comfort.',
                'price': Decimal('800.00'),
                'discount_price': Decimal('720.00'),
                'stock': 100,
                'unit': 'Box of 100 tabs',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/beximco-maxpro-20mg-esomeprazole-mups-angle-1.webp', 'Maxpro 20 MUPS Silver Foiled Pharmaceutical Box', 1),
                    ('products/gallery/beximco-maxpro-20mg-esomeprazole-mups-angle-2.webp', 'Cold-Form Alu-Alu Foil Strip of Pink Tablets', 2),
                    ('products/gallery/beximco-maxpro-20mg-esomeprazole-mups-angle-3.webp', 'Macro Shot of Scored Film-Coated Oval Tablet', 3),
                    ('products/gallery/beximco-maxpro-20mg-esomeprazole-mups-angle-4.webp', 'Beximco Security Hologram and Barcode Verification', 4),
                ]
            },
            {
                'slug': 'dettol-antiseptic-liquid-disinfectant-500ml',
                'name': 'Dettol Antiseptic Liquid Disinfectant & First Aid Wound Cleanser 500ml',
                'category': 'personal-hygiene',
                'brand': 'dettol',
                'short_description': 'Chloroxylenol hospital-grade disinfectant for first aid, cuts, scrapes, and personal hygiene.',
                'description': 'Dettol Antiseptic Liquid provides trusted protection against 100 illness-causing germs. Non-staining formulation ideal for wound cleansing, personal bathing, and laundry sanitization.',
                'price': Decimal('320.00'),
                'discount_price': Decimal('295.00'),
                'stock': 140,
                'unit': '500 ml',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/dettol-antiseptic-liquid-disinfectant-500ml-angle-1.webp', 'Dettol Iconic Amber Curved Bottle with Sword Logo', 1),
                    ('products/gallery/dettol-antiseptic-liquid-disinfectant-500ml-angle-2.webp', 'Milky Cloud Bloom Effect When Diluted in Water', 2),
                    ('products/gallery/dettol-antiseptic-liquid-disinfectant-500ml-angle-3.webp', 'Accurate Cap Measuring Guide for Dilution', 3),
                    ('products/gallery/dettol-antiseptic-liquid-disinfectant-500ml-angle-4.webp', 'Hospital Trial Clinical Certification Seal', 4),
                ]
            },
            {
                'slug': 'savlon-antiseptic-cream-healing-60g',
                'name': 'Savlon Antiseptic Soothing Healing Cream for Cuts & Burns 60g Tube',
                'category': 'first-aid',
                'brand': 'savlon',
                'short_description': 'Cetrimide and Chlorhexidine cream that cleanses minor wounds and prevents skin infection.',
                'description': 'Savlon Antiseptic Cream cleanses and aids the natural healing of minor wounds, cuts, grazes, bites, and superficial burns. Smooth soothing formulation moisturizes damaged skin while neutralizing harmful bacteria.',
                'price': Decimal('140.00'),
                'discount_price': Decimal('125.00'),
                'stock': 160,
                'unit': '60 gm',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/savlon-antiseptic-cream-healing-60g-angle-1.webp', 'Savlon 60g Blue and White Medical Tube Front', 1),
                    ('products/gallery/savlon-antiseptic-cream-healing-60g-angle-2.webp', 'Smooth White Healing Ointment Dispensed from Nozzle', 2),
                    ('products/gallery/savlon-antiseptic-cream-healing-60g-angle-3.webp', 'First-Aid Cross Antiseptic Healing Emblem', 3),
                    ('products/gallery/savlon-antiseptic-cream-healing-60g-angle-4.webp', 'Outer Carton with Emergency Application Instructions', 4),
                ]
            },
            {
                'slug': 'omron-hem-7120-automatic-blood-pressure-monitor',
                'name': 'Omron HEM-7120 Automatic Upper Arm Digital Blood Pressure Monitor',
                'category': 'first-aid',
                'brand': 'beximco',
                'short_description': 'Clinically validated IntelliSense digital blood pressure monitor with hypertension indicator.',
                'description': 'Omron HEM-7120 provides simple one-touch measurement of systolic, diastolic blood pressure and pulse rate. Features IntelliSense technology for comfortable, controlled inflation without pre-setting or re-inflation, plus body movement detection and cuff wrapping guide.',
                'price': Decimal('3650.00'),
                'discount_price': Decimal('3250.00'),
                'stock': 40,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/omron-hem-7120-automatic-blood-pressure-monitor-angle-1.webp', 'Omron HEM-7120 Digital Console with LCD Reading', 1),
                    ('products/gallery/omron-hem-7120-automatic-blood-pressure-monitor-angle-2.webp', 'IntelliSense Upper Arm Contour Cuff & Air Tube', 2),
                    ('products/gallery/omron-hem-7120-automatic-blood-pressure-monitor-angle-3.webp', 'One-Touch Start Button and Side Air Jack View', 3),
                    ('products/gallery/omron-hem-7120-automatic-blood-pressure-monitor-angle-4.webp', 'Zipper Travel Pouch & 3-Year Warranty Card', 4),
                ]
            },
            {
                'slug': 'square-pharma-ceevit-250mg-chewable-box',
                'name': 'Square Pharma Ceevit 250mg Vitamin C Chewable Tablets (Box of 240 Tablets)',
                'category': 'vitamins',
                'brand': 'square-pharma',
                'short_description': 'Delicious orange-flavored Ascorbic Acid chewable tablets for daily immune defense and collagen synthesis.',
                'description': 'Square Pharma Ceevit provides 250mg of essential Vitamin C (Ascorbic Acid BP) per tablet. Strengthens the immune system, promotes wound healing, combats free-radical oxidation, and supports gum and skin vitality. Sugar-balanced chewable formula suitable for family daily wellness.',
                'price': Decimal('480.00'),
                'discount_price': Decimal('430.00'),
                'stock': 180,
                'unit': 'Box of 240 tabs',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/square-pharma-ceevit-250mg-chewable-box-angle-1.webp', 'Square Pharma Ceevit 250mg Orange Box Front View', 1),
                    ('products/gallery/square-pharma-ceevit-250mg-chewable-box-angle-2.webp', 'Alu-Alu Foil Strip of Bright Orange Chewable Tablets', 2),
                    ('products/gallery/square-pharma-ceevit-250mg-chewable-box-angle-3.webp', 'Single Chewable Tablet Macro Showing Embossed C Mark', 3),
                    ('products/gallery/square-pharma-ceevit-250mg-chewable-box-angle-4.webp', 'DGDA QR Verification and Daily Recommended Dose Leaflet', 4),
                ]
            },
            {
                'slug': 'savlon-antiseptic-liquid-1000ml',
                'name': 'Savlon Hospital-Grade Antiseptic Liquid Disinfectant 1 Litre Bottle',
                'category': 'personal-hygiene',
                'brand': 'savlon',
                'short_description': 'Broad-spectrum Chlorhexidine & Cetrimide antiseptic for medical first aid, bathing, and sanitization.',
                'description': 'Savlon Antiseptic Liquid kills 99.9% of bacteria and viruses on skin and surfaces. Gentle non-staining germicidal action recommended by healthcare professionals for wound cleaning, post-natal care, laundry disinfection, and family personal hygiene.',
                'price': Decimal('460.00'),
                'discount_price': Decimal('395.00'),
                'stock': 130,
                'unit': '1 ltr',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/savlon-antiseptic-liquid-1000ml-angle-1.webp', 'Savlon 1 Litre Economy Plastic Bottle Front View', 1),
                    ('products/gallery/savlon-antiseptic-liquid-1000ml-angle-2.webp', 'Blue-tinted Liquid Disinfectant Pouring into Bathing Water', 2),
                    ('products/gallery/savlon-antiseptic-liquid-1000ml-angle-3.webp', 'Calibrated Dilution Cap and First Aid Application Guide', 3),
                    ('products/gallery/savlon-antiseptic-liquid-1000ml-angle-4.webp', 'Tamper-Proof Induction Seal and Hospital Endorsement Badge', 4),
                ]
            },

            # ==================== MEGA MARKET / GENERAL ====================
            {
                'slug': 'samsung-55-crystal-4k-uhd-smart-tv',
                'name': 'Samsung 55" Crystal 4K UHD Smart TV (Dynamic Crystal Color & AirSlim)',
                'category': 'electronics-appliances',
                'brand': 'samsung',
                'short_description': 'Crystal Processor 4K, HDR10+, Smart Hub, SolarCell Remote, and Q-Symphony sound.',
                'description': 'Elevate your home cinema with the Samsung 55" Crystal 4K UHD Smart TV. Features Dynamic Crystal Color for lifelike realism, AirSlim ultra-thin silhouette, Motion Xcelerator for fluid gaming, and Tizen OS with Netflix, YouTube, and Amazon Prime built-in.',
                'price': Decimal('78500.00'),
                'discount_price': Decimal('69900.00'),
                'stock': 15,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': True,
                'images': [
                    ('products/gallery/samsung-55-crystal-4k-uhd-smart-tv-angle-1.webp', 'Samsung 55" 4K Smart TV Bezel-Less Front Display', 1),
                    ('products/gallery/samsung-55-crystal-4k-uhd-smart-tv-angle-2.webp', 'AirSlim Profile Depth View Showing Thin Metal Edge', 2),
                    ('products/gallery/samsung-55-crystal-4k-uhd-smart-tv-angle-3.webp', 'HDMI 2.1 and Optical Audio Rear Connection Ports', 3),
                    ('products/gallery/samsung-55-crystal-4k-uhd-smart-tv-angle-4.webp', 'Eco-Friendly SolarCell Smart Voice Remote Control', 4),
                ]
            },
            {
                'slug': 'unilever-pureit-classic-mineral-water-purifier',
                'name': 'Unilever Pureit Classic Mineral RO+UV Water Purifier 23L',
                'category': 'electronics-appliances',
                'brand': 'unilever',
                'short_description': 'Multi-stage purification with Germkill technology without needing electricity or running tap.',
                'description': 'Unilever Pureit Classic delivers 100% safe drinking water adhering to stringent USEPA criteria. Features advanced Microfiber mesh, Activated Carbon trap, and Germkill processor to eliminate 99.99% of bacteria, parasites, and viruses while adding essential minerals.',
                'price': Decimal('4850.00'),
                'discount_price': Decimal('4250.00'),
                'stock': 25,
                'unit': '1 unit',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/unilever-pureit-classic-mineral-water-purifier-angle-1.webp', 'Unilever Pureit Classic 23L Purifier Front Angle', 1),
                    ('products/gallery/unilever-pureit-classic-mineral-water-purifier-angle-2.webp', 'Transparent Upper Storage Chamber and Dispenser Tap', 2),
                    ('products/gallery/unilever-pureit-classic-mineral-water-purifier-angle-3.webp', 'Internal Germkill Filter Cartridge Cross-Section', 3),
                    ('products/gallery/unilever-pureit-classic-mineral-water-purifier-angle-4.webp', 'Unilever Box Packaging with Safety Seal', 4),
                ]
            },
            {
                'slug': 'nestle-nescafe-gold-blend-coffee-200g',
                'name': 'Nestle Nescafe Gold Blend Rich & Smooth Instant Coffee 200g Jar',
                'category': 'groceries',
                'brand': 'nestle',
                'short_description': 'Expertly crafted golden roasted Arabica & Robusta beans with rich aromatic crema.',
                'description': 'Savor the distinctive taste of Nescafe Gold Blend. Masterfully blended Arabica and Robusta beans golden roasted to unlock delicate fruity and toasted notes. 100% pure instant coffee crafted in Switzerland.',
                'price': Decimal('1450.00'),
                'discount_price': Decimal('1290.00'),
                'stock': 60,
                'unit': '200 gm jar',
                'is_featured': True,
                'is_flash_sale': False,
                'images': [
                    ('products/gallery/nestle-nescafe-gold-blend-coffee-200g-angle-1.webp', 'Nescafe Gold Blend 200g Glass Jar Front View', 1),
                    ('products/gallery/nestle-nescafe-gold-blend-coffee-200g-angle-2.webp', 'Golden Foil Seal Under Cap Preserving Freshness', 2),
                    ('products/gallery/nestle-nescafe-gold-blend-coffee-200g-angle-3.webp', 'Golden Granular Coffee Crystals Close-Up Macro', 3),
                    ('products/gallery/nestle-nescafe-gold-blend-coffee-200g-angle-4.webp', 'Freshly Brewed Hot Coffee Mug with Velvety Crema', 4),
                ]
            },
        ]

        for p_data in products_data:
            cat_obj = cat_map.get(p_data['category']) or Category.objects.filter(slug=p_data['category']).first()
            brand_obj = brand_map.get(p_data['brand']) or Brand.objects.filter(slug=p_data['brand']).first()

            prod, _ = Product.objects.update_or_create(
                slug=p_data['slug'],
                defaults={
                    'name': p_data['name'],
                    'category': cat_obj,
                    'brand': brand_obj,
                    'short_description': p_data['short_description'],
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'discount_price': p_data['discount_price'],
                    'stock': p_data['stock'],
                    'unit': p_data.get('unit', '1 pc'),
                    'image': f"products/{p_data['slug']}.webp",
                    'is_featured': p_data.get('is_featured', True),
                    'is_flash_sale': p_data.get('is_flash_sale', False),
                    'is_active': True,
                }
            )

            # Synchronize multiple gallery images
            for img_path, alt_txt, order_num in p_data.get('images', []):
                ProductImage.objects.update_or_create(
                    product=prod,
                    order=order_num,
                    defaults={
                        'image': img_path,
                        'alt_text': alt_txt,
                    }
                )

        # Synchronize supplemental gallery images to guarantee >= 3-4 images for every product
        supplemental_gallery = {
            'tissue-paper-box-12': [
                ('products/gallery/tissue-paper-box-gallery-3.webp', 'Tissue Paper Box - Dispenser Pop-Up Detail', 3),
                ('products/gallery/tissue-paper-box-gallery-4.webp', 'Tissue Paper Box - 2-Ply Ultra Soft Texture & Pack', 4),
            ],
            'chicken-meat-11': [
                ('products/gallery/chicken-meat-gallery-3.webp', 'Chicken Meat - Fresh Cut Diced Pieces', 3),
                ('products/gallery/chicken-meat-gallery-4.webp', 'Chicken Meat - Vacuum Sealed Hygienic Pack', 4),
            ],
        }
        for p_slug, imgs in supplemental_gallery.items():
            p_obj = Product.objects.filter(slug=p_slug).first()
            if p_obj:
                for img_path, alt_txt, order_num in imgs:
                    ProductImage.objects.update_or_create(
                        product=p_obj,
                        order=order_num,
                        defaults={
                            'image': img_path,
                            'alt_text': alt_txt,
                        }
                    )

    def _ensure_media_assets(self):
        """
        Guarantees that all Category images, Brand logos, Product cover images,
        and Product gallery images physically exist in MEDIA_ROOT.
        If files are missing (e.g. after fresh clone or git pull where media/ is gitignored),
        this auto-generates clean, theme-aware, aesthetic placeholder images with Pillow.
        """
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.stdout.write(self.style.WARNING("  [WARN] Pillow is not installed; skipping placeholder image generation."))
            return

        def _get_theme_style_for_item(name, category_slug, brand_name):
            key_lower = f"{name} {category_slug} {brand_name}".lower()
            if any(k in key_lower for k in ['laptop', 'macbook', 'phone', 'iphone', 'samsung galaxy', 'rtx', 'asus', 'dell', 'logitech', 'headphone', 'tech', 'hardware', 'tablet', 'gadget']):
                return ((15, 23, 42), (241, 245, 249), (2, 132, 199), "Tech Flagship")
            elif any(k in key_lower for k in ['skin', 'cream', 'serum', 'cleanser', 'lipstick', 'mascara', 'makeup', 'fragrance', 'perfume', 'ordinary', 'cerave', 'mac', 'maybelline', 'loreal', 'chanel', 'beauty']):
                return ((253, 242, 248), (157, 23, 77), (219, 39, 119), "100% Authentic")
            elif any(k in key_lower for k in ['panjabi', 'kurti', 'saree', 'blazer', 'denim', 'jeans', 'oxford', 'shoe', 'shirt', 'dress', 'aarong', 'sailor', 'zara', 'apex', 'bata', 'fashion', 'formalwear']):
                return ((254, 252, 232), (124, 45, 18), (217, 119, 6), "Artisan Style")
            elif any(k in key_lower for k in ['rice', 'oil', 'honey', 'dates', 'nuts', 'ghee', 'chia', 'seed', 'organic', 'grocery', 'agro', 'khaas', 'chaldal', 'chinigura', 'groceries']):
                return ((240, 253, 244), (21, 128, 61), (22, 163, 74), "100% Organic")
            elif any(k in key_lower for k in ['pharma', 'medicine', 'prescription', 'napa', 'seclo', 'ceevit', 'maxpro', 'bextram', 'dettol', 'savlon', 'hygiene', 'antiseptic', 'monitor', 'first aid', 'vitamin']):
                return ((240, 253, 250), (15, 118, 110), (13, 148, 136), "DGDA Licensed")
            else:
                return ((248, 250, 252), (30, 41, 59), (248, 86, 6), "Marketplace")

        def _generate_placeholder(filepath, title, subtitle='', badge='', size=(800, 800), style_tuple=None):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            if style_tuple:
                bg_col, text_col, accent_col, default_badge = style_tuple
            else:
                bg_col, text_col, accent_col, default_badge = ((241, 245, 249), (30, 41, 59), (59, 130, 246), "Verified")

            badge = badge or default_badge
            img = Image.new('RGB', size, color=bg_col)
            draw = ImageDraw.Draw(img)
            w, h = size
            pad = 24
            is_light = bg_col[0] > 200
            card_bg = (255, 255, 255) if is_light else (30, 41, 59)
            border_col = (226, 232, 240) if is_light else (51, 65, 85)

            draw.rounded_rectangle([(pad, pad), (w - pad, h - pad)], radius=18, fill=card_bg, outline=border_col, width=2)
            draw.rounded_rectangle([(pad + 4, pad + 4), (w - pad - 4, pad + 14)], radius=4, fill=accent_col)

            if badge:
                draw.rounded_rectangle([(pad + 18, pad + 24), (pad + 200, pad + 62)], radius=10, fill=bg_col)
                draw.text((pad + 109, pad + 43), str(badge)[:22], fill=accent_col, anchor='mm')

            title_str = str(title).strip()
            if len(title_str) > 30:
                mid = title_str[:30].rfind(' ')
                if mid == -1: mid = 30
                line1 = title_str[:mid]
                line2 = title_str[mid:].strip()[:30]
                draw.text((w // 2, h // 2 - 30), line1, fill=text_col, anchor='mm')
                draw.text((w // 2, h // 2 + 5), line2, fill=text_col, anchor='mm')
            else:
                draw.text((w // 2, h // 2 - 12), title_str, fill=text_col, anchor='mm')

            if subtitle:
                draw.text((w // 2, h // 2 + 42), str(subtitle)[:40], fill=accent_col, anchor='mm')

            ext = os.path.splitext(filepath)[1].lower()
            fmt = 'WEBP' if ext == '.webp' else ('JPEG' if ext in ['.jpg', '.jpeg'] else 'PNG')
            img.save(filepath, format=fmt)

        generated_count = 0

        # 1. Categories
        for cat in Category.objects.all():
            if not cat.image:
                cat.image = f"categories/{cat.slug}.png"
                cat.save(update_fields=['image'])
            fp = os.path.join(settings.MEDIA_ROOT, str(cat.image))
            if not os.path.exists(fp):
                style = _get_theme_style_for_item(cat.name, cat.slug, '')
                _generate_placeholder(fp, cat.name, subtitle='Category Showcase', badge='Category', size=(600, 400), style_tuple=style)
                generated_count += 1

        # 2. Brands
        for brand in Brand.objects.all():
            if not brand.logo:
                brand.logo = f"brands/{brand.slug}.png"
                brand.save(update_fields=['logo'])
            fp = os.path.join(settings.MEDIA_ROOT, str(brand.logo))
            if not os.path.exists(fp):
                style = _get_theme_style_for_item(brand.name, '', brand.name)
                _generate_placeholder(fp, brand.name, subtitle='Official Brand', badge='Verified', size=(400, 400), style_tuple=style)
                generated_count += 1

        # 3. Products
        for prod in Product.objects.all():
            if not prod.image or str(prod.image) == 'products/.png':
                prod.image = f"products/{prod.slug}.webp"
                prod.save(update_fields=['image'])
            fp = os.path.join(settings.MEDIA_ROOT, str(prod.image))
            if not os.path.exists(fp):
                c_slug = prod.category.slug if prod.category else ''
                b_name = prod.brand.name if prod.brand else ''
                style = _get_theme_style_for_item(prod.name, c_slug, b_name)
                _generate_placeholder(fp, prod.name, subtitle=f"৳{prod.effective_price}", badge=b_name, size=(800, 800), style_tuple=style)
                generated_count += 1

        # 4. Product Gallery Images
        for pimg in ProductImage.objects.select_related('product', 'product__category', 'product__brand').all():
            if pimg.image:
                fp = os.path.join(settings.MEDIA_ROOT, str(pimg.image))
                if not os.path.exists(fp):
                    pname = pimg.product.name if pimg.product else 'Gallery'
                    c_slug = pimg.product.category.slug if (pimg.product and pimg.product.category) else ''
                    b_name = pimg.product.brand.name if (pimg.product and pimg.product.brand) else ''
                    style = _get_theme_style_for_item(pname, c_slug, b_name)
                    _generate_placeholder(
                        fp,
                        pname,
                        subtitle=f"Angle #{pimg.order} • Gallery",
                        badge=f"Angle {pimg.order}",
                        size=(800, 800),
                        style_tuple=style
                    )
                    generated_count += 1

        if generated_count > 0:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Successfully auto-generated {generated_count} missing media images."))
        else:
            self.stdout.write(self.style.SUCCESS("  [OK] All media image files are present on disk."))

    def _print_summary(self):
        """Prints a structured summary of seeded marketplace database records."""
        setting = SiteSetting.get_settings()
        self.stdout.write(self.style.SUCCESS("\n========================================================"))
        self.stdout.write(self.style.SUCCESS("  [SUCCESS] All E-Commerce Database Data Ready!"))
        self.stdout.write(self.style.SUCCESS("========================================================"))
        self.stdout.write(f"  * Store Branding:       {setting.site_name} ({setting.contact_phone})")
        self.stdout.write(f"  * Catalog Categories:   {Category.objects.count()} active categories")
        self.stdout.write(f"  * Catalog Brands:       {Brand.objects.count()} active brands")
        self.stdout.write(f"  * Marketplace Products: {Product.objects.count()} products")
        self.stdout.write(f"  * Product Gallery:      {ProductImage.objects.count()} high-res images")
        self.stdout.write(f"  * Customer Reviews:     {ProductReview.objects.count()} verified reviews")
        self.stdout.write(f"  * Delivery Slots:       {DeliverySlot.objects.count()} time slots")
        self.stdout.write(f"  * Discount Coupons:     {Coupon.objects.count()} promo coupons")
        self.stdout.write(f"  * Seeded Orders:        {Order.objects.count()} orders ({OrderItem.objects.count()} items)")
        self.stdout.write(f"  * RBAC Modules:         {Module.objects.count()} modules ({Submodule.objects.count()} submodules, {Permission.objects.count()} perms)")
        self.stdout.write(f"  * RBAC Roles:           {Role.objects.count()} roles ({RolePermission.objects.count()} assignments)")
        self.stdout.write(f"  * Registered Users:     {User.objects.count()} test accounts")
        self.stdout.write("--------------------------------------------------------")
        self.stdout.write("  Pre-configured Test Accounts:")
        self.stdout.write("    - superadmin    / Admin@12345    (Super Admin - unrestricted)")
        self.stdout.write("    - catalog_admin / Manager@12345  (Catalog Manager)")
        self.stdout.write("    - orders_staff  / Staff@12345    (Order Dispatcher)")
        self.stdout.write("    - customer_user / User@12345     (Customer Account)")
        self.stdout.write("========================================================\n")
