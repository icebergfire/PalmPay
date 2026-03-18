"""
History Screen - Transaction history
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QLineEdit)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
import json
import os


class TransactionRow(QFrame):
    def __init__(self, transaction, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }
            QFrame:hover {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(59,158,255,0.15);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Type icon
        amount = transaction.get('amount', 0)
        t_type = transaction.get('type', 'debit')
        is_credit = t_type == 'credit' or amount > 0

        icon_map = {
            'Кофейня': '☕',
            'Продуктовый магазин': '🛒',
            'Транспорт': '🚇',
            'Ресторан': '🍕',
            'Аптека': '💊',
            'Пополнение': '💳',
            'Магазин': '🏪',
        }
        merchant = transaction.get('merchant', transaction.get('description', 'Операция'))
        icon = icon_map.get(merchant, '💰' if is_credit else '💸')

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background: rgba({'19,160,90' if is_credit else '59,158,255'}, 0.12);
                border-radius: 20px;
                font-size: 18px;
            }}
        """)
        layout.addWidget(icon_lbl)

        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(3)

        merchant_lbl = QLabel(merchant)
        merchant_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600;")
        details_layout.addWidget(merchant_lbl)

        # Date/time
        timestamp = transaction.get('timestamp', '')
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M  %d.%m.%Y")
            except Exception:
                time_str = timestamp[:16]
        else:
            time_str = "—"

        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("color: #3A4858; font-size: 11px;")
        details_layout.addWidget(time_lbl)

        layout.addLayout(details_layout)
        layout.addStretch()

        # User info
        user_name = transaction.get('user_name', '')
        if user_name:
            user_lbl = QLabel(user_name)
            user_lbl.setStyleSheet("color: #4A5568; font-size: 12px;")
            user_lbl.setFixedWidth(120)
            layout.addWidget(user_lbl)

        # Amount
        abs_amount = abs(float(amount))
        sign = "+" if is_credit else "−"
        color = "#13A05A" if is_credit else "#E8EDF5"

        amount_lbl = QLabel(f"{sign}{abs_amount:,.0f} ₽")
        amount_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700;")
        amount_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amount_lbl.setFixedWidth(100)
        layout.addWidget(amount_lbl)


class HistoryScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top_bar = self._build_top_bar()
        layout.addWidget(top_bar)

        # Content
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)

        # Left stats panel
        self.stats_panel = self._build_stats_panel()
        content.addWidget(self.stats_panel, 1)

        # Right transactions list
        right = self._build_transactions_panel()
        content.addWidget(right, 2)

        layout.addLayout(content)

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)

        back_btn = QPushButton("← Назад")
        back_btn.setFixedSize(100, 34)
        back_btn.clicked.connect(self.main_window.show_home)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; color: #6B7A8F; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #E8EDF5; }
        """)
        layout.addWidget(back_btn)

        title = QLabel("История операций")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 600;")
        layout.addWidget(title, 0, Qt.AlignCenter)
        layout.addStretch()

        return bar

    def _build_stats_panel(self):
        panel = QFrame()
        panel.setFixedWidth(300)
        panel.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border-right: 1px solid rgba(255,255,255,0.06);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(16)

        title = QLabel("Сводка")
        title.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700;")
        layout.addWidget(title)
        layout.addSpacing(10)

        self.stat_cards = {}
        stat_defs = [
            ('total_operations', '📊', 'Всего операций', '#3B9EFF'),
            ('total_debit', '📤', 'Расходы сегодня', '#E05050'),
            ('total_credit', '📥', 'Пополнения', '#13A05A'),
            ('avg_check', '💡', 'Средний чек', '#F0C040'),
        ]

        for key, icon, label, color in stat_defs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.07);
                    border-radius: 12px;
                }}
            """)
            card.setFixedHeight(72)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 0, 16, 0)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"""
                font-size: 18px;
                background: rgba(255,255,255,0.04);
                border-radius: 20px;
                padding: 6px;
            """)
            icon_lbl.setFixedSize(38, 38)
            icon_lbl.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(icon_lbl)
            card_layout.addSpacing(12)

            info = QVBoxLayout()
            info.setSpacing(2)

            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700;")
            info.addWidget(val_lbl)

            lbl = QLabel(label)
            lbl.setStyleSheet("color: #3A4858; font-size: 10px;")
            info.addWidget(lbl)

            card_layout.addLayout(info)
            layout.addWidget(card)

            self.stat_cards[key] = val_lbl

        layout.addStretch()

        # Filter options
        filter_title = QLabel("ФИЛЬТР")
        filter_title.setStyleSheet("color: #2A3545; font-size: 10px; letter-spacing: 2px;")
        layout.addWidget(filter_title)
        layout.addSpacing(8)

        for label, handler in [("Все операции", None), ("Только расходы", None), ("Только пополнения", None)]:
            btn = QPushButton(label)
            btn.setFixedHeight(36)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px; color: #6B7A8F; font-size: 12px; text-align: left; padding: 0 14px;
                }
                QPushButton:hover { background: rgba(59,158,255,0.08); color: #3B9EFF; border-color: rgba(59,158,255,0.2); }
            """)
            layout.addWidget(btn)

        return panel

    def _build_transactions_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        header_lbl = QLabel("Все транзакции")
        header_lbl.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: 700;")
        header.addWidget(header_lbl)
        header.addStretch()

        refresh_btn = QPushButton("↻ Обновить")
        refresh_btn.setFixedSize(110, 34)
        refresh_btn.clicked.connect(self._load_transactions)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59,158,255,0.1); border: 1px solid rgba(59,158,255,0.2);
                border-radius: 8px; color: #3B9EFF; font-size: 12px;
            }
            QPushButton:hover { background: rgba(59,158,255,0.2); }
        """)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Column headers
        col_header = QHBoxLayout()
        for text, width in [("Операция", 200), ("Клиент", 120), ("Сумма", 100)]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #2A3545; font-size: 11px; letter-spacing: 1px;")
            col_header.addWidget(lbl)
        col_header.addStretch()
        layout.addLayout(col_header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.tx_container = QWidget()
        self.tx_container.setStyleSheet("background: transparent;")
        self.tx_layout = QVBoxLayout(self.tx_container)
        self.tx_layout.setContentsMargins(0, 0, 0, 0)
        self.tx_layout.setSpacing(8)
        self.tx_layout.addStretch()

        scroll.setWidget(self.tx_container)
        layout.addWidget(scroll)

        return panel

    def _load_transactions(self):
        from backend.database import Database
        db = Database()
        transactions = db.get_all_transactions()

        # Clear old rows
        while self.tx_layout.count() > 1:
            item = self.tx_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Sort by timestamp (newest first)
        transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        total_debit = 0
        total_credit = 0
        for tx in transactions:
            row = TransactionRow(tx)
            self.tx_layout.insertWidget(self.tx_layout.count() - 1, row)
            amount = float(tx.get('amount', 0))
            if tx.get('type') == 'credit' or amount > 0:
                total_credit += abs(amount)
            else:
                total_debit += abs(amount)

        # Update stats
        n = len(transactions)
        self.stat_cards['total_operations'].setText(str(n))
        self.stat_cards['total_debit'].setText(f"{total_debit:,.0f} ₽")
        self.stat_cards['total_credit'].setText(f"{total_credit:,.0f} ₽")
        avg = total_debit / max(1, n)
        self.stat_cards['avg_check'].setText(f"{avg:,.0f} ₽")

        if n == 0:
            empty_lbl = QLabel("Нет транзакций")
            empty_lbl.setStyleSheet("color: #2A3545; font-size: 14px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.tx_layout.insertWidget(0, empty_lbl)

    def on_enter(self):
        self._load_transactions()
