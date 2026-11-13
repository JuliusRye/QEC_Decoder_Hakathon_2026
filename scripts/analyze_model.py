"""Structural feasibility from the actual DEM, with exact integer memory bounds."""

import argparse
import json
from pathlib import Path
import numpy as np
import stim
from hackathon_2026 import problem_info


def rank_gf2(h):
    a = h.copy()
    rank = 0
    for col in range(a.shape[1]):
        rows = np.flatnonzero(a[rank:, col])
        if not len(rows):
            continue
        k = rank + rows[0]
        a[[rank, k]] = a[[k, rank]]
        for r in np.flatnonzero(a[:, col]):
            if r != rank:
                a[r] ^= a[rank]
        rank += 1
        if rank == len(a):
            break
    return rank


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--circuits", type=Path, default=Path("data/kaggle"))
    args = p.parse_args()
    result = {}
    for b in "XZ":
        c = stim.Circuit.from_file(args.circuits / f"{b}_circuit.stim")
        h = problem_info(c)["H"]
        rank = rank_gf2(h)
        degree, count = np.unique(h.sum(0), return_counts=True)
        result[b] = {
            "detectors": len(h),
            "mechanisms": h.shape[1],
            "rank_gf2": rank,
            "edges": int(h.sum()),
            "detector_degree_counts": dict(zip(map(str, degree), map(int, count))),
            "all_syndromes": 2**rank,
            "dense_packed_four_bit_lut_bytes": 2**rank * 4 // 8,
        }
    print(json.dumps(result, indent=2))
