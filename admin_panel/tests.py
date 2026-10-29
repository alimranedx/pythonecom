from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rbac.models import Module, Submodule, Permission
from product.models import Category, Brand, Product, ProductReview
from orders.models import Order, OrderItem
from accounts.models import CustomerProfile, Address


class AdminPanelSessionAndRBACNavigationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='test_superadmin',
            email='super@test.com',
            password='AdminPassword123'
        )
        self.module = Module.objects.create(name='Catalog', code='catalog', icon='bi-boxes', order=1)
        self.submodule = Submodule.objects.create(
            module=self.module,
            name='Products',
            code='catalog.products',
            url_name='admin_product_list',
            order=1
        )
        self.perm = Permission.objects.create(
            submodule=self.submodule,
            action='view',
            code='catalog.products.view',
            name='View Products'
        )

    def test_unauthenticated_admin_dashboard_redirects_to_admin_login(self):
        response = self.client.get('/app-admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/app-admin/login/', response.url)

    def test_superadmin_session_preserved_on_dashboard_and_reload(self):
        self.client.force_login(self.superuser)

        # Initial request
        res1 = self.client.get('/app-admin/')
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.wsgi_request.user.is_authenticated)
        content1 = res1.content.decode('utf-8')
        self.assertIn('Super Admin', content1)
        self.assertNotIn('No modules permitted. Contact your Super Administrator.', content1)
        self.assertIn('Catalog', content1)

        # Reloading dashboard
        res2 = self.client.get('/app-admin/')
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.wsgi_request.user.is_authenticated)
        content2 = res2.content.decode('utf-8')
        self.assertIn('Super Admin', content2)
        self.assertNotIn('No modules permitted. Contact your Super Administrator.', content2)

    def test_favicon_request_does_not_clear_admin_session(self):
        self.client.force_login(self.superuser)

        # Browser requests favicon
        self.client.get('/favicon.ico')

        # Dashboard remains logged in
        res = self.client.get('/app-admin/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.wsgi_request.user.is_authenticated)
        content = res.content.decode('utf-8')
        self.assertIn('Super Admin', content)
        self.assertNotIn('No modules permitted. Contact your Super Administrator.', content)


class AdminPanelCatalogAndBrandTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_catalog',
            email='catalog@test.com',
            password='Password123'
        )
        self.client.force_login(self.superuser)
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.brand = Brand.objects.create(name='Apple', slug='apple')
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            category=self.category,
            brand=self.brand,
            price=Decimal('999.00'),
            stock=10,
            is_active=True
        )

    def test_brand_crud(self):
        # List
        res = self.client.get('/app-admin/brands/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Apple', res.content.decode('utf-8'))

        # Create
        res_create = self.client.post('/app-admin/brands/create/', {
            'name': 'Samsung',
            'slug': 'samsung'
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Brand.objects.filter(slug='samsung').exists())

        # Edit
        samsung = Brand.objects.get(slug='samsung')
        res_edit = self.client.post(f'/app-admin/brands/{samsung.pk}/edit/', {
            'name': 'Samsung Electronics',
            'slug': 'samsung-electronics'
        })
        self.assertEqual(res_edit.status_code, 302)
        samsung.refresh_from_db()
        self.assertEqual(samsung.name, 'Samsung Electronics')

        # Delete
        res_delete = self.client.post(f'/app-admin/brands/{samsung.pk}/delete/')
        self.assertEqual(res_delete.status_code, 302)
        self.assertFalse(Brand.objects.filter(pk=samsung.pk).exists())

    def test_product_list_filters_and_pagination(self):
        # Search filter
        res_search = self.client.get('/app-admin/products/?q=iPhone')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn('iPhone 15', res_search.content.decode('utf-8'))

        # Category filter
        res_cat = self.client.get(f'/app-admin/products/?category={self.category.pk}')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn('iPhone 15', res_cat.content.decode('utf-8'))

        # Stock filter
        res_stock = self.client.get('/app-admin/products/?stock=in_stock')
        self.assertEqual(res_stock.status_code, 200)
        self.assertIn('iPhone 15', res_stock.content.decode('utf-8'))

    def test_review_moderation(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.superuser,
            rating=5,
            comment='Superb build quality!'
        )
        # List reviews
        res = self.client.get('/app-admin/reviews/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Superb build quality!', res.content.decode('utf-8'))

        # Filter by rating
        res_rating = self.client.get('/app-admin/reviews/?rating=5')
        self.assertEqual(res_rating.status_code, 200)
        self.assertIn('Superb build quality!', res_rating.content.decode('utf-8'))

        # Delete review
        res_del = self.client.post(f'/app-admin/reviews/{review.pk}/delete/')
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())


class AdminPanelOrderManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_orders',
            email='orders@test.com',
            password='Password123'
        )
        self.client.force_login(self.superuser)
        self.product = Product.objects.create(
            name='Sony Headphones',
            slug='sony-headphones',
            price=Decimal('200.00'),
            stock=15,
            is_active=True
        )
        self.order = Order.objects.create(
            full_name='Test Customer',
            email='test@example.com',
            phone='+8801700000000',
            street_address='123 Test Street',
            city='Dhaka',
            postal_code='1200',
            subtotal=Decimal('400.00'),
            shipping_fee=Decimal('0.00'),
            total_amount=Decimal('400.00'),
            status='pending',
            payment_status='pending'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            product_price=self.product.price,
            quantity=2
        )

    def test_order_list_search_and_filter(self):
        res = self.client.get(f'/app-admin/orders/?q={self.order.order_number}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(self.order.order_number, res.content.decode('utf-8'))

        res_status = self.client.get('/app-admin/orders/?status=pending')
        self.assertEqual(res_status.status_code, 200)
        self.assertIn(self.order.order_number, res_status.content.decode('utf-8'))

    def test_order_cancellation_restores_inventory(self):
        initial_stock = self.product.stock
        # Cancel order
        res = self.client.post(f'/app-admin/orders/{self.order.pk}/', {
            'status': 'cancelled',
            'payment_status': 'refunded'
        })
        self.assertEqual(res.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock + self.item.quantity)

        # Reopen order
        res2 = self.client.post(f'/app-admin/orders/{self.order.pk}/', {
            'status': 'processing',
            'payment_status': 'paid'
        })
        self.assertEqual(res2.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock)

    def test_order_invoice_view(self):
        res = self.client.get(f'/app-admin/orders/{self.order.pk}/invoice/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('INVOICE', content)
        self.assertIn(self.order.order_number, content)
        self.assertIn('Sony Headphones', content)
        self.assertIn('$400.00', content)

    def test_order_filters_multi_criteria_and_date_range(self):
        # Create second order with different status, payment method, customer
        order2 = Order.objects.create(
            full_name='Alice Smith',
            email='alice@example.com',
            phone='+1234567890',
            street_address='456 Elm St',
            city='New York',
            postal_code='10001',
            subtotal=Decimal('150.00'),
            shipping_fee=Decimal('10.00'),
            total_amount=Decimal('160.00'),
            status='delivered',
            payment_status='paid',
            payment_method='cod'
        )

        # 1. Filter by order_id
        res_oid = self.client.get(f'/app-admin/orders/?order_id={self.order.order_number}')
        self.assertEqual(res_oid.status_code, 200)
        self.assertIn(self.order.order_number, res_oid.content.decode('utf-8'))
        self.assertNotIn(order2.order_number, res_oid.content.decode('utf-8'))

        # 2. Filter by customer
        res_cust = self.client.get('/app-admin/orders/?customer=Alice')
        self.assertEqual(res_cust.status_code, 200)
        self.assertIn(order2.order_number, res_cust.content.decode('utf-8'))
        self.assertNotIn(self.order.order_number, res_cust.content.decode('utf-8'))

        # 3. Filter by payment_status
        res_paid = self.client.get('/app-admin/orders/?payment_status=paid')
        self.assertEqual(res_paid.status_code, 200)
        self.assertIn(order2.order_number, res_paid.content.decode('utf-8'))
        self.assertNotIn(self.order.order_number, res_paid.content.decode('utf-8'))

        # 4. Filter by amount range
        res_amt = self.client.get('/app-admin/orders/?min_amount=200&max_amount=500')
        self.assertEqual(res_amt.status_code, 200)
        self.assertIn(self.order.order_number, res_amt.content.decode('utf-8'))
        self.assertNotIn(order2.order_number, res_amt.content.decode('utf-8'))

        # 5. Filter by combined date_range string
        today_str = self.order.created_at.strftime('%Y/%m/%d')
        res_dr = self.client.get(f'/app-admin/orders/?date_range={today_str}+00:00:00+-+{today_str}+23:59:59')
        self.assertEqual(res_dr.status_code, 200)
        self.assertIn(self.order.order_number, res_dr.content.decode('utf-8'))
        self.assertIn(order2.order_number, res_dr.content.decode('utf-8'))

    def test_order_export_csv(self):
        res = self.client.get('/app-admin/orders/?export=csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename=', res['Content-Disposition'])
        csv_content = res.content.decode('utf-8')
        self.assertIn('Order Number', csv_content)
        self.assertIn(self.order.order_number, csv_content)
        self.assertIn('Test Customer', csv_content)

    def test_order_list_pagination_and_per_page_limits(self):
        # Create 14 additional orders for pagination testing (total 15 orders)
        for i in range(14):
            Order.objects.create(
                full_name=f'Pagination User {i}',
                email=f'user{i}@pagination.com',
                phone='+8801700000000',
                street_address='Street',
                city='City',
                postal_code='1000',
                subtotal=Decimal('100.00'),
                shipping_fee=Decimal('0.00'),
                total_amount=Decimal('100.00'),
                status='pending',
                payment_status='pending',
                payment_method='cod'
            )

        # 1. Custom per_page = 5 (should produce 3 pages: 15 / 5 = 3)
        res_p5 = self.client.get('/app-admin/orders/?per_page=5')
        self.assertEqual(res_p5.status_code, 200)
        self.assertEqual(len(res_p5.context['orders']), 5)
        self.assertEqual(res_p5.context['page_obj'].paginator.num_pages, 3)
        p5_html = res_p5.content.decode('utf-8')
        self.assertIn('Showing <strong>1</strong> to <strong>5</strong> of <strong>15</strong>', p5_html)
        self.assertIn('value="5" selected', p5_html)
        self.assertIn('page=2', p5_html)

        # 2. Navigate to Page 2 with per_page = 5 and a filter
        res_page2 = self.client.get('/app-admin/orders/?page=2&per_page=5&status=pending')
        self.assertEqual(res_page2.status_code, 200)
        self.assertEqual(res_page2.context['page_obj'].number, 2)
        p2_html = res_page2.content.decode('utf-8')
        self.assertIn('Page <strong>2</strong> of <strong>3</strong>', p2_html)
        # Verify previous page and next page links retain status=pending and per_page=5
        self.assertIn('page=1', p2_html)
        self.assertIn('page=3', p2_html)
        self.assertIn('status=pending', p2_html)
        self.assertIn('per_page=5', p2_html)

        # 3. Default per_page = 10 (should produce 2 pages: 15 / 10 = 2)
        res_default = self.client.get('/app-admin/orders/')
        self.assertEqual(res_default.status_code, 200)
        self.assertEqual(len(res_default.context['orders']), 10)
        self.assertEqual(res_default.context['page_obj'].paginator.num_pages, 2)


class AdminPanelCustomer360Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_customer',
            email='custadmin@test.com',
            password='Password123'
        )
        self.client.force_login(self.superuser)

        self.customer = User.objects.create_user(
            username='alice_customer',
            email='alice@test.com',
            first_name='Alice',
            last_name='Wonder',
            password='UserPass123'
        )
        CustomerProfile.objects.create(user=self.customer, phone='+8801811223344')
        Address.objects.create(
            user=self.customer,
            full_name='Alice Wonder',
            phone='+8801811223344',
            street_address='Road 5, House 12',
            city='Dhaka',
            postal_code='1212',
            is_default=True
        )
        self.order = Order.objects.create(
            user=self.customer,
            full_name='Alice Wonder',
            email='alice@test.com',
            phone='+8801811223344',
            street_address='Road 5, House 12',
            city='Dhaka',
            postal_code='1212',
            subtotal=Decimal('150.00'),
            shipping_fee=Decimal('0.00'),
            total_amount=Decimal('150.00'),
            status='delivered',
            payment_status='paid'
        )

    def test_customer_list_search_and_lifetime_spend(self):
        res = self.client.get('/app-admin/customers/?q=alice')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Alice Wonder', content)
        self.assertIn('$150.00', content)

    def test_customer_detail_360_view(self):
        res = self.client.get(f'/app-admin/customers/{self.customer.pk}/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Alice Wonder', content)
        self.assertIn('+8801811223344', content)
        self.assertIn('$150.00', content)
        self.assertIn('Road 5, House 12', content)

    def test_customer_toggle_status(self):
        self.assertTrue(self.customer.is_active)
        res = self.client.post(f'/app-admin/customers/{self.customer.pk}/toggle-status/')
        self.assertEqual(res.status_code, 302)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)

        # Reactivate
        res2 = self.client.post(f'/app-admin/customers/{self.customer.pk}/toggle-status/')
        self.assertEqual(res2.status_code, 302)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_active)


class AdminPanelDashboardAnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin_analytics',
            email='analytics@test.com',
            password='Password123'
        )
        self.client.force_login(self.superuser)

        Order.objects.create(
            full_name='Paid Order',
            email='paid@test.com',
            total_amount=Decimal('500.00'),
            status='processing',
            payment_status='paid'
        )

    def test_dashboard_kpis_and_aov(self):
        res = self.client.get('/app-admin/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('$500.00', content)
        self.assertIn('Avg Order Value (AOV)', content)
        self.assertIn('Processing', content)
