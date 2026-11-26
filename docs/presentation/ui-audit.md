# Find the keyboard and mobile-layout audit

From a checkout with Python 3.11 or newer, search using the task itself:

```sh
python3 nstack.py search "audit keyboard focus on a mobile layout" --brief --limit 1
```

The result is component `P202`. Its native names are `ui-quality-audit` and
`ui-reliability`. Choose **ui-quality-audit** to review a rendered interface.
Search treats each argument as a literal substring; the quoted example matches
a recorded task. For a differently worded brief, try a few distinctive terms:

```sh
python3 nstack.py search keyboard layout accessibility --brief --limit 1
python3 nstack.py search ui-quality-audit --limit 1
python3 nstack.py show P202
```

## Trace the result

The full search result pairs each native name with its source file under
`native_method_sources` and records the root license under `source_license`.
The selected audit comes from `pbakaus/impeccable` revision
`5af4319c4e7a7ee3e5e2b9fe899bcfb21c6190cb`. In the full component record,
`native_name` can retain an upstream alias. The brief search result shows the
names exposed in the current native profile.

| Native profile name | Selected source in the pinned distribution | Use |
| --- | --- | --- |
| `ui-quality-audit` | [audit.md](https://github.com/pbakaus/impeccable/blob/5af4319c4e7a7ee3e5e2b9fe899bcfb21c6190cb/skill/reference/audit.md), alias `impeccable-audit` | Review accessibility and responsive behavior. |
| `ui-reliability` | [harden.md](https://github.com/pbakaus/impeccable/blob/5af4319c4e7a7ee3e5e2b9fe899bcfb21c6190cb/skill/reference/harden.md), alias `impeccable-harden` | Review failure, empty and long-content states. |

The component record also lists [craft-floor.md](https://github.com/pbakaus/impeccable/blob/5af4319c4e7a7ee3e5e2b9fe899bcfb21c6190cb/skill/reference/craft-floor.md)
as supporting material. The repository declares [Apache-2.0](https://github.com/pbakaus/impeccable/blob/5af4319c4e7a7ee3e5e2b9fe899bcfb21c6190cb/LICENSE).
Retain the upstream notices. Optional tools and assets have their own requirements.

## Rehearse just the audit

In the [temporary-home rehearsal](../ONBOARDING.md#2-try-one-skill-in-a-separate-home),
replace `--only web-ui-design` with `--only ui-quality-audit`. The first run
may fetch the pinned source. Inspect the resulting `native-profile.json`:
its `names` array should contain only `ui-quality-audit`. The install prints
a rollback path for that rehearsal. The optional upstream detector and launcher
require separate setup. A completed installation establishes that the method
is available; testing keyboard order, visible focus and the actual phone layout
still requires a rendered application.
