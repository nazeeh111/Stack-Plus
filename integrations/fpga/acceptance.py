"""Exercise the exact upstream fixture and a contract-breaking RTL mutation."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import time


def main():
    started = time.monotonic()
    source = Path('/skill')
    output = Path('/output')
    original = (source/'assets/rv_buffer.sv').read_bytes()

    def fixture(root, name):
        result = subprocess.run(['/usr/bin/python3', '-I', '-B', str(root/'scripts/fpga_fixture.py'),
                                 '--json', '--output', str(output/name)],
                                cwd=output, capture_output=True, text=True, timeout=150)
        (output/(name+'-execution.json')).write_text(json.dumps(
            {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}, indent=2)+'\n')
        return result.returncode, json.loads(result.stdout)

    code, positive = fixture(source, 'positive')
    assert code == 0 and positive['status'] == 'passed', 'Original fixture failed'
    for kind in ('simulation', 'synthesis'):
        assert {x['width'] for x in positive[kind]} == {1, 8}
        assert all(x['status'] == 'passed' for x in positive[kind])
    # Keep exact logs and exercise counters, not only the runner's top-level label.
    for row in positive['simulation']:
        assert 'PASS width=' in row['run']['stdout']
        for token in ('in=', 'out=', 'stall=', 'simultaneous=', 'reset_occupied='):
            assert token in row['run']['stdout']
    for row in positive['synthesis']:
        netlist = json.loads(Path(row['netlist']).read_text())
        assert 'rv_buffer' in netlist['modules']

    mutant = output/'mutant'
    (mutant/'scripts').mkdir(parents=True)
    shutil.copyfile(source/'scripts/fpga_fixture.py', mutant/'scripts/fpga_fixture.py')
    shutil.copytree(source/'assets', mutant/'assets')
    before = "full <= 1'b1; data_reg <= in_data;"
    after = "full <= 1'b1; data_reg <= data_reg;"
    text = original.decode()
    assert text.count(before) == 2
    (mutant/'assets/rv_buffer.sv').write_text(text.replace(before, after))
    negative_code, negative = fixture(mutant, 'data-loss-negative')
    assert negative_code != 0 and negative['status'] == 'failed', 'Data-loss RTL was accepted'
    assert all(x['status'] == 'failed' and 'FAIL' in x['run']['stdout'] for x in negative['simulation'])
    assert all(x['status'] == 'passed' for x in negative['synthesis']), 'Control must compile/synthesize but violate behavior'
    assert (source/'assets/rv_buffer.sv').read_bytes() == original
    result = {'passed': True, 'elapsed_seconds': time.monotonic()-started,
        'source_rtl_sha256': hashlib.sha256(original).hexdigest(), 'widths': [1, 8],
        'positive': 'Exact source checker: simulation and generic synthesis passed',
        'negative': 'Data-loss mutation compiled and synthesized, but original scoreboard rejected both widths',
        'hardware': False, 'limits': ['No board/pin constraints', 'No placement/routing or static timing signoff',
            'No CDC/metastability, formal proof, programming or physical observation',
            'Linux amd64 tools run under the existing container engine on this Mac']}
    (output/'RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
