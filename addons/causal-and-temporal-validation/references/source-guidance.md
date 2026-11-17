# Pinned identification/refutation guidance

The preserved DoWhy sources document placebo and unobserved-confounding sensitivity tests. Its simulation-based sensitivity procedure needs plausible domain-specific confounder strengths and does not yield a p-value. Passing a chosen set of checks does not establish true causality. Some source prose overstates a passed check or a ranking among estimators; the entry preserves uncertainty rather than adopting that inference.

The audit-captured official scikit-learn TimeSeriesSplit page explains chronological training/test indices, gap semantics and equal-spacing conditions for comparable fold durations. It is not evidence that a generic split prevents all label/event leakage. Preserve the independent information-availability checks. The page is retained only with the audit; its URL is in SOURCE.json. DoWhy's MIT license is retained. No DoWhy/scikit-learn installation or execution is claimed. This is newly authored guidance, not an official PyWhy skill.

Pinned repository: https://github.com/py-why/dowhy/tree/45de9a90623bae166e32790a6bb5a77827ef91cd

Exact original files and hashes: see [SOURCE.json](../SOURCE.json). Original license and document paths remain under upstream-originals/.

Start with the [preserved operation guide](../upstream-originals/docs/source/user_guide/refuting_causal_estimates/index.rst); supporting files retain their original tree.
