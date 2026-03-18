"""
Payment Screen - Palm payment processing
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QLineEdit, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


DEMO_MERCHANTS = [
    ("☕", "Кофейня", 250),
    ("🛒", "Продуктовый магазин", 1200),
    ("🚇", "Транспорт", 75),
    ("🍕", "Ресторан", 890),
    ("💊", "Аптека", 430),
]


class PaymentScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._user = None
        self._amount = 350
        self._merchant = "Магазин"
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
        content.setSpacing(0)

        # Left: payment details
        self.left_panel = self._build_left_panel()
        content.addWidget(self.left_panel, 1)

        # Right: scanner
        self.right_panel = self._build_right_panel()
        content.addWidget(self.right_panel, 1)

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

        title = QLabel("Оплата ладонью")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 600;")
        layout.addWidget(title, 0, Qt.AlignCenter)
        layout.addStretch()

        return bar

    def _build_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border-right: 1px solid rgba(255,255,255,0.06);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(0)

        # Merchant selection
        merch_lbl = QLabel("ВЫБЕРИТЕ ОПЕРАЦИЮ")
        merch_lbl.setStyleSheet("color: #2A3545; font-size: 10px; letter-spacing: 2px; font-weight: 600;")
        layout.addWidget(merch_lbl)
        layout.addSpacing(16)

        for icon, name, amount in DEMO_MERCHANTS:
            btn = self._make_merchant_btn(icon, name, amount)
            layout.addWidget(btn)
            layout.addSpacing(10)

        layout.addSpacing(30)

        # Custom amount
        custom_lbl = QLabel("Произвольная сумма (₽)")
        custom_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px; font-weight: 500;")
        layout.addWidget(custom_lbl)
        layout.addSpacing(8)

        input_row = QHBoxLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Введите сумму...")
        self.amount_input.setFixedHeight(46)
        input_row.addWidget(self.amount_input)

        set_btn = QPushButton("Задать")
        set_btn.setFixedSize(80, 46)
        set_btn.clicked.connect(self._set_custom_amount)
        set_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59,158,255,0.15); border: 1px solid rgba(59,158,255,0.3);
                border-radius: 10px; color: #3B9EFF; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(59,158,255,0.25); }
        """)
        input_row.addWidget(set_btn)
        layout.addLayout(input_row)

        layout.addStretch()

        # Current payment summary
        summary = QFrame()
        summary.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
            }
        """)
        sum_layout = QVBoxLayout(summary)
        sum_layout.setContentsMargins(20, 18, 20, 18)
        sum_layout.setSpacing(8)

        sum_title = QLabel("К ОПЛАТЕ")
        sum_title.setStyleSheet("color: #2A3545; font-size: 10px; letter-spacing: 2px;")
        sum_layout.addWidget(sum_title)

        self.summary_merchant = QLabel("Магазин")
        self.summary_merchant.setStyleSheet("color: #8A9BB0; font-size: 13px;")
        sum_layout.addWidget(self.summary_merchant)

        self.summary_amount = QLabel("350 ₽")
        self.summary_amount.setStyleSheet("color: #FFFFFF; font-size: 34px; font-weight: 800; letter-spacing: -1px;")
        sum_layout.addWidget(self.summary_amount)

        layout.addWidget(summary)

        return panel

    def _make_merchant_btn(self, icon, name, amount):
        btn = QFrame()
        btn.setFixedHeight(54)
        btn.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 10px;
            }
            QFrame:hover {
                background: rgba(59,158,255,0.08);
                border: 1px solid rgba(59,158,255,0.2);
            }
        """)
        btn.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(16, 0, 16, 0)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        layout.addWidget(icon_lbl)
        layout.addSpacing(12)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("color: #C0C8D8; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(name_lbl)
        layout.addStretch()

        amount_lbl = QLabel(f"{amount:,} ₽")
        amount_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(amount_lbl)

        def click(event, n=name, a=amount):
            self._set_payment(n, a)
        btn.mousePressEvent = click

        return btn

    def _set_payment(self, merchant, amount):
        self._merchant = merchant
        self._amount = amount
        self.summary_merchant.setText(merchant)
        self.summary_amount.setText(f"{amount:,} ₽")

    def _set_custom_amount(self):
        try:
            amount = float(self.amount_input.text())
            self._set_payment("Произвольный платёж", amount)
        except ValueError:
            pass

    def _build_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #080C14; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(0)

        # Title
        title = QLabel("Идентификация")
        title.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)
        layout.addSpacing(6)

        sub = QLabel("Поднесите ладонь для подтверждения оплаты")
        sub.setStyleSheet("color: #4A5568; font-size: 13px;")
        layout.addWidget(sub)
        layout.addSpacing(40)

        # User recognition result (hidden initially)
        self.user_frame = QFrame()
        self.user_frame.setStyleSheet("""
            QFrame {
                background: rgba(59,158,255,0.07);
                border: 1px solid rgba(59,158,255,0.2);
                border-radius: 14px;
            }
        """)
        user_layout = QVBoxLayout(self.user_frame)
        user_layout.setContentsMargins(24, 20, 24, 20)
        user_layout.setSpacing(8)

        ident_lbl = QLabel("ИДЕНТИФИЦИРОВАН")
        ident_lbl.setStyleSheet("color: #3B9EFF; font-size: 10px; letter-spacing: 2px; font-weight: 600;")
        user_layout.addWidget(ident_lbl)

        self.user_name_lbl = QLabel("")
        self.user_name_lbl.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: 700;")
        user_layout.addWidget(self.user_name_lbl)

        self.similarity_lbl = QLabel("")
        self.similarity_lbl.setStyleSheet("color: #6B7A8F; font-size: 13px;")
        user_layout.addWidget(self.similarity_lbl)

        self.balance_lbl = QLabel("")
        self.balance_lbl.setStyleSheet("color: #8A9BB0; font-size: 13px;")
        user_layout.addWidget(self.balance_lbl)

        self.user_frame.hide()
        layout.addWidget(self.user_frame)
        layout.addSpacing(20)

        # Scan button
        self.scan_btn = QPushButton("🤚  Сканировать ладонь")
        self.scan_btn.setFixedHeight(56)
        self.scan_btn.setStyleSheet("""
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
        self.scan_btn.clicked.connect(self._start_scan)
        layout.addWidget(self.scan_btn)
        layout.addSpacing(20)

        # Confirm payment button (hidden initially)
        self.confirm_btn = QPushButton("✓  Подтвердить оплату")
        self.confirm_btn.setFixedHeight(56)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0D6B3A, stop:1 #13A05A);
                color: #FFFFFF; border: none; border-radius: 12px;
                font-size: 16px; font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #13A05A, stop:1 #18C46E);
            }
        """)
        self.confirm_btn.clicked.connect(self._confirm_payment)
        self.confirm_btn.hide()
        layout.addWidget(self.confirm_btn)

        # Payment result (hidden initially)
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background: rgba(19,160,90,0.1);
                border: 1px solid rgba(19,160,90,0.3);
                border-radius: 14px;
            }
        """)
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(24, 20, 24, 20)
        result_layout.setSpacing(10)

        self.result_icon = QLabel("✔")
        self.result_icon.setStyleSheet("color: #13A05A; font-size: 36px;")
        result_layout.addWidget(self.result_icon, 0, Qt.AlignCenter)

        self.result_title = QLabel("Платёж подтверждён")
        self.result_title.setStyleSheet("color: #13A05A; font-size: 18px; font-weight: 700;")
        result_layout.addWidget(self.result_title, 0, Qt.AlignCenter)

        self.result_details = QLabel("")
        self.result_details.setStyleSheet("color: #4A8A6A; font-size: 13px; line-height: 1.5;")
        self.result_details.setAlignment(Qt.AlignCenter)
        self.result_details.setWordWrap(True)
        result_layout.addWidget(self.result_details)

        home_btn = QPushButton("← Вернуться в меню")
        home_btn.setFixedHeight(40)
        home_btn.clicked.connect(self._reset_and_home)
        home_btn.setStyleSheet("""
            QPushButton {
                background: rgba(19,160,90,0.15); border: 1px solid rgba(19,160,90,0.3);
                border-radius: 8px; color: #13A05A; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(19,160,90,0.25); }
        """)
        result_layout.addWidget(home_btn)

        self.result_frame.hide()
        layout.addWidget(self.result_frame)

        layout.addStretch()

        # Instructions
        instr = QLabel("Биометрическая верификация защищена\nстандартом ISO/IEC 19794-6")
        instr.setStyleSheet("color: #2A3545; font-size: 11px; line-height: 1.5;")
        instr.setAlignment(Qt.AlignCenter)
        layout.addWidget(instr)

        return panel

    def set_user(self, user_data):
        self._user = user_data
        name = user_data.get('name', 'Неизвестно')
        similarity = user_data.get('similarity', 0.94)

        # Load actual balance from database
        from backend.database import Database
        db = Database()
        profile = db.get_user(user_data.get('client_id'))
        if profile:
            balance = profile.get('balance', 0)
        else:
            balance = user_data.get('balance', 0)

        self.user_name_lbl.setText(f"👤  {name}")
        self.similarity_lbl.setText(f"Совпадение: {int(similarity * 100)}%  •  Биометрия верифицирована")
        self.balance_lbl.setText(f"Баланс: {balance:,.0f} ₽")
        self._user['balance'] = balance

        self.user_frame.show()
        self.confirm_btn.show()
        self.scan_btn.setText("🔄  Повторить сканирование")

    def _start_scan(self):
        self.main_window.scan_screen.set_mode('payment', 'Сканирование для оплаты')
        self.main_window.show_scan()

    def _confirm_payment(self):
        if not self._user:
            return

        balance = self._user.get('balance', 0)
        if balance < self._amount:
            self.result_icon.setText("✗")
            self.result_icon.setStyleSheet("color: #E05050; font-size: 36px;")
            self.result_title.setText("Недостаточно средств")
            self.result_title.setStyleSheet("color: #E05050; font-size: 18px; font-weight: 700;")
            self.result_details.setText(f"Баланс: {balance:,.0f} ₽\nТребуется: {self._amount:,.0f} ₽")
            self.result_frame.setStyleSheet("""
                QFrame {
                    background: rgba(220,50,50,0.08);
                    border: 1px solid rgba(220,50,50,0.25);
                    border-radius: 14px;
                }
            """)
            self.result_frame.show()
            return

        # Process payment
        from backend.database import Database
        from backend.payments import PaymentProcessor
        db = Database()
        processor = PaymentProcessor(db)

        new_balance = processor.process_payment(
            self._user.get('client_id', ''),
            self._amount,
            self._merchant
        )

        self.result_icon.setText("✔")
        self.result_icon.setStyleSheet("color: #13A05A; font-size: 36px;")
        self.result_title.setText("Платёж подтверждён")
        self.result_title.setStyleSheet("color: #13A05A; font-size: 18px; font-weight: 700;")
        self.result_details.setText(
            f"Пользователь: {self._user.get('name')}\n"
            f"Сумма: {self._amount:,.0f} ₽\n"
            f"Остаток: {new_balance:,.0f} ₽"
        )
        self.result_frame.setStyleSheet("""
            QFrame {
                background: rgba(19,160,90,0.1);
                border: 1px solid rgba(19,160,90,0.3);
                border-radius: 14px;
            }
        """)
        self.result_frame.show()
        self.confirm_btn.hide()
        self.scan_btn.hide()

    def _reset_and_home(self):
        self.on_enter()
        self.main_window.show_home()

    def on_enter(self):
        self._user = None
        self.user_frame.hide()
        self.confirm_btn.hide()
        self.result_frame.hide()
        self.scan_btn.show()
        self.scan_btn.setText("🤚  Сканировать ладонь")
