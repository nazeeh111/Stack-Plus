# Restore the portable setup

GitHub stores the toolkit code, pinned source/provenance, selected method sources,
and optional runtime recipes. It does not back up private notes, conversations,
credentials, macOS apps/privacy grants, installed environments, container volumes,
or the original local recovery journals. Keep a separate verified private backup
for those. A successful source restore does not make a broad folder cleanup safe.

Use a fresh checkout and Python 3.11 or later. Follow the
[onboarding steps](ONBOARDING.md) to inspect the selection, rehearse in a
separate home and apply to the intended host. The
[complete-skills profile](../profiles/complete-skills.json) records 170 base
skills, 34 add-ons and 12 specialist skills. A clean complete install exposes
216 methods. An existing personal installation may instead keep the twelve
specialist copies it already owns and use 204 methods from the shared root.
Avoid duplicate active copies and check the selected list before any explicit
replacement.

The portable tests can be run before applying the profile:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

Use [OpenCode's guide](OPENCODE.md) after restoring shared skills, and see
[storage maintenance](storage.md) for recovery and local retention. Check
any configuration conflict before proceeding. Host model, effort,
permissions, credentials and account connections stay with their host.

Extra methods can be selected separately with repeated `--extra-skill NAME`:
ui-design-hallmark, pixel-art-effects, design-specification-workflow,
presentation-visual-design, iphone-mirroring-automation, agent-ui-streaming and
typed-graph-workflows. The five focused discipline additions are computational-photonics-verification, signal-and-control-verification, causal-and-temporal-validation, quantum-error-correction and production-observability-release. See [discipline coverage](DISCIPLINE_COVERAGE.md) for their scope. EGM provides design,
review, resolution and drift checks. 01 selects methods as needed.
Pixelfx source is bundled; existing Node is sufficient for its normal PNG tools.
Hallmark optional rendering needs a compatible browser/Puppeteer available in the
chosen project. Presentation methods use a selected native authoring provider.
Mirroir's exact source-build steps are in its add-on RUNTIME.md. No phone pairing,
private-screen observation, TCC grant or service registration follows installation.

Check actual post-restore skill paths/bodies, selected outputs and each required
runtime operation. OpenCode needs bounded asynchronous registration readback;
its global reload can cancel active work. Use the documented project-only idle
refresh when needed. Neither a GitHub commit nor a source snapshot proves a
complete machine restore or every runtime/account path.

AG-UI supplies an optional app/frontend interaction method; it does not add a
new native coordinator or SDK/service installation. Its pinned 1.0 rules differ
from some older concept pages. Omnigraph instructions restore independently of its CLI. The reviewed macOS arm64 CLI pin is edge-20261117-54ced5d, matching source 54ced5d3 and storage format 17. The optional local runner verifies the pinned bytes, requires one explicit project/target, fresh configuration and a native network/filesystem boundary. Its enduring setup and limits are in the add-on RUNTIME.md. No server, MCP connection, credentials or service is enabled. Stable 0.15.0 cannot read format-17 graphs: preserve original data and use the version matched to a graph. Do not infer cluster/auth/policy or hardware acceptance from the standalone trial.
