"""Portable NumPy inference for the team's two-layer ReLU network."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import numpy as np
import stim


def fingerprint(circuit):
    return sha256(str(circuit).encode()).hexdigest()


class MLP:
    def __init__(self, w0, b0, w1, b1):
        self.w0, self.b0, self.w1, self.b1 = (
            np.asarray(x, dtype=np.float32) for x in (w0, b0, w1, b1)
        )
        if (
            self.w0.ndim != 2
            or self.w1.ndim != 2
            or self.b0.shape != (self.w0.shape[1],)
            or self.w1.shape[0] != self.w0.shape[1]
            or self.b1.shape != (self.w1.shape[1],)
        ):
            raise ValueError("Invalid network shapes")
        if not all(np.isfinite(x).all() for x in (self.w0, self.b0, self.w1, self.b1)):
            raise ValueError("Nonfinite network weights")

    @classmethod
    def load(cls, path, circuit_hash):
        with np.load(path, allow_pickle=False) as f:
            if str(f["circuit_hash"]) != circuit_hash:
                raise ValueError("Circuit fingerprint mismatch")
            return cls(f["w0"], f["b0"], f["w1"], f["b1"])

    def logits(self, events):
        a = np.asarray(events)
        if a.ndim != 2 or a.shape[1] != len(self.w0) or not np.isin(a, (0, 1)).all():
            raise ValueError("Invalid detector array")
        return (
            np.maximum(a.astype(np.float32) @ self.w0 + self.b0, 0) @ self.w1 + self.b1
        )

    def predict(self, events):
        return (self.logits(events) > 0).astype(np.uint8)


@lru_cache(maxsize=2)
def _model(key):
    return MLP.load(Path(__file__).parent / "models" / f"{key}.npz", key)


def decode(circuit: stim.Circuit, detector_events: np.ndarray) -> np.ndarray:
    return _model(fingerprint(circuit)).predict(detector_events)
