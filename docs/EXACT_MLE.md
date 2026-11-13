# The exact most-likely-error (MLE) solver

On a small sample, this solver has our best measured accuracy so far: about **0.034** bitwise LER, versus 0.066 for BP-OSD-CS7 on the same shots. It is **too slow to submit as-is**. Treat it as the accuracy target, and as a ground-truth oracle when developing fast decoders.

Measured results are in [LITERATURE.md §6](LITERATURE.md#6-exact-mle-and-hybrid-lut-reference-results-m). The code is in [refbench.py](evidence/reference-benchmarks/refbench.py), in the ILP block.

## What the problem looks like

`problem_info(circuit)` turns each circuit into a detector error model (DEM). It lists about 2,470 independent fault mechanisms *i*. Each mechanism has:

- a probability `p_i` (most are about 1e-4 to 1e-3),
- a column `H[:, i]`: which of the 70 detectors it flips,
- a column `L[:, i]`: which of the 4 logical observables it flips.

A shot is a hidden fault vector `e ∈ {0,1}^2470`. We see the syndrome `s = H e mod 2` and must predict `o = L e mod 2`.

## What "exact MLE" means

Among all fault vectors that explain the observed syndrome, pick the single most probable one, then report its logical effect.

Faults are independent, so

$$P(e) = \prod_i p_i^{e_i}(1-p_i)^{1-e_i} \;\propto\; \prod_i \Big(\tfrac{p_i}{1-p_i}\Big)^{e_i},$$

and maximising P(e) is the same as **minimising the total weight** Σ wᵢ eᵢ, where wᵢ = log((1−pᵢ)/pᵢ). Rare faults are expensive and common faults are cheap. The decoding problem is therefore:

> minimise Σᵢ wᵢ eᵢ subject to H e ≡ s (mod 2), eᵢ ∈ {0,1}, then predict L e mod 2.

## How we solve it: integer linear programming (ILP)

Parity constraints are not linear, so each detector *d* gets an extra integer "slack" variable kₐ ≥ 0:

$$\sum_i H_{d i}\, e_i - 2k_d = s_d \quad\text{for each of the 70 detectors.}$$

When the left-hand sum is odd, it equals 1 + 2k; when it is even, it equals 0 + 2k. That is exactly the mod-2 condition.

- **Variables:** about 2,470 binary eᵢ plus 70 integer kₐ (bounded by 0 ≤ k ≤ 4, since each detector sees few faults).
- **Objective:** minimise Σ wᵢ eᵢ.
- **Constraints:** 70 linear equalities.
- **Solver:** SciPy's `scipy.optimize.milp`, which wraps the open-source HiGHS branch-and-bound solver.
  - This is a *general-purpose optimisation solver*, which the rules allow. It is not a QEC decoder library.
  - It returns a provably optimal e.

The answer is `L @ e mod 2`. One problem is solved per shot.

## Why it beats BP-OSD by about 2×

1. **BP is unreliable on this code.** BP is exact only on tree-like graphs. This DEM is dense in short cycles: mechanisms flip up to 7 detectors, and the 18-qubit code has many 4- and 6-cycles. So BP's per-fault marginals are poor.
2. **OSD can only search near BP's guess.** OSD orders faults by BP's beliefs and solves a linear system. With bad beliefs, the true minimum-weight error can fall outside OSD's search, even at OSD-CS order 12. In our data, order 12 is barely better than order 7.
3. **The ILP has no such blind spot.** It does a global search with an optimality proof, so it always finds the true minimum-weight explanation.

## Why it is not the final answer

- **Speed.** It takes 0.5–0.8 s per shot on one laptop core. 200k shots would take about 1–2 × 10⁵ CPU-seconds, roughly 40–60 minutes even on 48 cores. That exceeds the 5-minute hard limit, and the speed penalty applies well before that.
- **MLE is not the true optimum.** The metric scores each bit, so the Bayes-optimal decoder computes, for each observable j, P(oⱼ = 1 | s) summed over **all** fault vectors consistent with s. That is maximum-*likelihood* decoding, or MLD.
  - MLE keeps only the single best fault vector and ignores degeneracy: many different fault vectors can have the same logical effect.
  - With about 3 faults per shot, MLD could plausibly go below 0.034. [I]

## How we plan to get close to it fast

These follow from [LITERATURE.md §3–4](LITERATURE.md#3-decoders-state-of-the-art-ranked-by-expected-accuracy-on-this-problem):

- **Tesseract-style A\* search (team target).**
  - The search runs over sets of faults. Its cost is the sum of their weights, plus an admissible heuristic for the cost of still-unexplained detectors.
  - Beam pruning and several detector orderings keep it fast.
  - The Tesseract paper reports ILP-level accuracy at a fraction of the cost.
  - We reimplement it from the paper; the banned `tesseract-decoder` package is not used.
- **Hybrid.** A fast decoder handles every shot. The exact search runs only on shots flagged as hard, for example when BP did not converge or the candidates disagree.
- **Approximate MLD.** Keep the K best fault vectors found during the search, then sum their probabilities per logical class.

## Reproduce

```sh
# throwaway env; refbench also runs banned ldpc for the BP-OSD reference column
python docs/evidence/reference-benchmarks/refbench.py <repo-root> 300 4000 4000000
```

The ILP part alone needs only `numpy`, `scipy` and `stim`.

**How the reported number is combined.** The leaderboard averages over every bit of every row. X and Z rows are equal in number, so the combined score is the mean of the two bases: (0.037 + 0.032)/2 ≈ **0.034**. Each per-basis value has about ±0.01 uncertainty at 300 shots.
