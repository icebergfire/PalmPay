"""
Admin Dashboard Screen
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient
import math


class MiniChart(QWidget):
    """Simple bar chart widget"""
    def __init__(self, data=None, color="#3B9EFF", parent=None):
        super().__init__(parent)
        self.data = data or [30, 45, 60, 40, 80, 65, 90, 75, 55, 85, 70, 95]
        self.color = QColor(color)
        self.setFixedHeight(60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if not self.data:
            return

        max_val = max(self.data) or 1
        bar_width = (w - 4) / len(self.data)
        spacing = 2

        for i, val in enumerate(self.data):
            bh = int((val / max_val) * (h - 8))
            bx = int(i * bar_width + 2)
            by = h - bh - 2

            # Gradient fill
            grad = QLinearGradient(bx, by, bx, by + bh)
            c = self.color
            grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 200))
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 60))

            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bx, by, int(bar_width - spacing), bh, 2, 2)


class StatCard(QFrame):
    def __init__(self, icon, title, value, subtitle, color, chart_data=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 16px;
            }}
            QFrame:hover {{
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.12);
            }}
        """)
        self.setFixedHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"""
            font-size: 18px;
            background: rgba({self._hex_to_rgb(color)}, 0.12);
            border-radius: 18px;
            padding: 6px;
        """)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignCenter)
        top_row.addWidget(icon_lbl)
        top_row.addStretch()

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #3A4858; font-size: 11px; letter-spacing: 0.5px;")
        top_row.addWidget(title_lbl)
        layout.addLayout(top_row)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800; letter-spacing: -1px;")
        layout.addWidget(val_lbl)
        self._val_lbl = val_lbl

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #3A4858; font-size: 11px;")
        layout.addWidget(sub_lbl)

        if chart_data:
            chart = MiniChart(chart_data, color)
            layout.addWidget(chart)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"{r},{g},{b}"

    def update_value(self, value):
        self._val_lbl.setText(value)


class AdminScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._init_ui()

        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_stats)
        self._refresh_timer.start(5000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top_bar = self._build_top_bar()
        layout.addWidget(top_bar)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(50, 40, 50, 40)
        self.content_layout.setSpacing(30)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        self._build_dashboard()

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

        title = QLabel("PalmPay Dashboard")
        title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700;")
        layout.addWidget(title, 0, Qt.AlignCenter)
        layout.addStretch()

        # Real-time indicator
        rt = QLabel("● REAL-TIME")
        rt.setStyleSheet("color: #13A05A; font-size: 11px; letter-spacing: 1.5px; font-weight: 600;")
        layout.addWidget(rt)

        return bar

    def _build_dashboard(self):
        # Greeting
        header_layout = QHBoxLayout()
        greeting = QLabel("Панель управления")
        greeting.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;")
        header_layout.addWidget(greeting)
        header_layout.addStretch()

        from PyQt5.QtCore import QDate
        today = QDate.currentDate()
        date_lbl = QLabel(today.toString("dd.MM.yyyy"))
        date_lbl.setStyleSheet("color: #3A4858; font-size: 14px;")
        header_layout.addWidget(date_lbl)
        self.content_layout.addLayout(header_layout)

        # KPI Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        chart1 = [20, 35, 28, 55, 42, 68, 75, 62, 88, 71, 95, 108]
        chart2 = [90, 92, 94, 91, 95, 96, 94, 97, 96, 95, 97, 96]
        chart3 = [1.8, 1.6, 1.5, 1.7, 1.4, 1.3, 1.5, 1.2, 1.3, 1.2, 1.1, 1.2]

        self.card_clients = StatCard("👥", "КЛИЕНТОВ", "0", "Всего зарегистрировано", "#3B9EFF", chart1)
        self.card_tx = StatCard("💳", "ТРАНЗАКЦИЙ", "0", "Всего операций", "#13A05A", chart1)
        self.card_accuracy = StatCard("🎯", "ТОЧНОСТЬ", "96%", "Распознавание биометрии", "#F0C040", chart2)
        self.card_speed = StatCard("⚡", "СКОРОСТЬ", "1.2с", "Среднее время скан.", "#9B59FF", chart3)

        for card in [self.card_clients, self.card_tx, self.card_accuracy, self.card_speed]:
            cards_layout.addWidget(card)

        self.content_layout.addLayout(cards_layout)

        # Two column section
        two_col = QHBoxLayout()
        two_col.setSpacing(20)

        # Client list
        client_section = self._build_client_list()
        two_col.addWidget(client_section, 3)

        # System info
        sys_section = self._build_system_info()
        two_col.addWidget(sys_section, 2)

        self.content_layout.addLayout(two_col)

        # Bottom: recent activity
        activity = self._build_recent_activity()
        self.content_layout.addWidget(activity)

    def _build_client_list(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Зарегистрированные клиенты")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Table header
        col_header = QHBoxLayout()
        for text in ["Клиент", "ID", "Баланс", "Транзакций"]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #2A3545; font-size: 11px; letter-spacing: 0.5px;")
            col_header.addWidget(lbl)
        layout.addLayout(col_header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: rgba(255,255,255,0.06);")
        layout.addWidget(sep)

        self.client_list_layout = QVBoxLayout()
        self.client_list_layout.setSpacing(4)
        layout.addLayout(self.client_list_layout)

        return frame

    def _build_system_info(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Состояние системы")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        sys_items = [
            ("MediaPipe Hands", "Активно", "#13A05A", 100),
            ("OpenCV Camera", "Готово", "#13A05A", 100),
            ("PyTorch Engine", "Загружено", "#F0C040", 85),
            ("База данных", "Онлайн", "#13A05A", 100),
            ("Антиспуфинг", "Активно", "#13A05A", 100),
            ("Шифрование", "AES-256", "#3B9EFF", 100),
        ]

        for name, status, color, progress in sys_items:
            row = QVBoxLayout()
            row.setSpacing(4)

            info_row = QHBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px;")
            info_row.addWidget(name_lbl)
            info_row.addStretch()

            status_lbl = QLabel(f"● {status}")
            status_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
            info_row.addWidget(status_lbl)
            row.addLayout(info_row)

            bar = QProgressBar()
            bar.setFixedHeight(3)
            bar.setValue(progress)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: rgba(255,255,255,0.05); border: none; border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background: {color}; border-radius: 2px;
                }}
            """)
            row.addWidget(bar)
            layout.addLayout(row)

        layout.addStretch()

        # Demo mode button
        demo_btn = QPushButton("🗑  Очистить все данные")
        demo_btn.setFixedHeight(40)
        demo_btn.clicked.connect(self._clear_data)
        demo_btn.setStyleSheet("""
            QPushButton {
                background: rgba(224,80,80,0.1); border: 1px solid rgba(224,80,80,0.25);
                border-radius: 10px; color: #E05050; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(224,80,80,0.2); }
        """)
        layout.addWidget(demo_btn)

        return frame

    def _build_recent_activity(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("Последние операции")
        title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        layout.addWidget(title)

        self.activity_layout = QVBoxLayout()
        self.activity_layout.setSpacing(6)
        layout.addLayout(self.activity_layout)

        return frame

    def _refresh_stats(self):
        from backend.database import Database
        db = Database()
        stats = db.get_stats()
        users = db.get_all_users()
        transactions = db.get_all_transactions()

        self.card_clients.update_value(str(stats.get('total_clients', 0)))
        self.card_tx.update_value(str(len(transactions)))
        self.card_accuracy.update_value(f"{stats.get('accuracy', 96)}%")
        self.card_speed.update_value(f"{stats.get('avg_scan_time', 1.2)}с")

        # Update client list
        while self.client_list_layout.count():
            item = self.client_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for user in users[:8]:
            row = QFrame()
            row.setFixedHeight(42)
            row.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.02);
                    border-radius: 8px;
                }
                QFrame:hover { background: rgba(255,255,255,0.05); }
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 0, 12, 0)

            name_lbl = QLabel(f"👤 {user.get('name', '—')}")
            name_lbl.setStyleSheet("color: #C0C8D8; font-size: 13px;")
            row_layout.addWidget(name_lbl)

            id_lbl = QLabel(user.get('client_id', '—')[:8])
            id_lbl.setStyleSheet("color: #3A4858; font-size: 12px;")
            row_layout.addWidget(id_lbl)

            bal_lbl = QLabel(f"{user.get('balance', 0):,.0f} ₽")
            bal_lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600;")
            row_layout.addWidget(bal_lbl)

            tx_count = len(user.get('transactions', []))
            tx_lbl = QLabel(str(tx_count))
            tx_lbl.setStyleSheet("color: #3B9EFF; font-size: 13px;")
            row_layout.addWidget(tx_lbl)

            self.client_list_layout.addWidget(row)

        # Recent activity
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = sorted(transactions, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
        for tx in recent:
            row = QHBoxLayout()
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(tx.get('timestamp', ''))
                ts = dt.strftime("%H:%M")
            except Exception:
                ts = "—"

            ts_lbl = QLabel(ts)
            ts_lbl.setStyleSheet("color: #3A4858; font-size: 12px;")
            ts_lbl.setFixedWidth(50)
            row.addWidget(ts_lbl)

            merchant = tx.get('merchant', tx.get('description', 'Операция'))
            m_lbl = QLabel(merchant)
            m_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px;")
            row.addWidget(m_lbl)
            row.addStretch()

            amount = float(tx.get('amount', 0))
            is_credit = tx.get('type') == 'credit' or amount > 0
            color = "#13A05A" if is_credit else "#E8EDF5"
            sign = "+" if is_credit else "−"
            a_lbl = QLabel(f"{sign}{abs(amount):,.0f} ₽")
            a_lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
            row.addWidget(a_lbl)

            self.activity_layout.addLayout(row)

    def _clear_data(self):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 'Очистить данные',
            'Удалить всех клиентов и все транзакции?\nЭто действие нельзя отменить.',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from backend.database import Database
            db = Database()
            db.clear_all()
            self._refresh_stats()

    def on_enter(self):
        self._refresh_stats()
