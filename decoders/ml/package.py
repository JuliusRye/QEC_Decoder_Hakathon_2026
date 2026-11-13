"""Package only complete, hash-verified X/Z exports; never overwrite an archive."""

from hashlib import sha256
import json
from pathlib import Path
import zipfile
import stim


def package(folder: Path, circuits: Path, output: Path):
    paths = [folder / name for name in ("decoder.py", "requirements.txt", "train.py")]
    for basis in "XZ":
        circuit = stim.Circuit.from_file(circuits / f"{basis}_circuit.stim")
        key = sha256(str(circuit).encode()).hexdigest()
        weights = folder / "models" / f"{key}.npz"
        record = weights.with_suffix(".json")
        data = json.loads(record.read_text())
        if (
            data["circuit_hash"] != key
            or data["weights_sha256"] != sha256(weights.read_bytes()).hexdigest()
        ):
            raise ValueError(f"Unverified {basis} model export")
        paths.extend([weights, record])
    # Read every input before creating anything; incomplete candidates leave no ZIP.
    contents = {str(path.relative_to(folder)): path.read_bytes() for path in paths}
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    return output
