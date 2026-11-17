# Pinned signal/control guidance

The preserved python-control introduction, linear-system and input/output-system guides define model/timebase semantics and dependency conditions. In particular, dt=0, positive dt, dt=True and dt=None have different meanings; unspecified time is not a verified sampling period. Some advanced routines require Slycot, separately from NumPy/SciPy.

The captured official SciPy resample_poly documentation defines low-pass filtering, rate conversion and boundary assumptions. Read the current target version before invoking an API. python-control's BSD-3-Clause license is preserved. The captured web page is retained only with the source audit; its current official URL is in SOURCE.json. It is not a redistributed runtime. This newly authored entry does not claim comprehensive estimation/control expertise or physical validation.

Pinned repository: https://github.com/python-control/python-control/tree/bfe9380eedcfbc6e57c0a7117e77e633575e3a18

Exact original files and hashes: see [SOURCE.json](../SOURCE.json). Original license and document paths remain under upstream-originals/.

Start with the [preserved operation guide](../upstream-originals/doc/linear.rst); supporting files retain their original tree.
