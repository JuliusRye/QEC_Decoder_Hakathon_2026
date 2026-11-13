# Kaggle Data — verified context and capture gap

Source: https://www.kaggle.com/competitions/quantum-error-correction-decoder/data

A fresh rendered-page snapshot was not obtained on November 13, 2026. Native browser capture failed after reading the Overview; the unauthenticated Data-page fetch also failed. Do not treat this file as the Data page's exact wording.

The earlier downloaded five-file set and [setup verification](../../../evidence/setup-verification.json) establish the local operational context: `train.csv`, `test.csv`, `sample_submission.csv`, `X_circuit.stim`, and `Z_circuit.stim`. Train/test each contain 200,000 shots, equally split between X and Z. Train includes labels `L0`–`L3`; test supplies detector events `D0`–`D69` and basis. Each circuit has 70 detectors and four observables. Decode each basis with its matching circuit.

The initial downloaded sample IDs used `test_` while test rows used `gen_`. The subsequently observed Overview explicitly announced this typo and a corrected upload. Organizer commit `8447b59` supplies a root sample with `gen_` IDs. An old local download may still contain the first sample; validate against the current template and test IDs before upload.

The organizer README explains detector ordering: seven initial checks (`D0`–`D6`), four rounds of fourteen checks (`D7`–`D62`), and seven final-data measurements (`D63`–`D69`). Use `circuit.get_detector_coordinates()` to inspect the actual coordinates. The source circuits, rather than a presumed geometry, define the evaluated problem. Further labelled data can be sampled from the supplied circuits using Stim; record seeds and separate training from evaluation.
