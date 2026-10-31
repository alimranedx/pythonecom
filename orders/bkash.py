import json
import logging
import requests
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class BKashService:
    """
    Service wrapper for bKash Tokenized Checkout API (v1.2.0-beta).
    Handles authentication token grant, payment creation, and execution.
    """

    @classmethod
    def get_config(cls):
        return {
            'app_key': getattr(settings, 'BKASH_APP_KEY', ''),
            'app_secret': getattr(settings, 'BKASH_APP_SECRET', ''),
            'username': getattr(settings, 'BKASH_USERNAME', ''),
            'password': getattr(settings, 'BKASH_PASSWORD', ''),
            'base_url': getattr(settings, 'BKASH_BASE_URL', 'https://tokenized.sandbox.bka.sh/v1.2.0-beta').rstrip('/'),
        }

    @staticmethod
    def _parse_response(response) -> dict:
        """
        Safely parses JSON responses from bKash API.
        Uses strict=False to tolerate unescaped control characters (e.g. raw newlines)
        that bKash Sandbox error messages frequently contain.
        """
        try:
            return json.loads(response.text, strict=False)
        except Exception:
            try:
                return response.json()
            except Exception:
                return {
                    'statusCode': str(response.status_code),
                    'statusMessage': (response.text or '').strip(),
                }

    @classmethod
    def get_headers(cls, id_token: str = None) -> dict:
        config = cls.get_config()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if id_token:
            headers['Authorization'] = id_token
            headers['X-APP-Key'] = config['app_key']
        return headers

    @classmethod
    def grant_token(cls) -> tuple[bool, str, str]:
        """
        Retrieves a fresh id_token from bKash.
        Returns: (success: bool, id_token: str, message: str)
        """
        config = cls.get_config()
        url = f"{config['base_url']}/tokenized/checkout/token/grant"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'username': config['username'],
            'password': config['password'],
        }
        payload = {
            'app_key': config['app_key'],
            'app_secret': config['app_secret'],
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            data = cls._parse_response(response)
            if response.status_code == 200 and data.get('statusCode') == '0000':
                return True, data.get('id_token'), "Token granted successfully."
            msg = (data.get('statusMessage') or 'Failed to retrieve bKash auth token.').strip()
            return False, '', msg
        except Exception as e:
            logger.error("bKash token grant error: %s", e)
            return False, '', str(e)

    @classmethod
    def create_payment(cls, order, callback_url: str) -> tuple[bool, dict]:
        """
        Creates a payment session with bKash and returns the redirect URL (bkashURL).
        Returns: (success: bool, response_dict)
        """
        success, id_token, msg = cls.grant_token()
        if not success:
            return False, {'message': msg}

        config = cls.get_config()
        url = f"{config['base_url']}/tokenized/checkout/create"
        headers = cls.get_headers(id_token=id_token)

        payload = {
            'mode': '0011',
            'payerReference': order.phone or order.order_number,
            'callbackURL': callback_url,
            'amount': str(Decimal(order.total_amount).quantize(Decimal('0.01'))),
            'currency': 'BDT',
            'intent': 'sale',
            'merchantInvoiceNumber': order.order_number,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            data = cls._parse_response(response)
            if response.status_code == 200 and data.get('statusCode') == '0000':
                return True, {
                    'payment_id': data.get('paymentID'),
                    'bkash_url': data.get('bkashURL'),
                    'id_token': id_token,
                    'data': data,
                }
            msg = (data.get('statusMessage') or 'bKash payment initiation failed.').strip()
            return False, {'message': msg}
        except Exception as e:
            logger.error("bKash create payment error: %s", e)
            return False, {'message': str(e)}

    @classmethod
    def execute_payment(cls, payment_id: str) -> tuple[bool, dict]:
        """
        Executes and completes the payment once the user finishes OTP and PIN verification.
        Returns: (success: bool, response_dict)
        """
        success, id_token, msg = cls.grant_token()
        if not success:
            return False, {'message': msg}

        config = cls.get_config()
        url = f"{config['base_url']}/tokenized/checkout/execute"
        headers = cls.get_headers(id_token=id_token)
        payload = {'paymentID': payment_id}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            data = cls._parse_response(response)
            if response.status_code == 200 and data.get('statusCode') == '0000':
                return True, {
                    'trx_id': data.get('trxID'),
                    'payment_id': data.get('paymentID'),
                    'amount': data.get('amount'),
                    'customer_msisdn': data.get('customerMsisdn'),
                    'data': data,
                }
            msg = (data.get('statusMessage') or 'bKash execution failed.').strip()
            return False, {
                'message': msg,
                'statusCode': data.get('statusCode'),
            }
        except Exception as e:
            logger.error("bKash execute payment error: %s", e)
            return False, {'message': str(e)}

    @classmethod
    def query_payment(cls, payment_id: str) -> tuple[bool, dict]:
        """
        Queries the current status of a payment.
        """
        success, id_token, msg = cls.grant_token()
        if not success:
            return False, {'message': msg}

        config = cls.get_config()
        url = f"{config['base_url']}/tokenized/checkout/payment/status"
        headers = cls.get_headers(id_token=id_token)
        payload = {'paymentID': payment_id}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            data = cls._parse_response(response)
            if response.status_code == 200 and data.get('statusCode') == '0000':
                return True, data
            msg = (data.get('statusMessage') or 'Payment query failed.').strip()
            return False, {'message': msg}
        except Exception as e:
            return False, {'message': str(e)}
