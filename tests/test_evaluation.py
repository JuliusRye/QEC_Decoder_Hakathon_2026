import importlib.util
from pathlib import Path
import unittest
import numpy as np
import stim

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location(
        "evaluation", ROOT / "scripts/evaluate.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class EvaluationTests(unittest.TestCase):
    def test_mutating_the_circuit_is_rejected(self):
        ev = module()
        circuit = stim.Circuit(
            "R 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]"
        )
        events = np.zeros((2, 1), dtype=bool)

        def mutate(c, d):
            c.append("X", [0])
            return np.zeros((2, 1), dtype=np.uint8)

        with self.assertRaises(ValueError):
            ev.measure(mutate, circuit, events, events, 1)

    def test_bitwise_metric_and_invalid_values_before_conversion(self):
        ev = module()

        class Circuit:
            num_observables = 4

        events = np.zeros((2, 1), dtype=bool)
        labels = np.array([[1, 1, 0, 0], [0, 0, 0, 0]], dtype=bool)
        result, pred = ev.measure(
            lambda c, d: np.zeros((len(d), 4), dtype=np.uint8),
            Circuit(),
            events,
            labels,
            2,
        )
        self.assertEqual(result["ler"], 0.25)
        with self.assertRaises(ValueError):
            ev.measure(lambda c, d: np.full((2, 4), 0.5), Circuit(), events, labels, 1)
        with self.assertRaises(ValueError):
            ev.measure(lambda c, d: np.zeros((2, 1)), Circuit(), events, labels, 1)

    def test_nondeterminism_and_mutating_input_are_rejected(self):
        ev = module()

        class Circuit:
            num_observables = 1

        events = np.zeros((2, 1), dtype=bool)
        labels = events.copy()
        calls = []

        def randomish(c, d):
            calls.append(1)
            return np.full((2, 1), len(calls) % 2)

        with self.assertRaises(ValueError):
            ev.measure(randomish, Circuit(), events, labels, 2)

        def mutate(c, d):
            d[0, 0] = 1
            return d

        with self.assertRaises(ValueError):
            ev.measure(mutate, Circuit(), events, labels, 1)


if __name__ == "__main__":
    unittest.main()
