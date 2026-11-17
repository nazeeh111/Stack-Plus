"""Host-only dispatch of one prepared original-engine agent request.

Receives Docker client context from its owner. No native account/config write,
credential field access, model defaults, controller commands or paid fallback.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


t = module('nstack_managed_transport', 'transport.py')
g = module('nstack_metadata', 'metadata_gate.py')
a = module('nstack_no_model_setup', 'app_server_no_model.py')
live = module('nstack_bounded_turn', 'app_server_turn.py')
relay_module = module('nstack_stdio_relay', 'executor_relay.py')
atomic = module('nstack_private_atomic', 'docker_guard.py').atomic_json


class DispatchRefusal(RuntimeError):
    pass


def contains(root: str, path: str) -> bool:
    return path == root or path.startswith(root.rstrip('/') + '/')


def parse_headless(arguments: list[str], context: dict):
    values = list(arguments)
    while values[:1] == ['env']:
        values.pop(0)
        while values and '=' in values[0] and not values[0].startswith('--'):
            if values.pop(0) not in ('HEADLESS_MODELS_DEV_CACHE=', 'HEADLESS_BILLING=subscription',
                                      'HEADLESS_CAPACITY_RETRIES=0'):
                raise DispatchRefusal('unreviewed original launcher environment')
    if not values or values.pop(0) != '/usr/local/bin/headless':
        raise DispatchRefusal('prepared original Headless entrypoint differs')
    parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)
    parser.add_argument('agent', choices=['codex'])
    parser.add_argument('--debug', action='store_true'); parser.add_argument('--usage', action='store_true')
    parser.add_argument('--allow', choices=['yolo', 'read-only'], required=True)
    parser.add_argument('--model'); parser.add_argument('--reasoning-effort')
    parser.add_argument('--prompt'); parser.add_argument('--prompt-file')
    args, unknown = parser.parse_known_args(values)
    if unknown or bool(args.prompt) == bool(args.prompt_file):
        raise DispatchRefusal('prepared agent arguments are unsupported')
    if args.model not in (None, context['model']) or args.reasoning_effort not in (None, context['effort']):
        raise DispatchRefusal('prepared model or effort differs from live parent')
    return args


def verify_sealed_mounts(mounts: list[dict], visible: dict, role: str, empty_source: str):
    """Independent actual-namespace gate; never infer masks from launcher intent."""
    for row in mounts:
        source = PurePosixPath(row['Source'])
        if any(source.parts[i:i+2] == ('resources', 'final') for i in range(len(source.parts)-1)):
            raise DispatchRefusal('direct final-data mount is forbidden in a model role')
    final_dirs = visible.get('final_directories')
    evaluator_files = visible.get('final_evaluators')
    if (not isinstance(final_dirs, list) or not final_dirs or len(final_dirs) > 256
            or not isinstance(evaluator_files, list) or len(evaluator_files) > 256):
        raise DispatchRefusal('actual sealed namespace inventory is absent or excessive')
    for destination in final_dirs:
        if not any(row['Destination'] == destination and row['Source'] == empty_source
                   and row['RW'] is False for row in mounts):
            raise DispatchRefusal('actual final-data directory lacks its exact readonly empty mask')
    if role != 'task.sh':
        for destination in evaluator_files:
            if not any(row['Destination'] == destination and row['Source'] == '/dev/null'
                       and row['RW'] is False for row in mounts):
                raise DispatchRefusal('actual final evaluator lacks its exact readonly file mask')
    return {'final_directories': final_dirs, 'final_evaluators': evaluator_files,
            'actual_mount_masks_verified': True, 'final_designer_source_exception': role == 'task.sh'}


STAGED_METHOD_NAMES = frozenset({
    'create-idea', 'draft-task', 'edit-program', 'evaluate-program',
    'generate-concept-figure', 'memory-log', 'retrieve-references', 'review-paper',
    'scientific-evidence', 'validate-paper', 'verify-rubrics', 'write-paper',
    'write-paper-standalone'})


def validate_local_methods(rows, cwd):
    if not isinstance(rows, list) or len(rows) > len(STAGED_METHOD_NAMES):
        raise DispatchRefusal('local method index exceeds reviewed scope')
    ancestors = {str(path) for path in [PurePosixPath(cwd), *PurePosixPath(cwd).parents]
                 if contains('/workspace', str(path))}
    names = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'name', 'path', 'sha256', 'bytes'}
                or row['name'] not in STAGED_METHOD_NAMES or row['name'] in names
                or not re.fullmatch('[0-9a-f]{64}', row['sha256'])
                or type(row['bytes']) is not int or not 0 < row['bytes'] <= 262144
                or not any(row['path'] == root+'/.codex/skills/'+row['name']+'/SKILL.md'
                           for root in ancestors)):
            raise DispatchRefusal('local method entry is outside actual role cwd ancestors')
        names.add(row['name'])
    return rows


def compose_role_prompt(original, methods):
    if not methods: return original
    header = ('Role-local original method index:\n'
        'Follow the original task below. When it invokes a named workflow, read its complete '
        'SKILL.md and needed linked support from the matching role-local path listed here. '
        'Do not substitute a global same-name workflow. Report a missing invoked method. '
        'These files add no authority or tools; existing user/host instructions and current '
        'data/tool restrictions remain binding.\n')
    index = ''.join('- '+row['name']+': '+row['path']+' (sha256 '+row['sha256']+')\n'
                    for row in methods)
    effective = header+index+'\nOriginal task instructions follow verbatim:\n'+original
    if len(effective.encode()) > 2097152:
        raise DispatchRefusal('effective original role prompt exceeds bound')
    return effective


class HostDispatcher:
    def __init__(self, policy: dict, docker_binary: str, docker_environment: dict):
        self.policy = policy
        self.docker = docker_binary
        self.docker_env = docker_environment
        self.receipts = Path(policy['receipt_root'])
        self.known_mcp_names = None
        if (not self.receipts.is_dir() or self.receipts.is_symlink()
                or self.receipts.stat().st_mode & 0o077
                or not 1 <= policy['turn_timeout_seconds'] <= 600
                or not 1 <= policy['max_requests'] <= 100):
            raise DispatchRefusal('invalid private dispatch bounds')

    def native_configuration(self, context):
        binary = self.policy['codex_binary']; t.check_binary(binary)
        settings = g.native_setup_settings(context, self.known_mcp_names or [],
                                           [str(self.receipts), '/workspace'])
        command = [binary, 'app-server', '--listen', 'stdio://', '--strict-config']
        for key, value in settings.items(): command += ['-c', key + '=' + t.toml(value)]
        environment = t.clean_environment()
        environment['CODEX_EXEC_SERVER_URL'] = 'none'
        environment['CODEX_INTERNAL_APP_SERVER_REMOTE_CONTROL_DISABLED'] = '1'
        return command, environment

    async def discover(self, context):
        command, environment = self.native_configuration(context)
        async with a.NoModelClient(command, environment, self.receipts) as client:
            await client.initialize()
            providers = await client.request('modelProvider/list', {})
            config = await client.request('config/read', {'includeLayers': False})
            proof = g.project_policy(config, providers, context, require_mcp_disabled=False)
            self.known_mcp_names = proof['mcp_names']

    def docker_capture(self, arguments):
        return subprocess.run([self.docker, *arguments], env=self.docker_env,
                              capture_output=True, text=True, timeout=20, check=True)

    def verify_container(self, request):
        info = json.loads(self.docker_capture(['inspect', request['container']]).stdout)[0]
        # Read only enumerated policy metadata, never Config.Env values.
        labels = info['Config'].get('Labels') or {}
        launch = labels.get('nstack.research.launch', '')
        if (labels.get('nstack.research.owner') != self.policy['owner']
                or not re.fullmatch('[0-9a-f]{32}', launch)
                or labels.get('nstack.research.agent') != 'true'
                or info['Image'] not in self.policy['images']):
            raise DispatchRefusal('prepared container identity differs')
        ledger = Path(self.policy['ledger']) / (launch + '.json')
        if ledger.is_symlink() or not ledger.is_file():
            raise DispatchRefusal('prepared container has no private launch record')
        record = json.loads(ledger.read_text())
        if record.get('owner') != self.policy['owner'] or record.get('launch') != launch or record.get('agent') is not True:
            raise DispatchRefusal('prepared container ownership record differs')
        cfg = info['HostConfig']; security = cfg.get('SecurityOpt') or []
        if (cfg.get('NetworkMode') != 'none' or not cfg.get('ReadonlyRootfs')
                or cfg.get('Privileged') or cfg.get('CapDrop') != ['ALL']
                or 'no-new-privileges' not in security or cfg.get('CapAdd')
                or cfg.get('PidMode') or not 0 < cfg.get('PidsLimit', 0) <= 128
                or not 0 < cfg.get('Memory', 0) <= self.policy['max_agent_memory_bytes']
                or not 0 < cfg.get('NanoCpus', 0) <= self.policy['max_agent_cpus'] * 1_000_000_000
                or info['Config'].get('User') != self.policy['agent_user']):
            raise DispatchRefusal('prepared agent outer controls differ')
        profiles = [v[len('seccomp='):] for v in security if v.startswith('seccomp=')]
        if len(profiles) != 1:
            raise DispatchRefusal('prepared agent seccomp identity is missing')
        try: digest = hashlib.sha256(json.dumps(json.loads(profiles[0]), sort_keys=True).encode()).hexdigest()
        except ValueError: raise DispatchRefusal('agent seccomp response is not explicit JSON') from None
        if digest != self.policy['agent_seccomp_canonical_sha256']:
            raise DispatchRefusal('prepared agent seccomp differs')
        role = self.policy['roles'].get(request['role'])
        if not role or not contains('/workspace', request['cwd']) or '..' in PurePosixPath(request['cwd']).parts:
            raise DispatchRefusal('prepared role or cwd is outside reviewed policy')
        mounts = info.get('Mounts', [])
        for row in mounts:
            source = row['Source']; destination = row['Destination']
            if any(fragment in source or fragment in destination
                   for fragment in self.policy['forbidden_mount_fragments']):
                raise DispatchRefusal('prepared agent exposes a forbidden mount')
            if source == '/dev/null' and not row['RW']: continue
            allowed = [rule for rule in role['sources'] if contains(rule['root'], source)]
            if not allowed or (row['RW'] and not any(rule['writable'] for rule in allowed)):
                raise DispatchRefusal('prepared role mount is outside declared authority')
        for destination, source in role.get('required_masks', {}).items():
            if not any(row['Destination'] == destination and row['Source'] == source
                       and not row['RW'] for row in mounts):
                raise DispatchRefusal('prepared role sealed mask is missing')
        # Enumerate every actual role bind and tmpfs namespace, not two nominal
        # paths. The immutable base image contains no study data. No file content
        # is read; isolated Python ignores cwd/PYTHONPATH/user startup hooks.
        roots = sorted({row['Destination'] for row in mounts if row['Source'] != '/dev/null'}
                       | set((cfg.get('Tmpfs') or {}).keys()))
        probe = '''import json,os,sys
from pathlib import Path
roots=json.loads(sys.argv[1]); final=set(); evaluators=set(); count=0

def visit(path):
 if path.name=='final' and path.parent.name=='resources': final.add(str(path))
 if path.name=='evaluate_final.py' and (path.exists() or path.is_symlink()): evaluators.add(str(path))

def fail(error): raise error

for value in roots:
 root=Path(value);visit(root)
 if not root.is_dir(): continue
 for current,dirs,files in os.walk(root,followlinks=False,onerror=fail):
  count+=len(dirs)+len(files)
  if count>200000: raise RuntimeError('role inventory exceeds bound')
  here=Path(current);visit(here)
  if 'evaluate_final.py' in files: visit(here/'evaluate_final.py')
  if len(final)>256 or len(evaluators)>256: raise RuntimeError('sealed inventory exceeds bound')
print(json.dumps({'final_directories':sorted(final),'final_evaluators':sorted(evaluators)}))
'''
        visible = json.loads(self.docker_capture(['exec', info['Id'], '/usr/local/bin/python',
                              '-I', '-B', '-c', probe, json.dumps(roots)]).stdout)
        masks = verify_sealed_mounts(mounts, visible, request['role'], self.policy['empty_mask_source'])
        return {'container_id': info['Id'], 'image': info['Image'], 'role': request['role'],
                'launch': launch, 'mounts': mounts, 'outer_controls_verified': True,
                'sealed_namespace': masks, 'enumerated_role_roots': roots}

    def prompt(self, request, arguments):
        if arguments.prompt is not None: text = arguments.prompt
        else:
            # Read through the exact role container, never translate a Linux
            # prompt path into a host filesystem path.
            code = ('import os,stat,sys; p=sys.argv[1]; f=os.open(p,os.O_RDONLY|os.O_NONBLOCK); '
                    's=os.fstat(f); assert stat.S_ISREG(s.st_mode) and s.st_size<=2097152; '
                    'data=os.read(f,2097153); assert len(data)<=2097152; '
                    'sys.stdout.buffer.write(data)')
            text = self.docker_capture(['exec', '-w', request['cwd'], request['container'],
                                       '/usr/local/bin/python', '-B', '-c', code,
                                       arguments.prompt_file]).stdout
        if not text.strip() or len(text.encode()) > 2097152:
            raise DispatchRefusal('prepared prompt is empty or too large')
        return text

    def local_methods(self, request):
        # Only actual role cwd/ancestors within /workspace. No host/global catalog,
        # remote plugin registration, additional capability roots or tool calls.
        probe = "import hashlib,json,os,stat,sys\nfrom pathlib import Path\ncwd=Path(sys.argv[1]);names=json.loads(sys.argv[2]);seen=set();rows=[]\nparents=[cwd,*cwd.parents]\nif len(parents)>64:raise ValueError('role path too deep')\nfor parent in parents:\n if not (parent==Path('/workspace') or Path('/workspace') in parent.parents):continue\n root=parent/'.codex/skills'\n if not root.exists() and not root.is_symlink():continue\n if root.resolve()!=root or not root.is_dir():raise ValueError('local method root alias')\n for name in names:\n  if name in seen:continue\n  path=root/name/'SKILL.md'\n  if not path.exists() and not path.is_symlink():continue\n  if path.resolve()!=path:raise ValueError('local method path alias')\n  descriptor=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)\n  try:\n   info=os.fstat(descriptor)\n   if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or not 0<info.st_size<=262144:raise ValueError('local method metadata')\n   raw=os.read(descriptor,262145)\n   if len(raw)>262144:raise ValueError('local method grew beyond bound')\n  finally:os.close(descriptor)\n  seen.add(name);rows.append({'name':name,'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})\nprint(json.dumps(rows))\n"
        rows = json.loads(self.docker_capture(['exec', request['container'],
                    '/usr/local/bin/python', '-I', '-B', '-c', probe, request['cwd'],
                    json.dumps(sorted(STAGED_METHOD_NAMES))]).stdout)
        return validate_local_methods(rows, request['cwd'])

    async def dispatch(self, request, *, allow_inference=False):
        if (request.get('schema_version') != 1 or request.get('owner') != self.policy['owner']
                or not isinstance(request.get('expires_at'), (int, float))
                or not time.time() < request['expires_at'] <= time.time() + 660):
            raise DispatchRefusal('prepared request owner or deadline differs')
        ident = request['request_id']
        if not re.fullmatch('[0-9a-f]{32}', ident): raise DispatchRefusal('request identity invalid')
        if len(list(self.receipts.glob('request-*'))) >= self.policy['max_requests']:
            raise DispatchRefusal('reviewed native request budget exhausted')
        directory = self.receipts / ('request-' + ident); directory.mkdir(mode=0o700)
        receipt = {'state': 'preparing', 'request_id': ident, 'inference': 'not_requested'}
        client = None; relay = None
        try:
            if time.time() >= self.policy['deadline_at']: raise DispatchRefusal('campaign deadline exhausted')
            for name, expected in self.policy['binding_sha256'].items():
                if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != expected:
                    raise DispatchRefusal('reviewed native binding source drifted')
            context = t.current_context(Path(self.policy['context_reference']))
            args = parse_headless(request['arguments'], context)
            receipt['context'] = context; receipt['prepared_role'] = self.verify_container(request)
            request = {**request, 'container': receipt['prepared_role']['container_id']}
            original_prompt = self.prompt(request, args)
            receipt['original_prompt_sha256'] = hashlib.sha256(original_prompt.encode()).hexdigest()
            receipt['local_methods'] = self.local_methods(request)
            prompt = compose_role_prompt(original_prompt, receipt['local_methods'])
            receipt['effective_prompt_sha256'] = hashlib.sha256(prompt.encode()).hexdigest()
            receipt['prompt_sha256'] = receipt['effective_prompt_sha256']
            if self.known_mcp_names is None: await self.discover(context)
            command, environment = self.native_configuration(context); receipt['native_argv'] = command
            if not t.subscription_ready(self.policy['codex_binary']): raise DispatchRefusal('normal ChatGPT preflight refused')
            child = [self.docker, 'exec', '-i', request['container'], '/opt/codex/bin/codex-exec-server',
                     '--listen', 'stdio', '--strict-config', '-c', 'analytics.enabled=false', '-c', 'feedback.enabled=false']
            async with relay_module.ExecutorRelay(child, self.docker_env,
                       timeout_seconds=self.policy['turn_timeout_seconds'] + 60) as relay:
                journal = lambda state: atomic(directory / 'turn-state.json', state)
                async with live.NativeTurnClient(command, environment, directory,
                           journal=journal, timeout_seconds=60) as client:
                    await client.initialize()
                    providers = await client.request('modelProvider/list', {})
                    config = await client.request('config/read', {'includeLayers': False})
                    receipt['policy'] = g.project_policy(config, providers, context)
                    await client.request('environment/info', {'environmentId': 'local'}, expect_error=True)
                    eid = 'research-' + ident
                    await client.request('environment/add', {'environmentId': eid, 'execServerUrl': relay.url,
                                         'connectTimeoutMs': 20000, 'skills': {'required': []}})
                    selection = [{'environmentId': eid, 'cwd': request['cwd'], 'runtimeWorkspaceRoots': ['/workspace']}]
                    started = await client.request('thread/start', {'model': context['model'], 'modelProvider': 'openai',
                              'cwd': request['cwd'], 'runtimeWorkspaceRoots': ['/workspace'], 'approvalPolicy': 'never',
                              'sandbox': 'read-only', 'ephemeral': True, 'environments': selection,
                              'dynamicTools': [], 'selectedCapabilityRoots': []})
                    if any(p != str(Path.home()/'.codex/AGENTS.md') for p in started.get('instructionSources', [])):
                        raise DispatchRefusal('unexpected instruction source in research thread')
                    thread = started['thread']['id']; client.thread_settings.pop(thread, None)
                    policy = {'type': 'externalSandbox', 'networkAccess': 'restricted'}
                    await client.request('thread/settings/update', {'threadId': thread, 'model': context['model'],
                                         'effort': context['effort'], 'sandboxPolicy': policy,
                                         'approvalPolicy': 'never', 'environments': selection})
                    receipt['thread_policy'] = g.verify_thread_settings(await client.wait_settings(thread), context, eid)
                    mcp = await client.request('mcpServerStatus/list', {'threadId': thread, 'detail': 'toolsAndAuthOnly', 'limit': 100})
                    if mcp.get('nextCursor') or any(x.get('runtimeStatus') != 'disabled' or x.get('tools') for x in mcp.get('data', [])):
                        raise DispatchRefusal('research MCP tool inventory is not disabled')
                    hooks = await client.request('hooks/list', {'threadId': thread})
                    if any(h.get('enabled') for x in hooks.get('data', []) for h in x.get('hooks', [])):
                        raise DispatchRefusal('research thread has an enabled hook')
                    features = {}; cursor = None
                    for _ in range(10):
                        response = await client.request('experimentalFeature/list', {
                            'threadId': thread, 'limit': 100, 'cursor': cursor})
                        features.update({x['name']: x['enabled'] for x in response['data']})
                        cursor = response.get('nextCursor')
                        if not cursor: break
                    if cursor or any(features.get(name) is not False for name in g.CAPABILITIES):
                        raise DispatchRefusal('effective research thread capabilities differ')
                    receipt['thread_features_disabled'] = list(g.CAPABILITIES)
                    if t.current_context(Path(self.policy['context_reference'])) != context or not t.subscription_ready(self.policy['codex_binary']):
                        raise DispatchRefusal('current native preflight drifted')
                    if not allow_inference:
                        receipt['state'] = 'prepared_no_inference'
                        receipt['inference'] = 'not_requested'
                        return '', {'inference': 'not_requested'}
                    receipt['native_turn'] = await client.complete_turn({'threadId': thread,
                        'input': [{'type': 'text', 'text': prompt}], 'model': context['model'], 'effort': context['effort'],
                        'approvalPolicy': 'never', 'sandboxPolicy': policy, 'environments': selection,
                        'cwd': request['cwd'], 'runtimeWorkspaceRoots': ['/workspace'], 'serviceTierForTurn': 'default'},
                        timeout_seconds=min(self.policy['turn_timeout_seconds'], int(self.policy['deadline_at']-time.time())))
                    receipt['state'] = 'completed'; receipt['inference'] = 'occurred'
                    answer = client.final_answer
                    counts = client.usage
            return answer, {'agent': 'codex', 'provider': 'openai', 'model': context['model'],
                            'input_tokens': counts['inputTokens'], 'output_tokens': counts['outputTokens'],
                            'cached_input_tokens': counts['cachedInputTokens'], 'reasoning_output_tokens': counts['reasoningOutputTokens'],
                            'cost': None, 'costBasis': None, 'pricingStatus': 'unknown'}
        except BaseException as error:
            receipt['state'] = 'failed_before_inference'; receipt['failure_type'] = type(error).__name__
            if (directory/'turn-state.json').exists():
                receipt['state'] = 'failed_or_uncertain'
                receipt['turn_state'] = json.loads((directory/'turn-state.json').read_text())
                receipt['inference'] = receipt['turn_state'].get('inference', 'unknown')
            raise
        finally:
            if client and hasattr(client, 'process'):
                receipt['host_exit'] = client.process.returncode
                receipt['stderr_bytes'] = client.stderr_bytes; receipt['stderr_sha256'] = client.stderr_hash.hexdigest()
                if 'native_turn' not in receipt:
                    # Preserve measured partial evidence on interruption, never
                    # raw replies, commands, output, configuration or secrets.
                    receipt['partial_native'] = {
                        'items': list(client.items), 'usage': client.usage,
                        'notification_counts': dict(client.notification_counts),
                        'dollar_cost': None}
            if relay: receipt['relay'] = relay.events
            atomic(directory/'receipt.json', receipt)
