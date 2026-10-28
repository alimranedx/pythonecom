from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from product.models import Category, Product
from cart.models import Cart, CartItem
from cart.services import CartService


class CartFlowTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.p1 = Product.objects.create(
            name="MacBook Pro 16",
            slug="macbook-pro-16",
            category=self.category,
            price=Decimal("2000.00"),
            stock=10,
            is_active=True,
        )
        self.p2 = Product.objects.create(
            name="Apple Watch Ultra",
            slug="apple-watch-ultra",
            category=self.category,
            price=Decimal("800.00"),
            stock=5,
            is_active=True,
        )
        self.p_out_of_stock = Product.objects.create(
            name="Discontinued Item",
            slug="discontinued-item",
            category=self.category,
            price=Decimal("100.00"),
            stock=0,
            is_active=True,
        )
        self.staff_user = User.objects.create_user(
            username='staffadmin',
            password='password123',
            is_staff=True
        )
        self.customer_user = User.objects.create_user(
            username='customer_jane',
            password='password123',
            is_staff=False
        )

    def test_add_single_item(self):
        """Adding a new product once sets quantity=1 and total_items=1."""
        response = self.client.post(
            f'/cart/add/{self.p1.pk}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 1)
        self.assertIn("Added 'MacBook Pro 16' to cart!", data['message'])

    def test_add_duplicate_item_increments_quantity(self):
        """Adding the same product again increments its quantity rather than creating a duplicate row."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 2)
        self.assertIn("Increased 'MacBook Pro 16' quantity to 2 in cart.", data['message'])

    def test_add_two_different_products(self):
        """Adding two distinct products results in total_items=2 and unique_items=2."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response2 = self.client.post(f'/cart/add/{self.p2.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response2.status_code, 200)
        data = response2.json()
        self.assertEqual(data['total_items'], 2)
        self.assertEqual(data['subtotal'], '2800.00')

    def test_scenario_duplicate_plus_second_item(self):
        """
        Tests the exact user scenario:
        1x MacBook added first, 1x MacBook added again (qty=2), 1x Apple Watch added (qty=1).
        Result: 2 product rows, but total_items = 3.
        """
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        res = self.client.post(f'/cart/add/{self.p2.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = res.json()
        self.assertEqual(data['total_items'], 3)
        self.assertEqual(data['subtotal'], '4800.00')

    def test_update_quantity_via_ajax(self):
        """Decrementing quantity via AJAX updates total_items and subtotal."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post(
            f'/cart/update/{self.p1.pk}/',
            {'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 1)
        self.assertEqual(data['subtotal'], '2000.00')

    def test_update_quantity_to_zero_removes_item(self):
        """Setting quantity to 0 removes the item and updates totals."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post(
            f'/cart/update/{self.p1.pk}/',
            {'quantity': 0},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 0)
        self.assertEqual(data['subtotal'], '0')

    def test_remove_item_via_ajax(self):
        """Removing item via AJAX returns success and resets count."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post(f'/cart/remove/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 0)

    def test_out_of_stock_rejected(self):
        """Adding a product with stock=0 returns HTTP 400 with an error message."""
        response = self.client.post(
            f'/cart/add/{self.p_out_of_stock.pk}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("out of stock", data['message'])

    def test_exceeding_stock_rejected(self):
        """Requesting more units than in stock returns HTTP 400."""
        response = self.client.post(
            f'/cart/add/{self.p2.pk}/',
            {'quantity': 99},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("available in stock", data['message'])

    def test_cart_drawer_endpoint(self):
        """GET /cart/drawer/ renders the cart drawer partial with items and quantities."""
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.get('/cart/drawer/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("MacBook Pro 16", content)
        self.assertIn("drawer-qty-btn", content)

    def test_merge_guest_cart_on_login(self):
        """When an anonymous guest with cart items logs in, items merge correctly into user's cart."""
        user = User.objects.create_user(username='customer1', password='password123')
        self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post('/account/login/', {'username': 'customer1', 'password': 'password123'})
        res = self.client.post(f'/cart/add/{self.p2.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        user_cart = Cart.objects.get(user=user)
        self.assertEqual(user_cart.items.count(), 2)
        self.assertEqual(user_cart.total_items, 2)

    def test_staff_session_cleared_on_storefront_visit(self):
        """If an admin/staff user visits the root storefront, the staff session is cleared so the storefront is free."""
        self.client.force_login(self.staff_user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Verify user is now an AnonymousUser
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Content shows guest Account, not admin
        content = response.content.decode('utf-8')
        self.assertNotIn("Admin Panel", content)
        self.assertNotIn("staffadmin", content)
        self.assertIn("Account", content)
        self.assertIn("Sign In", content)

    def test_staff_can_add_to_cart_silently_after_storefront_frees_session(self):
        """When an admin user visits the storefront and clicks Add to Cart, it works silently as a guest shopper."""
        self.client.force_login(self.staff_user)
        # Visiting storefront or adding to cart clears staff session and adds as guest
        response = self.client.post(f'/cart/add/{self.p1.pk}/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_items'], 1)
        self.assertIn("Added 'MacBook Pro 16' to cart!", data['message'])

    def test_customer_session_cleared_on_admin_panel_visit(self):
        """If a customer visits any admin route (/app-admin/*), customer session is cleared so admin is isolated."""
        self.client.force_login(self.customer_user)
        response = self.client.get('/app-admin/')
        # Should redirect to admin login
        self.assertEqual(response.status_code, 302)
        # Verify user was logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)
