"""
Camera Manager - OpenCV camera handling
"""

import cv2
import numpy as np


class CameraManager:
    """Manages webcam capture with OpenCV"""

    def __init__(self, camera_index=0, width=640, height=480):
        self._cap = None
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._is_open = False

    def open(self) -> bool:
        """Open camera. Returns True if successful."""
        for idx in [self._camera_index, 1, 2, 0]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Test read
                ret, frame = cap.read()
                if ret and frame is not None:
                    self._cap = cap
                    self._is_open = True
                    return True
                cap.release()
        return False

    def read_frame(self):
        """Read a frame from the camera. Returns numpy array or None."""
        if not self._cap or not self._is_open:
            return None
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return None
        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        """Release the camera."""
        if self._cap:
            self._cap.release()
            self._cap = None
            self._is_open = False

    @property
    def is_open(self):
        return self._is_open

    def __del__(self):
        self.release()
