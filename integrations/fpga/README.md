# FPGA CPU verification

The complete MIT FPGA method is in `addons/fpga-development`. Its original
self-checking buffer fixture needs Icarus Verilog and Yosys. This optional runtime
provides those tools in an offline-built, on-demand Linux amd64 container using
the existing Docker engine. It does not install a daemon or change global PATH.

`PINS.json` fixes an official Node/Debian base by digest and 19 Debian packages by
version and SHA256. Only 20.8 MB of added packages are required. Icarus is
12.0-2+b1 and Yosys/ABC 0.52-2. The existing base's Debian keyring and default sqv
policy must authenticate the frozen InRelease. Offline apt simulation must match
the exact package set before build. No signature-policy override is supported.
The image build has no network and runs only the reviewed fixed packages' dpkg
installation scripts. It contains no REA, Ghidra, cloud agent or user repository.

Download the exact public package URLs in `PINS.json` into non-synced temporary
storage, verify their hashes, and include the exact signed release as `InRelease`.
Read package scripts and `licenses/` before preparing. Use a new durable state:

```sh
python3 /absolute/nstack/integrations/fpga/runtime.py prepare \
  --state /absolute/new/eda-state --debs /absolute/reviewed-downloads
python3 /absolute/nstack/integrations/fpga/runtime.py build --state /absolute/new/eda-state
python3 /absolute/nstack/integrations/fpga/runtime.py check \
  --state /absolute/new/eda-state --out /absolute/task/new-fpga-check
```

Docker calls use a fresh, temporary client HOME/config and a minimal environment.
Inherited Docker contexts, remote endpoints, credential helpers and proxy settings
are not used. The client finds an existing local Unix socket; `--docker-host
unix:///absolute/socket` selects another existing local socket explicitly. Standard
Docker Desktop CLI locations are supported even with a reduced PATH. No daemon is
started, and temporary client files are removed when the invocation ends.

Actual checking runs nonroot with no network, a read-only root, dropped capabilities,
no new privileges, 1 CPU, 512 MB and 64-process limit. Only the selected fixture and
integration are mounted read-only; a new owned output directory is writable. The
180-second host bound stops only that invocation's owned container on timeout.
No daemon lifecycle or unrelated container operations are performed.

The exact source checker simulates and synthesizes widths 1 and 8. Its scoreboard
covers reset, stalls and simultaneous transfers. The controlled data-loss mutation
still compiles and synthesizes, but must fail the original scoreboard for both
widths. Retain raw logs, netlists, source hashes, exact image and result.

For a real project, use the same verified image's `iverilog`, `vvp` and `yosys`
with your actual top module, sources, testbench and assertions. The following is
an example for a project containing `rtl/*.sv` and `sim/tb.sv`, with modules named
`top` and `tb`. Adjust those arguments to the project. After `check` succeeds,
run this from a Python script with explicit local paths:

```python
from pathlib import Path
import json, subprocess, sys, uuid
nstack = Path('/absolute/nstack')
sys.path.insert(0, str(nstack / 'lib'))
from docker_client import LocalDocker
state = Path('/absolute/eda-state')
project = Path('/absolute/authorized/project').resolve()
out = Path('/absolute/new/project-check')
out.mkdir(mode=0o700)  # Existing evidence is preserved by failing here.
image = json.loads((state / 'BUILD.json').read_text())['image_id']
name = 'nstack-fpga-project-' + uuid.uuid4().hex
with LocalDocker() as client:
    command = [client.binary, 'run', '--rm', '--name', name, '--pull=never',
        '--platform', 'linux/amd64', '--network', 'none', '--read-only',
        '--user', '1000:1000', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--memory', '512m', '--cpus', '1', '--pids-limit', '64',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777',
        '--mount', f'type=bind,src={project},dst=/rtl,readonly',
        '--mount', f'type=bind,src={out.resolve()},dst=/output',
        '--entrypoint', '/bin/sh', image, '-c',
        'iverilog -g2012 -s tb -o /output/sim /rtl/rtl/*.sv /rtl/sim/tb.sv'
        ' && vvp /output/sim'
        ' && yosys -p "read_verilog -sv /rtl/rtl/*.sv; hierarchy -check -top top;'
        ' proc; opt; check; write_json /output/netlist.json"']
    try:
        result = subprocess.run(command, env=client.env, capture_output=True,
                                text=True, timeout=180)
        (out / 'stdout.log').write_text(result.stdout)
        (out / 'stderr.log').write_text(result.stderr)
        result.check_returncode()
    finally:
        subprocess.run([client.binary, 'rm', '-f', name], env=client.env,
                       capture_output=True, timeout=30)
```

Select canonical project/output paths without commas or newlines, and mount only
the intended project. This template is an invocation example, not an accepted
hardware design. The runtime's fixture result never substitutes for a project's
own assertions, constraints, synthesis review or board acceptance.

These are generic CPU checks, not board/pin constraints, placement/routing, static
timing closure, CDC/metastability analysis, formal proof, programming or physical
verification. Missing tools/stages stay incomplete. Do not use the example as a
board project.

Preserve all package notices in the private local image. `licenses/` retains
copyright texts and source-package references; some package notices are symlinks
to another package's notice inside the image. Icarus includes GPL-2-or-later
components and readline GPL-3-or-later. No image or binary redistribution is part
of this integration. Any future redistribution needs its own complete notices
and corresponding-source compliance. The public repository stores recipes,
source references, notices and hashes, not the .deb files or built image.
