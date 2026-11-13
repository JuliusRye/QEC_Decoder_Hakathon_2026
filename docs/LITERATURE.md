# Literature review and baseline measurements: [[18,4,4]] code, SI1000 p=0.002, 5 rounds

Compiled November 13, 2026 (owner: Alec). Tags: **[V]** checked against the source text; **[S]** from an abstract or a secondary page only; **[I]** our own inference; **[M]** measured locally (scripts are in the "Reproducing" section).

This note covers the literature and *reference* numbers. The team's own implemented decoders and their measured results are in [ALGORITHMS.md](ALGORITHMS.md). On the full 200k labelled set, our original BP plus GF(2) fallback scores 0.0898 (see [bp-full-local.json](evidence/bp-full-local.json)).

## 1. The code

- **Source paper:** K. Wang et al., "Demonstration of low-overhead quantum error correction codes", arXiv:2505.09684, Nature Physics (2026), DOI 10.1038/s41567-025-03157-4. Run on the Zhejiang "Kunlun" superconducting processor. [V]
- **Construction:** a bivariate bicycle (BB) code with l = m = 3 and polynomials A = x + 1 + y², B = y + 1 + x². H_X = [A|B], H_Z = [Bᵀ|Aᵀ], and H_X = H_Z (self-dual). [V]
  - There are 9 weight-6 checks of each type, and 7 of each are independent.
  - The circuit drops X2, X8, Z3 and Z4 (see `metadata_18_4_4.json`). That leaves 18 data qubits + 14 check qubits = 32 qubits. [V]
- **It is the 6.6.6 (honeycomb) color code on a 3×3 torus.** Error Correction Zoo entry "[[18,4,4]] 6.6.6 color code": https://errorcorrectionzoo.org/c/stab_18_4_4 [V]
  - Qubits sit on vertices. Each of the 9 hexagonal faces carries both an X check and a Z check.
  - It is the smallest toric color code with d = 4.
  - Liang & Chen (arXiv:2510.05211) also call it "the [[18,4,4]] color code". [V]
- **What the paper did:**
  - Decoder: BP-OSD only, with max_iter 10,000 and OSD-CS order 7. It compared no other decoders. [V]
  - Noise model: fitted to the hardware, not SI1000. CZ error 9.8e-3, measurement error 4.0e-2. [V]
  - Reported logical error rate per logical qubit per cycle: about 8.9% in experiment and about 6% in simulation. [V]
  - These numbers do not transfer to our setting.

## 2. Measured properties of the competition problem [M]

| | X basis | Z basis |
|---|---|---|
| Detectors / observables | 70 / 4 | 70 / 4 |
| Merged error mechanisms (`problem_info`) | 2470 | 2465 |
| Detectors flipped per mechanism | 1–7; most flip 3–6 (hyperedges) | same |
| Expected faults per shot (Σp) | 3.10 | 3.05 |
| Mean detectors fired per shot | 7.4 | 7.3 |
| P(no detector fires) | 4.4% | 4.7% |
| Circuit-level distance (Stim search) | 3 | 3 |

What these numbers imply:

1. **The DEM is not graphlike.** Most mechanisms flip 3 or more detectors, so a plain matching decoder cannot be applied directly. Color-code matching decoders exist (Section 3D), but they need detector colouring, and they have to handle the two missing faces per basis.
2. **A pure lookup table does not work.** About 70% of syndromes are unique in 1M shots. A table built from 1M shots matches only 35% of new test shots, and its overall LER is about 0.24. All-zeros gets 0.29. A table is useful only as a cache in front of a real decoder.
3. **We are in a high-noise regime.** With about 3 faults per shot and d_circ = 3, failures are common. Small modelling gains, especially degeneracy-aware maximum-likelihood decoding, should be clearly visible in the LER.

### Reference LER from the banned `ldpc` library (benchmark only, never for submission) [M]

20,000 fresh shots per basis, competition metric (per-bit LER):

| Decoder (`ldpc` 2.4.1, min-sum, 100 iters) | X LER | Z LER | Fraction of shots with any bit wrong (X) |
|---|---|---|---|
| All-zeros | ≈0.29 | ≈0.29 | — |
| Lookup table, 1M shots | 0.240 | 0.233 | — |
| BP + OSD-0 | 0.113 | 0.109 | 0.210 |
| BP + OSD-CS order 7 | **0.0719** | **0.0690** | 0.133 |
| BP + OSD-CS order 12 | 0.0712 | 0.0685 | 0.132 |

OSD-CS roughly halves OSD-0's error. Going from order 7 to order 12 barely helps, which suggests BP-OSD is near its limit here. **Our own decoder has to beat about 0.07 just to match BP-OSD.** Exact MLE reaches about 0.034 (Section 6), which is about where the leaderboard sits, so ≈0.03 is the real target.

## 3. Decoders: state of the art, ranked by expected accuracy on this problem

### A. Maximum-likelihood decoding (MLD) over logical classes: expected best [I]

There are only 4 observables, which gives 16 logical classes. The best decision for each bit is the class with the largest *summed* probability, not the single most likely error. Degeneracy matters a lot at about 3 faults per shot.

- **HAMLD:** Chen et al., "Hypergraph-based approximate MLD", *Phys. Rev. Research* 8, 023191 (2026). Under circuit noise it reports average LER reductions of 27.8% on surface codes, 58.5% on color codes and 74.4% on BB codes, from being degeneracy-aware. [S]
- **Truncated free energies:** Liu, Zeng, Wu, Lao, arXiv:2609.03928 (2026). Approximate MLD built from a candidate pool. With the same candidates as BP-OSD it gives 13% lower LER on [[144,12,12]] (code-capacity noise). [V]
- **How to do this here:** collect many low-weight solutions per shot, then sum their probabilities per logical class. Sources of candidates: OSD-CS enumeration, an A* or beam search, or ILP with no-good cuts. [I]
  - Tensor-network contraction of the 70-detector DEM may also be feasible offline, as a ground-truth check.
- **Per-bit decision:** the metric scores each bit separately, so predict each bit from its own marginal probability. The arg-max over the 16 classes can disagree with the bit marginals. [I]

### B. Exact or near-exact most-likely-error (MLE) decoding

- **Tesseract:** Aghababaie Beni, Higgott, Shutty (Google), arXiv:2503.10988 (2025). An A* search with beam pruning. [V]
  - Accuracy is about the same as an ILP decoder, and it runs about 5× faster.
  - On bicycle codes its LER is 1–2 orders of magnitude below BP-OSD.
  - Typical settings: beam 15–20, 16–21 detector orderings.
  - The package is banned, but the algorithm can be reimplemented.
- **MaxSAT / decision-tree decoders:** Ott, Hetényi, Beverland, arXiv:2502.16408 (2025). MaxSAT gives "significantly lower" LER than BP-OSD but runs slowly. [V]
- **Beam-search decoder:** Ye, Wecker, Delfosse (IonQ), arXiv:2512.07057 (2025). It beats BP-OSD by 1.3–17× on [[144,12,12]] at p = 1e-3, depending on beam width, and is faster (2.3 ms vs 10.6 ms per shot). [V]
- **ILP with a general solver** (HiGHS, OR-tools, CP-SAT) is allowed under the rules. It is a good ground-truth MLE for measuring the gap; it is probably too slow for 200k shots unless it only handles the hard shots. [I]

### C. Neural decoders

They can learn the MLD posterior from unlimited Stim data. On small codes they beat BP-OSD, but none has yet been shown to beat MLE on a qLDPC code.

- **Transformer for BB codes:** Blue, Avlani, He, Ziyin, Chuang, arXiv:2504.13043 (Quantum 2026). About 5× lower LER than BP-OSD on [[72,12,6]] at p = 0.1%, but the BP-OSD baseline was weak. The authors note "a large gap" to MLE. [V]
- **GraphQEC:** Hu et al., arXiv:2502.19971 (2025). On a d=12 qLDPC code, 18× better than the previous best. [S]
- **AlphaQubit 2:** DeepMind, arXiv:2512.07737. On color codes under SI1000 it matches the Tesseract trend; it trained on about 1e9 samples. [V]
- **GNN decoders:** Lange et al., arXiv:2307.01241. Beat matching on surface codes with circuit noise. [V]
- **Astra:** Maan & Paler, arXiv:2408.07038. A GNN used in place of BP on BB codes, under code-capacity noise only. [V]
- **Why this fits our problem:** the input is only 70 bits and there are only 16 classes, training data is unlimited, and a B200 GPU is available at timing. An MLP or transformer that outputs 4 sigmoids directly targets the per-bit metric. It can also serve as a cheap first stage, with a search decoder taking over on low-confidence shots. [I]

### D. Color-code-specific (matching-based)

- **Chromobius / Möbius decoder:** Gidney & Jones, arXiv:2312.08813; Sahay & Brown, arXiv:2108.11395. [V]
  - It needs a colour and basis on every detector.
  - Its authors say it handles toric color codes *better when given less information*, which suggests substantial room for improvement on tori.
- **Concatenated MWPM:** Lee, Li, Bartlett, Quantum 9, 1609 (2025), arXiv:2404.07482. Threshold about 0.46% under circuit-level noise. [V]
- **Matching decoder for BB codes:** Sahay, Williamson, Brown, arXiv:2602.22770 (2026). Tested only under phenomenological noise. [S]
- **Caveats here [I]:**
  - The two missing faces per basis would need to be rebuilt from the per-colour product relations.
  - The lattice is tiny: 3 faces per colour.
  - Hook errors reduce the circuit distance to 3.
  - Matching decoders are generally *worse* than MLE on small codes, and we would have to write our own MWPM (blossom).
  - Lower priority than A–C.

### E. BP variants (fast, but lower accuracy than A–C)

- **Relay-BP:** Müller et al. (IBM), arXiv:2506.01779 (2025). It beats BP+OSD-CS-10 by 10–100× on the gross code at p = 3e-3. Its memory strength is drawn uniformly from [−0.24, 0.66], and the negative values matter. It is only a few hundred lines and parallelises well on GPU, so it is a strong fast candidate generator. [V]
- **BP-LSD:** Hillmann et al., arXiv:2406.18655. Same accuracy as OSD-CS-7, faster. [V]
- **Ambiguity Clustering:** Wolanski & Barber, arXiv:2406.14527. Same accuracy as BP-OSD, up to 27× faster. [V]
- **BP+OTF:** arXiv:2409.01440. **Closed-branch:** arXiv:2402.01532. Both are at best equal to BP-OSD. [V]
- **Greedy peeling:** Pakhunov, arXiv:2604.11352 (2026). Claims 3.71% vs 3.96% for BP-OSD on a Kunlun [[18,4,4]] reproduction. Single author; low confidence. [S]

## 4. Recommended plan [I]

1. **Baseline (hours 0–2):** our own BP (min-sum, vectorised in numpy/numba or torch) plus OSD-0/OSD-CS on the full DEM. Target LER of about 0.072, to match the `ldpc` reference above.
2. **Accuracy step:** turn OSD-CS (or a Tesseract-style A*/beam search) into a *candidate pool*. Sum probabilities per logical class and predict per-bit marginals. This is approximate MLD.
3. **Neural route, in parallel:** train an MLP or transformer on 1e8–1e9 Stim shots per basis, with 70 inputs and 4 sigmoid outputs, then compare against step 2. Ensemble, or gate by confidence.
4. **Cache:** a table of frequent syndromes (the top ~35% of shots) holding precomputed answers. It is cheap and exact for those shots.
5. **Speed:** the soft penalty is small: 10× over t_cap costs about 26% at α = 0.1. Prioritise LER, then batch and parallelise across 48 cores and the GPU.

## 5. Team questions turned into experiments

These questions came up in the team discussion on November 13. Section 6 answers them.

1. **How good is Tesseract-style exact search on this problem?** The `tesseract-decoder` package has no Windows wheel, and Section 3B shows Tesseract tracks ILP accuracy. So we measured the quantity it approximates directly: exact most-likely-error decoding by integer programming with SciPy/HiGHS (`milp`).
2. **A partial lookup table:** cover only the most frequent syndromes with a table and send every other shot to a real decoder. Does the table beat BP-OSD on the shots it covers?
3. **Warm-starting the A\* search** with BP posteriors is a natural design: use the BP posterior log-odds as edge costs or heuristic, and the BP-OSD solution as the initial upper bound. Not tested yet. [I]
4. **Sinter** (Stim's Monte Carlo sampling and collection tool) is fine for parallel benchmarking. It is not a decoder, so the decoder rules don't apply to it. A custom decoder plugs in through `sinter.Decoder`. Not set up yet. [I]

## 6. Exact-MLE and hybrid-LUT reference results [M]

**Run setup.** We used a light run so a teammate laptop stays usable.

- **Evaluation shots:** 4,000 fresh shots per basis, seed 7.
- **Exact MLE:** run on the first 300 of those shots per basis.
- **Hybrid lookup table:** built from 4M independent shots per basis, seeds 1000–1003.
- **Raw output:** [refbench_result.json](evidence/reference-benchmarks/refbench_result.json).

**Exact MLE by integer programming against BP-OSD-CS7, on the same 300 shots (1,200 bits) per basis:**

| Basis | ILP exact MLE | BP-OSD-CS7 | Bits only ILP got wrong | Bits only OSD got wrong | ILP time per shot (1 core, low priority) |
|---|---|---|---|---|---|
| X | **0.037** | 0.075 | 16 | 62 | 0.49 s |
| Z | **0.032** | 0.058 | 13 | 44 | 0.83 s |

1. **Exact MLE roughly halves BP-OSD's error.** The paired counts, 16 vs 62 and 13 vs 44, make the gap clear even though the sample is small. The size of the gap is still uncertain: 300 shots per basis gives roughly ±0.01 on each LER.
2. **This matches what we hear about the leaderboard.** Teammates report leaders at about 2–3× below the 0.08 baseline, so roughly 0.03, which is the exact-MLE level. **The accuracy target is ≈0.03, not 0.07.** [I]
3. **Plain ILP is far too slow.** At 0.5–0.8 s per shot, 200k shots need about 1–2 × 10⁵ CPU-seconds, about 40–60 minutes even on 48 cores. That is over the 5-minute hard limit.
4. **What we need is a *fast* near-MLE decoder.** Options:
   - a Tesseract-style A\* or beam search, warm-started from BP;
   - an ILP used only on the hard shots;
   - a neural decoder trained to imitate MLE or MLD.
5. **Fully degenerate MLD could go lower still.** MLD sums probability over all errors in each class rather than taking the single best error, so it could score below the MLE number. [I]

**Matt's hybrid lookup table (frequent syndromes, BP-OSD-CS7 fallback), on all 4,000 evaluation shots per basis:**

| Min. table count | Coverage X / Z | Hybrid LER X | Hybrid LER Z | Pure OSD-CS7 LER |
|---|---|---|---|---|
| 1 | 39.6% / 42.1% | 0.0686 | 0.0692 | 0.0704 / 0.0706 |
| 20 | 23.4% / 26.0% | 0.0698 | 0.0704 | |
| 1000 | 11.2% / 12.4% | 0.0704 | 0.0706 | |

- **The table only helps on easy shots.** On the shots it covers, it beats BP-OSD (for example 0.008 vs 0.012 at count ≥ 1), but those shots are already easy, so the overall gain is about 2%.
- **The errors are in the rare syndromes.** Those are exactly the ones a table cannot cover. Kevin's smoke test with our own BP found the same thing.
- **Verdict:** a table is a cheap speed cache, not an accuracy strategy.

## 7. Local Kaggle-style score tracker

[scripts/score_tracker.py](../scripts/score_tracker.py) reproduces the leaderboard metric locally. It never submits anything.

- **Metric:** the MAE over all rows × 4 bits, with columns matched by position, as Kaggle does.
- **Public/private split:** simulated as 30/70 with a fixed seed, since the real split is hidden.
- **Error bar:** a standard error computed per shot, because the 4 bits within a shot are correlated.
- **Final score:** both disputed (t_cap, α) pairs are reported, using local timing scaled to 200k rows, so it is indicative only.
- **Output:** each run appends a row to the git-ignored `runs/scoreboard.csv`.

It has two modes:

- `--decoder <folder>` runs a `decode()` folder on labelled rows from `data/train/train.csv`, 10k per basis by default.
- `--predictions <csv>` scores a submission-format file.

We could not read the live leaderboard: the page returns 404 without a signed-in invited account.

Local scoreboard as of this commit (10,000 labelled rows from `data/train/train.csv`, seed 2026, Windows laptop, 2 Numba threads):

| Entry | Score (MAE) ± SE | X | Z | Decode time |
|---|---|---|---|---|
| Team BP + GF(2) fallback (`decoders/bp`) | 0.0875 ± 0.0022 | 0.0886 | 0.0864 | 65.8 s for 10k rows |
| All-zeros template | 0.2932 ± 0.0030 | 0.2984 | 0.2879 | — |

Commands:

```sh
NUMBA_NUM_THREADS=2 python scripts/score_tracker.py --decoder decoders/bp --shots 5000 --name team-bp
python scripts/score_tracker.py --predictions runs/bp-full-local.csv --name bp-full
```

## Reproducing the measurements

The scripts and their raw output are in [evidence/reference-benchmarks/](evidence/reference-benchmarks/). They are **research-only references**:

- They import the banned `ldpc` package, `ldpc==2.4.1`, installed in a separate throwaway virtual environment that does not include the team's lockfile.
- They do this only to produce a reference number.
- Nothing under `decoders/` may import `ldpc`, and no candidate hand-in may depend on it.

Scripts:

- `analyze.py`: computes the DEM statistics and the lookup-table estimate.
- `bench.py`: the BP-OSD variants.
- `refbench.py`: BP-OSD-CS7, ILP exact MLE, and the hybrid lookup table on frozen seed-7 samples. The recorded run used `refbench.py <repo> 300 4000 4000000`.
