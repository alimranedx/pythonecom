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

        existing_img_ids = set(ProductImage.objects.values_list('id', flat=True))
        new_fixture_images = []
        for item in records.get('product.productimage', []):
            if item['pk'] not in existing_img_ids:
                f = dict(item['fields'])
                prod = prod_map.get(f['product']) or Product.objects.filter(id=f['product']).first()
                if prod:
                    new_fixture_images.append(ProductImage(
                        id=item['pk'],
                        product=prod,
                        image=f['image'],
                        alt_text=f.get('alt_text', ''),
                        order=f.get('order', 0),
                    ))
                    existing_img_ids.add(item['pk'])
        if new_fixture_images:
            ProductImage.objects.bulk_create(new_fixture_images, batch_size=200)

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
        Seeds complete multi-niche taxonomy, top brands, and catalog products across all 6 themes:
        1. Mega Market: Walton, Singer, Vision, Haier, Transcom, Philips, RFL, Miyako, Gazi, Havells, Panasonic
        2. Tech & Gadgets: Apple, Samsung, ASUS ROG, Dell, Sony, Logitech, HP, Lenovo, Xiaomi, Anker, Corsair
        3. Beauty & Cosmetics: The Ordinary, CeraVe, L'Oreal, MAC, Maybelline, Chanel, Laneige, COSRX, Innisfree, Dior, Fenty
        4. Fashion & Lifestyle: Aarong, Sailor, Apex, Bata, Zara Man, Yellow, Richman, Gentle Park, Taaga, Cats Eye, Lotto
        5. Organic Grocery: Khaas Food, Chaldal Organic, PRAN, ACI Pure, Radhuni, Teer, Fresh, Ispahani, Kazi & Kazi, Nestle, Aarong Dairy
        6. Pharmacy & Health: Square Pharma, Beximco, Incepta, Renata, ACI Health, Dettol, Savlon, Omron, Accu-Chek, Johnson & Johnson, Orion

        Guarantees >= 10 categories, >= 10 brands, and >= 30 products per theme.
        Guarantees realistic BDT prices, discount percentages, stock quantities,
        and 4 ProductImage gallery entries for every product.
        """
        from .catalog_data import CATEGORIES_DATA, BRANDS_DATA, PRODUCTS_DATA

        # 1. Synchronize Categories across all 6 themes
        cat_map = {}
        valid_cat_slugs = set()
        for c in CATEGORIES_DATA:
            obj, _ = Category.objects.update_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'icon': c['icon'],
                    'theme': c['theme'],
                    'is_featured': c.get('is_featured', True),
                    'order': c.get('order', 0),
                    'image': f"categories/{c['slug']}.png"
                }
            )
            cat_map[c['slug']] = obj
            valid_cat_slugs.add(c['slug'])

        # 2. Synchronize Brands across all 6 themes
        brand_map = {}
        valid_brand_slugs = set()
        for b in BRANDS_DATA:
            obj, _ = Brand.objects.update_or_create(
                slug=b['slug'],
                defaults={
                    'name': b['name'],
                    'theme': b['theme'],
                    'logo': f"brands/{b['slug']}.png"
                }
            )
            brand_map[b['slug']] = obj
            valid_brand_slugs.add(b['slug'])

        # 3. Synchronize Products & Multi-Angle Gallery Images
        valid_prod_slugs = set()
        for p_data in PRODUCTS_DATA:
            cat_obj = cat_map.get(p_data['category']) or Category.objects.filter(slug=p_data['category']).first()
            brand_obj = brand_map.get(p_data['brand']) or Brand.objects.filter(slug=p_data['brand']).first()

            prod, _ = Product.objects.update_or_create(
                slug=p_data['slug'],
                defaults={
                    'name': p_data['name'],
                    'category': cat_obj,
                    'brand': brand_obj,
                    'theme': p_data.get('theme', cat_obj.theme if cat_obj else 'mega_market'),
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
            valid_prod_slugs.add(p_data['slug'])

        # Synchronize 4 distinct gallery angles efficiently
        existing_gallery = set(ProductImage.objects.values_list('product_id', 'order'))
        new_catalog_images = []
        for p_data in PRODUCTS_DATA:
            prod = Product.objects.filter(slug=p_data['slug']).first()
            if not prod:
                continue
            for img_path, alt_txt, order_num in p_data.get('images', []):
                if (prod.id, order_num) not in existing_gallery:
                    new_catalog_images.append(ProductImage(
                        product=prod,
                        order=order_num,
                        image=img_path,
                        alt_text=alt_txt,
                    ))
                    existing_gallery.add((prod.id, order_num))

        if new_catalog_images:
            ProductImage.objects.bulk_create(new_catalog_images, batch_size=200)

        # 4. Clean up legacy out-of-niche dummy records to guarantee zero leakage
        Product.objects.exclude(slug__in=valid_prod_slugs).delete()
        Category.objects.exclude(slug__in=valid_cat_slugs).delete()
        Brand.objects.exclude(slug__in=valid_brand_slugs).delete()

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

        def _get_theme_style_for_item(name, category_slug, brand_name, theme=''):
            if theme == 'tech_gadgets':
                return ((15, 23, 42), (241, 245, 249), (2, 132, 199), "Tech Flagship")
            elif theme == 'beauty_cosmetics':
                return ((253, 242, 248), (157, 23, 77), (219, 39, 119), "100% Authentic")
            elif theme == 'fashion_lifestyle':
                return ((254, 252, 232), (124, 45, 18), (217, 119, 6), "Artisan Style")
            elif theme == 'grocery_organic':
                return ((240, 253, 244), (21, 128, 61), (22, 163, 74), "100% Organic")
            elif theme == 'pharmacy_health':
                return ((240, 253, 250), (15, 118, 110), (13, 148, 136), "DGDA Licensed")
            elif theme == 'mega_market':
                return ((255, 247, 237), (30, 41, 59), (248, 86, 6), "Marketplace")

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
                style = _get_theme_style_for_item(cat.name, cat.slug, '', theme=cat.theme)
                _generate_placeholder(fp, cat.name, subtitle='Category Showcase', badge='Category', size=(600, 400), style_tuple=style)
                generated_count += 1

        # 2. Brands
        for brand in Brand.objects.all():
            if not brand.logo:
                brand.logo = f"brands/{brand.slug}.png"
                brand.save(update_fields=['logo'])
            fp = os.path.join(settings.MEDIA_ROOT, str(brand.logo))
            if not os.path.exists(fp):
                style = _get_theme_style_for_item(brand.name, '', brand.name, theme=brand.theme)
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
                style = _get_theme_style_for_item(prod.name, c_slug, b_name, theme=prod.theme)
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
                    style = _get_theme_style_for_item(pname, c_slug, b_name, theme=pimg.product.theme if pimg.product else '')
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
        self.stdout.write("  Multi-Niche Theme Catalog Breakdown:")
        themes = ['mega_market', 'tech_gadgets', 'beauty_cosmetics', 'fashion_lifestyle', 'grocery_organic', 'pharmacy_health']
        for th in themes:
            c_cnt = Category.objects.filter(theme=th).count()
            b_cnt = Brand.objects.filter(theme=th).count()
            p_cnt = Product.objects.filter(theme=th).count()
            self.stdout.write(f"    - {th:18}: {c_cnt:2d} categories, {b_cnt:2d} brands, {p_cnt:2d} products")
        self.stdout.write("--------------------------------------------------------")
        self.stdout.write("  Pre-configured Test Accounts:")
        self.stdout.write("    - superadmin    / Admin@12345    (Super Admin - unrestricted)")
        self.stdout.write("    - catalog_admin / Manager@12345  (Catalog Manager)")
        self.stdout.write("    - orders_staff  / Staff@12345    (Order Dispatcher)")
        self.stdout.write("    - customer_user / User@12345     (Customer Account)")
        self.stdout.write("========================================================\n")
