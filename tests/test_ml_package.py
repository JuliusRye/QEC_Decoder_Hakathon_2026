import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import stim

ROOT = Path(__file__).resolve().parents[1]


class MLPackageTests(unittest.TestCase):
    def test_missing_or_modified_basis_cannot_be_packaged(self):
        spec = importlib.util.spec_from_file_location(
            "mlpackage", ROOT / "decoders/ml/package.py"
        )
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            models = root / "models"
            models.mkdir()
            for name in ("decoder.py", "train.py", "requirements.txt"):
                (root / name).write_text("fixture")
            for i, b in enumerate("XZ"):
                circuit = stim.Circuit(
                    f"X_ERROR({0.1 + i * 0.1}) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]"
                )
                (root / f"{b}_circuit.stim").write_text(str(circuit))
                key = sha256(str(circuit).encode()).hexdigest()
                weight = models / f"{key}.npz"
                weight.write_bytes(b"fixture weights")
                if b == "X":
                    (models / f"{key}.json").write_text(
                        json.dumps(
                            {
                                "circuit_hash": key,
                                "weights_sha256": sha256(
                                    weight.read_bytes()
                                ).hexdigest(),
                            }
                        )
                    )
            out = root / "handin.zip"
            with self.assertRaises(FileNotFoundError):
                m.package(root, root, out)
            self.assertFalse(out.exists())
            meta = models / f"{key}.json"
            meta.write_text(
                json.dumps({"circuit_hash": key, "weights_sha256": "wrong"})
            )
            with self.assertRaises(ValueError):
                m.package(root, root, out)
            self.assertFalse(out.exists())
            meta.write_text(
                json.dumps(
                    {
                        "circuit_hash": key,
                        "weights_sha256": sha256(weight.read_bytes()).hexdigest(),
                    }
                )
            )
            m.package(root, root, out)
            with zipfile.ZipFile(out) as z:
                self.assertEqual(len(z.namelist()), 7)
            with self.assertRaises(FileExistsError):
                m.package(root, root, out)


if __name__ == "__main__":
    unittest.main()
