from decimal import Decimal
from datetime import time, timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth.models import User
from product.models import Product, Category
from cart.models import Cart, CartItem
from orders.models import Order, DeliverySlot, Coupon


class CouponAndDeliverySlotTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Groceries', slug='groceries')
        self.product = Product.objects.create(
            name='Basmati Rice',
            slug='basmati-rice',
            price=Decimal('100.00'),
            stock=50,
            unit='1 kg'
        )
        now = timezone.now()
        self.coupon_percent = Coupon.objects.create(
            code='SAVE10',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('200.00'),
            max_discount_amount=Decimal('50.00'),
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
            is_active=True
        )
        self.coupon_fixed = Coupon.objects.create(
            code='FLAT50',
            discount_type='fixed',
            discount_value=Decimal('50.00'),
            min_order_amount=Decimal('150.00'),
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=30),
            is_active=True
        )
        self.slot = DeliverySlot.objects.create(
            title='Morning Slot (08:00 AM - 11:00 AM)',
            start_time=time(8, 0),
            end_time=time(11, 0),
            is_express=False,
            extra_fee=Decimal('0.00'),
            order=1
        )
        self.express_slot = DeliverySlot.objects.create(
            title='⚡ Express 1-Hour',
            start_time=time(9, 0),
            end_time=time(20, 0),
            is_express=True,
            extra_fee=Decimal('30.00'),
            order=2
        )

    def test_coupon_validation_and_calculation(self):
        # 1. Under minimum spend threshold
        valid, msg = self.coupon_percent.is_valid(subtotal=Decimal('150.00'))
        self.assertFalse(valid)
        self.assertIn('Minimum order amount', msg)

        # 2. Valid percentage calculation
        valid, _ = self.coupon_percent.is_valid(subtotal=Decimal('300.00'))
        self.assertTrue(valid)
        # 10% of 300 = 30.00
        self.assertEqual(self.coupon_percent.calculate_discount(Decimal('300.00')), Decimal('30.00'))

        # 3. Max discount cap enforcement
        # 10% of 1000 = 100, but cap is 50.00
        self.assertEqual(self.coupon_percent.calculate_discount(Decimal('1000.00')), Decimal('50.00'))

        # 4. Inactive coupon check
        self.coupon_percent.is_active = False
        self.coupon_percent.save()
        valid, msg = self.coupon_percent.is_valid(subtotal=Decimal('300.00'))
        self.assertFalse(valid)

    def test_apply_and_remove_coupon_views(self):
        # Add 3 units of Basmati Rice (3 x 100 = 300)
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 3})

        # Apply valid coupon
        res = self.client.post('/cart/coupon/apply/', {'coupon_code': 'SAVE10'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['coupon_code'], 'SAVE10')
        self.assertEqual(data['discount_amount'], '30.00')

        # Apply non-existent coupon
        res_fake = self.client.post('/cart/coupon/apply/', {'coupon_code': 'FAKEXX'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_fake.status_code, 400)
        self.assertFalse(res_fake.json()['success'])

        # Remove coupon
        res_rem = self.client.post('/cart/coupon/remove/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res_rem.status_code, 200)
        self.assertEqual(res_rem.json()['coupon_code'], '')

    def test_checkout_with_delivery_slot_and_area(self):
        # Add 2 units of Basmati Rice (2 x 100 = 200)
        self.client.post(f'/cart/add/{self.product.pk}/', {'quantity': 2})

        today_str = timezone.localdate().strftime('%Y-%m-%d')
        post_data = {
            'full_name': 'Rahim Uddin',
            'email': 'rahim@example.com',
            'phone': '+8801711223344',
            'street_address': 'Road 10, House 5, Gulshan',
            'city': 'Dhaka',
            'postal_code': '1212',
            'country': 'Bangladesh',
            'delivery_area': 'Inside Dhaka',
            'delivery_date': today_str,
            'delivery_slot': str(self.slot.pk),
            'payment_method': 'cod',
        }
        res = self.client.post('/orders/checkout/', post_data)
        self.assertEqual(res.status_code, 302)

        order = Order.objects.filter(email='rahim@example.com').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.delivery_area, 'Inside Dhaka')
        self.assertEqual(order.delivery_slot, self.slot)
        # Inside Dhaka (< 500) = shipping 49.00
        self.assertEqual(order.shipping_fee, Decimal('49.00'))
        self.assertEqual(order.total_amount, Decimal('249.00'))

    def test_admin_delivery_slots_and_coupons_management(self):
        admin_user = User.objects.create_superuser('admin_mgr', 'mgr@test.com', 'Pass123')
        self.client.force_login(admin_user)

        # 1. View delivery slots list
        res_slots = self.client.get('/app-admin/orders/delivery-slots/')
        self.assertEqual(res_slots.status_code, 200)
        self.assertIn('Morning Slot', res_slots.content.decode('utf-8'))

        # 2. Toggle slot
        res_tog = self.client.get(f'/app-admin/orders/delivery-slots/{self.slot.pk}/toggle/')
        self.assertEqual(res_tog.status_code, 302)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)

        # 3. View coupons list
        res_coupons = self.client.get('/app-admin/orders/coupons/')
        self.assertEqual(res_coupons.status_code, 200)
        self.assertIn('SAVE10', res_coupons.content.decode('utf-8'))

        # 4. Create new coupon
        res_create = self.client.post('/app-admin/orders/coupons/create/', {
            'code': 'SPECIAL20',
            'discount_type': 'percent',
            'discount_value': '20',
            'min_order_amount': '250',
            'valid_days': '15',
        })
        self.assertEqual(res_create.status_code, 302)
        self.assertTrue(Coupon.objects.filter(code='SPECIAL20').exists())
