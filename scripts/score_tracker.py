"""Local Kaggle-style score tracker. Never submits anything to Kaggle.

Mirrors the leaderboard metric as documented in the Kaggle Overview capture
(docs/sources/kaggle/2026-11-13/overview-0715.md, "Evaluation"):

* Leaderboard score = mean absolute error between predicted and true flips over every
  shot and all four observables (= bitwise LER for 0/1 predictions). Columns are matched
  BY POSITION (id, L0, L1, L2, L3), as Kaggle does. Lower is better.
* Kaggle splits test.csv into ~30% Public / ~70% Private rows; the real split is hidden,
  so we simulate it with a fixed random permutation (seeded) and report both parts.
* Final ranking (top 10 only): LER * max(1, t / t_cap) ** alpha. The constants conflict
  between sources (docs/COMPETITION.md), so both sets are reported. Local runtime is NOT
  organizer-machine runtime.

Two modes:
  # Run a decoder folder on labelled rows (default data/train/train.csv) and score it
  python scripts/score_tracker.py --decoder decoders/bp --shots 10000 --name bp-baseline
  # Score an existing submission-format CSV against a labelled CSV, exactly by position
  python scripts/score_tracker.py --predictions runs/bp-full-local.csv --name bp-full

Each run appends one row to runs/scoreboard.csv (git-ignored) and prints the scoreboard.
"""

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import stim

ROOT = Path(__file__).resolve().parents[1]
SCOREBOARD = ROOT / "runs" / "scoreboard.csv"
# (label, t_cap seconds, alpha) - see docs/COMPETITION.md "Unresolved source conflicts".
SPEED_RULES = [("overview", 15.4, 0.2), ("rules6", 0.56, 0.07)]
PUBLIC_FRACTION = 0.30
FIELDS = ["at", "name", "commit", "source", "rows", "score", "score_se", "public", "private",
          "X", "Z", "zero_ler", "seconds", "final_overview", "final_rules6"]


def load_labelled(path):
    """Read a Kaggle-format CSV with labels: id, basis, D0..D69, L0..L3."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    det = [i for i, h in enumerate(header) if h.startswith("D")]
    obs = [header.index(f"L{j}") for j in range(4)]
    ids = np.array([r[0] for r in rows])
    basis = np.array([r[header.index("basis")] for r in rows])
    events = np.array([[r[i] == "1" for i in det] for r in rows], dtype=bool)
    labels = np.array([[int(r[i]) for i in obs] for r in rows], dtype=np.uint8)
    return ids, basis, events, labels


def load_predictions(path):
    """Read a submission CSV the way Kaggle does: header row, then columns by position."""
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            sys.exit(f"{path} is empty; a submission needs a header row and one row per test id")
        if header[:5] != ["id", "L0", "L1", "L2", "L3"]:
            print(f"warning: header {header[:5]} is not id,L0,L1,L2,L3; scoring by position anyway")
        rows = list(reader)
    return np.array([r[0] for r in rows]), np.array([[int(x) for x in r[1:5]] for r in rows], dtype=np.uint8)


def kaggle_scores(pred, labels, seed):
    """MAE overall, simulated Public/Private split, and a shot-level standard error."""
    shot_err = np.mean(pred != labels, axis=1)  # bits within a shot are correlated
    perm = np.random.default_rng(seed).permutation(len(shot_err))
    cut = int(round(PUBLIC_FRACTION * len(shot_err)))
    return {
        "score": float(shot_err.mean()),
        "score_se": float(shot_err.std(ddof=1) / np.sqrt(len(shot_err))),
        "public": float(shot_err[perm[:cut]].mean()),
        "private": float(shot_err[perm[cut:]].mean()),
    }


def run_decoder(folder, ids, basis, events, root):
    spec = importlib.util.spec_from_file_location("candidate", Path(folder) / "decoder.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pred = np.zeros((len(ids), 4), dtype=np.uint8)
    seconds = 0.0
    for b in "XZ":
        rows = basis == b
        circuit = stim.Circuit.from_file(root / f"{b}_circuit.stim")
        start = time.perf_counter()  # only the decode calls are timed, as on the timing machine
        out = np.asarray(module.decode(circuit, events[rows]))
        seconds += time.perf_counter() - start
        if out.shape != (rows.sum(), 4) or not np.isin(out, (0, 1)).all():
            raise ValueError(f"invalid decoder output for basis {b}: shape {out.shape}")
        pred[rows] = out.astype(np.uint8)
    return pred, seconds


def subsample(ids, basis, events, labels, shots, seed):
    """Take the same `shots` rows per basis every time (fixed seed), for laptop-friendly runs."""
    if not shots:
        return ids, basis, events, labels
    rng = np.random.default_rng(seed)
    keep = np.concatenate([np.sort(rng.permutation(np.flatnonzero(basis == b))[:shots]) for b in "XZ"])
    return ids[keep], basis[keep], events[keep], labels[keep]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--decoder", type=Path, help="folder containing decoder.py with decode()")
    src.add_argument("--predictions", type=Path, help="submission-format CSV to score")
    p.add_argument("--labelled", type=Path, default=ROOT / "data/train/train.csv")
    p.add_argument("--shots", type=int, default=10000, help="rows per basis for --decoder (0 = all)")
    p.add_argument("--name", required=True, help="scoreboard label")
    p.add_argument("--seed", type=int, default=2026, help="subsample and Public/Private split seed")
    p.add_argument("--no-log", action="store_true", help="do not append to runs/scoreboard.csv")
    a = p.parse_args()

    ids, basis, events, labels = load_labelled(a.labelled)
    seconds = None
    if a.decoder:
        ids, basis, events, labels = subsample(ids, basis, events, labels, a.shots, a.seed)
        pred, seconds = run_decoder(a.decoder, ids, basis, events, a.labelled.parent)
        source = str(a.decoder)
    else:
        pid, pred = load_predictions(a.predictions)
        if len(pid) != len(ids):
            sys.exit(f"row count mismatch: {len(pid)} predictions vs {len(ids)} labelled rows")
        if not np.array_equal(pid, ids):
            print("warning: ids differ from the labelled file; Kaggle would reject or misalign this file")
        source = str(a.predictions)

    s = kaggle_scores(pred, labels, a.seed)
    row = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "name": a.name,
           "commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True).stdout.strip(),
           "source": source, "rows": len(ids), **{k: round(v, 6) for k, v in s.items()},
           "zero_ler": round(float(labels.mean()), 6)}
    for b in "XZ":
        m = basis == b
        row[b] = round(float(np.mean(pred[m] != labels[m])), 6)
    row["seconds"] = "" if seconds is None else round(seconds, 3)
    for label, t_cap, alpha in SPEED_RULES:
        # Local timing on a subsample is scaled to the 200,000-row test size; indicative only.
        if seconds is None:
            row[f"final_{label}"] = ""
        else:
            t_full = seconds * 200_000 / len(ids)
            row[f"final_{label}"] = round(s["score"] * max(1.0, t_full / t_cap) ** alpha, 6)

    print(f"\n{a.name}: score (MAE) {s['score']:.5f} +/- {s['score_se']:.5f}  "
          f"public~{s['public']:.5f}  private~{s['private']:.5f}  X {row['X']:.5f}  Z {row['Z']:.5f}  "
          f"(all-zeros {row['zero_ler']:.5f}, {len(ids)} rows)")
    if seconds is not None:
        print(f"decode time {seconds:.2f} s local for {len(ids)} rows "
              f"(~{seconds * 200_000 / len(ids):.1f} s scaled to 200k; not organizer hardware)")

    if not a.no_log:
        SCOREBOARD.parent.mkdir(exist_ok=True)
        new = not SCOREBOARD.exists()
        with open(SCOREBOARD, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerow(row)
        with open(SCOREBOARD, newline="") as f:
            board = sorted(csv.DictReader(f), key=lambda r: float(r["score"]))
        print(f"\nLocal scoreboard ({SCOREBOARD.relative_to(ROOT)}), lower is better:")
        print(f"{'#':>3} {'name':<28} {'score':>9} {'+/-':>8} {'X':>8} {'Z':>8} {'rows':>7} {'sec':>8}")
        for i, r in enumerate(board, 1):
            print(f"{i:>3} {r['name'][:28]:<28} {float(r['score']):>9.5f} {float(r['score_se']):>8.5f} "
                  f"{float(r['X']):>8.5f} {float(r['Z']):>8.5f} {r['rows']:>7} {r['seconds']:>8}")


if __name__ == "__main__":
    main()
