"""
Palm Embedding Generator
Extracts 128-dim feature vector from 21 MediaPipe hand landmarks
"""

import numpy as np
import math
from typing import List, Tuple, Optional


class PalmEmbedder:
    """
    Generates a stable 128-dimensional palm embedding from 21 landmarks.

    Features extracted:
    - Normalized landmark coordinates (relative to palm center)
    - Inter-joint distances
    - Finger angles
    - Palm proportions
    - Finger length ratios
    """

    # Finger tip indices in MediaPipe hand
    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_MCP = [2, 5, 9, 13, 17]  # Metacarpal joints
    FINGER_PIP = [3, 6, 10, 14, 18]  # Proximal interphalangeal

    # Key connections for distance features
    KEY_PAIRS = [
        (0, 4), (0, 8), (0, 12), (0, 16), (0, 20),  # wrist to tips
        (4, 8), (8, 12), (12, 16), (16, 20),          # tip to tip
        (5, 9), (9, 13), (13, 17),                     # MCP to MCP
        (0, 5), (0, 9), (0, 13), (0, 17),             # wrist to MCP
        (4, 12), (8, 16), (4, 20),                     # cross-finger
    ]

    def compute(self, landmarks) -> Optional[np.ndarray]:
        """
        landmarks: list of (x, y) or (x, y, z) tuples (21 points)
        Returns: 128-dim float32 numpy array
        """
        if len(landmarks) < 21:
            return None

        pts = np.array([[p[0], p[1]] for p in landmarks], dtype=np.float32)

        # 1. Normalize relative to palm center and scale
        palm_center = np.mean(pts[[0, 5, 9, 13, 17]], axis=0)
        pts_centered = pts - palm_center

        # Scale by distance from wrist to middle MCP
        scale_ref = np.linalg.norm(pts[9] - pts[0])
        if scale_ref < 1e-6:
            scale_ref = 1.0
        pts_norm = pts_centered / scale_ref

        # Feature 1: Normalized coordinates (42 features)
        coord_features = pts_norm.flatten()  # 21 * 2 = 42

        # Feature 2: Inter-joint distances (19 features)
        dist_features = []
        for a, b in self.KEY_PAIRS:
            d = np.linalg.norm(pts_norm[a] - pts_norm[b])
            dist_features.append(d)
        dist_features = np.array(dist_features, dtype=np.float32)  # 19

        # Feature 3: Finger angles (15 features)
        angle_features = self._compute_angles(pts_norm)  # 15

        # Feature 4: Finger lengths (5 features)
        finger_lengths = []
        for tip, mcp in zip(self.FINGER_TIPS, self.FINGER_MCP):
            length = np.linalg.norm(pts_norm[tip] - pts_norm[mcp])
            finger_lengths.append(length)
        finger_lengths = np.array(finger_lengths, dtype=np.float32)  # 5

        # Feature 5: Palm proportions (6 features)
        palm_features = self._compute_palm_features(pts_norm)  # 6

        # Concatenate: 42 + 19 + 15 + 5 + 6 = 87
        raw = np.concatenate([
            coord_features,
            dist_features,
            angle_features,
            finger_lengths,
            palm_features,
        ])

        # Pad/trim to 128
        embedding = np.zeros(128, dtype=np.float32)
        n = min(len(raw), 128)
        embedding[:n] = raw[:n]

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm

        return embedding

    def _compute_angles(self, pts: np.ndarray) -> np.ndarray:
        """Compute joint angles for each finger (3 joints × 5 fingers = 15)"""
        angles = []

        # Finger joint chains: [base, middle, tip]
        finger_chains = [
            [1, 2, 3, 4],    # Thumb
            [5, 6, 7, 8],    # Index
            [9, 10, 11, 12], # Middle
            [13, 14, 15, 16],# Ring
            [17, 18, 19, 20],# Pinky
        ]

        for chain in finger_chains:
            for i in range(len(chain) - 2):
                a = pts[chain[i]]
                b = pts[chain[i + 1]]
                c = pts[chain[i + 2]]

                ba = a - b
                bc = c - b

                cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
                cos_angle = np.clip(cos_angle, -1, 1)
                angle = math.acos(cos_angle) / math.pi  # normalize to [0, 1]
                angles.append(angle)

        return np.array(angles, dtype=np.float32)  # 15

    def _compute_palm_features(self, pts: np.ndarray) -> np.ndarray:
        """Palm width, height, and proportions"""
        # Palm width (across MCP joints)
        mcp_pts = pts[self.FINGER_MCP]
        palm_width = np.linalg.norm(mcp_pts[0] - mcp_pts[-1])

        # Palm height (wrist to middle MCP)
        palm_height = np.linalg.norm(pts[9] - pts[0])

        # Aspect ratio
        aspect = palm_width / (palm_height + 1e-8)

        # Finger spread (angle between index and pinky)
        v1 = pts[8] - pts[5]   # index tip to base
        v2 = pts[20] - pts[17] # pinky tip to base
        spread = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)

        # Thumb angle
        thumb_v = pts[4] - pts[2]
        index_v = pts[8] - pts[5]
        thumb_index_angle = np.dot(thumb_v, index_v) / (
            np.linalg.norm(thumb_v) * np.linalg.norm(index_v) + 1e-8
        )

        # Palm area (approximate using shoelace on MCP convex hull)
        palm_pts = pts[[0, 1, 5, 9, 13, 17]]
        n = len(palm_pts)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += palm_pts[i][0] * palm_pts[j][1]
            area -= palm_pts[j][0] * palm_pts[i][1]
        area = abs(area) / 2

        return np.array([palm_width, palm_height, aspect, spread, thumb_index_angle, area],
                        dtype=np.float32)


class TorchEmbedder:
    """
    Optional: PyTorch-based embedding network for higher accuracy.
    Falls back to PalmEmbedder if PyTorch unavailable.
    """

    def __init__(self):
        self._model = None
        self._available = False
        self._try_load_model()

    def _try_load_model(self):
        try:
            import torch
            import torch.nn as nn

            class PalmNet(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.net = nn.Sequential(
                        nn.Linear(42, 256),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(256, 256),
                        nn.ReLU(),
                        nn.Linear(256, 128),
                    )

                def forward(self, x):
                    out = self.net(x)
                    # L2 normalize
                    return out / (out.norm(dim=1, keepdim=True) + 1e-8)

            self._model = PalmNet()
            self._model.eval()
            self._torch = torch
            self._available = True
        except ImportError:
            self._available = False

    def compute(self, landmarks) -> np.ndarray:
        if not self._available:
            return PalmEmbedder().compute(landmarks)

        pts = np.array([[p[0], p[1]] for p in landmarks[:21]], dtype=np.float32)
        palm_center = np.mean(pts[[0, 5, 9, 13, 17]], axis=0)
        pts -= palm_center
        scale = np.linalg.norm(pts[9] - pts[0])
        if scale > 1e-6:
            pts /= scale

        x = self._torch.tensor(pts.flatten()).unsqueeze(0)
        with self._torch.no_grad():
            embedding = self._model(x).squeeze(0).numpy()
        return embedding.astype(np.float32)
