import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


class MLInferenceTests(unittest.TestCase):
    def test_exported_relu_network_has_hand_calculated_predictions(self):
        spec = importlib.util.spec_from_file_location(
            "ml", ROOT / "decoders/ml/decoder.py"
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "weights.npz"
            np.savez(
                p,
                w0=np.eye(2, dtype=np.float32),
                b0=np.zeros(2, dtype=np.float32),
                w1=np.array([[1, -1], [-1, 1]], dtype=np.float32),
                b1=np.zeros(2, dtype=np.float32),
                circuit_hash="fixture",
            )
            model = m.MLP.load(p, "fixture")
            np.testing.assert_array_equal(
                model.predict(np.array([[0, 0], [1, 0], [0, 1]], dtype=bool)),
                [[0, 0], [1, 0], [0, 1]],
            )
            self.assertEqual(model.predict(np.empty((0, 2), dtype=bool)).shape, (0, 2))
            with self.assertRaises(ValueError):
                m.MLP.load(p, "wrong circuit")
            with self.assertRaises(ValueError):
                model.predict(np.array([[2, 0]]))


if __name__ == "__main__":
    unittest.main()
