"""
Register Screen - Client registration with palm scanning
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QLineEdit, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont
import time


class RegistrationThread(QThread):
    progress_changed = pyqtSignal(int, str)
    frame_ready = pyqtSignal(object, object)
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, client_name, parent=None):
        super().__init__(parent)
        self.client_name = client_name
        self._running = False

    def run(self):
        from backend.camera import CameraManager
        from backend.recognition import PalmRecognizer
        from backend.database import Database
        import numpy as np

        self._running = True
        camera = CameraManager()
        recognizer = PalmRecognizer()

        self.progress_changed.emit(0, "Инициализация камеры...")

        if not camera.open():
            # Demo mode
            self._run_demo(self.client_name)
            return

        frames_collected = 0
        target_frames = 50
        embeddings = []
        landmarks_list = []
        sides = []

        self.progress_changed.emit(5, "Поместите открытую ладонь в зону сканирования")

        try:
            while self._running and frames_collected < target_frames:
                frame = camera.read_frame()
                if frame is None:
                    continue

                hand_data = recognizer.detect_hands(frame)
                self.frame_ready.emit(frame, hand_data)

                # Используем только открытую ладонь в зоне сканирования
                if (
                    hand_data
                    and hand_data.get('in_zone')
                    and hand_data.get('pose') == 'palm'
                ):
                    emb = recognizer.extract_embedding(hand_data)
                    if emb is not None:
                        embeddings.append(emb)
                        landmarks_list.append(hand_data.get('landmarks', []))
                        side = hand_data.get('side') or "unknown"
                        sides.append(side)
                        frames_collected += 1
                        progress = int(5 + (frames_collected / target_frames) * 80)
                        msg = f"Сбор данных: {frames_collected}/{target_frames} кадров"
                        self.progress_changed.emit(progress, msg)
                    time.sleep(0.05)
                else:
                    time.sleep(0.03)

            if not self._running:
                return

            if len(embeddings) < 20:
                self.failed.emit("Недостаточно данных для регистрации")
                return

            self.progress_changed.emit(88, "Генерация биометрического профиля...")
            mean_emb = np.mean(embeddings, axis=0).tolist()

            # Определяем сторону по большинству кадров
            hand_side = "unknown"
            if sides:
                left_count = sum(1 for s in sides if s == "left")
                right_count = sum(1 for s in sides if s == "right")
                if left_count > right_count and left_count >= 10:
                    hand_side = "left"
                elif right_count > left_count and right_count >= 10:
                    hand_side = "right"

            self.progress_changed.emit(94, "Сохранение профиля...")
            db = Database()
            profile = db.register_user(self.client_name, mean_emb, hand_side=hand_side)

            self.progress_changed.emit(100, "✓ Регистрация завершена!")
            self.completed.emit(profile)

        finally:
            camera.release()

    def _run_demo(self, client_name):
        import numpy as np
        steps = [
            (5, "Инициализация (демо режим)..."),
            (15, "Поместите ладонь в зону сканирования"),
            (30, "Сбор данных: 15/50 кадров"),
            (50, "Сбор данных: 25/50 кадров"),
            (70, "Сбор данных: 35/50 кадров"),
            (85, "Сбор данных: 50/50 кадров"),
            (90, "Генерация биометрического профиля..."),
            (95, "Анализ уникальных признаков..."),
            (100, "✓ Регистрация завершена!"),
        ]
        for progress, msg in steps:
            if not self._running:
                return
            self.progress_changed.emit(progress, msg)
            time.sleep(0.8)

        demo_emb = np.random.randn(128).tolist()
        db = __import__('backend.database', fromlist=['Database']).Database()
        profile = db.register_user(client_name, demo_emb)
        self.completed.emit(profile)

    def stop(self):
        self._running = False
        self.wait(2000)


class RegisterScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._reg_thread = None
        self._last_profile = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left info panel
        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Right form panel
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, 1)

    def _build_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050B18, stop:1 #080D1A);
                border-right: 1px solid rgba(255,255,255,0.06);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)

        back_btn = QPushButton("← Назад")
        back_btn.setFixedSize(100, 34)
        back_btn.clicked.connect(self._go_back)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                color: #6B7A8F; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #E8EDF5; }
        """)
        layout.addWidget(back_btn, 0, Qt.AlignLeft)
        layout.addSpacing(60)

        tag = QLabel("НОВЫЙ КЛИЕНТ")
        tag.setStyleSheet("color: #3B9EFF; font-size: 11px; letter-spacing: 3px; font-weight: 600;")
        layout.addWidget(tag)
        layout.addSpacing(12)

        title = QLabel("Регистрация\nклиента")
        title.setStyleSheet("color: #FFFFFF; font-size: 38px; font-weight: 800; line-height: 1.15; letter-spacing: -1px;")
        layout.addWidget(title)
        layout.addSpacing(20)

        desc = QLabel("Создайте биометрический профиль\nклиента для бесконтактной оплаты\nладонью в любом терминале.")
        desc.setStyleSheet("color: #4A5568; font-size: 14px; line-height: 1.6;")
        layout.addWidget(desc)
        layout.addSpacing(50)

        # Process steps
        steps = [
            ("01", "Введите имя клиента"),
            ("02", "Начните сканирование"),
            ("03", "Поднесите ладонь (50 кадров)"),
            ("04", "Профиль сохранён"),
        ]

        for num, text in steps:
            step_layout = QHBoxLayout()

            num_lbl = QLabel(num)
            num_lbl.setFixedSize(36, 36)
            num_lbl.setAlignment(Qt.AlignCenter)
            num_lbl.setStyleSheet("""
                color: #3B9EFF; font-size: 12px; font-weight: 700;
                background: rgba(59,158,255,0.1);
                border: 1px solid rgba(59,158,255,0.3);
                border-radius: 18px;
            """)
            step_layout.addWidget(num_lbl)
            step_layout.addSpacing(14)

            text_lbl = QLabel(text)
            text_lbl.setStyleSheet("color: #6B7A8F; font-size: 13px;")
            step_layout.addWidget(text_lbl)
            step_layout.addStretch()

            layout.addLayout(step_layout)
            layout.addSpacing(14)

        layout.addStretch()

        # Security note
        note = QFrame()
        note.setStyleSheet("""
            QFrame {
                background: rgba(19,160,90,0.07);
                border: 1px solid rgba(19,160,90,0.2);
                border-radius: 10px;
            }
        """)
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(16, 12, 16, 12)

        note_title = QLabel("🔒 Защита данных")
        note_title.setStyleSheet("color: #13A05A; font-size: 12px; font-weight: 600;")
        note_layout.addWidget(note_title)

        note_text = QLabel("Биометрические данные хранятся\nв зашифрованном виде (AES-256)\nи не передаются третьим лицам.")
        note_text.setStyleSheet("color: #3A5A48; font-size: 11px; line-height: 1.5;")
        note_layout.addWidget(note_text)
        layout.addWidget(note)

        return panel

    def _build_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background: #080C14; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(70, 70, 70, 70)
        layout.setAlignment(Qt.AlignTop)

        # Form title
        form_title = QLabel("Данные клиента")
        form_title.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: 700;")
        layout.addWidget(form_title)
        layout.addSpacing(8)

        form_sub = QLabel("Заполните форму для создания профиля")
        form_sub.setStyleSheet("color: #4A5568; font-size: 13px;")
        layout.addWidget(form_sub)
        layout.addSpacing(36)

        # Name input
        name_lbl = QLabel("Имя клиента")
        name_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px; font-weight: 500; letter-spacing: 0.5px;")
        layout.addWidget(name_lbl)
        layout.addSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите полное имя...")
        self.name_input.setFixedHeight(50)
        layout.addWidget(self.name_input)
        layout.addSpacing(20)

        # Initial balance
        bal_lbl = QLabel("Начальный баланс (₽)")
        bal_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px; font-weight: 500; letter-spacing: 0.5px;")
        layout.addWidget(bal_lbl)
        layout.addSpacing(8)

        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("5000")
        self.balance_input.setText("5000")
        self.balance_input.setFixedHeight(50)
        layout.addWidget(self.balance_input)
        layout.addSpacing(36)

        # Start button
        self.start_btn = QPushButton("🤚  Начать сканирование")
        self.start_btn.setFixedHeight(54)
        self.start_btn.setStyleSheet("""
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
        self.start_btn.clicked.connect(self._start_registration)
        layout.addWidget(self.start_btn)
        layout.addSpacing(30)

        # Progress section (hidden initially)
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 14px;
            }
        """)
        prog_layout = QVBoxLayout(self.progress_frame)
        prog_layout.setContentsMargins(24, 20, 24, 20)
        prog_layout.setSpacing(12)

        self.progress_title = QLabel("Идёт сканирование...")
        self.progress_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 600;")
        prog_layout.addWidget(self.progress_title)

        self.progress_msg = QLabel("Поместите ладонь в зону сканирования")
        self.progress_msg.setStyleSheet("color: #6B7A8F; font-size: 13px;")
        prog_layout.addWidget(self.progress_msg)

        self.side_label = QLabel("Рука: не определена")
        self.side_label.setStyleSheet("color: #6B7A8F; font-size: 12px;")
        prog_layout.addWidget(self.side_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,0.05);
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0F4C8A, stop:1 #3B9EFF);
                border-radius: 3px;
            }
        """)
        prog_layout.addWidget(self.progress_bar)

        self.progress_frame.hide()
        layout.addWidget(self.progress_frame)
        layout.addSpacing(20)

        # Result frame (hidden initially)
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background: rgba(19,160,90,0.08);
                border: 1px solid rgba(19,160,90,0.25);
                border-radius: 14px;
            }
        """)
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(24, 20, 24, 20)
        result_layout.setSpacing(8)

        self.result_title = QLabel("✓ Клиент зарегистрирован")
        self.result_title.setStyleSheet("color: #13A05A; font-size: 16px; font-weight: 700;")
        result_layout.addWidget(self.result_title)

        self.result_details = QLabel("")
        self.result_details.setStyleSheet("color: #6B8A7A; font-size: 13px; line-height: 1.6;")
        self.result_details.setWordWrap(True)
        result_layout.addWidget(self.result_details)

        home_btn = QPushButton("← Вернуться в меню")
        home_btn.setFixedHeight(42)
        home_btn.clicked.connect(self.main_window.show_home)
        home_btn.setStyleSheet("""
            QPushButton {
                background: rgba(19,160,90,0.15);
                border: 1px solid rgba(19,160,90,0.3);
                border-radius: 8px;
                color: #13A05A; font-size: 13px; font-weight: 600;
                margin-top: 8px;
            }
            QPushButton:hover { background: rgba(19,160,90,0.25); }
        """)
        result_layout.addWidget(home_btn)

        self.result_frame.hide()
        layout.addWidget(self.result_frame)

        # Button to add second hand (hidden by default)
        self.add_second_hand_btn = QPushButton("Добавить вторую руку")
        self.add_second_hand_btn.setFixedHeight(42)
        self.add_second_hand_btn.clicked.connect(self._start_second_hand_registration)
        self.add_second_hand_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59,158,255,0.12);
                border: 1px solid rgba(59,158,255,0.4);
                border-radius: 8px;
                color: #3B9EFF; font-size: 13px; font-weight: 600;
                margin-top: 8px;
            }
            QPushButton:hover { background: rgba(59,158,255,0.2); }
        """)
        self.add_second_hand_btn.hide()
        layout.addWidget(self.add_second_hand_btn)

        layout.addStretch()

        return panel

    def _start_registration(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setStyleSheet("""
                QLineEdit {
                    background: rgba(220,50,50,0.1);
                    border: 1px solid rgba(220,50,50,0.5);
                    border-radius: 10px;
                    padding: 14px 18px;
                    color: #E8EDF5; font-size: 15px;
                }
            """)
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Сканирование...")
        self.progress_frame.show()
        self.result_frame.hide()

        balance = 5000
        try:
            balance = float(self.balance_input.text() or 5000)
        except ValueError:
            pass

        self._reg_thread = RegistrationThread(name)
        self._reg_thread._initial_balance = balance
        self._reg_thread.progress_changed.connect(self._on_progress)
        self._reg_thread.frame_ready.connect(self._on_frame)
        self._reg_thread.completed.connect(self._on_complete)
        self._reg_thread.failed.connect(self._on_failed)
        self._reg_thread.start()

    def _on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_msg.setText(message)
        if value == 100:
            self.progress_title.setText("✓ Готово!")
            self.progress_title.setStyleSheet("color: #13A05A; font-size: 15px; font-weight: 600;")

    def _on_frame(self, frame, hand_data):
        side_text = "не определена"
        if hand_data:
            side = hand_data.get('side')
            if side == 'left':
                side_text = "левая рука"
            elif side == 'right':
                side_text = "правая рука"
        self.side_label.setText(f"Рука: {side_text}")

    def _on_complete(self, profile):
        self.progress_frame.hide()
        self.result_frame.show()
        self._last_profile = profile

        hand_side = profile.get('hand_side', 'unknown')
        if hand_side == 'left':
            side_human = "левая рука"
            other_side_human = "правую руку"
        elif hand_side == 'right':
            side_human = "правая рука"
            other_side_human = "левую руку"
        else:
            side_human = "не определена"
            other_side_human = None

        self.result_details.setText(
            f"ID клиента: {profile.get('client_id', 'N/A')}\n"
            f"Имя: {profile.get('name', '')}\n"
            f"Баланс: {profile.get('balance', 0):,.0f} ₽\n"
            f"Биометрия: Зарегистрирована\n"
            f"Рука: {side_human}"
        )
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🤚  Начать сканирование")

        # If система уверенно определила сторону — предложить добавить вторую
        if other_side_human:
            self.add_second_hand_btn.setText(f"Добавить {other_side_human}")
            self.add_second_hand_btn.show()
        else:
            self.add_second_hand_btn.hide()

    def _on_failed(self, message):
        self.progress_msg.setText(f"Ошибка: {message}")
        self.progress_msg.setStyleSheet("color: #E05050; font-size: 13px;")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🤚  Повторить сканирование")

    def _start_second_hand_registration(self):
        """Повторный запуск сканирования для второй руки с тем же именем клиента."""
        if not self._last_profile:
            return

        name = self._last_profile.get('name', '').strip()
        if not name:
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Сканирование второй руки...")
        self.progress_frame.show()
        self.result_frame.hide()
        self.add_second_hand_btn.hide()

        # Для второй руки используем тот же ввод баланса, но это можно скорректировать вручную
        balance = 5000
        try:
            balance = float(self.balance_input.text() or 5000)
        except ValueError:
            pass

        self._reg_thread = RegistrationThread(name)
        self._reg_thread._initial_balance = balance
        self._reg_thread.progress_changed.connect(self._on_progress)
        self._reg_thread.frame_ready.connect(self._on_frame)
        self._reg_thread.completed.connect(self._on_complete)
        self._reg_thread.failed.connect(self._on_failed)
        self._reg_thread.start()

    def _go_back(self):
        if self._reg_thread and self._reg_thread.isRunning():
            self._reg_thread.stop()
        self.main_window.show_home()

    def on_enter(self):
        self.name_input.clear()
        self.name_input.setStyleSheet("")
        self.progress_frame.hide()
        self.result_frame.hide()
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🤚  Начать сканирование")
