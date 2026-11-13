"""Paired fresh-sample evaluation. Never submits predictions to Kaggle."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
import numpy as np
import stim

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def measure(decode, circuit, events, labels, runs):
    if runs < 1:
        raise ValueError("At least one timing run required")
    events = np.asarray(events)
    labels = np.asarray(labels)
    frozen = events.copy()
    first = None
    times = []
    for _ in range(runs):
        sample = frozen.copy()
        circuit_text = str(circuit) if isinstance(circuit, stim.Circuit) else None
        sample_circuit = circuit.copy() if circuit_text is not None else circuit
        start = time.perf_counter()
        raw = np.asarray(decode(sample_circuit, sample))
        times.append(time.perf_counter() - start)
        if circuit_text is not None and str(sample_circuit) != circuit_text:
            raise ValueError("Decoder mutated the circuit")
        if not np.array_equal(sample, frozen):
            raise ValueError("Decoder mutated detector inputs")
        if (
            raw.shape != (len(events), circuit.num_observables)
            or not np.isin(raw, (0, 1)).all()
        ):
            raise ValueError("Invalid decoder output")
        current = raw.astype(np.uint8)
        if first is None:
            first = current.copy()
        elif not np.array_equal(first, current):
            raise ValueError("Predictions differ between repeats")
    return {
        "ler": float(np.mean(first != labels)),
        "first_call_seconds": times[0],
        "seconds": times,
        "median_seconds": statistics.median(times),
        "prediction_sha256": digest(first.tobytes()),
    }, first


def load_decoder(folder):
    source = folder / "decoder.py"
    spec = importlib.util.spec_from_file_location("candidate_" + folder.name, source)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoders", nargs="+", default=["bp", "lut"])
    parser.add_argument("--circuits", type=Path, default=ROOT / "data/kaggle")
    parser.add_argument("--shots", type=int, default=2000, help="fresh shots per basis")
    parser.add_argument("--seed", type=int, default=719)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.shots < 1 or args.runs < 1:
        parser.error("shots and runs must be positive")
    # A failed run stays on disk and cannot be silently overwritten.
    args.out.mkdir(parents=True, exist_ok=False)
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "shots_per_basis": args.shots,
        "seed": args.seed,
        "runs": args.runs,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": {d.metadata["Name"]: d.version for d in metadata.distributions()},
        "git_commit": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
            ).strip()
        ),
        "sources": {},
        "bases": {},
    }
    candidates = {
        name: load_decoder(ROOT / "decoders" / name) for name in args.decoders
    }
    for name in candidates:
        folder = ROOT / "decoders" / name
        paths = sorted(folder.glob("*.py")) + sorted(folder.glob("*.txt"))
        paths += sorted((folder / "models").glob("*.npz"))
        paths += sorted((folder / "models").glob("*.json"))
        report["sources"][name] = {
            str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths
        }
        for p in paths:
            target = args.out / "source" / name / p.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    for i, b in enumerate("XZ"):
        circuit = stim.Circuit.from_file(args.circuits / f"{b}_circuit.stim")
        text = str(circuit)
        (args.out / f"{b}_circuit.stim").write_text(text)
        events, labels = circuit.compile_detector_sampler(seed=args.seed + i).sample(
            args.shots, separate_observables=True
        )
        np.savez_compressed(args.out / f"{b}_samples.npz", events=events, labels=labels)
        basis = {
            "circuit_sha256": digest(text.encode()),
            "events_sha256": digest(events.tobytes()),
            "labels_sha256": digest(labels.tobytes()),
            "zero_ler": float(labels.mean()),
            "candidates": {},
        }
        predictions = {}
        for name, module in candidates.items():
            result, predictions[name] = measure(
                module.decode, circuit, events, labels, args.runs
            )
            if name == "bp":
                result["diagnostics"] = module._state(text).last_stats
            if name == "lut":
                result["coverage"] = module._model(
                    module.fingerprint(circuit)
                ).last_coverage
            basis["candidates"][name] = result
            np.save(
                args.out / f"{b}_{name}_predictions.npy",
                predictions[name],
                allow_pickle=False,
            )
            print(b, name, json.dumps(result), flush=True)
        names = list(predictions)
        basis["paired_bit_counts"] = {}
        for a in range(len(names)):
            for j in range(a + 1, len(names)):
                left, right = names[a], names[j]
                le = predictions[left] != labels
                re = predictions[right] != labels
                basis["paired_bit_counts"][left + " vs " + right] = {
                    "left_only_wrong": int(np.sum(le & ~re)),
                    "right_only_wrong": int(np.sum(re & ~le)),
                    "both_wrong": int(np.sum(le & re)),
                }
        report["bases"][b] = basis
        (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Saved evidence to", args.out, flush=True)


if __name__ == "__main__":
    main()
