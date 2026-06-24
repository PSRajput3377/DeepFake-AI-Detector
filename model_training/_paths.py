"""Make `backend.app.ml.model` importable from the trainer.

Both the trainer and the inference backend share the same model
definition, so we add the project root to ``sys.path`` once and use the
canonical class from ``backend/app/ml/model.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for p in (str(BACKEND_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

# Re-export for convenience
from app.ml.model import DeepFakeDetector, ModelConfig, load_checkpoint  # noqa: E402

__all__ = ["DeepFakeDetector", "ModelConfig", "load_checkpoint", "PROJECT_ROOT"]
