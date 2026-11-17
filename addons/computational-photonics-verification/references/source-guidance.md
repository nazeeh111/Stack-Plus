# Pinned solver guidance

Use the preserved Meep adjoint tutorial for objective/material mappings, finite-difference checks and minimum-feature constraints. Follow the selected solver's current normalization and boundary documentation for each forward task. The preserved tutorial explicitly reports discretization-dependent gradient error and restricts its level-set grating demonstration to S/Ez polarization; do not generalize that particular example to P polarization. The audit inspected upstream test source; it is neither bundled nor reported as a test run.

Meep source is GPL-2.0 with the exact upstream LICENSE preserved. No Meep runtime is added or commissioned by this package. This entry is newly authored workflow guidance, not an official Meep skill or full tutorial translation.

Pinned repository: https://github.com/NanoComp/meep/tree/84cbc56a2e94b90acfa05dee78247b565b68d04c

Exact original files and hashes: see [SOURCE.json](../SOURCE.json). Original license and document paths remain under upstream-originals/.

Start with the [preserved operation guide](../upstream-originals/doc/docs/Python_Tutorials/Adjoint_Solver.md); supporting files retain their original tree.
