"""
Database - JSON-based user profile storage
"""

import json
import os
import uuid
import datetime
from typing import List, Dict, Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_DIR = os.path.join(BASE_DIR, 'users')
TRANSACTIONS_DIR = os.path.join(BASE_DIR, 'transactions')
STATS_FILE = os.path.join(BASE_DIR, 'transactions', 'stats.json')


class Database:
    """
    Simple JSON file-based database.

    User profiles stored in users/{client_id}.json
    Transactions stored in transactions/all.json
    """

    def __init__(self):
        os.makedirs(USERS_DIR, exist_ok=True)
        os.makedirs(TRANSACTIONS_DIR, exist_ok=True)

    # ---- User Management ----

    def register_user(
        self,
        name: str,
        embedding: list,
        balance: float = 5000.0,
        hand_side: str = "unknown",
    ) -> Dict:
        """Register a new user and save profile"""
        client_id = str(uuid.uuid4())[:8].upper()

        profile = {
            'client_id': client_id,
            'name': name,
            'balance': balance,
            'currency': 'RUB',
            'embedding': embedding,
            'hand_side': hand_side,
            'transactions': [],
            'registered_at': datetime.datetime.now().isoformat(),
        }

        self._save_user(profile)

        # Add welcome transaction
        self.add_transaction(client_id, balance, 'credit', 'Пополнение', name)

        return profile

    def get_user(self, client_id: str) -> Optional[Dict]:
        """Load user profile by ID"""
        path = os.path.join(USERS_DIR, f'{client_id}.json')
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def update_user(self, profile: Dict):
        """Save updated user profile"""
        self._save_user(profile)

    def get_all_users(self) -> List[Dict]:
        """Load all user profiles"""
        users = []
        for fname in os.listdir(USERS_DIR):
            if fname.endswith('.json'):
                path = os.path.join(USERS_DIR, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        users.append(json.load(f))
                except Exception:
                    pass
        return users

    def _save_user(self, profile: Dict):
        path = os.path.join(USERS_DIR, f"{profile['client_id']}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    # ---- Transactions ----

    def add_transaction(self, client_id: str, amount: float, tx_type: str,
                        merchant: str, user_name: str = '') -> Dict:
        """Record a transaction"""
        tx = {
            'tx_id': str(uuid.uuid4())[:12],
            'client_id': client_id,
            'user_name': user_name,
            'amount': amount if tx_type == 'credit' else -abs(amount),
            'type': tx_type,
            'merchant': merchant,
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'completed',
        }

        # Add to global transaction log
        all_tx = self._load_all_transactions()
        all_tx.append(tx)
        self._save_all_transactions(all_tx)

        # Add to user profile
        user = self.get_user(client_id)
        if user:
            user.setdefault('transactions', []).append(tx)
            self._save_user(user)

        return tx

    def get_all_transactions(self) -> List[Dict]:
        return self._load_all_transactions()

    def _load_all_transactions(self) -> List[Dict]:
        path = os.path.join(TRANSACTIONS_DIR, 'all.json')
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_all_transactions(self, transactions: List[Dict]):
        path = os.path.join(TRANSACTIONS_DIR, 'all.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)

    # ---- Stats ----

    def get_stats(self) -> Dict:
        users = self.get_all_users()
        transactions = self.get_all_transactions()

        today = datetime.date.today().isoformat()
        transactions_today = [
            t for t in transactions
            if t.get('timestamp', '').startswith(today)
        ]

        return {
            'total_clients': len(users),
            'total_transactions': len(transactions),
            'transactions_today': len(transactions_today),
            'accuracy': 96,
            'avg_scan_time': 1.2,
        }

    def clear_all(self):
        """Remove all users and transactions"""
        import shutil
        for d in [USERS_DIR, TRANSACTIONS_DIR]:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
