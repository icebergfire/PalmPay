"""
Balance Screen - Check account balance via palm scan
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame)
from PyQt5.QtCore import Qt


class BalanceScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._user = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top bar
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(24, 0, 24, 0)

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
        bar_layout.addWidget(back_btn)

        title = QLabel("Баланс")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 600;")
        bar_layout.addWidget(title, 0, Qt.AlignCenter)
        bar_layout.addStretch()
        layout.addWidget(bar)

        # Content
        content = QVBoxLayout()
        content.setContentsMargins(60, 60, 60, 60)
        content.setAlignment(Qt.AlignCenter)

        # Scan button (shown when no user)
        self.scan_section = QFrame()
        scan_layout = QVBoxLayout(self.scan_section)
        scan_layout.setAlignment(Qt.AlignCenter)

        scan_title = QLabel("Проверка баланса")
        scan_title.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 700;")
        scan_title.setAlignment(Qt.AlignCenter)
        scan_layout.addWidget(scan_title)
        scan_layout.addSpacing(12)

        scan_sub = QLabel("Отсканируйте ладонь для просмотра баланса счёта")
        scan_sub.setStyleSheet("color: #4A5568; font-size: 14px;")
        scan_sub.setAlignment(Qt.AlignCenter)
        scan_layout.addWidget(scan_sub)
        scan_layout.addSpacing(40)

        scan_btn = QPushButton("🤚  Сканировать ладонь")
        scan_btn.setFixedSize(260, 54)
        scan_btn.clicked.connect(self._start_scan)
        scan_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F4C8A, stop:1 #1A6DC4);
                color: #FFFFFF; border: none; border-radius: 12px;
                font-size: 16px; font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1A6DC4, stop:1 #2485E8);
            }
        """)
        scan_layout.addWidget(scan_btn, 0, Qt.AlignCenter)
        content.addWidget(self.scan_section)

        # Balance display (hidden until user scanned)
        self.balance_section = QFrame()
        bal_layout = QVBoxLayout(self.balance_section)
        bal_layout.setAlignment(Qt.AlignCenter)
        bal_layout.setSpacing(0)

        self.user_lbl = QLabel("")
        self.user_lbl.setStyleSheet("color: #8A9BB0; font-size: 16px;")
        self.user_lbl.setAlignment(Qt.AlignCenter)
        bal_layout.addWidget(self.user_lbl)
        bal_layout.addSpacing(20)

        lbl = QLabel("Баланс счёта")
        lbl.setStyleSheet("color: #3A4858; font-size: 13px; letter-spacing: 2px;")
        lbl.setAlignment(Qt.AlignCenter)
        bal_layout.addWidget(lbl)

        self.balance_display = QLabel("")
        self.balance_display.setStyleSheet("color: #FFFFFF; font-size: 64px; font-weight: 800; letter-spacing: -2px;")
        self.balance_display.setAlignment(Qt.AlignCenter)
        bal_layout.addWidget(self.balance_display)
        bal_layout.addSpacing(30)

        # Transaction summary
        self.tx_summary = QLabel("")
        self.tx_summary.setStyleSheet("color: #4A5568; font-size: 13px; line-height: 1.6;")
        self.tx_summary.setAlignment(Qt.AlignCenter)
        bal_layout.addWidget(self.tx_summary)
        bal_layout.addSpacing(40)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        pay_btn = QPushButton("💳 Перейти к оплате")
        pay_btn.setFixedSize(200, 46)
        pay_btn.clicked.connect(self.main_window.show_payment)
        pay_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F4C8A, stop:1 #1A6DC4);
                color: #FFFFFF; border: none; border-radius: 10px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background: #2485E8; }
        """)
        btn_row.addWidget(pay_btn)

        home_btn = QPushButton("← Меню")
        home_btn.setFixedSize(120, 46)
        home_btn.clicked.connect(self.main_window.show_home)
        home_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px; color: #6B7A8F; font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #E8EDF5; }
        """)
        btn_row.addWidget(home_btn)
        bal_layout.addLayout(btn_row)

        self.balance_section.hide()
        content.addWidget(self.balance_section)

        layout.addLayout(content)
        layout.addStretch()

    def set_user(self, user_data):
        self._user = user_data
        name = user_data.get('name', '')
        client_id = user_data.get('client_id', '')

        from backend.database import Database
        db = Database()
        profile = db.get_user(client_id)
        if profile:
            balance = profile.get('balance', 0)
            txs = profile.get('transactions', [])
        else:
            balance = 0
            txs = []

        self.scan_section.hide()
        self.balance_section.show()

        self.user_lbl.setText(f"👤  {name}  •  ID: {client_id[:8]}")
        self.balance_display.setText(f"{balance:,.0f} ₽")

        tx_count = len(txs)
        if txs:
            last_tx = txs[-1] if txs else {}
            last_amount = float(last_tx.get('amount', 0))
            last_sign = "+" if last_amount > 0 else "−"
            summary = f"Транзакций: {tx_count}  •  Последняя: {last_sign}{abs(last_amount):,.0f} ₽"
        else:
            summary = "Нет транзакций"
        self.tx_summary.setText(summary)

    def _start_scan(self):
        self.main_window.scan_screen.set_mode('balance', 'Идентификация для проверки баланса')
        self.main_window.show_scan()

    def on_enter(self):
        if not self._user:
            self.scan_section.show()
            self.balance_section.hide()
