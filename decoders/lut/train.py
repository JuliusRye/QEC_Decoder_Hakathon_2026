"""Generate independent labelled training shots; never read Kaggle test labels."""

import argparse
from pathlib import Path
import json
import stim
from decoder import LookupTable, fingerprint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--circuits", type=Path, default=Path("data/kaggle"))
    parser.add_argument("--shots", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=20261113)
    args = parser.parse_args()
    if args.shots < 1:
        parser.error("--shots must be positive")
    target = Path(__file__).parent / "models"
    target.mkdir(exist_ok=True)
    for i, b in enumerate("XZ"):
        c = stim.Circuit.from_file(args.circuits / f"{b}_circuit.stim")
        d, y = c.compile_detector_sampler(seed=args.seed + i).sample(
            args.shots, separate_observables=True
        )
        key = fingerprint(c)
        model = LookupTable.fit(d, y, key)
        path = target / f"{key}.npz"
        if path.exists():
            raise FileExistsError(
                f"{path} exists; preserve or move the prior artifact explicitly"
            )
        model.save(path)
        record = {
            "basis": b,
            "shots": args.shots,
            "seed": args.seed + i,
            "circuit_hash": key,
            "unique_syndromes": len(model.keys),
            "table_payload_bytes": model.keys.nbytes + model.predictions.nbytes,
            "file_bytes": path.stat().st_size,
        }
        path.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps(record))
