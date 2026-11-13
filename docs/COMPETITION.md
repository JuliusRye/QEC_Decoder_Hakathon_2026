# Competition format and rules

Checked November 13, 2026 against the signed-in Kaggle pages in Firefox, including all competition-specific rules and all 18 foundational-rule sections. This is an operational summary; the linked rules remain the source.

Sources: [Overview](https://www.kaggle.com/competitions/quantum-error-correction-decoder/overview), [Data](https://www.kaggle.com/competitions/quantum-error-correction-decoder/data), [Rules](https://www.kaggle.com/competitions/quantum-error-correction-decoder/rules), and the organizer README at revision `6c03afb`. Kaggle takes precedence over the README. Kaggle's foundational rules take precedence over contrary competition-specific rules.

## Decoder and submission contract

The problem uses the [[18,4,4]] qLDPC code, five rounds, SI1000 noise strength 0.002. Decode each basis using its own supplied circuit.

| Item | Required format |
| --- | --- |
| Entrypoint | `decode(circuit: stim.Circuit, detector_events: np.ndarray) -> np.ndarray` in `decoder.py` |
| Input | Boolean `(shots, 70)`, detector columns `D0` through `D69` |
| Output | Binary `(shots, 4)`, observable columns `L0` through `L3` |
| CSV | `id,L0,L1,L2,L3` in exactly that order; one row per test shot |
| Metric | Mean error over all four bits of every shot; lower is better |
| Leaderboard split | About 30% public, 70% private |
| Submission allowance | 10 total per team; select at most 2 finals; better private score counts |
| Hand-in | Self-contained folder with `decoder.py`, exact package pins, loaded artifacts and the code that made them |
| Runtime | Offline; two calls, one per basis on 100,000 shots each; median total time over 5 runs |

The test CSV is one dataset. Do not follow the README's obsolete two-file public/private submission workflow. Scoring is per observable bit, not the previous practice harness's any-error-per-shot metric.

Only the two decode calls are timed; importing the decoder and import-time setup happen before timing. The organizer describes a fresh Linux environment with Python `[3.13]`, but also says exact Python/CUDA details will be published. Hardware: one NVIDIA B200, 48 AMD EPYC 9655 vCPUs, 288 GB RAM, thread limits 48. A laptop implementation is allowed. Runs exceeding 5 minutes are disqualified.

## What is allowed

Write an original decoder. Existing QEC decoder implementations, copied decoder code, and other people's pretrained decoders are prohibited. Named examples include `pymatching`, `ldpc`, `stimbposd`, `beliefmatching`, `tesseract-decoder`, and `fusion-blossom`.

General-purpose libraries such as NumPy, SciPy, Numba, PyTorch, JAX, scikit-learn, graph libraries, and general LP/ILP/SAT solvers are allowed. Stim may load circuits, sample data, and build detector error models. Unlimited generated training data and models trained by the team are allowed. The published rules do not explicitly settle AI-assistance policy.

Predictions must come from running the decoder on detector events. No manual labels, edited predictions, or leaderboard tuning of individual predictions. Preserve seeds and artifacts so the selected submission can be reproduced. Tutorial notebooks contain prohibited decoder dependencies and must not be copied wholesale into a submission.

## Teams and sharing

Invite-only; all members must be enrolled university students, at least 18, with at most 4 per team and one Kaggle account each. Each member registers individually and confirms official Kaggle team membership. GitHub access does not establish Kaggle team membership.

No private code, prediction, or data sharing outside the official team. Public code sharing must be available to all participants through the competition's Kaggle Discussion or Code tabs and satisfy the license rules. The data and organizer repo are MIT licensed; foundational rules require qualifying open-source licenses for incorporated code. Check uncertain libraries or permissions with organizers before relying on them.

## Unresolved source conflicts

| Issue | Evidence | Current handling |
| --- | --- | --- |
| Test IDs | Downloaded `test.csv`: `gen_X_00000`; sample: `test_X_00000`. Each has 200,000 unique IDs, with zero shared IDs. Replacing only `gen_` by `test_` would align them in order. | Do not rewrite IDs or upload a file until the organizer clarifies which ID set is scored. The source generator writes the `gen_` prefix. |
| Speed score | Kaggle Overview: `t_cap=15.4 s`, `alpha=0.2`; Kaggle Rules §6: `0.56 s`, `0.07`; README: provisional `3 s`, `0.1`. | Formula is `LER * max(1,t/t_cap)**alpha`, but keep the constants unresolved. Do not optimize around an assumed value. |
| Reproduction tolerance | Rules §5 requires matching every shot; Overview allows at least 99.9% matching rows. | Aim for exact reproduction; obtain clarification before relying on tolerance. |
| Tie-break | Specific rules use shorter runtime; foundational rules use earlier submission and state they override conflicting specific rules. | Record the conflict; do not assume the speed tie-break is authoritative. |
| Bundled layout | README references `data/test_set/` and separate public/private folders; the checked-out repo has `data/train/` and `data/test/`. | Use the actual Kaggle download in `data/kaggle/`; keep bundled files intact. |

No question has been posted or sent to the organizers. Local verification evidence is in [setup-verification.json](evidence/setup-verification.json).

## Deadlines in Eastern Standard Time

| Milestone | EST |
| --- | --- |
| Competition closes | November 13, 2026, 6:00 p.m. |
| Top-10 code hand-in | November 14, 2026, 1:00 a.m. |
| Top-3 announcement / closing remarks | November 14, 2026, 6:45–7:00 a.m. |
| Top-3 five-minute video due by email | November 16, 2026, 1:00 a.m. |
| Winner chosen | November 16, 2026, 5:00 a.m. |
| Prize trip booked by | January 16, 2027 |

Registration closed November 11 at 6:00 a.m. EST. Technical support windows on November 13 are 6:00–7:00 a.m. and 10:00–11:00 a.m. EST. The top 10 undergo code validation and accuracy/speed ranking; judges from Riverlane and NVIDIA select the winner from the top 3 videos.

## Remaining foundational and prize terms

Foundational sections cover eligibility/sanctions and truthful registration; sponsor versus Kaggle responsibilities; changing deadlines; valid and timely entry; one account/team and merger limits; code sharing and licenses; judging and ties; winner notification and disqualification; prize verification and acceptance paperwork; taxes; applicable laws; publicity; collection and transfer of registration data; original-work warranties, indemnity and releases; network failures; cancellation or modification; no employment relationship; and competition definitions. Entering on behalf of an institution carries authority/policy obligations. These requirements are not resolved by setting up a repository.

The Copenhagen prize covers economy return travel, three nights' accommodation, and local transport for eligible winning members. Dates and budget need written organizer approval before booking; booking must occur within two months of results. Passports, visas, insurance, personal expenses and taxes are the winners' responsibility. NQCP student members can compete but cannot receive the prize. Travel, sanctions and university policies may affect eligibility; the prize may be adapted, replaced, postponed or cancelled and cannot be transferred or exchanged for cash. The organizers, not Kaggle, provide it.
