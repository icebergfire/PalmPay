"""
Centralized configuration for biometric thresholds and timeouts.
"""

# Recognition thresholds
SIMILARITY_THRESHOLD = 0.85  # cosine similarity for palm embeddings
MIN_MARGIN = 0.03            # minimum gap between best and second-best match

# Liveness detector
LIVENESS_MIN_MOVEMENT_SCORE = 0.015  # minimum finger movement
LIVENESS_MIN_FRAMES = 15             # frames needed for liveness decision
LIVENESS_MOTION_WINDOW = 20          # window of frames to track movement

# Scan / UI behaviour (desktop)
PALM_TIMEOUT_SEC = 8.0  # seconds to wait for open palm after liveness
