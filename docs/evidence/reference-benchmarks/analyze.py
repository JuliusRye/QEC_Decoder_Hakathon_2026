# RESEARCH-ONLY REFERENCE BENCHMARK. Not a decoder candidate. bench.py/refbench.py import the banned
# 'ldpc' package (installed in a throwaway venv) purely to obtain reference numbers. Never import from decoders/.
# Usage: python analyze.py <repo-root> [args]
import sys, stim, numpy as np, collections, time
sys.path.insert(0, sys.argv[1] + "/src")
from hackathon_2026 import problem_info
root = sys.argv[1]
for b in "XZ":
    c = stim.Circuit.from_file(f"{root}/data/train/{b}_circuit.stim")
    m = problem_info(c); H, L, p = m["H"], m["L"], m["p"]
    w = H.sum(0)
    print(f"[{b}] detectors={H.shape[0]} mechanisms={H.shape[1]} obs={L.shape[0]}  det-weight hist={np.bincount(w)}  sum p={p.sum():.3f}  mean#errors/shot~{p.sum():.2f}")
    # circuit distance
    dem = c.detector_error_model(decompose_errors=False)
    err = dem.shortest_graphlike_error(ignore_ungraphlike_errors=False) if False else None
    try:
        se = c.search_for_undetectable_logical_errors(dont_explore_detection_event_sets_with_size_above=4, dont_explore_edges_with_degree_above=9999, dont_explore_edges_increasing_symptom_degree=False)
        print("   circuit distance (min undetectable logical) =", len(se))
    except Exception as e: print("   distance search failed", e)
    N = 2_000_000
    t=time.time()
    d, o = c.compile_detector_sampler(seed=1).sample(N, separate_observables=True)
    print(f"   sampled {N} in {time.time()-t:.1f}s; P(trivial syndrome)={np.mean(~d.any(1)):.4f}; mean dets fired={d.sum(1).mean():.2f}")
    keys = np.packbits(d, axis=1, bitorder='little')
    k = keys.view(np.uint8).copy()
    kk = np.zeros(N, dtype=np.uint128) if hasattr(np,'uint128') else None
    # hash to bytes
    kb = [bytes(r) for r in k]
    ob = np.packbits(o, axis=1, bitorder='little')[:,0]
    # train/test split for LUT estimate
    tr = N//2
    table = collections.defaultdict(lambda: np.zeros(16, np.int64))
    for i in range(tr): table[kb[i]][ob[i]] += 1
    print(f"   distinct syndromes in {tr} train shots: {len(table)}")
    hit=0; err_bits=0.0; miss_bits=0.0
    obits = o[tr:].astype(int)
    for j,i in enumerate(range(tr,N)):
        t_ = table.get(kb[i])
        if t_ is not None:
            hit+=1; guess=int(t_.argmax())
        else:
            guess=0
        gb = np.array([(guess>>q)&1 for q in range(4)])
        e = np.abs(gb-obits[j]).sum()/4
        err_bits+=e
        if t_ is None: miss_bits+=e
    n=N-tr
    print(f"   LUT(1M train) test-hit-rate={hit/n:.4f}  LER={err_bits/n:.5f}  (of which from misses={miss_bits/n:.5f})")
