"""
Home Screen - PalmPay Terminal
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient, QPen, QBrush
import math


class LogoWidget(QWidget):
    """Animated palm logo"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)

    def _animate(self):
        self._angle = (self._angle + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        r = 50

        # Rotating ring
        for i in range(12):
            angle = math.radians(self._angle + i * 30)
            alpha = int(255 * (i / 12))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            color = QColor(59, 158, 255, alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            dot_r = 3 + i * 0.3
            painter.drawEllipse(int(x - dot_r), int(y - dot_r), int(dot_r * 2), int(dot_r * 2))

        # Center glow
        grad = QLinearGradient(cx - 30, cy - 30, cx + 30, cy + 30)
        grad.setColorAt(0, QColor(59, 158, 255, 200))
        grad.setColorAt(1, QColor(26, 109, 196, 200))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - 30, cy - 30, 60, 60)

        # Palm icon
        painter.setPen(QPen(QColor(255, 255, 255, 230), 2))
        painter.setBrush(Qt.NoBrush)
        # Simple hand outline
        points = [
            (cx, cy + 18), (cx - 18, cy + 5), (cx - 22, cy - 8),
            (cx - 18, cy - 20), (cx - 10, cy - 22), (cx - 6, cy - 10),
            (cx - 4, cy - 24), (cx + 2, cy - 25), (cx + 6, cy - 12),
            (cx + 7, cy - 24), (cx + 13, cy - 23), (cx + 15, cy - 10),
            (cx + 18, cy - 18), (cx + 23, cy - 12), (cx + 20, cy - 2),
            (cx + 18, cy + 18), (cx, cy + 18)
        ]
        from PyQt5.QtGui import QPolygon
        from PyQt5.QtCore import QPoint
        poly = QPolygon([QPoint(int(x), int(y)) for x, y in points])
        painter.drawPolygon(poly)


class HomeScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left sidebar
        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        # Main content
        content = self._build_content()
        layout.addWidget(content)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050810, stop:1 #0A1220);
                border-right: 1px solid rgba(59,158,255,0.15);
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(36, 48, 36, 36)
        layout.setSpacing(0)

        # Logo
        logo_widget = LogoWidget()
        logo_widget.setFixedSize(80, 80)
        layout.addWidget(logo_widget, 0, Qt.AlignLeft)
        layout.addSpacing(24)

        # Brand
        brand_label = QLabel("PalmPay")
        brand_label.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;")
        layout.addWidget(brand_label)

        tagline = QLabel("Биометрический терминал")
        tagline.setStyleSheet("color: #3B9EFF; font-size: 11px; letter-spacing: 2px; text-transform: uppercase;")
        layout.addWidget(tagline)
        layout.addSpacing(60)

        # Status indicator
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background: rgba(19, 160, 90, 0.1);
                border: 1px solid rgba(19, 160, 90, 0.3);
                border-radius: 8px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(14, 10, 14, 10)

        dot = QLabel("●")
        dot.setStyleSheet("color: #13A05A; font-size: 10px;")
        status_layout.addWidget(dot)

        status_text = QLabel("Система активна")
        status_text.setStyleSheet("color: #13A05A; font-size: 12px; font-weight: 500;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        layout.addWidget(status_frame)
        layout.addSpacing(40)

        # System info
        info_items = [
            ("Версия", "v2.4.1"),
            ("Камера", "HD Ready"),
            ("База данных", "Активна"),
            ("Шифрование", "AES-256"),
        ]

        for label, value in info_items:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #4A5568; font-size: 12px;")
            val = QLabel(value)
            val.setStyleSheet("color: #8A9BB0; font-size: 12px; font-weight: 500;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            layout.addLayout(row)
            layout.addSpacing(12)

        layout.addStretch()

        # Clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: 300; letter-spacing: 2px;")
        layout.addWidget(self.clock_label)

        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #4A5568; font-size: 12px;")
        layout.addWidget(self.date_label)
        layout.addSpacing(8)

        from PyQt5.QtCore import QDate
        self._update_clock()

        # Version tag
        ver = QLabel("© 2024 PalmPay Systems")
        ver.setStyleSheet("color: #2A3545; font-size: 10px;")
        layout.addWidget(ver)

        return sidebar

    def _update_clock(self):
        from PyQt5.QtCore import QTime, QDate
        t = QTime.currentTime()
        self.clock_label.setText(t.toString("HH:mm:ss"))
        d = QDate.currentDate()
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        months = ["янв", "фев", "мар", "апр", "май", "июн",
                  "июл", "авг", "сен", "окт", "ноя", "дек"]
        day_name = days[d.dayOfWeek() - 1]
        self.date_label.setText(f"{day_name}, {d.day()} {months[d.month()-1]} {d.year()}")

    def _build_content(self):
        content = QFrame()
        content.setStyleSheet("QFrame { background: transparent; }")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(0)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Добро пожаловать")
        title.setStyleSheet("color: #FFFFFF; font-size: 36px; font-weight: 700; letter-spacing: -1px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Exit button
        exit_btn = QPushButton("✕ Выход")
        exit_btn.setObjectName("secondary")
        exit_btn.setFixedSize(120, 40)
        exit_btn.clicked.connect(self._exit)
        exit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                color: #6B7A8F;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(220,50,50,0.15);
                border: 1px solid rgba(220,50,50,0.3);
                color: #E05050;
            }
        """)
        header_layout.addWidget(exit_btn)
        layout.addLayout(header_layout)

        subtitle = QLabel("Выберите операцию для продолжения")
        subtitle.setStyleSheet("color: #4A5568; font-size: 15px; margin-top: 8px;")
        layout.addWidget(subtitle)
        layout.addSpacing(60)

        # Main buttons grid
        grid = QHBoxLayout()
        grid.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        right_col = QVBoxLayout()
        right_col.setSpacing(20)

        buttons = [
            ("🤚", "Оплата", "Оплатить по биометрии ладони", "#0F4C8A", "#1A6DC4", self.main_window.show_payment),
            ("👤", "Регистрация\nклиента", "Добавить нового пользователя", "#0D5C3A", "#13A05A", self.main_window.show_register),
            ("💳", "Баланс", "Проверить баланс счёта", "#3D2F80", "#6048C8", self.main_window.show_balance),
            ("📋", "История\nопераций", "Просмотр транзакций", "#5C3A0D", "#B87020", self.main_window.show_history),
            ("⚙️", "Админ-\nпанель", "Управление и статистика", "#2A2A2A", "#505050", self.main_window.show_admin),
        ]

        for i, (icon, title_text, desc, c1, c2, action) in enumerate(buttons):
            btn = self._make_menu_btn(icon, title_text, desc, c1, c2, action)
            if i < 3:
                left_col.addWidget(btn)
            else:
                right_col.addWidget(btn)

        right_col.addStretch()
        grid.addLayout(left_col)
        grid.addLayout(right_col)
        layout.addLayout(grid)
        layout.addStretch()

        # Bottom stats bar
        stats_bar = self._build_stats_bar()
        layout.addWidget(stats_bar)

        return content

    def _make_menu_btn(self, icon, title_text, desc, c1, c2, action):
        btn = QFrame()
        btn.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 20px;
            }}
            QFrame:hover {{
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(59,158,255,0.2);
            }}
        """)
        btn.setFixedHeight(120)
        btn.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(20)

        # Icon circle
        icon_circle = QLabel(icon)
        icon_circle.setFixedSize(52, 52)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c1}, stop:1 {c2});
                border-radius: 26px;
                font-size: 22px;
            }}
        """)
        layout.addWidget(icon_circle)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("color: #4A5568; font-size: 12px; background: transparent; border: none;")
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        arrow = QLabel("→")
        arrow.setStyleSheet("color: #2A3545; font-size: 20px; background: transparent; border: none;")
        layout.addWidget(arrow)

        # Make clickable
        def make_click_handler(a, b, c):
            def mousePressEvent(event):
                c()
            return mousePressEvent

        btn.mousePressEvent = make_click_handler(icon, title_text, action)

        return btn

    def _build_stats_bar(self):
        from backend.database import Database
        db = Database()
        stats = db.get_stats()

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px;
            }
        """)
        frame.setFixedHeight(72)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(30, 0, 30, 0)

        stat_items = [
            ("Клиентов", str(stats.get('total_clients', 0))),
            ("Транзакций сегодня", str(stats.get('transactions_today', 0))),
            ("Точность распознавания", f"{stats.get('accuracy', 96)}%"),
            ("Среднее время скан.", f"{stats.get('avg_scan_time', 1.2)}с"),
        ]

        for i, (label, value) in enumerate(stat_items):
            if i > 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setStyleSheet("color: rgba(255,255,255,0.08);")
                layout.addWidget(sep)

            item_layout = QVBoxLayout()
            item_layout.setSpacing(2)
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet("color: #3B9EFF; font-size: 18px; font-weight: 700;")
            lbl_lbl = QLabel(label)
            lbl_lbl.setStyleSheet("color: #3A4858; font-size: 11px;")
            item_layout.addWidget(val_lbl, 0, Qt.AlignCenter)
            item_layout.addWidget(lbl_lbl, 0, Qt.AlignCenter)
            layout.addLayout(item_layout)

        return frame

    def _exit(self):
        import sys
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()

    def on_enter(self):
        pass
