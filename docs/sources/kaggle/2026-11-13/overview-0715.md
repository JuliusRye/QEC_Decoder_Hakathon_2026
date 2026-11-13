# Kaggle Overview — captured November 13, 2026, 07:15 EST

Source: https://www.kaggle.com/competitions/quantum-error-correction-decoder/overview

Signed-in Firefox Save Page, followed by Defuddle extraction. Main Overview content follows verbatim; cookie/navigation/account material and volatile participation/footer counters were omitted. Relative math/code formatting follows the extraction.

---

## Overview

## Description

The goal of this competition is to build a decoder for the `[[18,4,4]]` qLDPC code presented experimentally in [Wang et al. (2026)](https://doi.org/10.1038/s41567-025-03157-4), under SI1000 circuit-level noise ([Gidney et al. (2021)](https://doi.org/10.22331/q-2021-12-20-605)).

Circuit-level noise means that every quantum gate, measurement and reset can fail with some small probability. For the SI1000 noise model these errors are:

| Operation | Error | Technical term |
| --- | --- | --- |
| Single-qubit gate | A random Pauli error ($X$, $Y$ or $Z$) on the qubit with probability $p / 10$ after the gate | $\text{Depolarization}_1(p/10)$ |
| Two-qubit gate (CZ) | A random non-identity two-qubit Pauli error (one of 15) on the qubit pair with probability $p$ after the gate | $\text{Depolarization}_2(p)$ |
| Reset | The qubit is prepared in the wrong state (bit flip, $X$) with probability $2 p$ after the reset | $\text{Bit flip}(2p)$ |
| Measurement | The measurement outcome is flipped with probability $5p$ | $\text{Bit flip}(5p)$ |
| Idle qubit | A random Pauli error with probability $p/10$ for each layer of gates the qubit is not used in | $\text{Depolarization}_1(p/10)$ |
| Idle qubit during measurement or reset | A random Pauli error with probability $2p$ for each measurement or reset layer the qubit is not used in | $\text{Depolarization}_1(2p)$ |

In this competition $p = 0.002$, and every experiment runs 5 rounds of error correction.

The code is an `[[n,k,d]]` = `[[18,4,4]]` code. It has $n=18$ data qubits (32 qubits including the check qubits), $k = 4$ logical qubits and code distance $d = 4$: at least four errors are needed to create an undetectable logical error. Under circuit-level noise, the circuit used here reduces the distance from 4 to 3; see [Wang et al. (2026)](https://doi.org/10.1038/s41567-025-03157-4) for details.

### Who can take part

This is a student hackathon: the competition is open to students only, in teams of up to 4. See the Rules for the details.

### Prize

The winning team is invited on a trip to Copenhagen to visit the Novo Nordisk Foundation Quantum Computing Programme (NQCP) at the Niels Bohr Institute, University of Copenhagen.

Winners are responsible for holding valid travel documents. Winners are responsible for obtaining any required visa or entry authorization for Denmark — the organizers will provide an official invitation letter to support visa applications, but cannot guarantee issuance.

See the Rules for who can receive the prize, what the trip covers and the other terms.

## The decoding problem

If you are new to quantum error correction, you can think of the decoding problem in a simplified way.

Every error that can occur in the circuit can be turned into a binary event: either an error occurred at a given location or it didn't. Each location has a probability that an error occurred. The binary vector saying whether an error occurred at each location is denoted $e$, and the **probability vector** is denoted $p$. In a single shot, $e_{i} \sim \text{Bernoulli} \left(p_{i}\right)$, so it is 1 with probability $p_{i}$.

The error vector $e$ is hidden. Instead you see the detector events $D$, also a vector. The relation between $e$ and $D$ is given by a binary parity **check matrix** $H$:

 $D = H e mod 2$ 
$$
D = He \mod 2
$$

Your task is to predict, from $D$, which logical qubits had an error. This is the logical observable vector $O$, which is related to $e$ by a binary **observable matrix** $L$:

 $O = L e mod 2$ 
$$
O = Le \mod 2
$$

You can get $H$, $L$ and $p$ from a circuit file with Stim. Error mechanisms with the same effect are merged into one column, so every column is unique:

```
import numpy as np
import stim

def problem_info(circuit):
    """Returns H (detectors x mechanisms), L (observables x mechanisms) and p (probability of each mechanism)."""
    dem = circuit.detector_error_model()
    columns, priors = {}, []
    for instruction in dem.flattened():
        if instruction.type != "error":
            continue
        detectors, observables = set(), set()
        for target in instruction.targets_copy():
            if target.is_relative_detector_id():
                detectors ^= {target.val}
            elif target.is_logical_observable_id():
                observables ^= {target.val}
        key, p = (frozenset(detectors), frozenset(observables)), instruction.args_copy()[0]
        if key in columns:  # same effect as an earlier mechanism: merge them
            q = priors[columns[key]]
            priors[columns[key]] = q * (1 - p) + p * (1 - q)
        else:
            columns[key] = len(priors)
            priors.append(p)
    H = np.zeros((dem.num_detectors, len(priors)), dtype=np.uint8)
    L = np.zeros((dem.num_observables, len(priors)), dtype=np.uint8)
    for (detectors, observables), j in columns.items():
        H[list(detectors), j] = 1
        L[list(observables), j] = 1
    return H, L, np.array(priors)
```

## Decoder ideas

**Lookup-table (LUT) decoder.** A LUT decoder goes through a lot of example data and records the correct answer $O$ for each set of detector events $D$ it sees. When decoding, it uses this table to guess the answer. You will have to decide what the output $\hat{O}$ should be for a $D$ that isn't in the table: should it assume no logical errors occurred, or is there a better way to come up with an answer? You can generate as much training data as you need (see the Data page).

**Belief propagation (BP) decoder.** A BP decoder works directly with the decoding problem described above. It passes messages back and forth on the graph defined by the check matrix $H$, starting from the prior probabilities $p$, to estimate how likely each error $e_{i}$ is given the observed detector events $D$. If the most likely error $\hat{e}$ it finds satisfies $H \hat{e} = D mod 2$, the prediction is simply $\hat{O} = L \hat{e} mod 2$. Unlike the LUT and ML decoders, BP needs no training data, but it does not always converge. You will have to decide what to do when it doesn't. Can you use the probabilities BP produces to construct a valid $\hat{e}$ yourself (for example by solving $H \hat{e} = D mod 2$ while preferring the most likely errors), or should you fall back on another decoder?

**Machine learning (ML) decoder.** An ML decoder is a powerful and versatile way to build a decoder tailored to a specific code, and you are free to choose the architecture. You can generate as much training data as you need (see the Data page).

Whatever you build, you must write the decoder yourself: see the Rules for which libraries are allowed.

## Evaluation

The decoder takes the detector events $D$ and predicts the observable flips $\hat{O}$. The logical error rate (LER), the fraction of wrong predictions, is

 $\text{LER} = \frac{1}{N_{\text{trials}}} \sum_{i = 1}^{N_{\text{trials}}} \frac{1}{k} \sum_{j = 1}^{k} \left[O_{j}^{\left(i\right)} \neq \hat{O}_{j}^{\left(i\right)}\right]$ 
$$
\text{LER} = \frac{1}{N_\text{trials}}\sum_{i=1}^{N_\text{trials}}\frac{1}{k}\sum_{j=1}^k\left[O_j^{(i)}\neq\hat O_j^{(i)}\right]
$$

where $N_\text{trials}$ is the number of shots, $k = 4$ is the number of logical qubits, and $\left[\cdot\right]$ is 1 if the statement inside is true and 0 otherwise. Every logical qubit of every shot counts separately: a shot where 2 of the 4 predictions are wrong counts as half a failure.

On the leaderboard, submissions are scored with the mean absolute error (MAE) between your predictions and the true flips, over every shot and observable. With 0/1 predictions this is exactly the LER. **Lower is better.** X and Z shots count equally. Predicting all zeros already gives an LER of about 0.29.

### Submission file

For every `id` in `test.csv`, predict the four observable flips `L0` to `L3`, each 0 or 1. The file needs a header row and the columns `id, L0, L1, L2, L3` **in exactly that order**, like `sample_submission.csv`. The metric matches columns by position, not by name.

```dart
id,L0,L1,L2,L3
gen_X_00000,0,0,0,0
gen_X_00001,0,0,0,0
...
```

**NOTE THAT THERE WAS A TYPO IN THE FIRST VERSION OF THE TEST SUBMISSION FILE, IT SHOULD BE FORMATTED AS ABOVE! AN UPDATED VERSION HAS BEEN UPLOADED ON THE DATA TAB**

## Final ranking: accuracy and speed

A good decoder must also be fast, so the final ranking is decided in three steps.

**Step 1: accuracy.** The leaderboard ranks every submission by its LER. When the competition closes, the top 10 teams on the Private leaderboard go through to step 2. All other teams keep their Private leaderboard order.

**Step 2: accuracy and speed.** The top 10 teams hand in their decoder (see the Rules). We run it on our timing machine, one NVIDIA B200 GPU with 48 CPU cores and the same for every team (see the Rules), and measure its runtime $t$: the total wall-clock time to decode all test shots, X and Z, taking the median of 5 runs. You don't need such a machine yourself: a decoder written for a laptop, even one that uses a single CPU core, is fine. The timing machine is the most your decoder can use, not what it must use. Only the two decode calls are timed: importing your decoder, and anything it builds or loads when it is imported, happens before the clock starts. These teams are then ranked by

 $\text{final score} = \text{LER} \times max \left(1 , \frac{t}{t_{\text{cap}}}\right)^{\alpha}$ 
$$
\text{final score} = \text{LER} \times \max\left(1, \frac{t}{t_\text{cap}}\right)^{\alpha}
$$

where LER is the team's Private leaderboard score. Lower is better.

The target runtime $t_\text{cap}$ is the runtime of our own reference decoder (BP+OSD) on all test shots with 32 CPU threads: **15.4 s**. We time your decoder with 48 threads, so a decoder that parallelises well can gain from the extra cores. A decoder that finishes within $t_{\text{cap}}$ keeps its full value: its final score is just its LER. Beyond the cap, the decoder keeps only a share $\left(\right. t_{\text{cap}} / t \left.\right)^{\alpha}$ of its value, so every doubling of the runtime multiplies its final score by $2^{\alpha}$. We use $\alpha = 0.2$, so each doubling costs about 15%:

![Share of its value a decoder keeps against its runtime, for alpha = 0.2: full value up to t_cap, 87% at twice t_cap, 63% at ten times t_cap, and 55% at the 5-minute hard limit](kaggle-overview-current_files/final_score_penalty_f2Wq.png)

| Runtime | Score multiplier | Value kept |
| --- | --- | --- |
| up to $t_\text{cap}$ | ×1.00 | 100% |
| $2\,t_\text{cap}$ | ×1.15 | 87% |
| $10\,t_\text{cap}$ | ×1.58 | 63% |
| 5 minutes ($19.5\,t_\text{cap}$), the hard limit | ×1.81 | 55% |

Accuracy and runtime go hand in hand in the final score. A decoder whose LER is 5% lower than another's can run up to 1.3 × $t_\text{cap}$ before the less accurate decoder under the cap beats it; with a 10% lower LER it can run up to 1.7 × $t_{\text{cap}}$, and with a 20% lower LER up to 3.1 × $t_{\text{cap}}$.

- **Hard limit:** decoders that take longer than $t_\text{max}$ = 5 minutes are not ranked.
- **Ties** in the final score are broken by the shorter runtime.

**Step 3: presentations.** The top 3 teams in the final score each submit a 5-minute video explaining their solution, by email by 16 November at 07:00 CET. Judges from Riverlane and NVIDIA pick the winning team from these videos, and it wins the prize. See the Rules for the full timeline.

## Getting started

This notebook cell reads the test set, runs a decoder on each basis and writes a submission. Replace `decode` with your own decoder. The top 10 teams hand in the same `decode(circuit, detector_events)` function for the code check (see the Rules).

```
import numpy as np
import pandas as pd
import stim

DATA = "/kaggle/input/[competition-slug]"
DET = [f"D{i}" for i in range(70)]
OBS = ["L0", "L1", "L2", "L3"]

def decode(circuit, detector_events):
    """Your decoder: (shots, 70) bool array -> (shots, 4) array of 0/1."""
    return np.zeros((len(detector_events), 4), dtype=np.uint8)

test = pd.read_csv(f"{DATA}/test.csv")
parts = []
for basis in "XZ":
    circuit = stim.Circuit.from_file(f"{DATA}/{basis}_circuit.stim")
    rows = test[test.basis == basis]
    predictions = decode(circuit, rows[DET].values.astype(bool))
    parts.append(pd.DataFrame(predictions, columns=OBS).assign(id=rows.id.values))
pd.concat(parts)[["id", *OBS]].to_csv("submission.csv", index=False)
```

To check your decoder before submitting, score it on freshly sampled shots:

```
circuit = stim.Circuit.from_file(f"{DATA}/X_circuit.stim")
detector_events, observables = circuit.compile_detector_sampler().sample(100_000, separate_observables=True)
print("LER:", np.mean(decode(circuit, detector_events) != observables))
```

## Handing in your code

If your team finishes in the top 10, you hand in your decoder after the competition closes (see the Rules for the deadline). We run it on the timing machine exactly the way we run our own reference decoders there: from your folder alone, in a fresh Python environment. Test this before you hand in.

**1\. Put everything in one folder.**

```
my_team/
├── decoder.py          # defines decode(circuit, detector_events), see the Rules
├── requirements.txt    # every package you use, with its exact version
└── ...                 # any other modules or files decode needs, such as trained weights,
                        # together with the code that created them
```

Pin every package you use, including `numpy` and `stim`, for example:

```
numpy==2.2.6
numba==0.68.1
stim==1.16.0
```

If `decode` uses a GPU library such as PyTorch or JAX, it must install from `requirements.txt` too.

**2\. What we do with it.** On the timing machine (Linux, Python \[3.13\]) we run, in your folder:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Then, without internet access, we import `decode` from `decoder.py`, call it once per basis on the test shots, and take the median runtime over 5 runs. Nothing else is installed, and nothing can be downloaded while `decode` runs.

**The predictions must match your submission.** Your handed-in code must give the same predictions as your selected submission on the leaderboard for at least 99.9% of the test shots. If it doesn't, your team is disqualified. A handful of shots may differ between machines because of floating-point rounding, which is why the limit isn't 100%. Fix any random seeds, and make sure GPU code gives the same result on every run.

**3\. Test it the same way.**

1. Copy your folder somewhere new and add the two circuit files from the Data tab.
2. Run the two commands above in it.
3. Run this script from inside the folder:
```
# check_handin.py: run inside your hand-in folder, in the fresh environment
import time
import numpy as np
import stim
from decoder import decode

total = 0.0
for basis in "XZ":
    circuit = stim.Circuit.from_file(f"{basis}_circuit.stim")
    events, flips = circuit.compile_detector_sampler(seed=1).sample(100_000, separate_observables=True)
    start = time.perf_counter()
    predictions = np.asarray(decode(circuit, events))
    total += time.perf_counter() - start
    assert predictions.shape == flips.shape and np.isin(predictions, (0, 1)).all()
    print(f"{basis}: LER {np.mean(predictions != flips):.5f}")
print(f"decode time: {total:.1f} s")
```

It should print an LER close to your leaderboard score. If the script fails in a fresh environment, it will also fail on ours.

1. In the same environment, run your decoder on `test.csv`, for example with the Getting started cell. Check that the `submission.csv` it writes matches the submission you selected on Kaggle. It should be identical, and at least 99.9% of the rows must match.

Don't include the `.venv` folder in your hand-in.
