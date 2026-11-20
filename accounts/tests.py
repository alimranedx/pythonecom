from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import CustomerProfile


class AuthenticationAuditTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='01711111111',
            password='Password123!',
            first_name='Test',
            last_name='User',
            email='test@example.com',
            is_active=True,
            is_staff=False,
        )
        CustomerProfile.objects.create(user=self.user, phone='01711111111')

        self.inactive_user = User.objects.create_user(
            username='01722222222',
            password='Password123!',
            first_name='Inactive',
            last_name='User',
            email='inactive@example.com',
            is_active=False,
            is_staff=False,
        )
        CustomerProfile.objects.create(user=self.inactive_user, phone='01722222222')

        self.staff_user = User.objects.create_user(
            username='staff_member',
            password='Password123!',
            first_name='Staff',
            last_name='Admin',
            email='staff@example.com',
            is_active=True,
            is_staff=True,
        )

    def test_login_failure_logs_warning_footprint(self):
        with self.assertLogs('django.security.Auth', level='WARNING') as cm:
            response = self.client.post(
                '/account/login/',
                {'username': '01711111111', 'password': 'WrongPassword'},
                REMOTE_ADDR='203.0.113.195',
                HTTP_USER_AGENT='SecurityTester/1.0',
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any(
                'Authentication failed: target=\'01711111111\'' in msg and
                'client_ip=\'203.0.113.195\'' in msg and
                'SecurityTester/1.0' in msg
                for msg in cm.output
            ))

    def test_login_inactive_user_logs_warning_footprint(self):
        with self.assertLogs('django.security.Auth', level='WARNING') as cm:
            response = self.client.post(
                '/account/login/',
                {'username': '01722222222', 'password': 'Password123!'},
                REMOTE_ADDR='198.51.100.42',
                HTTP_USER_AGENT='InactiveBot/2.0',
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any(
                'Authentication failed: target=\'01722222222\'' in msg and
                'client_ip=\'198.51.100.42\'' in msg
                for msg in cm.output
            ))

    def test_login_staff_storefront_panel_isolation_warning(self):
        with self.assertLogs('django.security.Auth', level='WARNING') as cm:
            response = self.client.post(
                '/account/login/',
                {'username': 'staff_member', 'password': 'Password123!'},
                REMOTE_ADDR='198.51.100.77',
            )
            self.assertRedirects(response, '/app-admin/login/')
            self.assertTrue(any(
                'staff panel isolation attempt' in msg and
                'target=\'staff_member\'' in msg
                for msg in cm.output
            ))

    def test_registration_logs_audit_footprint(self):
        with self.assertLogs('django.security.Auth', level='INFO') as cm:
            response = self.client.post(
                '/account/register/',
                {
                    'first_name': 'New',
                    'last_name': 'Customer',
                    'phone': '01733333333',
                    'email': 'newcustomer@example.com',
                    'password': 'StrongPassword123!',
                    'confirm_password': 'StrongPassword123!',
                },
                REMOTE_ADDR='192.0.2.88',
                HTTP_USER_AGENT='LegitBrowser/1.0',
            )
            self.assertEqual(response.status_code, 302)
            self.assertTrue(any(
                'Customer registration footprint' in msg and
                '01733333333' in msg and
                'client_ip=\'192.0.2.88\'' in msg
                for msg in cm.output
            ))

    def test_registration_failure_logs_warning_footprint(self):
        with self.assertLogs('django.security.Auth', level='WARNING') as cm:
            response = self.client.post(
                '/account/register/',
                {
                    'first_name': 'Bot',
                    'phone': 'invalid_phone',
                    'password': 'short',
                    'confirm_password': 'mismatch',
                },
                REMOTE_ADDR='192.0.2.99',
                HTTP_USER_AGENT='MaliciousBot/1.0',
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any(
                'Customer registration attempt failed' in msg and
                'client_ip=\'192.0.2.99\'' in msg
                for msg in cm.output
            ))
