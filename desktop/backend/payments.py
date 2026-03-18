"""
Payment Processor
"""

import datetime
from typing import Dict, Optional
from backend.database import Database


class PaymentProcessor:
    """Handles payment processing logic"""

    def __init__(self, db: Database = None):
        self._db = db or Database()

    def process_payment(self, client_id: str, amount: float, merchant: str) -> float:
        """
        Process a payment for a user.
        Deducts amount from balance and records transaction.
        Returns new balance.
        """
        user = self._db.get_user(client_id)
        if not user:
            raise ValueError(f"User {client_id} not found")

        current_balance = float(user.get('balance', 0))
        if current_balance < amount:
            raise ValueError("Insufficient funds")

        new_balance = current_balance - amount
        user['balance'] = new_balance
        self._db.update_user(user)

        self._db.add_transaction(
            client_id,
            amount,
            'debit',
            merchant,
            user.get('name', '')
        )

        return new_balance

    def add_funds(self, client_id: str, amount: float, source: str = 'Пополнение') -> float:
        """Add funds to user account. Returns new balance."""
        user = self._db.get_user(client_id)
        if not user:
            raise ValueError(f"User {client_id} not found")

        new_balance = float(user.get('balance', 0)) + amount
        user['balance'] = new_balance
        self._db.update_user(user)

        self._db.add_transaction(
            client_id,
            amount,
            'credit',
            source,
            user.get('name', '')
        )

        return new_balance

    def get_balance(self, client_id: str) -> Optional[float]:
        """Get current balance for user"""
        user = self._db.get_user(client_id)
        return float(user['balance']) if user else None
