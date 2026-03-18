"""
Palm Recognition - MediaPipe Hands + embedding comparison
"""

import json
import math
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.config import MIN_MARGIN, SIMILARITY_THRESHOLD


class PalmRecognizer:
    """
    Uses MediaPipe Hands to detect 21 landmarks,
    extract features and compare palm embeddings.
    """

    SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD
    MIN_MARGIN = MIN_MARGIN  # минимальный разрыв между 1-м и 2-м кандидатом

    # Palm outline zone (normalized, center of frame)
    ZONE_X1, ZONE_Y1 = 0.34, 0.19
    ZONE_X2, ZONE_Y2 = 0.66, 0.81

    def __init__(self):
        self._mp_hands = None
        self._hands = None
        self._db = None
        self._initialized = False
        self._init_mediapipe()

    def _init_mediapipe(self):
        try:
            import mediapipe as mp
            self._mp_hands = mp.solutions.hands
            self._hands = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5
            )
            self._initialized = True
        except ImportError:
            # MediaPipe not available - use mock
            self._initialized = False
        except Exception:
            self._initialized = False

    @staticmethod
    def _infer_side(results) -> str:
        """
        Infer hand side (left/right) from MediaPipe handedness.
        Returns 'left', 'right' or 'unknown'.
        """
        try:
            if results.multi_handedness:
                handed = results.multi_handedness[0].classification[0].label.lower()
                if handed in ("left", "right"):
                    return handed
        except Exception:
            pass
        return "unknown"

    @staticmethod
    def _classify_pose(landmarks_3d: List[Tuple[float, float, float]]) -> str:
        """
        Roughly classify hand pose based on fingertip extension.
        Returns 'palm' when fingers are extended, otherwise 'unknown'.
        """
        if not landmarks_3d or len(landmarks_3d) < 21:
            return "unknown"

        # Wrist is landmark 0, fingertips are 4, 8, 12, 16, 20
        wrist = np.array(landmarks_3d[0][:2], dtype=np.float32)
        tip_indices = [4, 8, 12, 16, 20]
        tips = np.array([landmarks_3d[i][:2] for i in tip_indices], dtype=np.float32)

        # Distances from wrist to tips
        dists = np.linalg.norm(tips - wrist, axis=1)
        mean_dist = float(np.mean(dists))

        # Spread of fingertips (open palm has larger spread)
        spread = float(np.max(dists) - np.min(dists))

        # Thresholds tuned empirically for normalized coordinates
        if mean_dist > 0.18 and spread > 0.05:
            return "palm"

        return "unknown"

    def detect_hands(self, frame) -> Optional[Dict]:
        """
        Detect hand landmarks in frame.
        Returns dict with landmarks, or None.
        """
        if not self._initialized:
            return self._mock_detection()

        import cv2
        import mediapipe as mp

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)

        if not results.multi_hand_landmarks:
            return None

        hand_lm = results.multi_hand_landmarks[0]

        # Extract normalized coordinates (21 landmarks)
        landmarks_3d = [(lm.x, lm.y, lm.z) for lm in hand_lm.landmark]

        # Check if palm wrist (landmark 0) is in the scan zone
        wrist = landmarks_3d[0]
        palm_center_x = np.mean([landmarks_3d[i][0] for i in [0, 5, 9, 13, 17]])
        palm_center_y = np.mean([landmarks_3d[i][1] for i in [0, 5, 9, 13, 17]])

        in_zone = (self.ZONE_X1 < palm_center_x < self.ZONE_X2 and
                   self.ZONE_Y1 < palm_center_y < self.ZONE_Y2)

        side = self._infer_side(results)
        pose = self._classify_pose(landmarks_3d)

        return {
            'landmarks': [(lm.x, lm.y) for lm in hand_lm.landmark],
            'landmarks_3d': landmarks_3d,
            'in_zone': in_zone,
            'palm_center': (palm_center_x, palm_center_y),
            'side': side,
            'pose': pose,
        }

    def _mock_detection(self):
        """Simulate hand detection for demo mode"""
        import random
        import time

        # Occasionally "detect" a hand
        t = time.time()
        if math.sin(t * 0.5) > 0.3:
            # Generate mock 21 landmarks in/near the zone
            cx, cy = 0.5 + math.sin(t * 0.3) * 0.05, 0.5 + math.cos(t * 0.4) * 0.05
            landmarks = []
            # Approximate hand shape
            offsets = [
                (0, 0.15), (-0.05, 0.08), (-0.07, 0), (-0.08, -0.07), (-0.08, -0.13),
                (-0.04, -0.03), (-0.04, -0.12), (-0.04, -0.19), (-0.04, -0.24),
                (0, -0.04), (0, -0.14), (0, -0.22), (0, -0.28),
                (0.04, -0.03), (0.04, -0.12), (0.04, -0.19), (0.04, -0.24),
                (0.08, 0), (0.09, -0.08), (0.09, -0.15), (0.09, -0.20),
            ]
            for dx, dy in offsets:
                landmarks.append((cx + dx, cy + dy))

            return {
                'landmarks': landmarks,
                'landmarks_3d': [(x, y, 0) for x, y in landmarks],
                'in_zone': True,
                'palm_center': (cx, cy),
                'side': 'right',
                'pose': 'palm',
            }
        return None

    def extract_embedding(self, hand_data: Dict) -> Optional[np.ndarray]:
        """
        Extract a 128-dimensional palm embedding from hand data.
        """
        landmarks = hand_data.get('landmarks_3d') or hand_data.get('landmarks')
        if not landmarks or len(landmarks) < 21:
            return None

        from backend.embedding import PalmEmbedder
        embedder = PalmEmbedder()
        return embedder.compute(landmarks)

    def identify_user(self, hand_data: Dict) -> Optional[Dict]:
        """
        Compare current palm embedding to all registered users.
        Returns best match if above threshold.
        """
        embedding = self.extract_embedding(hand_data)
        if embedding is None:
            return None

        from backend.database import Database
        db = Database()
        users = db.get_all_users()

        if not users:
            return None

        best_match = None
        best_similarity = 0.0
        second_best_similarity = 0.0

        current_side = hand_data.get('side')

        for user in users:
            stored_emb = user.get('embedding')
            if not stored_emb:
                continue

            # If both current scan and stored profile have a known side,
            # require them to match (левая/правая рука не взаимозаменяемы).
            stored_side = user.get('hand_side')
            if (
                current_side in ('left', 'right')
                and stored_side in ('left', 'right')
                and current_side != stored_side
            ):
                continue

            stored = np.array(stored_emb, dtype=np.float32)
            sim = self._cosine_similarity(embedding, stored)
            if sim > best_similarity:
                # Сдвигаем предыдущий лучший как второй лучший
                second_best_similarity = best_similarity
                best_similarity = sim
                best_match = user
            elif sim > second_best_similarity:
                second_best_similarity = sim

        if best_match and best_similarity >= self.SIMILARITY_THRESHOLD:
            # Дополнительная защита: если разрыв между первым и вторым
            # кандидатом слишком маленький, считаем, что пользователь не найден.
            margin = best_similarity - second_best_similarity
            if margin < self.MIN_MARGIN:
                self._log_no_match(
                    hand_data,
                    best_similarity,
                    second_best_similarity,
                    reason="margin_too_small",
                )
                return None

            return {
                'client_id': best_match['client_id'],
                'name': best_match['name'],
                'similarity': float(best_similarity),
                'balance': best_match.get('balance', 0)
            }

        # Логируем спорные кейсы «пользователь не найден» для анализа
        self._log_no_match(
            hand_data,
            best_similarity,
            second_best_similarity,
            reason="below_threshold_or_no_match",
        )
        return None

    def _log_no_match(
        self,
        hand_data: Dict,
        best_similarity: float,
        second_best_similarity: float,
        reason: str,
    ) -> None:
        """
        Log ambiguous / no-match recognition cases to a file for later analysis.
        """
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logs_dir = os.path.join(base_dir, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            path = os.path.join(logs_dir, 'recognition_issues.log')

            record = {
                'ts': datetime.utcnow().isoformat() + 'Z',
                'reason': reason,
                'side': hand_data.get('side'),
                'pose': hand_data.get('pose'),
                'in_zone': bool(hand_data.get('in_zone')),
                'palm_center': hand_data.get('palm_center'),
                'best_similarity': float(best_similarity),
                'second_best_similarity': float(second_best_similarity),
                'margin': float(best_similarity - second_best_similarity),
                'threshold': float(self.SIMILARITY_THRESHOLD),
            }

            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception:
            # Никогда не роняем основной поток из-за логирования
            pass

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def __del__(self):
        if self._hands:
            self._hands.close()
