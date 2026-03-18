"""
Liveness Detection - Anti-spoofing
Detects finger movement and palm rotation across frames
"""

import time
from collections import deque
from typing import Dict, List, Optional

import numpy as np

from backend.config import (
    LIVENESS_MIN_FRAMES,
    LIVENESS_MIN_MOVEMENT_SCORE,
    LIVENESS_MOTION_WINDOW,
)


class LivenessDetector:
    """
    Anti-spoofing system that verifies liveness by:
    1. Detecting finger movement between frames
    2. Analyzing slight palm rotation
    3. Checking natural tremor/micro-movements
    """

    # Thresholds (configurable)
    MIN_MOVEMENT_SCORE = LIVENESS_MIN_MOVEMENT_SCORE
    MIN_FRAMES = LIVENESS_MIN_FRAMES
    MOTION_WINDOW = LIVENESS_MOTION_WINDOW

    def __init__(self):
        self._frame_history: deque = deque(maxlen=self.MOTION_WINDOW)
        self._timestamps: deque = deque(maxlen=self.MOTION_WINDOW)
        self._movement_scores: List[float] = []
        self._rotation_scores: List[float] = []
        self._is_live: Optional[bool] = None

    def add_frame(self, hand_data: Dict):
        """Add a detected hand frame for analysis"""
        landmarks = hand_data.get('landmarks', [])
        if not landmarks:
            return

        pts = np.array([[p[0], p[1]] for p in landmarks], dtype=np.float32)
        self._frame_history.append(pts)
        self._timestamps.append(time.time())

        if len(self._frame_history) >= 3:
            self._compute_movement()

    def _compute_movement(self):
        """Compute movement score between last two frames"""
        if len(self._frame_history) < 2:
            return

        prev = self._frame_history[-2]
        curr = self._frame_history[-1]

        # Focus on finger tips (indices 4, 8, 12, 16, 20)
        tip_indices = [4, 8, 12, 16, 20]
        if len(curr) > max(tip_indices):
            prev_tips = prev[tip_indices]
            curr_tips = curr[tip_indices]

            # Movement = mean displacement of finger tips
            displacement = np.linalg.norm(curr_tips - prev_tips, axis=1)
            movement = float(np.mean(displacement))
            self._movement_scores.append(movement)

            # Keep only recent scores
            if len(self._movement_scores) > self.MOTION_WINDOW:
                self._movement_scores.pop(0)

    def _compute_rotation(self):
        """Detect palm rotation from wrist and MCP positions"""
        if len(self._frame_history) < 5:
            return 0.0

        first = self._frame_history[0]
        last = self._frame_history[-1]

        if len(first) > 9 and len(last) > 9:
            # Palm axis: wrist (0) to middle MCP (9)
            v1 = first[9] - first[0]
            v2 = last[9] - last[0]

            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
            angle_change = 1.0 - float(np.clip(cos_angle, -1, 1))
            return angle_change
        return 0.0

    def is_live(self) -> bool:
        """
        Returns True if liveness is detected.
        Requires minimum movement across frames.
        """
        if len(self._frame_history) < self.MIN_FRAMES:
            return False  # Not enough data yet

        if not self._movement_scores:
            return False

        # Check for natural variation in movement (not static)
        recent_scores = self._movement_scores[-self.MIN_FRAMES:]
        mean_movement = np.mean(recent_scores)
        movement_variance = np.std(recent_scores)

        # Live hand should have:
        # - Some movement (tremor, micro-adjustments)
        # - Some variation (not perfectly static)
        rotation = self._compute_rotation()

        is_live = (
            mean_movement > self.MIN_MOVEMENT_SCORE or
            movement_variance > 0.005 or
            rotation > 0.01
        )

        self._is_live = is_live
        return is_live

    def get_score(self) -> float:
        """Returns liveness confidence 0.0 - 1.0"""
        if not self._movement_scores:
            return 0.0

        recent = self._movement_scores[-10:] if len(self._movement_scores) >= 10 else self._movement_scores
        mean_mov = np.mean(recent)
        rotation = self._compute_rotation()

        # Score based on movement and rotation
        mov_score = min(mean_mov / 0.05, 1.0)
        rot_score = min(rotation / 0.05, 1.0)

        return float(max(mov_score, rot_score))

    def reset(self):
        """Reset detector state"""
        self._frame_history.clear()
        self._timestamps.clear()
        self._movement_scores.clear()
        self._rotation_scores.clear()
        self._is_live = None

    def get_status(self) -> Dict:
        """Get current liveness analysis status"""
        frames = len(self._frame_history)
        progress = min(frames / self.MIN_FRAMES, 1.0)
        score = self.get_score()

        return {
            'frames_collected': frames,
            'progress': progress,
            'liveness_score': score,
            'is_live': self.is_live() if frames >= self.MIN_FRAMES else None,
            'mean_movement': (
                float(np.mean(self._movement_scores))
                if self._movement_scores
                else 0.0
            ),
        }
