"""Original normalized min-sum BP with a reliability-guided GF(2) fallback.

No existing decoder implementation was consulted or imported. See docs/ALGORITHMS.md.
The global correction step is deliberately not labelled LSD or higher-order OSD.
"""

from functools import lru_cache
import numpy as np
import stim
from numba import njit, prange


def matrices(circuit):
    """Independent DEM mechanisms; merge only equal detector AND logical effects."""
    merged = {}
    for op in circuit.detector_error_model().flattened():
        if op.type != "error":
            continue
        detectors, observables = set(), set()
        for t in op.targets_copy():
            if t.is_relative_detector_id():
                detectors.symmetric_difference_update([t.val])
            elif t.is_logical_observable_id():
                observables.symmetric_difference_update([t.val])
        key = (tuple(sorted(detectors)), tuple(sorted(observables)))
        p = op.args_copy()[0]
        q = merged.get(key, 0.0)
        merged[key] = q * (1 - p) + p * (1 - q)
    h = np.zeros((circuit.num_detectors, len(merged)), dtype=np.uint8)
    logical = np.zeros((circuit.num_observables, len(merged)), dtype=np.uint8)
    for j, (ds, ls) in enumerate(merged):
        h[list(ds), j] = 1
        logical[list(ls), j] = 1
    return h, logical, np.asarray(list(merged.values()))


def binary(value, width):
    a = np.asarray(value)
    if a.ndim != 2 or a.shape[1] != width or not np.isin(a, (0, 1)).all():
        raise ValueError(
            "Expected a binary two-dimensional array with the specified width"
        )
    return np.ascontiguousarray(a, dtype=np.uint8)


@njit
def _linear_correction(masks, syndrome, order, n_checks):
    """Grow an independent column basis until its span contains the residual.

    Two uint64 words hold up to 128 detector bits. The second pair of words
    tracks which independent original columns make each basis vector.
    """
    basis = np.zeros((n_checks, 4), dtype=np.uint64)
    selected = np.empty(n_checks, dtype=np.int64)
    target = np.zeros(2, dtype=np.uint64)
    chosen = np.zeros(2, dtype=np.uint64)
    for i in range(n_checks):
        if syndrome[i]:
            target[i // 64] ^= np.uint64(1) << np.uint64(i % 64)
    rank = 0
    for j in order:
        if target[0] == 0 and target[1] == 0:
            break
        v0, v1 = masks[j, 0], masks[j, 1]
        c0, c1 = np.uint64(0), np.uint64(0)
        for i in range(n_checks):
            bit = np.uint64(1) << np.uint64(i % 64)
            active = (v0 if i < 64 else v1) & bit
            if not active:
                continue
            if basis[i, 0] != 0 or basis[i, 1] != 0:
                v0 ^= basis[i, 0]
                v1 ^= basis[i, 1]
                c0 ^= basis[i, 2]
                c1 ^= basis[i, 3]
            else:
                selected[rank] = j
                if rank < 64:
                    c0 ^= np.uint64(1) << np.uint64(rank)
                else:
                    c1 ^= np.uint64(1) << np.uint64(rank - 64)
                rank += 1
                basis[i] = np.array([v0, v1, c0, c1], dtype=np.uint64)
                # Pivots arrive in reliability order, not row order. A newly
                # added earlier pivot can reactivate a later existing pivot.
                # Reduce through the whole current basis in ascending row order.
                for row in range(n_checks):
                    active_bit = np.uint64(1) << np.uint64(row % 64)
                    if (target[0] if row < 64 else target[1]) & active_bit:
                        target[0] ^= basis[row, 0]
                        target[1] ^= basis[row, 1]
                        chosen[0] ^= basis[row, 2]
                        chosen[1] ^= basis[row, 3]
                break
    correction = np.zeros(len(order), dtype=np.uint8)
    for k in range(rank):
        if chosen[k // 64] & (np.uint64(1) << np.uint64(k % 64)):
            correction[selected[k]] = 1
    return correction, target[0] == 0 and target[1] == 0


@njit
def _one(s, check_ptr, variables, prior, masks, max_iter, scale, damping):
    n = len(prior)
    q = prior[variables].copy()
    r = np.zeros(len(variables))
    posterior = prior.copy()
    error = (posterior < 0).astype(np.uint8)
    for iteration in range(max_iter + 1):
        valid = True
        residual = s.copy()
        for i in range(len(s)):
            for k in range(check_ptr[i], check_ptr[i + 1]):
                residual[i] ^= error[variables[k]]
            if residual[i]:
                valid = False
        if valid:
            return error, True, True
        if iteration == max_iter:
            break
        for i in range(len(s)):
            start, stop = check_ptr[i], check_ptr[i + 1]
            smallest, second, argmin = 50.0, 50.0, -1
            sign = int(s[i])
            for k in range(start, stop):
                sign ^= int(q[k] < 0)
                a = abs(q[k])
                if a < smallest:
                    second, smallest, argmin = smallest, a, k
                elif a < second:
                    second = a
            for k in range(start, stop):
                magnitude = second if k == argmin else smallest
                r[k] = (-1.0 if sign ^ int(q[k] < 0) else 1.0) * scale * magnitude
        posterior = prior.copy()
        for k in range(len(variables)):
            posterior[variables[k]] += r[k]
        for k in range(len(variables)):
            message = posterior[variables[k]] - r[k]
            q[k] = damping * q[k] + (1 - damping) * max(-50.0, min(50.0, message))
        error = (posterior < 0).astype(np.uint8)
    # Preserve BP's reliable decisions, then flip a low-reliability set to fix H e = s.
    # Stable sorting in the Python wrapper isn't needed: ties use index explicitly.
    order = np.argsort(np.abs(posterior) + np.arange(n) * 1e-12)
    correction, solved = _linear_correction(masks, residual, order, len(s))
    return error ^ correction, False, solved


@njit(parallel=True)
def _batch(
    events,
    check_ptr,
    variables,
    prior,
    masks,
    logical,
    max_iter,
    scale,
    damping,
    return_errors,
):
    width = len(prior) if return_errors else logical.shape[0]
    out = np.zeros((len(events), width), dtype=np.uint8)
    converged = np.zeros(len(events), dtype=np.uint8)
    solved = np.zeros(len(events), dtype=np.uint8)
    for shot in prange(len(events)):
        e, bp_ok, ok = _one(
            events[shot], check_ptr, variables, prior, masks, max_iter, scale, damping
        )
        converged[shot], solved[shot] = bp_ok, ok
        if return_errors:
            out[shot] = e
        else:
            for i in range(logical.shape[0]):
                bit = np.uint8(0)
                for j in range(len(e)):
                    bit ^= logical[i, j] & e[j]
                out[shot, i] = bit
    return out, converged, solved


class BPDecoder:
    def __init__(self, h, logical, probabilities, max_iter=30, scale=0.8, damping=0.2):
        raw = np.asarray(h)
        if raw.ndim != 2 or not 1 <= raw.shape[0] <= 128:
            raise ValueError("Supports 1 to 128 detectors")
        self.h = binary(raw, raw.shape[1])
        self.logical = binary(logical, raw.shape[1])
        p = np.asarray(probabilities, dtype=float)
        if (
            p.shape != (raw.shape[1],)
            or not np.isfinite(p).all()
            or np.any((p <= 0) | (p >= 1))
        ):
            raise ValueError(
                "BP requires finite probabilities strictly between 0 and 1"
            )
        if (
            not isinstance(max_iter, int)
            or max_iter < 0
            or not 0 < scale <= 1
            or not 0 <= damping < 1
        ):
            raise ValueError("Invalid BP parameters")
        self.max_iter, self.scale, self.damping = max_iter, scale, damping
        self.prior = np.log(
            (1 - np.clip(p, 1e-12, 1 - 1e-12)) / np.clip(p, 1e-12, 1 - 1e-12)
        )
        rows, cols = np.nonzero(self.h)
        self.variables = cols.astype(np.int64)
        self.ptr = np.r_[0, np.cumsum(np.bincount(rows, minlength=len(self.h)))].astype(
            np.int64
        )
        self.masks = np.zeros((raw.shape[1], 2), dtype=np.uint64)
        for i, j in zip(rows, cols):
            self.masks[j, i // 64] |= np.uint64(1) << np.uint64(i % 64)
        self.last_stats = {}

    def _run(self, events, return_errors):
        events = binary(events, len(self.h))
        out, converged, solved = _batch(
            events,
            self.ptr,
            self.variables,
            self.prior,
            self.masks,
            self.logical,
            self.max_iter,
            self.scale,
            self.damping,
            return_errors,
        )
        if not solved.all():
            raise ValueError("Syndrome is outside the span of H")
        self.last_stats = {
            "shots": len(events),
            "bp_converged": int(converged.sum()),
            "linear_fallback": int((1 - converged).sum()),
        }
        return out

    def errors(self, events):
        return self._run(events, True)

    def predict(self, events):
        return self._run(events, False)


@lru_cache(maxsize=2)
def _state(circuit_text):
    return BPDecoder(*matrices(stim.Circuit(circuit_text)))


def decode(circuit: stim.Circuit, detector_events: np.ndarray) -> np.ndarray:
    return _state(str(circuit)).predict(detector_events)
