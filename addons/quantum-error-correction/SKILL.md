---
name: quantum-error-correction
description: "Design and verify quantum error-correction experiments: stabilizers, syndrome/detector extraction, decoders and logical failure rates. Use for repetition/surface-code studies or injected-fault validation; not ordinary circuit simulation, error mitigation or a claim of hardware fault tolerance."
metadata:
  category: Quantum error correction and verification
---

# Quantum error correction

Use the existing Cirq or Qiskit method/runtime for circuit execution and QuTiP for justified open-system dynamics. This method supplies the missing correction/decoder contract. Installing instructions installs no SDK, decoder, hardware connection or provider. Keep tasks local unless separately authorized; preserve the chosen host/model and existing environment. Read [contracts and pinned sources](references/contracts.md) before interpreting a decoder result.

## Define the protected information

Record the code/stabilizers, logical observables, encoding/initial state, data/ancilla order, measurement-bit order, rounds, boundaries and correction policy. State which errors are correctable. Three-qubit bit-flip repetition corrects one data X fault under ideal extraction; it does not correct arbitrary quantum noise or establish distance three against Z errors. Preserve coherence: checking only computational-basis outcomes misses phase failure.

Specify noise locations and channels separately: data X/Z/Y, correlated faults, gate/idle noise, preparation, measurement/reset error and leakage. Perfect syndrome extraction with one inserted X is not a circuit-level noise study. Keep physical noise probability distinct from logical failure probability, and report whether the latter is per shot, round or experiment.

## Extract and decode

A syndrome is a measured stabilizer outcome. A detector is an expected measurement parity, often a change between rounds with preparation/final-readout boundary terms. Derive detector indices and boundary edges explicitly; raw parity bits are not automatically a valid detector history. Check noiseless determinism and asymmetric single-fault patterns before batching.

For data order q0,q1,q2 and parity order (q0 XOR q1, q1 XOR q2), the ideal X-only repetition lookup is 00:none, 10:q0, 11:q1, 01:q2. Verify that order through the actual simulator; never infer it from displayed bitstrings. Avoid measuring the encoded logical state during syndrome extraction.

Use a lookup only for its stated small code. For larger Clifford circuits consider Stim's detector error model and a compatible decoder. Standard matching assumes graphlike independent error mechanisms; correlated/hyperedge models require appropriate decomposition/correlation handling or a different decoder. Match tool versions and detector/observable ordering before use; a source reference is not an installed runtime. Compare predicted logical-frame changes with observed logical outcomes, rather than requiring the guessed physical mask to equal the injected mask.

## Verify and report

Test no-fault and each correctable fault, several logical states including complex superpositions, wrong parity/decoder mapping, multiple faults and an error outside the protected channel. A decoder returning an answer is not correction success. Compare with independent parity/majority or small-state-vector oracles; keep shots aligned across syndrome and logical readout.

Save circuits, parameters, package versions, seed, raw outcomes, decoder configuration and failures. Report failures/shots with uncertainty. For zero failures in N independent Bernoulli shots, the one-sided 95% binomial upper bound is 1−0.05^(1/N), not zero. State independence assumptions; correlated/reused trajectories need different uncertainty treatment.

A tiny ideal repetition-code result demonstrates that lane only. Threshold claims require justified noise/decoder models, multiple code sizes/distances and sufficient statistics. It proves neither a general quantum memory nor hardware fault tolerance, real-time decoder performance, a research breakthrough or quantum advantage.
