# Kaggle Overview — rendered-page observations

Source: https://www.kaggle.com/competitions/quantum-error-correction-decoder/overview

Observed November 13, 2026 in signed-in Firefox through the native accessibility tree. This is a paraphrased operational record of the rendered page, not a verbatim source snapshot. Browser Save Page failed afterward; see [source coverage](../../README.md).

## Experiment and objective

The page describes a decoder for the `[[18,4,4]]` code used by Wang et al., with 18 data qubits, 32 qubits including checks, four logical qubits, five rounds, and SI1000 strength `p=0.002`. It states that this syndrome-extraction circuit reduces effective distance from four to three. The noise table assigns probabilities `p/10` to single-qubit gates and ordinary idling, `p` to two-qubit gates, `2p` to reset and idling during measurement/reset, and `5p` to measurement flips.

The decoding formulation is `D = H e mod 2` and `O = L e mod 2`, with hidden error mechanisms and priors from Stim. Mechanisms with the same detector and observable effects are merged by odd-parity probability. The page presents LUT, BP, and ML as possible original methods; unlimited generated training data is allowed. BP requires a response to nonconvergence, and a LUT requires a response to unseen syndromes.

## Metric and submission correction

LER is the mean error over all four observable bits of every shot. Binary predictions make this equal to MAE. X and Z count equally; an all-zero predictor is described as approximately 0.29 LER. Submission columns are `id,L0,L1,L2,L3` in that order; position matters. The example uses `gen_X_00000` and `gen_X_00001`. The page explicitly says the first test submission file had a typo and that an updated version was uploaded on the Data tab.

## Ranking and timing

The top ten teams on the Private leaderboard undergo code validation and timing. The rendered formula is:

`final_score = Private_LER * max(1, t / 15.4 seconds)**0.2`.

The reference is BP+OSD using 32 CPU threads; candidates receive 48 threads. The described machine has one NVIDIA B200. Runtime is the total of two decode calls (X and Z), using the median of five runs. Imports and import-time preparation precede the clock. A runtime over five minutes is excluded; the Overview uses shorter runtime for final-score ties. These constants differ from the earlier saved Rules §6 and the older duplicate organizer README section.

## Hand-in and timeline

The hand-in folder must contain `decoder.py`, exact package pins including NumPy and Stim, and required models/files with their creation code. The stated process creates a fresh Linux Python `[3.13]` virtual environment, installs requirements, imports `decode` from that folder, and runs offline. The page permits at least 99.9% row agreement with the selected leaderboard submission because of possible floating-point differences; saved Rules §5 requires every shot to match. Aim for exact reproduction.

The Overview's checks sample fresh labelled shots, validate binary shape, measure decode time, and compare a regenerated test submission with the selected CSV. It says to exclude the virtual environment from the hand-in. The top three teams submit a five-minute video by November 16 at 07:00 CET; Riverlane/NVIDIA judges select the winner. The competition closes November 13 at 24:00 CET. Rules govern detailed eligibility, prize, and hand-in deadlines.
