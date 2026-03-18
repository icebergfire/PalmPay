"""
Scan Screen - Palm biometric scanning UI
"""

import math
import time

import cv2
import numpy as np
from PyQt5.QtCore import QMutex, QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter,
                         QPen, QPixmap, QFont)
from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QVBoxLayout, QWidget)

from backend.config import PALM_TIMEOUT_SEC


class CameraThread(QThread):
    frame_ready = pyqtSignal(object, object, float)  # frame, hand_data, similarity
    status_changed = pyqtSignal(str, str)  # message, color

    def __init__(self, mode='payment', parent=None):
        super().__init__(parent)
        self._running = False
        self.mode = mode
        self._mutex = QMutex()
        self._palm_timeout_sec = PALM_TIMEOUT_SEC

    def run(self):
        from backend.camera import CameraManager
        from backend.recognition import PalmRecognizer
        from backend.liveness import LivenessDetector

        camera = CameraManager()
        recognizer = PalmRecognizer()
        liveness = LivenessDetector()

        self._running = True
        self.status_changed.emit("Поместите ладонь в контур", "white")

        frame_count = 0
        last_emit = time.time()
        liveness_passed = False
        palm_wait_start = None

        if not camera.open():
            self.status_changed.emit("Камера недоступна — демо режим", "orange")
            # Demo mode: emit synthetic frames
            self._run_demo_mode()
            return

        try:
            while self._running:
                frame = camera.read_frame()
                if frame is None:
                    continue

                # Process with MediaPipe
                hand_data = recognizer.detect_hands(frame)
                similarity = 0.0
                status_msg = "Поместите ладонь в контур"
                status_color = "white"

                if hand_data and hand_data.get('in_zone'):
                    # Шаг 1: накапливаем данные для liveness
                    liveness.add_frame(hand_data)
                    frame_count += 1

                    pose = hand_data.get('pose')

                    # Обновляем прогресс по этапам до прохождения liveness
                    if not liveness_passed:
                        # Если ладонь согнута или повернута так, что поза не считается palm —
                        # сразу подсказываем пользователю.
                        if pose != 'palm':
                            status_msg = "Покажите открытую ладонь"
                            status_color = "#F0C040"
                        elif frame_count < 10:
                            status_msg = "Сканирование ладони..."
                            status_color = "#3B9EFF"
                        elif frame_count < 25:
                            status_msg = "Анализ биометрии и живости..."
                            status_color = "#F0C040"
                        else:
                            status_msg = "Проверка живости..."
                            status_color = "#F0C040"

                        # Как только liveness подтверждён — переходим в режим ожидания раскрытой ладони
                        if liveness.is_live():
                            liveness_passed = True
                            liveness_start_time = time.time()
                            palm_wait_start = time.time()
                            status_msg = "Ждём открытую ладонь"
                            status_color = "#3B9EFF"
                    else:
                        # Liveness уже пройден: ждём именно открытую ладонь
                        if pose == 'palm':
                            status_msg = "Поиск пользователя по биометрии..."
                            status_color = "#13A05A"

                            if self.mode == 'payment':
                                result = recognizer.identify_user(hand_data)
                                if result:
                                    similarity = result['similarity']
                                    self.frame_ready.emit(frame, hand_data, similarity)
                                    self.status_changed.emit(f"✓ Пользователь определён: {result['name']}", "#13A05A")
                                    self._recognized_user = result
                                    time.sleep(1.5)
                                    break
                                else:
                                    status_msg = "Пользователь не найден"
                                    status_color = "#E05050"
                                    # Слегка откатываемся, чтобы дать шанс повторить
                                    frame_count = max(20, frame_count)
                        else:
                            # Рука есть, живость подтверждена, но ладонь не раскрыта
                            status_msg = "Покажите открытую ладонь"
                            status_color = "#F0C040"
                            if palm_wait_start is None:
                                palm_wait_start = time.time()

                            # Таймаут ожидания раскрытой ладони
                            if time.time() - palm_wait_start > self._palm_timeout_sec:
                                self.status_changed.emit("Ладонь не распознана", "#E05050")
                                time.sleep(1.5)
                                break

                elif hand_data:
                    status_msg = "Расположите ладонь ровнее в контур"
                    status_color = "#F0C040"
                    frame_count = max(0, frame_count - 1)
                else:
                    frame_count = max(0, frame_count - 2)

                self.status_changed.emit(status_msg, status_color)

                now = time.time()
                if now - last_emit > 0.04:  # ~25fps
                    self.frame_ready.emit(frame, hand_data, similarity)
                    last_emit = now

        finally:
            camera.release()

    def _run_demo_mode(self):
        """Simulate scanning in demo mode without real camera"""
        import time
        steps = [
            (2.0, "Поместите ладонь в контур", "white"),
            (1.5, "Сканирование ладони...", "#3B9EFF"),
            (1.5, "Анализ биометрии...", "#F0C040"),
            (1.0, "Поиск пользователя...", "#13A05A"),
            (0.5, "✓ Пользователь определён", "#13A05A"),
        ]

        for duration, msg, color in steps:
            if not self._running:
                break
            self.status_changed.emit(msg, color)
            end_time = time.time() + duration
            while time.time() < end_time and self._running:
                # Emit synthetic frame
                demo_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # Add grid pattern
                for i in range(0, 640, 40):
                    cv2.line(demo_frame, (i, 0), (i, 480), (20, 25, 35), 1)
                for i in range(0, 480, 40):
                    cv2.line(demo_frame, (0, i), (640, i), (20, 25, 35), 1)
                self.frame_ready.emit(demo_frame, None, 0.0)
                time.sleep(0.04)

        if self._running and self.mode == 'payment':
            self.status_changed.emit("Нет зарегистрированных клиентов", "#E05050")
            self._recognized_user = None

    def stop(self):
        self._running = False
        self.wait(2000)

    def get_recognized_user(self):
        return getattr(self, '_recognized_user', None)


class PalmOverlayWidget(QWidget):
    """Widget that renders the camera feed with palm overlay"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self._frame = None
        self._hand_data = None
        self._scan_line_y = 0
        self._scan_direction = 1
        self._outline_color = QColor(59, 158, 255, 180)
        self._scan_progress = 0.0
        self._hand_in_zone = False

        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(30)

    def _animate(self):
        self._scan_line_y += 4 * self._scan_direction
        h = self.height()
        zone_top = int(h * 0.15)
        zone_bot = int(h * 0.85)
        if self._scan_line_y > zone_bot:
            self._scan_direction = -1
        elif self._scan_line_y < zone_top:
            self._scan_direction = 1
        self.update()

    def update_frame(self, frame, hand_data, similarity):
        self._frame = frame
        self._hand_data = hand_data
        self._hand_in_zone = bool(hand_data and hand_data.get('in_zone'))
        if self._hand_in_zone:
            self._outline_color = QColor(19, 160, 90, 200)
        else:
            self._outline_color = QColor(59, 158, 255, 180)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(8, 12, 20))

        # Draw camera frame
        if self._frame is not None:
            frame_rgb = cv2.cvtColor(self._frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (w, h))
            qimg = QImage(frame_rgb.data, w, h, w * 3, QImage.Format_RGB888)
            painter.setOpacity(0.7)
            painter.drawImage(0, 0, qimg)
            painter.setOpacity(1.0)

        # Dark vignette overlay
        self._draw_vignette(painter, w, h)

        # Palm outline zone
        self._draw_palm_outline(painter, w, h)

        # Scanning line
        self._draw_scan_line(painter, w, h)

        # Hand skeleton if detected
        if self._hand_data and self._hand_data.get('landmarks'):
            self._draw_skeleton(painter, w, h)

        # Corner decorations
        self._draw_corners(painter, w, h)

    def _draw_vignette(self, painter, w, h):
        from PyQt5.QtGui import QRadialGradient
        grad = QRadialGradient(w // 2, h // 2, max(w, h) // 2)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 0, 0, 180))
        painter.fillRect(0, 0, w, h, QBrush(grad))

    def _draw_palm_outline(self, painter, w, h):
        cx, cy = w // 2, h // 2
        ow, oh = int(w * 0.32), int(h * 0.62)

        # Outer glow
        for i in range(3, 0, -1):
            alpha = 40 - i * 10
            pen = QPen(QColor(self._outline_color.red(), self._outline_color.green(),
                              self._outline_color.blue(), alpha))
            pen.setWidth(i * 3)
            painter.setPen(pen)
            painter.drawRoundedRect(cx - ow // 2 - i*3, cy - oh // 2 - i*3,
                                    ow + i*6, oh + i*6, 30, 30)

        # Main outline
        pen = QPen(self._outline_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cx - ow // 2, cy - oh // 2, ow, oh, 26, 26)

        # Inner subtle fill
        fill_color = QColor(self._outline_color.red(), self._outline_color.green(),
                            self._outline_color.blue(), 15)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(cx - ow // 2, cy - oh // 2, ow, oh, 26, 26)

        # Finger guides (5 small dots at top)
        painter.setPen(Qt.NoPen)
        finger_y = cy - oh // 2 - 12
        for i in range(5):
            fx = cx - ow // 2 + int(ow * (i + 1) / 6)
            dot_color = QColor(self._outline_color.red(), self._outline_color.green(),
                               self._outline_color.blue(), 120)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(fx - 5, finger_y - 5, 10, 10)

    def _draw_scan_line(self, painter, w, h):
        if not self._hand_in_zone:
            return
        cx = w // 2
        ow = int(w * 0.32)
        cy = h // 2
        oh = int(h * 0.62)
        zone_top = cy - oh // 2
        zone_bot = cy + oh // 2

        sy = max(zone_top, min(zone_bot, self._scan_line_y))

        # Glow line
        grad = QLinearGradient(cx - ow // 2, sy, cx + ow // 2, sy)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.3, QColor(59, 158, 255, 180))
        grad.setColorAt(0.5, QColor(120, 200, 255, 240))
        grad.setColorAt(0.7, QColor(59, 158, 255, 180))
        grad.setColorAt(1, QColor(0, 0, 0, 0))

        pen = QPen(QBrush(grad), 2)
        painter.setPen(pen)
        painter.drawLine(cx - ow // 2, sy, cx + ow // 2, sy)

        # Glow halo
        for i in range(5):
            alpha = 30 - i * 6
            pen2 = QPen(QColor(59, 158, 255, alpha))
            pen2.setWidth(i * 2 + 1)
            painter.setPen(pen2)
            painter.drawLine(cx - ow // 2, sy, cx + ow // 2, sy)

    def _draw_skeleton(self, painter, w, h):
        lm = self._hand_data.get('landmarks', [])
        if not lm:
            return

        # MediaPipe connections
        connections = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (5,9),(9,10),(10,11),(11,12),
            (9,13),(13,14),(14,15),(15,16),
            (13,17),(17,18),(18,19),(19,20),
            (0,17)
        ]

        pen = QPen(QColor(59, 158, 255, 160))
        pen.setWidth(2)
        painter.setPen(pen)

        for a, b in connections:
            if a < len(lm) and b < len(lm):
                x1, y1 = int(lm[a][0] * w), int(lm[a][1] * h)
                x2, y2 = int(lm[b][0] * w), int(lm[b][1] * h)
                painter.drawLine(x1, y1, x2, y2)

        painter.setPen(Qt.NoPen)
        for i, (lx, ly) in enumerate(lm):
            x, y = int(lx * w), int(ly * h)
            if i == 0:
                painter.setBrush(QBrush(QColor(255, 200, 50, 220)))
                painter.drawEllipse(x - 5, y - 5, 10, 10)
            elif i in [4, 8, 12, 16, 20]:
                painter.setBrush(QBrush(QColor(19, 160, 90, 220)))
                painter.drawEllipse(x - 4, y - 4, 8, 8)
            else:
                painter.setBrush(QBrush(QColor(59, 158, 255, 180)))
                painter.drawEllipse(x - 3, y - 3, 6, 6)

    def _draw_corners(self, painter, w, h):
        size = 24
        thickness = 3
        color = QColor(59, 158, 255, 140)
        pen = QPen(color)
        pen.setWidth(thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        corners = [
            (20, 20, 1, 1),
            (w - 20, 20, -1, 1),
            (20, h - 20, 1, -1),
            (w - 20, h - 20, -1, -1),
        ]
        for cx, cy, dx, dy in corners:
            painter.drawLine(cx, cy, cx + dx * size, cy)
            painter.drawLine(cx, cy, cx, cy + dy * size)


class ScanScreen(QWidget):
    scan_complete = pyqtSignal(dict)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._camera_thread = None
        self._mode = 'payment'
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

        # Camera view
        self.overlay = PalmOverlayWidget()
        content.addWidget(self.overlay, 3)

        # Right panel
        right_panel = self._build_right_panel()
        content.addWidget(right_panel, 1)

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
        back_btn.setObjectName("secondary")
        back_btn.setFixedSize(100, 34)
        back_btn.clicked.connect(self._go_back)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                color: #6B7A8F;
                font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.1); color: #E8EDF5; }
        """)
        layout.addWidget(back_btn)

        self.screen_title = QLabel("Сканирование ладони")
        self.screen_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: 600;")
        layout.addWidget(self.screen_title, 0, Qt.AlignCenter)

        layout.addStretch()

        badge = QLabel("● LIVE")
        badge.setStyleSheet("color: #13A05A; font-size: 12px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(badge)

        return bar

    def _build_right_panel(self):
        panel = QFrame()
        panel.setFixedWidth(320)
        panel.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.02);
                border-left: 1px solid rgba(255,255,255,0.06);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 36, 28, 36)
        layout.setSpacing(20)

        # Status section
        status_header = QLabel("СТАТУС СКАНИРОВАНИЯ")
        status_header.setStyleSheet("color: #2A3545; font-size: 10px; letter-spacing: 2px; font-weight: 600;")
        layout.addWidget(status_header)

        self.status_label = QLabel("Поместите ладонь в контур")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 500; line-height: 1.4;")
        layout.addWidget(self.status_label)

        # Hand side label
        self.side_label = QLabel("Рука: не определена")
        self.side_label.setStyleSheet("color: #4A5568; font-size: 12px;")
        layout.addWidget(self.side_label)

        # Progress steps
        layout.addSpacing(20)
        steps_header = QLabel("ЭТАПЫ ПРОВЕРКИ")
        steps_header.setStyleSheet("color: #2A3545; font-size: 10px; letter-spacing: 2px; font-weight: 600;")
        layout.addWidget(steps_header)

        self.steps = []
        step_texts = ["Обнаружение руки", "Анализ биометрии", "Антиспуфинг", "Идентификация"]
        for text in step_texts:
            step_frame = QFrame()
            step_frame.setStyleSheet("QFrame { background: rgba(255,255,255,0.03); border-radius: 8px; }")
            step_layout = QHBoxLayout(step_frame)
            step_layout.setContentsMargins(14, 10, 14, 10)

            dot = QLabel("○")
            dot.setStyleSheet("color: #2A3545; font-size: 14px;")
            step_layout.addWidget(dot)

            lbl = QLabel(text)
            lbl.setStyleSheet("color: #4A5568; font-size: 13px;")
            step_layout.addWidget(lbl)
            step_layout.addStretch()

            layout.addWidget(step_frame)
            self.steps.append((dot, lbl))

        layout.addStretch()

        # Instructions
        instr_frame = QFrame()
        instr_frame.setStyleSheet("""
            QFrame {
                background: rgba(59,158,255,0.05);
                border: 1px solid rgba(59,158,255,0.15);
                border-radius: 12px;
            }
        """)
        instr_layout = QVBoxLayout(instr_frame)
        instr_layout.setContentsMargins(16, 14, 16, 14)

        instr_title = QLabel("Инструкции")
        instr_title.setStyleSheet("color: #3B9EFF; font-size: 12px; font-weight: 600;")
        instr_layout.addWidget(instr_title)

        instructions = [
            "• Держите ладонь открытой",
            "• Расстояние 20–40 см",
            "• Хорошее освещение",
            "• Слегка двигайте пальцами",
        ]
        for instr in instructions:
            lbl = QLabel(instr)
            lbl.setStyleSheet("color: #4A6080; font-size: 11px;")
            instr_layout.addWidget(lbl)

        layout.addWidget(instr_frame)

        # Cancel button
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self._go_back)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                color: #6B7A8F;
                font-size: 14px;
                padding: 12px;
            }
            QPushButton:hover { background: rgba(220,50,50,0.1); color: #E05050; border-color: rgba(220,50,50,0.3); }
        """)
        layout.addWidget(cancel_btn)

        return panel

    def set_mode(self, mode, title=None):
        self._mode = mode
        if title:
            self.screen_title.setText(title)

    def on_enter(self):
        self._reset_steps()
        self._start_camera()

    def _reset_steps(self):
        for dot, lbl in self.steps:
            dot.setText("○")
            dot.setStyleSheet("color: #2A3545; font-size: 14px;")
            lbl.setStyleSheet("color: #4A5568; font-size: 13px;")

    def _activate_step(self, index):
        for i, (dot, lbl) in enumerate(self.steps):
            if i < index:
                dot.setText("✓")
                dot.setStyleSheet("color: #13A05A; font-size: 14px;")
                lbl.setStyleSheet("color: #6B7A8F; font-size: 13px;")
            elif i == index:
                dot.setText("●")
                dot.setStyleSheet("color: #3B9EFF; font-size: 14px;")
                lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600;")

    def _start_camera(self):
        if self._camera_thread and self._camera_thread.isRunning():
            self._camera_thread.stop()

        self._camera_thread = CameraThread(mode=self._mode)
        self._camera_thread.frame_ready.connect(self._on_frame)
        self._camera_thread.status_changed.connect(self._on_status)
        self._camera_thread.start()

    def _on_frame(self, frame, hand_data, similarity):
        self.overlay.update_frame(frame, hand_data, similarity)

        if hand_data:
            self._activate_step(0)
            if hand_data.get('in_zone'):
                self._activate_step(1)

        # Update hand side label
        side_text = "не определена"
        if hand_data:
            side = hand_data.get('side')
            if side == 'left':
                side_text = "левая рука"
            elif side == 'right':
                side_text = "правая рука"
        self.side_label.setText(f"Рука: {side_text}")

    def _on_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: 500;")

        if "Анализ" in message:
            self._activate_step(2)
        elif "Поиск" in message:
            self._activate_step(3)
        elif "определён" in message or "Пользователь" in message:
            self._activate_step(4)
            QTimer.singleShot(1500, self._handle_recognition_complete)

    def _handle_recognition_complete(self):
        if self._camera_thread:
            user = self._camera_thread.get_recognized_user()
            if user:
                self.scan_complete.emit(user)
                if self._mode == 'payment':
                    self.main_window.payment_screen.set_user(user)
                    self.main_window.show_payment()
                elif self._mode == 'balance':
                    self.main_window.balance_screen.set_user(user)
                    self.main_window.show_balance()

    def _go_back(self):
        if self._camera_thread and self._camera_thread.isRunning():
            self._camera_thread.stop()
        self.main_window.show_home()

    def hideEvent(self, event):
        if self._camera_thread and self._camera_thread.isRunning():
            self._camera_thread.stop()
        super().hideEvent(event)
