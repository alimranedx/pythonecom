from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentStrategy(ABC):
    """
    Abstract Strategy interface for all payment providers.
    """

    @abstractmethod
    def process_payment(self, order, payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes payment processing and returns a transaction result dictionary.
        """
        pass


class CashOnDeliveryStrategy(PaymentStrategy):
    """
    Handles Cash on Delivery (COD) payment flow.
    """

    def process_payment(self, order, payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        order.payment_status = 'pending'
        order.save(update_fields=['payment_status'])
        return {
            'success': True,
            'message': 'Order placed successfully with Cash on Delivery.',
            'transaction_id': f"COD-{order.order_number}",
        }


class CardPaymentStrategy(PaymentStrategy):
    """
    Handles Credit / Debit Card payments (Mock Gateway / Stripe ready).
    """

    def process_payment(self, order, payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        # Simulated payment verification
        order.payment_status = 'paid'
        order.status = 'processing'
        order.save(update_fields=['payment_status', 'status'])
        return {
            'success': True,
            'message': 'Card payment authorized and processed successfully.',
            'transaction_id': f"TXN-CARD-{order.order_number}",
        }


class MobileBankingStrategy(PaymentStrategy):
    """
    Handles Mobile Financial Services (bKash, Nagad, Rocket).
    """

    def process_payment(self, order, payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        order.payment_status = 'pending'
        order.save(update_fields=['payment_status'])
        return {
            'success': True,
            'message': 'Mobile banking payment pending customer verification.',
            'transaction_id': f"MFS-{order.order_number}",
        }


class PaymentStrategyFactory:
    """
    Factory creating concrete payment strategies based on method key.
    """
    _STRATEGIES = {
        'cod': CashOnDeliveryStrategy,
        'card': CardPaymentStrategy,
        'mobile_banking': MobileBankingStrategy,
    }

    @classmethod
    def get_strategy(cls, payment_method: str) -> PaymentStrategy:
        strategy_class = cls._STRATEGIES.get(payment_method)
        if not strategy_class:
            raise ValueError(f"Unsupported payment method: '{payment_method}'")
        return strategy_class()
