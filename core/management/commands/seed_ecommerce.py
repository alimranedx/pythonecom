from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rbac.models import Module, Submodule, Permission, Role, RolePermission, UserRole
from accounts.models import CustomerProfile, Address
from product.models import Category, Brand, Product, ProductReview
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Seeds initial RBAC modules, permissions, test users, categories, and marketplace products."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Seeding RBAC Modules & Permissions..."))
        self._seed_rbac()

        self.stdout.write(self.style.NOTICE("==> Seeding Test Users & Role Assignments..."))
        self._seed_users()

        self.stdout.write(self.style.NOTICE("==> Seeding Marketplace Catalog (Categories, Brands, Products)..."))
        self._seed_catalog()

        self.stdout.write(self.style.SUCCESS("[SUCCESS] All e-commerce seed data successfully generated!"))

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
            from django.utils.text import slugify
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
            {
                'name': 'Sony WH-1000XM5 Wireless Headphones',
                'slug': 'sony-wh-1000xm5-wireless-headphones',
                'category': 'audio-headphones',
                'brand': 'Sony',
                'short_description': 'Industry-leading noise cancellation with 30-hour battery life.',
                'description': 'Our industry-leading noise canceling headphones with two processors and eight microphones for unprecedented noise cancellation and exceptional call quality.',
                'price': Decimal('399.00'),
                'discount_price': Decimal('349.00'),
                'stock': 35,
                'is_featured': True,
                'is_flash_sale': False,
            },
            {
                'name': 'Nike Air Zoom Pegasus 40',
                'slug': 'nike-air-zoom-pegasus-40',
                'category': 'fashion-apparel',
                'brand': 'Nike',
                'short_description': 'A springy ride for any run with breathable engineered mesh.',
                'description': 'The Pegasus 40 offers a responsive ride with familiar support, engineered to help you conquer all your running goals in maximum style and cushion comfort.',
                'price': Decimal('140.00'),
                'discount_price': Decimal('119.00'),
                'stock': 42,
                'is_featured': True,
                'is_flash_sale': True,
            },
            {
                'name': 'Apple Watch Ultra 2 GPS + Cellular',
                'slug': 'apple-watch-ultra-2',
                'category': 'watches-wearables',
                'brand': 'Apple',
                'short_description': 'Rugged 49mm titanium case and precision dual-frequency GPS.',
                'description': 'The most capable and rugged Apple Watch pushes boundaries with the S9 SiP, precision dual-frequency GPS, and up to 36 hours of battery life.',
                'price': Decimal('799.00'),
                'discount_price': None,
                'stock': 8,
                'is_featured': True,
                'is_flash_sale': False,
            },
            {
                'name': 'Dell XPS 15 9530 Core i9',
                'slug': 'dell-xps-15-9530',
                'category': 'electronics-laptops',
                'brand': 'Dell',
                'short_description': 'OLED 3.5K touch display with RTX 4070 graphics.',
                'description': 'The perfect balance of power and portability. The XPS 15 laptop delivers stellar performance with 13th Gen Intel Core processors and brilliant OLED display.',
                'price': Decimal('2199.00'),
                'discount_price': Decimal('1999.00'),
                'stock': 11,
                'is_featured': False,
                'is_flash_sale': False,
            },
            {
                'name': 'Logitech MX Master 3S Wireless Mouse',
                'slug': 'logitech-mx-master-3s',
                'category': 'audio-headphones',
                'brand': 'Logitech',
                'short_description': 'Performance wireless mouse with 8K DPI sensor and Quiet Clicks.',
                'description': 'An icon remastered. Feel every moment of your workflow with even more precision, tactility, and performance, thanks to Quiet Clicks and an 8,000 DPI sensor.',
                'price': Decimal('99.00'),
                'discount_price': None,
                'stock': 50,
                'is_featured': False,
                'is_flash_sale': False,
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

        # Seed sample demo order
        customer = User.objects.get(username='customer_user')
        if not Order.objects.filter(user=customer).exists():
            first_product = Product.objects.first()
            order = Order.objects.create(
                user=customer,
                full_name='John Customer',
                email='customer@pythonecom.local',
                phone='+880 1819-001122',
                street_address='House 42, Road 11, Banani',
                city='Dhaka',
                postal_code='1213',
                country='Bangladesh',
                subtotal=first_product.effective_price,
                shipping_fee=Decimal('0.00'),
                total_amount=first_product.effective_price,
                payment_method='cod',
                payment_status='pending',
                status='processing',
            )
            OrderItem.objects.create(
                order=order,
                product=first_product,
                product_name=first_product.name,
                product_price=first_product.effective_price,
                quantity=1,
            )
