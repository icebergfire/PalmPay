#!/usr/bin/env python3
"""
PalmPay Biometric Terminal
Main entry point
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow

def main():
    # High DPI support — MUST be set BEFORE QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("PalmPay Biometric Terminal")
    app.setOrganizationName("PalmPay")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.showFullScreen()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
