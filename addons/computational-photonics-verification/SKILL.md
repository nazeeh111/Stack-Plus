---
name: computational-photonics-verification
description: Verify electromagnetic forward simulations and adjoint inverse designs, including normalization, boundary conditions, discretization convergence, gradient checks and fabrication robustness. Use for Meep/FDTD/photonic-device results; robot-engine selection is separate.
metadata:
  category: Electromagnetics and numerical verification
---

# Verify the electromagnetic result

Establish the device, observable, wavelength/frequency range, material model, polarization, excitation and boundary conditions. State the length/time conventions and power/field normalization. Preserve a selected solver; a new solver or an archived example is not automatically needed. Read the task's current solver documentation and [source guidance](references/source-guidance.md) for the operation in use.

Build a forward reference before optimizing. Match its excitation, monitor positions, boundaries, geometry conventions and normalization to the device run. For scattering or diffraction, identify every counted order or mode, propagation direction and reference plane; distinguish amplitude from power and normalized efficiency. Use an empty/reference run, field subtraction or deembedding only when that observable and solver formulation require it. Preserve those reference data with the result.

Separate numerical convergence from agreement with a physical device. Vary the consequential grid, domain/PML, propagation or decay time and spectral/monitor settings independently enough to identify the limiting error. Use an analytic/reference geometry or an independently justified comparator when available. Check conservation/passivity within the material model, while accounting for absorption, evanescent modes and finite monitor coverage. Report unresolved residuals; a visually smooth field is insufficient.

For inverse design, define the objective, design variables, parameter-to-material mapping, constraints and evaluation budget first. Keep the baseline and best feasible result. Before trusting an adjoint or automatic gradient, compare directional derivatives or selected components against finite differences across a useful perturbation range. Choose absolute and relative tolerances appropriate to scale; near-zero derivatives need absolute checks. Resolve signs, indexing, filtering/projection and discretization effects before optimization. A gradient check on one polarization or smooth geometry does not validate another path.

Re-evaluate the final exported geometry using the forward solver. Measure the actual feature sizes and constraints after thresholding/export; optimization penalties alone do not establish manufacturability. Where the task requires robustness, test the chosen wavelength/material/fabrication perturbations and compare the resulting objective with the nominal result. Preserve failed cases and distinguish a solver optimum from a fabricated-device claim.

Deliver geometry/material/source versions, raw or reproducible observables, reference normalization, convergence/gradient evidence, constraints and remaining uncertainty. Existing measurement-uncertainty or scientific-reporting methods can contribute separately when their inputs exist. This method installs no runtime and grants no compute, fabrication, lab or cloud authority. Historical Meep fixtures are reference evidence until their current environment and task path are verified.
