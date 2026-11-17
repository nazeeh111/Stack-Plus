"""Native research transport rejects stale context and enforces real boundaries.

No test calls a model, reads auth stores, changes login, or uses an external API.
"""
import importlib.util
import asyncio
import json
import io
import ast
import tarfile
import re
from pathlib import PurePosixPath
from types import SimpleNamespace
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "integrations/research/codex-transport/transport.py"
spec = importlib.util.spec_from_file_location("research_transport", SOURCE)
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
patch_spec = importlib.util.spec_from_file_location(
    "research_engine_patches", SOURCE.with_name("apply_engine_patches.py"))
engine_patches = importlib.util.module_from_spec(patch_spec)
patch_spec.loader.exec_module(engine_patches)
gate_spec = importlib.util.spec_from_file_location(
    "research_metadata_gate", SOURCE.with_name("metadata_gate.py"))
metadata_gate = importlib.util.module_from_spec(gate_spec)
gate_spec.loader.exec_module(metadata_gate)
setup_spec = importlib.util.spec_from_file_location(
    "research_native_setup", SOURCE.with_name("app_server_no_model.py"))
native_setup = importlib.util.module_from_spec(setup_spec)
setup_spec.loader.exec_module(native_setup)
turn_spec = importlib.util.spec_from_file_location(
    "research_native_turn", SOURCE.with_name("app_server_turn.py"))
native_turn = importlib.util.module_from_spec(turn_spec)
turn_spec.loader.exec_module(native_turn)
guard_spec = importlib.util.spec_from_file_location(
    "research_docker_guard", SOURCE.with_name("docker_guard.py"))
docker_guard = importlib.util.module_from_spec(guard_spec)
guard_spec.loader.exec_module(docker_guard)


class ResearchTransport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nstack-transport-test-", dir="/private/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "public"
        self.receipts = self.root / "receipts"
        self.private = self.root / "private"
        for path in (self.workspace, self.receipts, self.private):
            path.mkdir(mode=0o700)
        self.source = self.root / "metadata.jsonl"
        self.source.write_text(json.dumps({"type": "session_meta", "payload": {
            "id": "thread-test", "model_provider": "openai"}}) + "\n" +
            json.dumps({"type": "response_item", "payload": {"text": "DO NOT RETAIN THIS"}}) + "\n" +
            json.dumps({"type": "turn_context", "payload": {
                "turn_id": "turn-one", "model": "test-current-model", "effort": "high"}}) + "\n")
        self.reference = self.root / "reference.json"
        self.reference.write_text(json.dumps({"source": str(self.source), "thread_id": "thread-test",
                                              "expected_turn_id": "turn-one"}))
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps({"schema_version": 1,
            "context_reference": str(self.reference), "workspace": str(self.workspace),
            "read_roots": [str(self.workspace)], "write_roots": [str(self.workspace)],
            "deny_roots": [str(self.private)], "receipt_dir": str(self.receipts),
            "timeout_seconds": 120}))
        self.manifest = transport.load_manifest(self.manifest_path)

    def test_setup_gate_cannot_send_model_auth_or_configuration_mutation(self):
        client = native_setup.NoModelClient(['/absolute/native/codex'], {}, self.workspace)
        for method in ('turn/start', 'account/login/start', 'config/value/write',
                       'thread/resume', 'command/exec'):
            with self.assertRaises(native_setup.NativeSetupRefusal):
                asyncio.run(client.request(method, {}))
        self.assertEqual(client.methods, [])

    def test_live_turn_gate_requires_explicit_settings_and_projects_counts_only(self):
        client = native_turn.NativeTurnClient(['/absolute/native/codex'], {}, self.workspace)
        with self.assertRaises(RuntimeError):
            asyncio.run(client.complete_turn({'threadId': 'fixture'}, timeout_seconds=10))
        self.assertEqual(client.methods, [])
        counts = dict.fromkeys(('totalTokens', 'inputTokens', 'cachedInputTokens',
                               'outputTokens', 'reasoningOutputTokens'), 1)
        client.observe_notification('thread/tokenUsage/updated', {
            'tokenUsage': {'total': counts, 'unknown_secret': 'SYNTHETIC-SECRET'}})
        client.observe_notification('item/completed', {'item': {
            'type': 'commandExecution', 'id': 'fixture', 'exitCode': 0,
            'status': 'completed', 'aggregatedOutput': 'SYNTHETIC-SECRET'}})
        self.assertEqual(client.usage, counts)
        self.assertNotIn('SYNTHETIC-SECRET', json.dumps(client.items))

    def test_live_turn_journal_precedes_dispatch_and_preserves_uncertain_failures(self):
        states = []
        client = native_turn.NativeTurnClient(
            ['/absolute/native/codex'], {}, self.workspace, journal=states.append)
        params = dict.fromkeys(('threadId', 'input', 'model', 'effort',
                               'approvalPolicy', 'sandboxPolicy', 'environments'), 'fixture')

        async def failed_request(method, payload):
            self.assertEqual(states[-1]['state'], 'attempted')
            self.assertEqual(states[-1]['inference'], 'unknown')
            raise OSError('synthetic pipe failure')
        client.request = failed_request
        with self.assertRaises(OSError):
            asyncio.run(client.complete_turn(params, timeout_seconds=10))
        self.assertEqual(states[0]['state'], 'attempted')
        self.assertEqual(states[-1]['state'], 'interruption_unavailable')
        self.assertIsNone(states[-1]['turn_id'])
        self.assertEqual(states[-1]['inference'], 'unknown')
        self.assertNotIn('model_calls', states[-1])
        client.request_sent('turn/start')
        self.assertEqual(states[-1]['state'], 'sent_to_native')
        self.assertEqual(states[-1]['inference'], 'unknown')

    def test_turn_silence_uses_outer_budget_and_restores_rpc_timeout(self):
        # A real local child pipe stands in for native JSON RPC. It performs no
        # inference, tools, authentication or network operations.
        fake = self.private/'fake-native.py'
        fake.write_text('''import json,sys,time,threading
lock=threading.Lock()
def emit(value):
 with lock:print(json.dumps(value),flush=True)
def finish():
 time.sleep(float(sys.argv[1]))
 emit({'method':'item/completed','params':{'item':{'type':'agentMessage','id':'a','phase':'final_answer','text':'synthetic'}}})
 emit({'method':'turn/completed','params':{'turn':{'id':'t','status':'completed','error':None}}})
for line in sys.stdin:
 request=json.loads(line);method=request['method']
 if method=='initialize':emit({'id':request['id'],'result':{}})
 elif method=='turn/start':
  emit({'id':request['id'],'result':{'turn':{'id':'t'}}})
  emit({'method':'item/completed','params':{'item':{'type':'commandExecution','id':'c','status':'completed','exitCode':0,'aggregatedOutput':'NEVER-RETAIN-RAW'}}})
  emit({'method':'thread/tokenUsage/updated','params':{'tokenUsage':{'total':dict.fromkeys(['totalTokens','inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens'],1)}}})
  threading.Thread(target=finish,daemon=True).start()
 elif method=='turn/interrupt':emit({'id':request['id'],'result':{}})
''')
        params = dict.fromkeys(('threadId','input','model','effort','approvalPolicy','sandboxPolicy','environments'),'synthetic')
        async def scenario(delay, succeeds):
            states=[]
            async with native_turn.NativeTurnClient([sys.executable,'-I','-B',str(fake),str(delay)],
                    {'PATH':'/usr/bin:/bin'},self.private,journal=states.append,timeout_seconds=5) as client:
                # Separate child startup from the short RPC/long turn contract.
                await client.request('initialize', {})
                client.timeout = 0.03
                if succeeds:
                    result=await client.complete_turn(params,timeout_seconds=1)
                    self.assertEqual(result['status'],'completed')
                else:
                    with self.assertRaises(TimeoutError):await client.complete_turn(params,timeout_seconds=1)
                    self.assertEqual(states[-1]['state'],'interruption_acknowledged')
                    self.assertIn('turn/interrupt',client.methods)
                self.assertEqual(client.timeout,0.03)
                self.assertEqual(client.usage['inputTokens'],1)
                self.assertEqual(client.items[0]['exitCode'],0)
                self.assertNotIn('NEVER-RETAIN-RAW',json.dumps(client.items))
            return states
        asyncio.run(scenario(0.12,True)) # silent four times longer than RPC budget
        asyncio.run(scenario(1.5,False)) # explicit outer budget still interrupts

    def test_whole_turn_budget_includes_ack_and_caps_chatty_rpc_waits(self):
        fake=self.private/'fake-ack-native.py'
        fake.write_text('''import json,sys,time,threading
lock=threading.Lock();mode=sys.argv[1]
def emit(value):
 with lock:print(json.dumps(value),flush=True)
def notify(method,params):emit({'method':method,'params':params})
def finish(ident):
 notify('item/completed',{'item':{'type':'commandExecution','id':'partial','status':'completed','exitCode':0,'aggregatedOutput':'RAW-MUST-NOT-SURVIVE'}})
 if mode=='chatty-ack':
  for _ in range(100):
   time.sleep(.02);notify('synthetic/progress',{})
  return
 time.sleep(1.2 if mode=='late-ack' else .65 if mode=='split-budget' else .15)
 emit({'id':ident,'result':{'turn':{'id':'t'}}})
 notify('thread/tokenUsage/updated',{'tokenUsage':{'total':dict.fromkeys(['totalTokens','inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens'],1)}})
 time.sleep(.65 if mode=='split-budget' else .15)
 notify('item/completed',{'item':{'type':'agentMessage','id':'answer','phase':'final_answer','text':'synthetic'}})
 notify('turn/completed',{'turn':{'id':'t','status':'completed','error':None}})
for line in sys.stdin:
 request=json.loads(line)
 if request['method']=='turn/start':threading.Thread(target=finish,args=(request['id'],),daemon=True).start()
 elif request['method']=='turn/interrupt':emit({'id':request['id'],'result':{}})
''')
        params=dict.fromkeys(('threadId','input','model','effort','approvalPolicy','sandboxPolicy','environments'),'synthetic')
        async def scenario(mode,rpc_timeout):
            states=[]
            async with native_turn.NativeTurnClient([sys.executable,'-I','-B',str(fake),mode],
                    {'PATH':'/usr/bin:/bin'},self.private,journal=states.append,timeout_seconds=rpc_timeout) as client:
                started=asyncio.get_running_loop().time()
                if mode=='success':
                    result=await client.complete_turn(params,timeout_seconds=1)
                    self.assertEqual(result['status'],'completed')
                else:
                    with self.assertRaises(TimeoutError):
                        await client.complete_turn(params,timeout_seconds=1)
                    elapsed=asyncio.get_running_loop().time()-started
                    self.assertLess(elapsed,1.18 if mode!='chatty-ack' else .5)
                    if mode=='split-budget':
                        self.assertIn('turn/interrupt',client.methods)
                        self.assertEqual(states[-1]['state'],'interruption_acknowledged')
                        self.assertEqual(client.usage['inputTokens'],1)
                    else:
                        self.assertEqual(client.methods,['turn/start'])
                        self.assertEqual(states[-1]['state'],'interruption_unavailable')
                        self.assertIsNone(states[-1]['turn_id'])
                        self.assertIsNone(client.usage)
                    self.assertEqual(states[-1]['inference'],'unknown')
                self.assertEqual(client.timeout,rpc_timeout)
                self.assertEqual(client.items[0]['exitCode'],0)
                self.assertNotIn('RAW-MUST-NOT-SURVIVE',json.dumps(client.items))
        asyncio.run(scenario('success',.5))
        asyncio.run(scenario('late-ack',2)) # the outer1s budget includes its ack
        asyncio.run(scenario('chatty-ack',.1)) # notifications cannot reset RPC cap
        asyncio.run(scenario('split-budget',2)) # ack and completion share1s

    def test_interrupt_restores_rpc_timeout_and_has_bounded_cleanup_grace(self):
        states=[];timeouts=[]
        client=native_turn.NativeTurnClient(['/absolute/native/codex'],{},self.workspace,
                    journal=states.append,timeout_seconds=.05)
        params=dict.fromkeys(('threadId','input','model','effort','approvalPolicy','sandboxPolicy','environments'),'fixture')
        async def request(method,payload):
            if method=='turn/start':return {'turn':{'id':'t'}}
            timeouts.append(client.timeout)
            # Simulate a chatty/nonresponding interrupt RPC. Its whole cleanup
            # grace remains bounded independently from the inference deadline.
            while True:await asyncio.sleep(.01)
        async def message():await asyncio.sleep(2)
        client.request=request;client._message=message
        async def scenario():
            started=asyncio.get_running_loop().time()
            with self.assertRaises(TimeoutError):await client.complete_turn(params,timeout_seconds=1)
            self.assertLess(asyncio.get_running_loop().time()-started,1.3)
        asyncio.run(scenario())
        self.assertEqual(timeouts,[.05])
        self.assertEqual(client.timeout,.05)
        self.assertEqual(states[-1]['state'],'interruption_attempted')
        self.assertEqual(states[-1]['inference'],'unknown')

    def test_cleanup_requires_private_launch_identity_and_uses_immutable_id(self):
        ledger = self.private / 'ledger'; ledger.mkdir()
        owner = 'a' * 32; launch = 'b' * 32; ident = 'c' * 64
        docker_guard.atomic_json(ledger / (launch + '.json'), {'owner': owner, 'launch': launch})
        labels = {docker_guard.OWNER: owner, docker_guard.LAUNCH: launch}
        def capture(*args, **kwargs):
            return subprocess.CompletedProcess([], 0, json.dumps(ident) + ' ' + json.dumps(labels), '')
        policy = {'real_docker': '/opt/docker/bin/docker-real', 'owner': owner,
                  'ledger': str(ledger), 'empty_home': str(self.private),
                  'empty_config': str(self.private)}
        guard = docker_guard.DockerGuard(policy, capture=capture)
        self.assertEqual(guard.prepare(['rm', '-f', 'reused-name']), ['rm', '-f', ident])
        labels[docker_guard.OWNER] = 'd' * 32
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare(['rm', '-f', 'foreign-name'])
        labels[docker_guard.OWNER] = owner
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare(['exec', 'reused-name', 'true'])
        docker_guard.atomic_json(ledger / (launch + '.json'),
                                {'owner': owner, 'launch': launch, 'agent': True})
        self.assertEqual(guard.prepare(['exec', '-i', '-w', '/workspace', 'reused-name', 'true']),
                         ['exec', '-i', '-w', '/workspace', ident, 'true'])
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare(['exec', '--privileged', 'reused-name', 'true'])
        (ledger / (launch + '.json')).unlink()
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare(['rm', '-f', ident])

    def test_child_launch_records_identity_before_run_and_rejects_broader_options(self):
        ledger = self.private / 'ledger'; ledger.mkdir()
        image = 'sha256:' + 'e' * 64
        policy = {'real_docker': '/opt/docker/bin/docker-real', 'owner': 'a' * 32,
                  'ledger': str(ledger), 'empty_home': str(self.private),
                  'empty_config': str(self.private), 'images': [image],
                  'max_cpus': 2, 'max_pids': 4096, 'max_memory_bytes': 2 * 1024 ** 3,
                  'forbidden_mount_fragments': ['docker.sock', '/run/private-control'],
                  'empty_env_file': '/run/private-control/empty.env'}
        guard = docker_guard.DockerGuard(policy)
        result = guard.prepare(['run', '--network', 'none', image, 'true'])
        self.assertIn('--read-only', result)
        self.assertIn('--memory', result)
        self.assertEqual(len(list(ledger.glob('*.json'))), 1)
        for bad in (['--network', 'host'], ['--network', 'none', '--privileged'],
                    ['--network', 'none', '-v', '/var/run/docker.sock:/socket']):
            with self.assertRaises(docker_guard.GuardRefusal):
                guard.prepare(['run', *bad, image, 'true'])

    def test_process_settings_preserve_literal_mcp_names_and_workspace_paths(self):
        settings = metadata_gate.native_setup_settings(
            {'model': 'current', 'effort': 'high'}, ['server.with.dot'],
            ['/private/task.with.dot'])
        self.assertEqual(settings['mcp_servers'], {'server.with.dot': {'enabled': False}})
        self.assertEqual(settings['projects'], {
            '/private/task.with.dot': {'trust_level': 'untrusted'}})
        self.assertFalse(settings['features.shell_snapshot'])
        self.assertFalse(settings['features.undo'])
        with self.assertRaises(metadata_gate.MetadataRefusal):
            metadata_gate.native_setup_settings({'model': 'current'}, [], [])

    def test_native_controller_rejects_present_or_symlink_setup_before_execution(self):
        specification = json.loads((SOURCE.parent / 'patches/manifest.json').read_text())
        item = next(x for x in specification['files']
                    if x['path'] == 'src/investigation/task_setup.py')
        namespace = {'__name__': 'reviewed_setup_binding'}
        exec(compile(item['replace_after'], 'reviewed_setup_binding', 'exec'), namespace)
        setup = self.workspace / 'setup.py'
        with patch.dict(os.environ, {'NSTACK_NATIVE_BRIDGE': '1'}), \
             patch.object(subprocess, 'run', side_effect=AssertionError('setup executed')):
            self.assertTrue(namespace['run_task_setup'](self.workspace, {}))
            setup.write_text('raise RuntimeError("must not execute")\n')
            self.assertFalse(namespace['run_task_setup'](self.workspace, {}))
            setup.unlink(); setup.symlink_to(self.workspace / 'absent-target')
            self.assertFalse(namespace['run_task_setup'](self.workspace, {}))

    def test_guard_mount_grammar_matches_checked_source_mode_and_no_new_privileges(self):
        ledger = self.private/'ledger'; ledger.mkdir()
        public = self.workspace/'allowed'; public.mkdir()
        secret = self.workspace/'control-private'; secret.mkdir()
        alias = public/'alias'; alias.symlink_to(secret, target_is_directory=True)
        image = 'sha256:'+'e'*64
        policy = {'real_docker': '/opt/docker/bin/docker', 'owner': 'a'*32,
                  'ledger': str(ledger), 'empty_home': str(self.private),
                  'empty_config': str(self.private), 'images': [image],
                  'max_cpus': 1, 'max_pids': 128, 'max_memory_bytes': 1024**3,
                  'forbidden_mount_fragments': ['control-private'],
                  'empty_env_file': '/empty.env', 'agent_seccomp_path': '/approved.json',
                  'bind_roots': [{'root': str(self.workspace), 'writable': False}]}
        guard = docker_guard.DockerGuard(policy)
        base = ['run', '--network', 'none', '--mount']
        invalid = [f'type=bind,src={public},dst=/out,readonly=false',
                   f'type=bind,src={public},source={secret},dst=/out,readonly',
                   f'type=bind,SOURCE={public},dst=/out,readonly',
                   f'type=bind,src="{public}",dst=/out,readonly',
                   f'type=bind,src={alias},dst=/out,readonly']
        for mount in invalid:
            with self.assertRaises(docker_guard.GuardRefusal):
                guard.prepare([*base, mount, image, 'true'])
        # A harmless-looking alias must not inject parser fields after resolve.
        injected = public/'payload,source='/'synthetic/outside'; injected.mkdir(parents=True)
        comma_alias = public/'comma-alias'; comma_alias.symlink_to(injected, target_is_directory=True)
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare([*base, f'type=bind,src={comma_alias},dst=/out,readonly', image, 'true'])
        colon = public/'payload:extra'; colon.mkdir()
        colon_alias = public/'colon-alias'; colon_alias.symlink_to(colon, target_is_directory=True)
        with self.assertRaises(docker_guard.GuardRefusal):
            guard.prepare(['run', '--network', 'none', '-v', f'{colon_alias}:/out:ro', image, 'true'])
        result = guard.prepare([*base, f'type=bind,src={public},dst=/out,readonly',
                                '--security-opt', 'seccomp=/approved.json', image, 'true'])
        self.assertIn(f'type=bind,src={public.resolve()},dst=/out,readonly', result)
        self.assertIn('no-new-privileges', result)
        self.assertIn('never', result)

    def test_workspace_masks_cover_nested_final_copies_and_fail_closed_on_aliases(self):
        spec = importlib.util.spec_from_file_location("reviewed_engine_bridge", SOURCE.with_name("engine_bridge.py"))
        bridge = importlib.util.module_from_spec(spec); spec.loader.exec_module(bridge)
        ledger = self.private/'ledger'; ledger.mkdir()
        final = self.workspace/'task-copy/resources/final'; final.mkdir(parents=True)
        (final/'sealed.txt').write_text('synthetic sealed fixture')
        evaluator = final.parent.parent/'evaluate_final.py'; evaluator.write_text('# synthetic evaluator')
        empty = self.workspace/'empty'; empty.mkdir()
        policy = {'real_docker': '/opt/docker/bin/docker', 'owner': 'a'*32,
                  'ledger': str(ledger), 'empty_home': str(self.private), 'empty_config': str(self.private),
                  'forbidden_mount_fragments': ['private-control'],
                  'bind_roots': [{'root': str(self.workspace), 'writable': False}]}
        policy_path = self.private/'policy.json'; policy_path.write_text(json.dumps(policy))
        environment = {'NSTACK_DOCKER_GUARD_POLICY': str(policy_path), 'NSTACK_NATIVE_EMPTY_MASK': str(empty)}
        with patch.dict(os.environ, environment):
            output = io.BytesIO()
            with patch.object(sys, 'stdout', SimpleNamespace(buffer=output)):
                bridge.masks(str(self.workspace), '/workspace', 'run.sh')
            tokens = output.getvalue().decode().split('\0')
            self.assertIn(str(empty)+':/workspace/task-copy/resources/final:ro', tokens)
            self.assertIn('/dev/null:/workspace/task-copy/evaluate_final.py:ro', tokens)
            output = io.BytesIO()
            with patch.object(sys, 'stdout', SimpleNamespace(buffer=output)):
                bridge.masks(str(self.workspace), '/workspace', 'task.sh')
            self.assertNotIn('evaluate_final.py', output.getvalue().decode())
            with self.assertRaises(ValueError): bridge.masks(str(final), '/workspace', 'task.sh')
            shutil.rmtree(final); final.symlink_to(self.private, target_is_directory=True)
            with self.assertRaises(ValueError): bridge.masks(str(self.workspace), '/workspace', 'task.sh')

    def test_independent_namespace_gate_rejects_unmasked_copies_and_direct_final_mounts(self):
        tree = ast.parse(SOURCE.with_name('native_dispatch.py').read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'verify_sealed_mounts')
        class Refusal(RuntimeError): pass
        namespace = {'PurePosixPath': PurePosixPath, 'DispatchRefusal': Refusal}
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'actual_sealed_gate', 'exec'), namespace)
        verify = namespace['verify_sealed_mounts']
        empty = '/owned/empty-mask'
        destinations = ['/workspace/task/resources/final', '/task-source/resources/final']
        mounts = [{'Source': empty, 'Destination': p, 'RW': False} for p in destinations]
        mounts += [{'Source': '/dev/null', 'Destination': '/task-source/evaluate_final.py', 'RW': False}]
        visible = {'final_directories': destinations,
                   'final_evaluators': ['/task-source/evaluate_final.py']}
        self.assertTrue(verify(mounts, visible, 'run.sh', empty)['actual_mount_masks_verified'])
        for invalid in (mounts[:1]+mounts[2:], mounts[:2],
                        [*mounts, {'Source': '/owned/task/resources/final', 'Destination': '/raw-alias', 'RW': False}]):
            with self.assertRaises(Refusal): verify(invalid, visible, 'run.sh', empty)
        altered = [dict(row) for row in mounts]; altered[1]['RW'] = True
        with self.assertRaises(Refusal): verify(altered, visible, 'run.sh', empty)
        self.assertTrue(verify(mounts[:2], visible, 'task.sh', empty)['final_designer_source_exception'])
        with self.assertRaises(Refusal): verify([], {'final_directories': [], 'final_evaluators': []}, 'task.sh', empty)

    def test_original_controller_exec_and_timeout_stop_use_verified_full_id(self):
        spec = importlib.util.spec_from_file_location('reviewed_ais_driver', SOURCE.parent.parent/'ai_scientist.py')
        driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
        class Stream:
            async def read(self, count): return b''
        class Process:
            returncode = None
            stdout = Stream(); stderr = Stream()
            async def wait(self): return self.returncode
        process = Process(); created = []; stopped = []
        class Client:
            binary = '/absolute/owned/docker'; env = {'PATH':'/usr/bin:/bin'}
            def run(self, arguments, **kwargs):
                stopped.append(arguments); process.returncode = 0
        async def launch(*arguments, **kwargs):
            created.append(arguments); return process
        plan = {'host_dispatch_policy':{'deadline_seconds_after_launch':10},
                'controller_name':'mutable-name','pipeline_argv':['python','-m','original.cli']}
        ident = 'c'*64
        with patch.object(driver,'module',return_value=SimpleNamespace(HostDispatcher=lambda *a: object())),              patch.object(driver.asyncio,'create_subprocess_exec',side_effect=launch),              patch.object(driver.queue,'pending',side_effect=RuntimeError('synthetic stop path')):
            with self.assertRaisesRegex(RuntimeError,'synthetic stop path'):
                asyncio.run(driver.run_original(Client(),plan,self.workspace,ident))
        self.assertEqual(created[0][1:3],('exec',ident))
        self.assertEqual(stopped,[['stop','--time','10',ident]])
        self.assertNotIn('mutable-name',str(created)+str(stopped))

    def test_cli_refuses_success_when_export_or_cleanup_is_incomplete(self):
        spec = importlib.util.spec_from_file_location('reviewed_ais_delivery', SOURCE.parent.parent/'ai_scientist.py')
        driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
        for failure in ({'artifact_exported':False}, {'controller_cleanup_exit':1},
                        {'volume_cleanup_exit':1}, {'child_cleanup_exit':1}):
            receipt = {'controller_exit':0,'artifact_exported':True,
                       'controller_cleanup_exit':0,'volume_cleanup_exit':0,**failure}
            with patch.object(sys,'argv',['ai_scientist.py','run','--launch','/not-read',
                                          '--inputs','/not-read','--state','/not-created']),                  patch.object(driver,'load_plan',return_value={}),                  patch.object(driver,'execute',return_value=receipt):
                self.assertNotEqual(driver.main(),0)
            self.assertEqual(receipt['controller_exit'],0)
        self.assertEqual(driver.overall_exit({'controller_exit':7}),7)

    def test_staged_skill_copy_is_writable_without_changing_source_or_untracked_paths(self):
        specification=json.loads((SOURCE.parent/'patches/manifest.json').read_text())
        item=next(row for row in specification['files'] if row['path']=='src/investigation/skill_scope.py')
        original_root=Path(os.environ.get('NSTACK_AIS_ORIGINAL_SOURCE',
                           '/private/tmp/nstack-research-AI-Scientist-v3'))
        original=original_root/'src/investigation/skill_scope.py'
        if not original.is_file(): self.skipTest('Actual reviewed original source unavailable')
        raw=original.read_text();self.assertEqual(engine_patches.digest(raw.encode()),item['original_sha256'])
        for change in item['replacements']:raw=raw.replace(change['before'],change['after'],1)
        namespace={'__name__':'exact_reviewed_staging'};exec(compile(raw,'exact_reviewed_staging','exec'),namespace)
        src=self.private/'readonly-source';src.mkdir();(src/'child').mkdir()
        for name,text in [('SKILL.md','Task {TASK} instructions'),('helper.sh','#!/bin/sh\n'),
                          ('child/SKILL.md','new canonical text'),('format.sty','style bytes')]:
            (src/name).write_text(text);(src/name).chmod(0o555 if name.endswith('.sh') else 0o444)
        (src/'child').chmod(0o555);src.chmod(0o555)
        dst=self.workspace/'skill';dst.mkdir();extra=dst/'untracked.txt';extra.write_text('preserve');extra.chmod(0o400)
        before={str(p.relative_to(src)):(p.read_bytes(),p.stat().st_mode) for p in src.rglob('*') if p.is_file()}
        canonical=self.private/'canonical';canonical.mkdir();(canonical/'SKILL.md').write_text('protected original')
        protected=((canonical/'SKILL.md').read_bytes(),(canonical/'SKILL.md').stat().st_mode)
        with patch.dict(os.environ,{'NSTACK_NATIVE_BRIDGE':'1','NSTACK_NATIVE_STAGING_ROOTS':json.dumps([str(self.workspace)])}):
            for _ in range(2):
                namespace['stage_skill_tree'](src,dst)
                (dst/'SKILL.md').write_text((dst/'SKILL.md').read_text().replace('{TASK}','real task'))
                namespace['stage_skill_tree'](src/'child',dst/'child')
                namespace['stage_skill_file'](src/'format.sty',self.workspace/'article.sty')
            alias_dst=self.workspace/'aliased-skill';alias_dst.mkdir();(alias_dst/'child').symlink_to(canonical,target_is_directory=True)
            with self.assertRaises(ValueError):namespace['stage_skill_tree'](src,alias_dst)
            leaf=self.workspace/'aliased-style';leaf.symlink_to(canonical/'SKILL.md')
            with self.assertRaises(ValueError):namespace['stage_skill_file'](src/'format.sty',leaf)
            self.assertTrue(leaf.is_symlink());self.assertTrue((alias_dst/'child').is_symlink())
            with self.assertRaises(ValueError):namespace['stage_skill_tree'](src,src/'outside-destination')
        self.assertEqual(protected,((canonical/'SKILL.md').read_bytes(),(canonical/'SKILL.md').stat().st_mode))
        self.assertEqual(before,{str(p.relative_to(src)):(p.read_bytes(),p.stat().st_mode) for p in src.rglob('*') if p.is_file()})
        self.assertTrue((dst/'helper.sh').stat().st_mode&0o100)
        self.assertEqual(extra.stat().st_mode&0o777,0o400)
        self.assertEqual((dst/'SKILL.md').read_text(),'Task real task instructions')
        self.assertEqual((self.workspace/'article.sty').read_text(),'style bytes')

    def test_raw_archive_preserves_readonly_modes_without_host_extraction_and_refuses_bad_producer(self):
        spec=importlib.util.spec_from_file_location('reviewed_ais_archive',SOURCE.parent.parent/'ai_scientist.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w') as archive:
            folder=tarfile.TarInfo('run/readonly');folder.type=tarfile.DIRTYPE;folder.mode=0o555;archive.addfile(folder)
            raw=b'original staged method';file=tarfile.TarInfo('run/readonly/SKILL.md');file.mode=0o444;file.size=len(raw);archive.addfile(file,io.BytesIO(raw))
            link=tarfile.TarInfo('run/alias');link.type=tarfile.SYMTYPE;link.linkname='/outside-not-extracted';archive.addfile(link)
        payload=stream.getvalue()
        class Process:
            def __init__(self,code):self.returncode=code
            def poll(self):return self.returncode
            def wait(self,**kwargs):return self.returncode
        client=SimpleNamespace(binary='/not-executed/docker',env={})
        for label,code,content in [('good',0,payload),('producer-failed',1,payload),('truncated',0,payload[:1024]),('oversized-stderr',0,payload)]:
            state=self.workspace/label;state.mkdir()
            def produce(*a,**kwargs):
                kwargs['stdout'].write(content);kwargs['stdout'].flush();kwargs['stderr'].write(b'x'*(16*1024**2+1) if label=='oversized-stderr' else b'kept diagnostic');kwargs['stderr'].flush();return Process(code)
            with patch.object(driver.subprocess,'Popen',side_effect=produce):
                receipt=driver.archive_artifacts(client,'c'*64,'/owned/run',state)
            self.assertEqual(receipt['verified'],label=='good')
            self.assertFalse((state/'run').exists())
            self.assertEqual((state/'artifacts.tar').read_bytes(),content)
            self.assertEqual((state/'artifact-export.stderr.log').read_bytes(),b'x'*(16*1024**2+1) if label=='oversized-stderr' else b'kept diagnostic')
            if label=='good':
                row=next(x for x in receipt['members'] if x['name'].endswith('SKILL.md'))
                self.assertEqual(row['mode'],0o444)
                self.assertEqual(row['sha256'],engine_patches.digest(raw))
                self.assertFalse(receipt['extracted'])

    def test_launch_rejects_volume_identity_mismatch_before_source_or_docker_side_effects(self):
        spec=importlib.util.spec_from_file_location('reviewed_ais_volume',SOURCE.parent.parent/'ai_scientist.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        mount='/var/lib/docker/volumes/nstack-owned/_data'
        base={'owner':'a'*32,'image_id':'sha256:'+'b'*64,
              'host_dispatch_policy':{'max_requests':1,'turn_timeout_seconds':1,'deadline_seconds_after_launch':30},
              'volume':'nstack-owned','volume_mountpoint':mount,'linux_root':mount+'/run',
              'controller_mounts':[{'type':'volume','source':'nstack-owned','destination':mount}]}
        cases=[]
        for field,value in [('source','retained-other-run'),('destination','/other-destination')]:
            case=json.loads(json.dumps(base));case['controller_mounts'][0][field]=value;cases.append(case)
        for field,value in [('volume_mountpoint','/other-mountpoint'),('linux_root',mount+'/other-run')]:
            case=json.loads(json.dumps(base));case[field]=value;cases.append(case)
        for index,case in enumerate(cases):
            path=self.private/('bad-launch-'+str(index)+'.json');path.write_text(json.dumps(case))
            with patch.object(driver,'tree',side_effect=AssertionError('Source access before identity gate')),                  patch.object(driver.subprocess,'run',side_effect=AssertionError('Docker/model side effect')):
                with self.assertRaisesRegex(ValueError,'volume source/destination'):
                    driver.load_plan(path)

    def test_local_method_index_is_role_scoped_and_preserves_original_prompt_bytes(self):
        tree=ast.parse(SOURCE.with_name('native_dispatch.py').read_text())
        selected=[node for node in tree.body if
                  isinstance(node,ast.FunctionDef) and node.name in {'contains','validate_local_methods','compose_role_prompt'}
                  or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STAGED_METHOD_NAMES' for t in node.targets)]
        class Refusal(RuntimeError):pass
        namespace={'PurePosixPath':PurePosixPath,'re':re,'DispatchRefusal':Refusal}
        exec(compile(ast.Module(body=selected,type_ignores=[]),'actual_role_index','exec'),namespace)
        row={'name':'edit-program','path':'/workspace/.codex/skills/edit-program/SKILL.md','sha256':'a'*64,'bytes':4000}
        methods=namespace['validate_local_methods']([row],'/workspace/attempt')
        original='  # Original role\r\nUse `edit-program` and preserve β.\n'
        effective=namespace['compose_role_prompt'](original,methods)
        self.assertTrue(effective.encode().endswith(original.encode()))
        self.assertIn(row['path'],effective);self.assertIn('read its complete SKILL.md',effective)
        self.assertIn('Do not substitute a global same-name workflow',effective)
        self.assertEqual(namespace['compose_role_prompt'](original,[]),original)
        for changed in ({'path':'/host/.codex/skills/edit-program/SKILL.md'},
                        {'path':'/workspace/sibling/.codex/skills/edit-program/SKILL.md'},
                        {'name':'unreviewed-method'},{'bytes':262145},{'sha256':'bad'}):
            with self.assertRaises(Refusal):namespace['validate_local_methods']([{**row,**changed}],'/workspace/attempt')
        with self.assertRaises(Refusal):namespace['validate_local_methods']([row,row],'/workspace/attempt')

    def test_native_metadata_gate_projects_no_secret_values_and_rejects_drift(self):
        context = {'model': 'current-native-model', 'effort': 'high'}
        cfg = {'model_provider': 'openai', 'model': context['model'],
               'model_reasoning_effort': context['effort'],
               'approval_policy': 'never', 'web_search': 'disabled',
               'project_doc_max_bytes': 0,
               'features': {name: False for name in metadata_gate.CAPABILITIES},
               'memories': {'generate_memories': False, 'use_memories': False,
                            'dedicated_tools': False},
               'skills': {'include_instructions': False, 'bundled': {'enabled': False}},
               'cloud': {'skills': {'enabled': False}},
               'mcp_servers': {'fixture': {'enabled': False,
                                          'http_headers': {'Authorization': 'SYNTHETIC-SECRET'}}},
               'unknown_sensitive_field': 'SYNTHETIC-SECRET'}
        providers = {'defaultProviderId': 'openai', 'data': [
            {'id': 'openai', 'settings': {'type': 'openai'}, 'baseUrl': None}]}
        proof = metadata_gate.project_policy({'config': cfg}, providers, context)
        self.assertNotIn('SYNTHETIC-SECRET', json.dumps(proof))
        self.assertEqual(proof['mcp_names'], ['fixture'])
        cfg['mcp_servers']['fixture']['enabled'] = True
        with self.assertRaises(metadata_gate.MetadataRefusal):
            metadata_gate.project_policy({'config': cfg}, providers, context)
        cfg['mcp_servers']['fixture']['enabled'] = False
        cfg['model'] = 'drifted-default'
        with self.assertRaises(metadata_gate.MetadataRefusal):
            metadata_gate.project_policy({'config': cfg}, providers, context)
        cfg['model'] = context['model']
        cfg['chatgpt_base_url'] = 'SYNTHETIC-SECRET'
        with self.assertRaises(metadata_gate.MetadataRefusal) as caught:
            metadata_gate.project_policy({'config': cfg}, providers, context)
        self.assertNotIn('SYNTHETIC-SECRET', str(caught.exception))

    def test_native_thread_gate_rejects_local_fallback_and_nonexternal_policy(self):
        context = {'model': 'current-native-model', 'effort': 'high'}
        settings = {'model': context['model'], 'effort': context['effort'],
                    'modelProvider': 'openai', 'approvalPolicy': 'never',
                    'environments': [{'environmentId': 'owned-remote'}],
                    'sandboxPolicy': {'type': 'externalSandbox', 'networkAccess': 'restricted'}}
        metadata_gate.verify_thread_settings(settings, context, 'owned-remote')
        settings['environments'].append({'environmentId': 'local'})
        with self.assertRaises(metadata_gate.MetadataRefusal):
            metadata_gate.verify_thread_settings(settings, context, 'owned-remote')
        settings['environments'].pop()
        settings['sandboxPolicy'] = {'type': 'dangerFullAccess'}
        with self.assertRaises(metadata_gate.MetadataRefusal):
            metadata_gate.verify_thread_settings(settings, context, 'owned-remote')

    @unittest.skipUnless(importlib.util.find_spec("websockets"),
                         "pinned optional relay runtime is not installed")
    def test_relay_requires_capability_rejects_origins_and_owns_one_child(self):
        relay_spec = importlib.util.spec_from_file_location(
            "research_executor_relay", SOURCE.with_name("executor_relay.py"))
        relay_module = importlib.util.module_from_spec(relay_spec)
        relay_spec.loader.exec_module(relay_module)
        from websockets.asyncio.client import connect
        from websockets.exceptions import InvalidStatus

        async def scenario():
            async with relay_module.ExecutorRelay(
                    ["/bin/cat"], {"PATH": "/usr/bin:/bin"},
                    timeout_seconds=5, max_bytes=4096) as relay:
                wrong = relay.url.rsplit("/", 1)[0] + "/wrong"
                with self.assertRaises(InvalidStatus):
                    async with connect(wrong, proxy=None):
                        self.fail("wrong endpoint accepted")
                with self.assertRaises(InvalidStatus):
                    async with connect(relay.url, origin="https://example.invalid", proxy=None):
                        self.fail("browser Origin accepted")
                self.assertFalse(relay.events["child_started"])
                self.assertNotIn(relay._capability, relay.redact(relay.url))
                async with connect(relay.url, proxy=None) as websocket:
                    await websocket.send('{"fixture":true}')
                    self.assertEqual(await websocket.recv(), '{"fixture":true}')
                    with self.assertRaises(InvalidStatus):
                        async with connect(relay.url, proxy=None):
                            self.fail("second client accepted")
                await asyncio.wait_for(relay.done.wait(), 5)
                self.assertEqual(relay.events["accepted_connections"], 1)
                self.assertEqual(relay.events["rejected_connections"], 3)
                self.assertIsNotNone(relay.process.returncode)
        asyncio.run(scenario())

    def test_engine_patches_check_all_preimages_and_preserve_recoverable_originals(self):
        source = self.root / "engine"
        source.mkdir()
        package = self.root / "patcher"
        (package / "patches").mkdir(parents=True)
        items = []
        for name in ("one.py", "two.py"):
            original = b"VALUE = 1\n"
            changed = b"VALUE = 2\n"
            (source / name).write_bytes(original)
            patch_name = name + ".patch"
            (package / "patches" / patch_name).write_text("saved reviewed diff\n")
            items.append({"path": name,
                          "original_sha256": engine_patches.digest(original),
                          "patched_sha256": engine_patches.digest(changed),
                          "replace_before": original.decode(),
                          "replace_after": changed.decode(), "patch": patch_name})
        (package / "patches/manifest.json").write_text(json.dumps(
            {"repository": "fixture", "commit": "pin", "files": items}))
        archive = self.root / "saved-originals"
        (source / "two.py").write_text("VALUE = 3\n")
        with patch.object(engine_patches, "__file__", str(package / "patcher.py")):
            with self.assertRaisesRegex(ValueError, "preimage drift"):
                engine_patches.apply(source, archive)
            self.assertEqual((source / "one.py").read_bytes(), b"VALUE = 1\n")
            self.assertFalse(archive.exists())
            (source / "two.py").write_bytes(b"VALUE = 1\n")
            engine_patches.apply(source, archive)
            for item in items:
                name = item["path"]
                self.assertEqual((source / name).read_bytes(), b"VALUE = 2\n")
                self.assertEqual((archive / name).read_bytes(), b"VALUE = 1\n")
                # Restoration is rehearsed in this separate disposable tree.
                shutil.copyfile(archive / name, source / name)
                self.assertEqual(engine_patches.digest((source / name).read_bytes()),
                                 item["original_sha256"])
            with self.assertRaises(FileExistsError):
                engine_patches.apply(source, archive)

    def test_context_tracks_live_metadata_and_refuses_advanced_turn(self):
        initial = transport.current_context(self.reference)
        self.assertEqual(initial["model"], "test-current-model")
        self.assertNotIn("DO NOT RETAIN THIS", json.dumps(initial))
        with self.source.open("a") as stream:
            stream.write(json.dumps({"type": "turn_context", "payload": {
                "turn_id": "turn-one", "model": "new-current-model", "effort": "medium"}}) + "\n")
        self.assertEqual(transport.current_context(self.reference)["model"], "new-current-model")
        with self.source.open("a") as stream:
            stream.write(json.dumps({"type": "turn_context", "payload": {
                "turn_id": "turn-two", "model": "new-current-model", "effort": "high"}}) + "\n")
        with self.assertRaisesRegex(transport.TransportError, "advanced"):
            transport.current_context(self.reference)

    def test_wrong_thread_missing_effort_and_symlink_reference_fail(self):
        self.source.write_text(json.dumps({"type": "session_meta", "payload": {
            "id": "other-thread", "model_provider": "openai"}}) + "\n")
        with self.assertRaises(transport.TransportError):
            transport.current_context(self.reference)
        link = self.root / "link.json"
        link.symlink_to(self.reference)
        with self.assertRaises(transport.TransportError):
            transport.current_context(link)

    def test_command_preserves_context_and_never_uses_fallback_or_permission_bypass(self):
        context = transport.current_context(self.reference)
        command = transport.build_command("/native/codex", self.manifest, context,
                                          self.workspace, read_only=False)
        self.assertIn("test-current-model", command)
        self.assertIn('model_reasoning_effort="high"', command)
        self.assertIn('model_provider="openai"', command)
        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("--ignore-rules", command)
        joined = " ".join(command)
        self.assertNotIn("dangerously", joined.replace('"dangerously_allow_all_unix_sockets"=false', ''))
        self.assertNotIn("forced_login_method", joined)
        self.assertIn("features.multi_agent_v2=false", command)
        self.assertIn("features.plugins=false", command)
        self.assertIn("mcp_servers={}", command)
        self.assertEqual(transport.policy(self.manifest, read_only=True)["filesystem"][str(self.workspace)], "read")
        with self.assertRaises(transport.TransportError):
            transport.build_command("/native/codex", self.manifest, context, self.root, read_only=False)

    def test_clean_client_environment_excludes_provider_keys_and_remote_executor(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-never-export",
                     "CODEX_API_KEY": "synthetic-never-export", "CODEX_EXEC_SERVER_URL": "http://invalid",
                     "HEADLESS_BILLING": "api"}):
            clean = transport.clean_environment()
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertNotIn("CODEX_API_KEY", clean)
        self.assertNotIn("CODEX_EXEC_SERVER_URL", clean)
        self.assertNotIn("HEADLESS_BILLING", clean)

    def test_native_status_is_reduced_without_leaking_or_mutating_auth(self):
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "API key configured - synthetic\n")) as run:
            self.assertFalse(transport.subscription_ready("codex"))
            self.assertEqual(run.call_args.args[0], ["codex", "login", "status"])
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "Logged in using ChatGPT\n")):
            self.assertTrue(transport.subscription_ready("codex"))

    def test_missing_native_usage_fails_and_measured_usage_has_no_fabricated_cost(self):
        context = transport.current_context(self.reference)
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": "answer"}},
                  {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2,
                   "cached_input_tokens": 0, "reasoning_output_tokens": 1}}]
        answer, usage = transport.parse_events("\n".join(map(json.dumps, events)), context)
        self.assertEqual(answer, "answer")
        self.assertIsNone(usage["cost"])
        self.assertEqual(usage["input_tokens"], 10)
        events[-1]["usage"].pop("input_tokens")
        with self.assertRaises(transport.TransportError):
            transport.parse_events("\n".join(map(json.dumps, events)), context)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("codex"), "requires installed native Codex sandbox")
    def test_real_native_policy_denies_private_symlinks_ancestor_rename_and_sockets(self):
        group = self.workspace / "group"
        group.mkdir()
        sealed = group / "sealed"
        sealed.mkdir()
        (sealed / "hidden.txt").write_text("synthetic protected")
        (self.private / "hidden.txt").write_text("synthetic protected")
        (self.workspace / "public.txt").write_text("synthetic public")
        (self.workspace / "escape").symlink_to(self.private, target_is_directory=True)
        self.manifest["deny_roots"].append(sealed)
        server = socket.socket(socket.AF_UNIX)
        self.addCleanup(server.close)
        sock_path = self.workspace / "synthetic-docker.sock"
        server.bind(str(sock_path))
        server.listen(1)
        probe = self.workspace / "probe.py"
        probe.write_text('''import json,os,pathlib,socket,sys
w=pathlib.Path(sys.argv[1]);p=pathlib.Path(sys.argv[2]);r={}
for name,path in [('public',w/'public.txt'),('private',p/'hidden.txt'),('symlink',w/'escape'/'hidden.txt'),('sealed',w/'group'/'sealed'/'hidden.txt')]:
 try:path.read_bytes();r[name]=True
 except PermissionError:r[name]=False
try:(w/'new.txt').write_text('public output');r['write']=True
except PermissionError:r['write']=False
try:os.rename(w/'group',w/'moved');r['rename']=True
except PermissionError:r['rename']=False
for name,family,address in [('unix',socket.AF_UNIX,str(w/'synthetic-docker.sock')),('tcp',socket.AF_INET,('127.0.0.1',9))]:
 try:
  s=socket.socket(family);s.settimeout(1);s.connect(address);r[name]=True
 except PermissionError:r[name]=False
print(json.dumps(r))
''')
        profile = transport.policy(self.manifest, read_only=False)
        command = [shutil.which("codex"), "sandbox", "-P", "nstack_probe", "-C", str(self.workspace),
                   "-c", "permissions.nstack_probe=" + transport.toml(profile), "--",
                   "/usr/bin/python3", str(probe), str(self.workspace), str(self.private)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30,
                                env=transport.clean_environment())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"public": True, "private": False,
             "symlink": False, "sealed": False, "write": True, "rename": False,
             "unix": False, "tcp": False})
