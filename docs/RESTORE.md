# Restore the portable setup

GitHub stores the toolkit code, pinned source/provenance, selected method sources,
and optional runtime recipes. It does not back up private notes, conversations,
credentials, macOS apps/privacy grants, installed environments, container volumes,
or the original local recovery journals. Keep a separate verified private backup
for those. A successful source restore does not make a broad folder cleanup safe.

Use a fresh checkout with Python3.11+ and inspect the installation guidance first.
The complete-skills profile records the170base,34existingadd-on and7 specialist
choices. It installs211 methods on a new host, with no specialist runtime/service
activation. The existing personal installation can instead retain204 shared
methods plus seven user-owned copies. Never install duplicate active copies.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 - <<'PYCODE'
import json,subprocess,sys
from pathlib import Path
arguments=json.loads(Path('profiles/complete-skills.json').read_text())['arguments']
subprocess.run([sys.executable,'native_setup.py','install',*arguments],check=True)
PYCODE
python3 opencode_setup.py install
```

This shared-collection replacement needs review on a populated host. Existing
configuration conflicts and user-owned extra skills stop installation; reconcile
rather than force them. Host/model/effort, permissions, credentials and account
connections stay with their host. Read [onboarding](ONBOARDING.md),
[OpenCode](OPENCODE.md) and [storage maintenance](storage.md).

Extra methods can be selected separately with repeated `--extra-skill NAME`:
ui-design-hallmark, pixel-art-effects, design-specification-workflow,
presentation-visual-design, iphone-mirroring-automation, agent-ui-streaming and
typed-graph-workflows. EGM provides design,
review/resolution and drift methods;01 continues choosing useful combinations.
Pixelfx source is bundled; existingNode is sufficient for its normal PNG tools.
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
new native coordinator or SDK/service installation. Its pinned1.0 rules differ
from some older concept pages. The Omnigraph method is source-only: the reviewed
0.15.1 source policy fix is absent from the available stable0.15.0 artifact, and
the one temporary Mac artifact assessment was rejected before anyCLI execution.
No Omnigraph runtime, database, account, service or MCP connection was installed.
Match source/runtime and clear the applicable readiness gates for a real project;
do not treat the source-method restore as graph/security acceptance.
