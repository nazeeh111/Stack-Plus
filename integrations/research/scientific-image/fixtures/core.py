from pathlib import Path
import hashlib,importlib,importlib.metadata,json,os,site,subprocess
expected=json.loads(Path('/input/debian-expected.json').read_text())
audit=subprocess.run(['dpkg','--audit'],capture_output=True,text=True);assert audit.returncode==0 and not audit.stdout.strip() and not audit.stderr.strip(),audit.stdout+audit.stderr
query=subprocess.run(['dpkg-query','-W','-f=${Package}\t${Version}\n'],capture_output=True,text=True,check=True)
installed=dict(line.split('\t',1) for line in query.stdout.splitlines());assert all(installed.get(k)==v for k,v in expected.items())
pip=subprocess.run(['/usr/local/bin/python','-I','-B','-m','pip','--isolated','--disable-pip-version-check','check'],capture_output=True,text=True,check=True)
assert __import__('platform').machine()=='aarch64' and __import__('platform').python_version()=='3.12.16'
for distribution,version in json.loads(Path('/input/python-expected.json').read_text()).items():assert importlib.metadata.version(distribution)==version
names={'pandas':'pandas','matplotlib':'matplotlib','numpy':'numpy','scipy':'scipy','PyYAML':'yaml','hydra-core':'hydra','omegaconf':'omegaconf','fastapi':'fastapi','uvicorn':'uvicorn','pypdf':'pypdf','scholarly':'scholarly','httpx':'httpx'}
versions={}
for dist,module in names.items():importlib.import_module(module);versions[dist]=importlib.metadata.version(dist)
import numpy as np
from scipy.linalg import solve
assert np.allclose(np.linalg.solve([[3.,1.],[1.,2.]],[9.,8.]),[2.,3.])
assert np.allclose(solve([[3.,1.],[1.,2.]],[9.,8.]),[2.,3.])
import pandas as pd
assert pd.DataFrame({'v':[2,3]}).sum()['v']==5
import yaml
assert yaml.load('a: 3',Loader=yaml.CSafeLoader)=={'a':3}
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
fig,ax=plt.subplots(figsize=(4,3),dpi=100);ax.plot([0,1,2],[0,1,4]);ax.set(xlabel='x',ylabel='x squared',title='Dependency verification fixture');fig.tight_layout();fig.savefig('/output/native-kernel-plot.png');plt.close(fig)
from PIL import Image
with Image.open('/output/native-kernel-plot.png') as im:assert im.size==(400,300)
tools={}
for program,args in [('pdflatex',['--version']),('bibtex',['--version']),('pdftotext',['-v'])]:
 p=subprocess.run([program,*args],capture_output=True,text=True,check=True);tools[program]=(p.stdout or p.stderr).splitlines()[0]
hooks=[]
for root in site.getsitepackages():
 for p in Path(root).glob('*.pth'):hooks.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert sorted(h['file'] for h in hooks)==['distutils-precedence.pth','sphinxcontrib_jsmath-1.0.1-py3.7-nspkg.pth']
assert hashlib.sha256(Path('/opt/codex/bin/codex-exec-server').read_bytes()).hexdigest()=='f8fa755640761ebe3d235b3c0e2f71fabbce008194595e7ec3f5a1126ebcf93d'
assert hashlib.sha256(Path('/opt/codex/bin/codex-resources/bwrap').read_bytes()).hexdigest()=='0f543a7356ab343b4827222f910461d4196778f328b28acd6c126ef18e9557ab'
result={'dpkg_audit_empty':True,'all115_debian_versions_exact':True,'debian_versions':{k:installed[k] for k in expected},'pip_check':pip.stdout.strip(),'mandatory12_import_versions':versions,'native_numpy_scipy_pandas_pyyaml_plot':'passed','tool_versions':tools,'startup_pth_inventory':hooks,'docker_socket_absent':not Path('/var/run/docker.sock').exists(),'host_users_tree_absent':not Path('/Users').exists()}
Path('/output/CORE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
