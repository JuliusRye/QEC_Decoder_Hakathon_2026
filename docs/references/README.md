# Papers and technical references

Primary references checked November 13, 2026. These notes identify relevant methods and limits; reading a paper does not establish that its decoder is implemented here. Competition rules require original decoder code. Full paper text and existing decoder implementations are not copied into this repository.

| Reference | Why read it | Implementation boundary |
| --- | --- | --- |
| Ke Wang et al., **Demonstration of low-overhead quantum error correction codes**. [arXiv:2505.09684](https://arxiv.org/abs/2505.09684), [Nature Physics DOI](https://doi.org/10.1038/s41567-025-03157-4) | Experimental origin of the small distance-four code and syndrome-extraction circuit used by the competition. | Use the supplied X/Z Stim circuits for actual detector and observable conventions; paper results are not this team's benchmark. |
| Zijian Liang and Yu-An Chen, **Self-dual bivariate bicycle codes with transversal Clifford gates**. [arXiv:2510.05211](https://arxiv.org/abs/2510.05211), [provided journal DOI](https://doi.org/10.1038/s41534-026-01303-1) | Explains the relationship between self-dual BB codes and color codes; the [full text](https://arxiv.org/html/2510.05211v2) identifies the `[[18,4,4]]` example on a `3 × 3` torus as a color code. | The code label alone does not supply a decoder for this circuit-level detector model. |
| Aleksander Kubica and Nicolas Delfosse, **Efficient color code decoders in d ≥ 2 dimensions from toric code decoders**. [arXiv:1905.07393](https://arxiv.org/abs/1905.07393), [Quantum DOI](https://doi.org/10.22331/q-2023-02-21-929) | The Restriction Decoder projects to toric-code decoding problems and locally lifts solutions. | Ordinary matching on the raw detector hypergraph does not implement projection and lifting. Circuit-level adaptation needs an explicit construction and tests; it is not implemented here. |
| Timo Hillmann et al., **Localized statistics decoding for quantum low-density parity-check codes**. [arXiv:2406.18655](https://arxiv.org/abs/2406.18655), [Nature Communications DOI](https://doi.org/10.1038/s41467-025-63214-7) | Reliability-guided local decoding regions with on-the-fly matrix elimination. | A global reliability-ordered GF(2) fallback alone is not LSD. No claim of reproducing the paper's runtime or algorithm follows from using BP plus elimination. |
| Craig Gidney et al., **A fault-tolerant honeycomb memory**. [Quantum DOI](https://doi.org/10.22331/q-2021-12-20-605) | SI1000 noise reference linked by the competition. | The supplied circuits fix the challenge's actual noisy operations; changing noise creates a different training/evaluation condition. |

## Official tool documentation

- [Stim repository and API documentation](https://github.com/quantumlib/Stim): circuit parsing, detector sampling, detector error models, and detector coordinates. Version in the verified environment: 1.16.0.
- [NumPy documentation](https://numpy.org/doc/): numerical arrays and binary operations. Version in the verified environment: 2.2.6.
- [Numba documentation](https://numba.readthedocs.io/en/stable/): compiled numerical loops and threading. Candidate requirements and the lockfile specify the version; check Python compatibility before upgrading.
- [Kaggle Rules capture](../sources/kaggle/2026-11-13/rules.md): allowed libraries, original-code requirement, and submission/hand-in constraints.

The Liang/Chen journal DOI was supplied in the project context but did not resolve through the browsing tool during this check; the arXiv abstract and full text were accessible and support the technical note.
