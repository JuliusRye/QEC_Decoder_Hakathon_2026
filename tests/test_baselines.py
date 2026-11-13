"""Hand-derived oracles, not comparisons with banned decoder implementations."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from functools import lru_cache
import numpy as np
import stim

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=None)
def load(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "decoders" / name / "decoder.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BeliefPropagationTests(unittest.TestCase):
    def test_deterministic_faults_are_rejected_instead_of_softened(self):
        bp = load("bp")
        h = np.ones((1, 1), dtype=np.uint8)
        for p in (0.0, 1.0):
            with self.assertRaises(ValueError):
                bp.BPDecoder(h, h, np.array([p]))

    def test_later_column_can_introduce_an_earlier_pivot(self):
        bp = load("bp")
        h = np.array([[0, 1], [1, 1]], dtype=np.uint8)
        decoder = bp.BPDecoder(
            h, np.eye(2, dtype=np.uint8), np.array([0.2, 0.1]), max_iter=0
        )
        np.testing.assert_array_equal(
            decoder.errors(np.array([[1, 0]], dtype=np.uint8)), [[1, 1]]
        )

    def test_fallback_crosses_the_64_bit_boundary(self):
        bp = load("bp")
        h = np.eye(70, dtype=np.uint8)
        decoder = bp.BPDecoder(h, h, np.full(70, 0.1), max_iter=0)
        s = np.zeros((1, 70), dtype=np.uint8)
        s[0, [63, 64, 69]] = 1
        np.testing.assert_array_equal(decoder.errors(s), s)

    def test_single_fault_is_identified_by_its_detector(self):
        bp = load("bp")
        decoder = bp.BPDecoder(
            np.eye(2, dtype=np.uint8),
            np.array([[1, 0], [0, 1]], dtype=np.uint8),
            np.array([0.1, 0.2]),
        )
        syndromes = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=np.uint8)
        np.testing.assert_array_equal(decoder.errors(syndromes), syndromes)

    def test_linear_fallback_preserves_the_observed_syndrome(self):
        bp = load("bp")
        # Columns 0+1 produce [1,0,1]. The third row is dependent.
        h = np.array([[1, 0, 1], [1, 1, 0], [0, 1, 1]], dtype=np.uint8)
        decoder = bp.BPDecoder(
            h, np.eye(3, dtype=np.uint8), np.array([0.1, 0.2, 0.3]), max_iter=0
        )
        s = np.array([[1, 0, 1], [0, 1, 1]], dtype=np.uint8)
        e = decoder.errors(s)
        np.testing.assert_array_equal((e @ h.T) % 2, s)
        with self.assertRaises(ValueError):
            decoder.errors(np.array([[1, 0, 0]], dtype=np.uint8))

    def test_standalone_circuit_contract_and_empty_batch(self):
        bp = load("bp")
        circuit = stim.Circuit(
            "X_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]"
        )
        s = np.array([[0], [1], [1], [0]], dtype=bool)
        np.testing.assert_array_equal(bp.decode(circuit, s), s)
        self.assertEqual(bp.decode(circuit, np.empty((0, 1), dtype=bool)).shape, (0, 1))
        with self.assertRaises(ValueError):
            bp.decode(circuit, np.array([[2]]))


class LookupTests(unittest.TestCase):
    def test_bitwise_majority_is_not_joint_label_mode(self):
        lut = load("lut")
        # 000 occurs twice (joint mode); each other label once. Each bit is 1 three times.
        d = np.zeros((5, 2), dtype=bool)
        y = np.array(
            [[0, 0, 0], [0, 0, 0], [1, 1, 0], [1, 0, 1], [0, 1, 1]], dtype=np.uint8
        )
        # Here every bit ties below 1/2: add 111 so each bit is 3/6 -> deterministic zero.
        model = lut.LookupTable.fit(d, y, "fixture")
        np.testing.assert_array_equal(
            model.predict(np.array([[0, 0], [1, 0]], dtype=bool)),
            [[0, 0, 0], [0, 0, 0]],
        )
        y = np.array(
            [[0, 0, 0], [0, 0, 0], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]],
            dtype=np.uint8,
        )
        model = lut.LookupTable.fit(np.zeros((6, 2), dtype=bool), y, "fixture")
        np.testing.assert_array_equal(
            model.predict(np.zeros((1, 2), dtype=bool)), [[0, 0, 0]]
        )
        # Unique joint mode is 000 (three votes), but each bit has six of eleven
        # votes for 1. A joint-mode implementation would fail this oracle.
        y = np.array(
            [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
                [1, 1, 0],
                [1, 1, 0],
                [1, 0, 1],
                [1, 0, 1],
                [0, 1, 1],
                [0, 1, 1],
                [1, 1, 1],
                [1, 1, 1],
            ],
            dtype=np.uint8,
        )
        model = lut.LookupTable.fit(np.zeros((11, 2), dtype=bool), y, "fixture")
        np.testing.assert_array_equal(
            model.predict(np.zeros((1, 2), dtype=bool)), [[1, 1, 1]]
        )
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "model.npz"
            model.save(p)
            restored = lut.LookupTable.load(p, "fixture")
            np.testing.assert_array_equal(
                restored.predict(np.zeros((1, 2), dtype=bool)), [[1, 1, 1]]
            )
            with self.assertRaises(ValueError):
                lut.LookupTable.load(p, "wrong circuit")
        self.assertEqual(model.predict(np.empty((0, 2), dtype=bool)).shape, (0, 3))


if __name__ == "__main__":
    unittest.main()
