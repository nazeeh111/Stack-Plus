---
name: causal-and-temporal-validation
description: Validate observational causal-effect analyses and time-ordered predictive backtests through explicit identification assumptions, leakage controls, refutation and out-of-sample checks. Use for econometrics, policy effects or historical strategies; a predictive backtest is not a causal effect or trading authority.
metadata:
  category: Causal inference and quantitative validation
---

# Define the claim and available information

Distinguish descriptive association, predictive performance and intervention effects. State the population, independent unit, target effect or prediction horizon, decision time, information actually available then and data provenance. Choose the needed mode below; do not run a causal library merely because the data are time series. Read [source guidance](references/source-guidance.md) and the exact chosen estimator's assumptions.

For a causal claim, make treatment, outcome, timing, confounders, selection and relevant mechanisms explicit. Assess whether the effect is identifiable under the stated graph/design. Do not force estimation past failed identification or silently treat unknown confounding as absent. Avoid inappropriate adjustment for post-treatment variables or colliders. Match the estimator and uncertainty procedure to the actual assignment, clustering and dependence; no design is automatically superior for every target population.

Run suitable placebo/negative-control, subset/resampling and sensitivity checks. For serial or grouped data, preserve the dependence needed for a valid null rather than shuffling indiscriminately. Explain which assumption each check challenges and its expected result, retain failures, and use plausible confounder strengths. Passing refutations cannot prove the assumptions. Report sensitivity and unidentified quantities beside any point estimate.

For a predictive/backtest claim, use chronological evaluation with an untouched final period or an appropriate rolling/expanding design. Prevent label-horizon overlap, future-revised fields, survivor selection and preprocessing fit on test data. Choose gaps or purged intervals from the actual information/label availability; a generic row gap is not an automatic leakage cure. Tune only within the training/validation history and record the number of models/strategies tried. Compare appropriate naive baselines and report variation across relevant periods or regimes.

For a historical strategy, make execution timing, position accounting, fees, spread/slippage, liquidity/capacity and corporate-action conventions explicit where applicable. Compare gross and net results and check whether the claimed actions could have used the recorded information. A correct calculation on historical data does not establish future performance, causal mechanism or permission to trade.

Deliver a reproducible analysis with dataset/version/time ranges, assumptions, splits, estimator/model, uncertainty, failed controls and remaining threats. Use the existing statistical-analysis, experimental-design or data-source methods for their distinct contributions when needed. Missing data/access should narrow the claim, not be filled with invented observations. This method installs no libraries and starts no provider, account, private-data or financial transaction.
