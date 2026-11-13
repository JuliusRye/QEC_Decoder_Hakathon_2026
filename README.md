# Cornell-QCA QEC decoder hackathon — November 13, 2026

Original decoders for the `[[18,4,4]]` memory experiment under SI1000 circuit noise. This is the Cornell-QCA fork of [the organizer starter](https://github.com/JuliusRye/QEC_Decoder_Hakathon_2026). The competition runs on [Kaggle](https://www.kaggle.com/competitions/quantum-error-correction-decoder); live Kaggle instructions take precedence over organizer repository prose.

Start with [team setup and commands](docs/README.md), [the competition contract and source conflicts](docs/COMPETITION.md), and [contributing](CONTRIBUTING.md). Agents should read [AGENTS.md](AGENTS.md).

```sh
python3 scripts/bootstrap.py
source .venv/bin/activate
NUMBA_NUM_THREADS=2 python -m unittest discover -s tests -v
```

Team onboarding automatically clones or updates private transcript memory outside this checkout and installs the locked environment. Accept your private GitHub invitation and sign in first; see [memory setup](docs/memory/README.md). Agents discover the same procedure through `AGENTS.md`/`CLAUDE.md`. Public contributors can install the decoder environment alone with `uv sync --locked --extra baselines`.

Download `train.csv`, `test.csv`, `sample_submission.csv`, `X_circuit.stim`, and `Z_circuit.stim` from the [Data tab](https://www.kaggle.com/competitions/quantum-error-correction-decoder/data) into `data/kaggle/`. The download and generated runs are ignored by Git. Read [the ID correction](docs/COMPETITION.md#source-conflicts-and-corrections) before preparing predictions.

## Decoder contract

Each candidate provides `decoder.py` with `decode(circuit, detector_events)`: a Boolean `(shots, 70)` array in detector order `D0`–`D69` produces binary `(shots, 4)` predictions in observable order `L0`–`L3`. Decode X and Z with their corresponding supplied circuit. Submit columns `id,L0,L1,L2,L3` in exactly that order, preserving test IDs. Score the mean error over individual observable bits.

## Where to work

| Path | Purpose |
| --- | --- |
| `decoders/` | Original candidate implementations, training code, requirements, and model files |
| `scripts/evaluate.py` | Fresh frozen paired evaluation with source and data fingerprints |
| `scripts/analyze_model.py` | Detector-model rank, degree counts, and full-table memory bound |
| `tests/` | Interface, algorithm, and evaluation regression checks |
| `src/hackathon_2026/` | Organizer circuit construction, noise, data, and DEM utilities |
| `submission_template/` | Organizer entrypoint and local runner; its decoder is an all-zero placeholder |
| [docs/](docs/README.md) | Setup, rules, evidence, references, decisions, and team procedure |
| [docs/memory/](docs/memory/README.md) | Approved summaries and access boundary for the private source archive |

Existing QEC decoder implementations and other people's pretrained decoders are prohibited. The `tutorials` extra includes prohibited decoder dependencies; keep it out of candidate environments. General numerical libraries and Stim simulation are allowed. All local benchmark results need their run record; local timing does not establish timing on the organizer's B200 machine.

For the organizer's full background, circuit/noise description, examples, tutorials, and glossary, see the [dated organizer README](docs/sources/organizer-readme-2614389.md) and [source index](docs/sources/README.md). That source has duplicate evaluation sections with different constants; [the conflict table](docs/COMPETITION.md#source-conflicts-and-corrections) records them.

MIT; see [LICENSE](LICENSE).
