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
            self._seed_catalog()

        # 3. Always synchronize RBAC modules, permissions & superuser roles
        self.stdout.write(self.style.NOTICE("==> Synchronizing RBAC Modules & Permissions..."))
        self._seed_rbac()

        # 4. Synchronize demo accounts & passwords
        self.stdout.write(self.style.NOTICE("==> Verifying Demo Accounts & Passwords..."))
        self._seed_users()

        # 5. Synchronize Store & Brand Settings
        self.stdout.write(self.style.NOTICE("==> Verifying Store & Brand Settings..."))
        self._seed_site_settings()

        # 6. Print summary
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
            setting.site_name = "PythonEcom"
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
            defaults={
                'full_name': 'John Customer',
                'phone': '+880 1819-001122',
                'street_address': 'House 42, Road 11, Banani',
                'apartment': 'Suite 4B',
                'city': 'Dhaka',
                'postal_code': '1213',
                'country': 'Bangladesh',
                'is_default': True,
            }
        )

    def _seed_catalog(self):
        categories_data = [
            {'name': 'Electronics & Laptops', 'slug': 'electronics-laptops', 'icon': 'bi-laptop', 'is_featured': True, 'order': 1},
            {'name': 'Smartphones & Tablets', 'slug': 'smartphones-tablets', 'icon': 'bi-phone', 'is_featured': True, 'order': 2},
            {'name': 'Fashion & Apparel', 'slug': 'fashion-apparel', 'icon': 'bi-bag-heart', 'is_featured': True, 'order': 3},
            {'name': 'Audio & Headphones', 'slug': 'audio-headphones', 'icon': 'bi-headphones', 'is_featured': True, 'order': 4},
            {'name': 'Watches & Wearables', 'slug': 'watches-wearables', 'icon': 'bi-smartwatch', 'is_featured': True, 'order': 5},
            {'name': 'Home & Living', 'slug': 'home-living', 'icon': 'bi-house-heart', 'is_featured': False, 'order': 6},
        ]

        cat_map = {}
        for c in categories_data:
            obj, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'icon': c['icon'],
                    'is_featured': c['is_featured'],
                    'order': c['order']
                }
            )
            cat_map[c['slug']] = obj

        brands_data = ['Apple', 'Samsung', 'Sony', 'Nike', 'Dell', 'Logitech']
        brand_map = {}
        for b in brands_data:
            obj, _ = Brand.objects.update_or_create(
                slug=slugify(b),
                defaults={'name': b}
            )
            brand_map[b] = obj

        products_data = [
            {
                'name': 'MacBook Pro 16" M3 Max',
                'slug': 'macbook-pro-16-m3-max',
                'category': 'electronics-laptops',
                'brand': 'Apple',
                'short_description': 'Supercharged by M3 Max with up to 16-core CPU and 40-core GPU.',
                'description': 'The most advanced Mac laptop ever built for pro workflows. With Liquid Retina XDR display, incredible battery life up to 22 hours, and high-performance unified memory.',
                'price': Decimal('2499.00'),
                'discount_price': Decimal('2299.00'),
                'stock': 14,
                'is_featured': True,
                'is_flash_sale': True,
            },
            {
                'name': 'iPhone 15 Pro Max 256GB',
                'slug': 'iphone-15-pro-max-256gb',
                'category': 'smartphones-tablets',
                'brand': 'Apple',
                'short_description': 'Titanium design with A17 Pro chip and 5x Telephoto zoom.',
                'description': 'Forged in aerospace-grade titanium, featuring the groundbreaking A17 Pro chip, customizable Action button, and the most powerful iPhone camera system ever.',
                'price': Decimal('1199.00'),
                'discount_price': None,
                'stock': 28,
                'is_featured': True,
                'is_flash_sale': False,
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'slug': 'samsung-galaxy-s24-ultra',
                'category': 'smartphones-tablets',
                'brand': 'Samsung',
                'short_description': 'Galaxy AI is here. Epic titanium frame and embedded S Pen.',
                'description': 'Meet Galaxy S24 Ultra, the ultimate form of Galaxy Ultra with a new titanium exterior and a 6.8 inch flat display with Quad Tele zoom system.',
                'price': Decimal('1299.00'),
                'discount_price': Decimal('1149.00'),
                'stock': 19,
                'is_featured': True,
                'is_flash_sale': True,
            },
        ]

        for p_data in products_data:
            Product.objects.update_or_create(
                slug=p_data['slug'],
                defaults={
                    'name': p_data['name'],
                    'category': cat_map.get(p_data['category']),
                    'brand': brand_map.get(p_data['brand']),
                    'short_description': p_data['short_description'],
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'discount_price': p_data['discount_price'],
                    'stock': p_data['stock'],
                    'is_featured': p_data['is_featured'],
                    'is_flash_sale': p_data['is_flash_sale'],
                    'is_active': True,
                }
            )

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
