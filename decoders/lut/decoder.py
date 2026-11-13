"""Sparse empirical per-bit MAP table; unseen syndromes predict zero."""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import numpy as np
import stim


def fingerprint(circuit):
    return sha256(str(circuit).encode()).hexdigest()


def packed(events, width):
    a = np.asarray(events)
    if a.ndim != 2 or a.shape[1] != width or not np.isin(a, (0, 1)).all():
        raise ValueError("Invalid detector array")
    nbytes = (width + 7) // 8
    if nbytes == 0:
        raise ValueError("At least one detector is required")
    return (
        np.ascontiguousarray(np.packbits(a.astype(bool), axis=1, bitorder="little"))
        .view(f"V{nbytes}")
        .reshape(-1)
    )


class LookupTable:
    def __init__(self, keys, predictions, width, circuit_hash):
        self.keys, self.predictions, self.width, self.circuit_hash = (
            keys,
            predictions,
            int(width),
            str(circuit_hash),
        )
        self.last_coverage = 0.0

    @classmethod
    def fit(cls, events, labels, circuit_hash):
        events = np.asarray(events)
        labels = np.asarray(labels)
        if (
            events.ndim != 2
            or labels.ndim != 2
            or len(events) != len(labels)
            or not len(events)
            or not np.isin(labels, (0, 1)).all()
        ):
            raise ValueError("Nonempty aligned binary training arrays required")
        keys, inverse, counts = np.unique(
            packed(events, events.shape[1]), return_inverse=True, return_counts=True
        )
        votes = np.stack(
            [
                np.bincount(inverse, weights=labels[:, i], minlength=len(keys))
                for i in range(labels.shape[1])
            ],
            axis=1,
        )
        # Each observable is a separate scored decision. Ties choose zero.
        predictions = (2 * votes > counts[:, None]).astype(np.uint8)
        return cls(keys, predictions, events.shape[1], circuit_hash)

    def predict(self, events):
        keys = packed(events, self.width)
        idx = np.searchsorted(self.keys, keys)
        found = idx < len(self.keys)
        found[found] &= self.keys[idx[found]] == keys[found]
        out = np.zeros((len(keys), self.predictions.shape[1]), dtype=np.uint8)
        out[found] = self.predictions[idx[found]]
        self.last_coverage = float(found.mean()) if len(keys) else 0.0
        return out

    def save(self, path):
        np.savez_compressed(
            path,
            keys=self.keys,
            predictions=self.predictions,
            width=self.width,
            circuit_hash=self.circuit_hash,
        )

    @classmethod
    def load(cls, path, circuit_hash):
        with np.load(path, allow_pickle=False) as f:
            if str(f["circuit_hash"]) != circuit_hash:
                raise ValueError("Circuit fingerprint mismatch")
            return cls(
                f["keys"], f["predictions"], int(f["width"]), str(f["circuit_hash"])
            )


@lru_cache(maxsize=2)
def _model(circuit_hash):
    return LookupTable.load(
        Path(__file__).parent / "models" / f"{circuit_hash}.npz", circuit_hash
    )


def decode(circuit: stim.Circuit, detector_events: np.ndarray) -> np.ndarray:
    return _model(fingerprint(circuit)).predict(detector_events)
