"""
Main Window - PalmPay Terminal
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient

from ui.home_screen import HomeScreen
from ui.scan_screen import ScanScreen
from ui.register_screen import RegisterScreen
from ui.payment_screen import PaymentScreen
from ui.history_screen import HistoryScreen
from ui.admin_screen import AdminScreen
from ui.balance_screen import BalanceScreen

STYLE = """
QMainWindow, QWidget {
    background-color: #080C14;
    color: #E8EDF5;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0F4C8A, stop:1 #1A6DC4);
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 16px 32px;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1A6DC4, stop:1 #2485E8);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0A3560, stop:1 #0F4C8A);
}

QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8A1515, stop:1 #C42020);
}

QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0D6B3A, stop:1 #13A05A);
}

QPushButton#secondary {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #A0ADBF;
}

QPushButton#secondary:hover {
    background: rgba(255,255,255,0.1);
    color: #E8EDF5;
}

QLineEdit {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 14px 18px;
    color: #E8EDF5;
    font-size: 15px;
}

QLineEdit:focus {
    border: 1px solid #1A6DC4;
    background: rgba(26, 109, 196, 0.1);
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: rgba(255,255,255,0.03);
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.2);
    border-radius: 3px;
}

QFrame#card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
}

QLabel#title {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

QLabel#subtitle {
    color: #6B7A8F;
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

QLabel#accent {
    color: #3B9EFF;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PalmPay Biometric Terminal")
        self.setStyleSheet(STYLE)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize screens
        self.home_screen = HomeScreen(self)
        self.scan_screen = ScanScreen(self)
        self.register_screen = RegisterScreen(self)
        self.payment_screen = PaymentScreen(self)
        self.history_screen = HistoryScreen(self)
        self.admin_screen = AdminScreen(self)
        self.balance_screen = BalanceScreen(self)

        self.stack.addWidget(self.home_screen)       # 0
        self.stack.addWidget(self.scan_screen)       # 1
        self.stack.addWidget(self.register_screen)   # 2
        self.stack.addWidget(self.payment_screen)    # 3
        self.stack.addWidget(self.history_screen)    # 4
        self.stack.addWidget(self.admin_screen)      # 5
        self.stack.addWidget(self.balance_screen)    # 6

        self.show_screen(0)

    def show_screen(self, index):
        self.stack.setCurrentIndex(index)
        widget = self.stack.currentWidget()
        if hasattr(widget, 'on_enter'):
            widget.on_enter()

    def show_home(self):
        self.show_screen(0)

    def show_scan(self):
        self.show_screen(1)

    def show_register(self):
        self.show_screen(2)

    def show_payment(self):
        self.show_screen(3)

    def show_history(self):
        self.show_screen(4)

    def show_admin(self):
        self.show_screen(5)

    def show_balance(self):
        self.show_screen(6)
