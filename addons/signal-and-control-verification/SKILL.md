---
name: signal-and-control-verification
description: Validate sampled signals, spectral/filter estimates and simulated feedback controllers against timebase, units, causal execution and stability requirements. Use for DSP, estimation, system identification and control analysis; physical instrument operation remains separate.
metadata:
  category: Signal processing, estimation and control
---

# Verify the sampled system

Define the measured/input/output quantities, units, sample timestamps, sample rate, noise/missing-data assumptions and required latency. Distinguish Hz from radians per second and continuous-time from discrete-time models. Inspect the actual data and implementation before choosing transforms or a controller. Read the operation-specific official documentation and [source guidance](references/source-guidance.md).

Check timestamp order, duplicates, irregular spacing, dropout and clipping before treating a record as uniformly sampled. State any interpolation, resampling or detrending. For spectral estimates, retain sample rate, window, segment length, overlap, scaling and one/two-sided convention. Compare a known tone/impulse or other justified reference and verify magnitude, frequency and units, rather than accepting a plotted peak.

Choose resampling and filtering for the signal's assumptions. Anti-alias before downsampling; define boundary treatment and verify the transient region. A Fourier resampler's periodic assumption may be unsuitable for a finite nonperiodic record. Separate offline zero-phase filtering from causal streaming: future samples are unavailable online. Preserve filter state across chunks, test chunk boundaries and reset behavior, and check latency and numerical stability for the actual representation/precision.

For estimation or system identification, distinguish fit data from validation data. Check whether the experiment excites the identifiable modes, and assess residual correlation and sensitivity to noise/model assumptions. Report unidentifiable parameters instead of manufacturing precise estimates. Use measurement/covariance propagation where it affects the decision.

For control, record state/output definitions, feedback sign, sample period, delays, constraints and operating point. Match all connected timebases. Check closed-loop internal stability and the relevant performance/robustness criteria; one favorable step response or SISO margin does not prove MIMO or nonlinear stability. Simulate representative disturbances, noise, saturation and sample/delay variations before reporting the controller usable. A discretized model needs its own check; continuous-time stability does not establish discrete-time stability.

Deliver reproducible raw/synthetic inputs, model/filter coefficients and versions, transformations, independent checks and stated domain of validity. Compare with a simpler analytic/reference result where possible. Keep last valid output if a revised fit/controller fails. Real HIL/device work requires the existing instrument/embedded method, explicit equipment authority, known limits and independent physical observations. No device, driver, real-time, or safety acceptance follows from a CPU simulation.
