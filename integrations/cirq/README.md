# Cirq local CPU workflow

The complete Cirq source leaf adds topology-aware circuits, noise models and
characterization to the existing Qiskit, QuTiP and PennyLane methods. The optional
runtime is separate and does not modify their environment.

`requirements.lock` selects 20 exact official binary wheels for CPython 3.13 on
macOS arm64, including `cirq-core==1.7.0`. Read the metadata, legal notices and
wheel hashes before acquisition. Use existing uv and compatible Python; no global
installation, cloud package or account is needed. Keep downloads in allowed
non-synced temporary storage and the new environment in durable user-owned storage.

```sh
uv venv --no-config --python /absolute/python3.13 /absolute/new/cirq-env
uv pip install --no-config --python /absolute/new/cirq-env/bin/python \
  --index-url https://pypi.org/simple --only-binary :all: --require-hashes \
  -r /absolute/nstack/integrations/cirq/requirements.lock
python3 /absolute/nstack/integrations/cirq/check.py \
  --python /absolute/new/cirq-env/bin/python --out /absolute/task/new-cirq-check
```

The check requires the macOS network-denial boundary, uses a clean environment,
restricts writes to a new evidence directory and bounds the child to 180 seconds.
A denied boundary is a failed check, never permission to remove the boundary.
It exercises explicit qubit order, Bell joint samples, routing maps, CZ compilation
and an authored local line device, amplitude damping against independent Kraus
matrices, T1/T2 coherence, actual Clifford RB inversion/survival, linear XEB and
lossless result archiving. Deliberately wrong orders, marginal factorization,
device edges/gates, thermal model, inverse and estimator substitutions must fail.

The custom line device is not a Google processor. Ideal RB data are not fitted
for error rate. The small XEB API check is not a fidelity experiment. Provider
packages, Google QVM, QASM import extras, ReCirq, QPU execution, QEC, quantum
advantage and research claims were not commissioned. Inspect the actual result
and record the explicit interpreter only after acceptance passes.
