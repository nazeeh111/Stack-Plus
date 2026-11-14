# Local quantum computing and physics

Use the existing Qiskit, QuTiP and PennyLane skills for circuit algorithms,
open-system dynamics and differentiable quantum models. They share one optional
CPU environment; there is no additional research controller or background service.
The three methods remain useful independently.

This hash lock was commissioned on Apple Silicon macOS with CPython 3.13.
It pins 26 official binary-wheel distributions, including Qiskit 2.5.2,
QuTiP 5.3.1 and PennyLane 0.45.1. Other platforms/interpreters require their own
compatible reviewed lock. Preserve an existing environment rather than updating
it in place. Use an existing compatible Python and uv; do not install globally.

For a new explicitly chosen environment, substitute absolute paths below.
Keep downloads/cache in non-synced temporary storage, dependencies in durable
user-owned storage, and evidence with the task. Do not inherit provider secrets.

```sh
uv venv --no-config --python /absolute/python3.13 /absolute/new/quantum-env
uv pip install --no-config --python /absolute/new/quantum-env/bin/python \
  --index-url https://pypi.org/simple --only-binary :all: --require-hashes \
  -r /absolute/nstack/integrations/quantum/requirements.lock
python3 /absolute/nstack/integrations/quantum/check.py \
  --python /absolute/new/quantum-env/bin/python --out /absolute/task/new-check
```

Read the dependency metadata/licenses and retain wheel hashes. Only after the
actual check passes, record this environment's absolute interpreter and guide
as one local runtime with aliases Qiskit, QuTiP and PennyLane. An installation
record is not acceptance. The check refuses an existing output directory and
requires macOS network denial; a refused boundary is not a reason to remove it.
The interpreter itself is an ordinary tool, not a general-purpose sandbox.

Checks exercise Bell correlations, sampling, asymmetric qubit order and
transpilation; unitary and Lindblad dynamics with analytic references,
trace/positivity/Hermiticity and tolerance convergence; and PennyLane gradients
and optimization against formulas and finite differences. Known-wrong answers
must fail. These are small CPU fixtures, not quantum advantage or research
validation. The optional plotting stack, large/noisy algorithms, GPU/compiler
extras and IBM hardware/provider authentication were not commissioned here.

No cloud account or paid hardware is needed for these local checks. Preserve
the user's subscriptions, model and effort. A real experiment still needs its
own physical assumptions, basis/units, convergence and claim checks.
