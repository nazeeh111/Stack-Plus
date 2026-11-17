#!/usr/bin/env python3
"""Run the original six-phase AIS CLI with its reviewed native transport.

A caller supplies one concrete reviewed launch document and exact task inputs.
This owns ordinary local containers and a private prepared-request queue only.
Scientific stages, decisions, evaluators and paper validation remain upstream.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import subprocess
import time
import tarfile
import signal
import stat

HERE = Path(__file__).resolve().parent
CODE = HERE/'codex-transport'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


queue = module('nstack_ais_queue', CODE/'request_queue.py')
LocalDocker = module('nstack_ais_local_docker', HERE.parents[1]/'lib/docker_client.py').LocalDocker


def save(path, value):
    queue._atomic.atomic_json(path, value)


def tree(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink(): raise ValueError('Source/input aliases are unsupported')
        if path.is_file(): result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def load_plan(path):
    plan = json.loads(path.read_text())
    if (not re.fullmatch('[0-9a-f]{32}', plan['owner']) or not re.fullmatch('sha256:[0-9a-f]{64}', plan['image_id'])
            or not 1 <= plan['host_dispatch_policy']['max_requests'] <= 40
            or not 1 <= plan['host_dispatch_policy']['turn_timeout_seconds'] <= 600
            or not 1 <= plan['host_dispatch_policy']['deadline_seconds_after_launch'] <= 14400):
        raise ValueError('Concrete launch identity or bounds differ')
    volumes=[row for row in plan['controller_mounts'] if row['type']=='volume']
    expected_mount='/var/lib/docker/volumes/'+plan['volume']+'/_data'
    if (len(volumes)!=1 or volumes[0]['source']!=plan['volume']
            or volumes[0]['destination']!=plan['volume_mountpoint']
            or plan['volume_mountpoint']!=expected_mount
            or plan['linux_root']!=expected_mount+'/run'):
        raise ValueError('Concrete volume source/destination/mountpoint/run-root identity differs')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=plan['driver']['sha256']:
        raise ValueError('Reviewed campaign driver differs')
    controller_cli=Path(plan['controller_cli']['path'])
    if (controller_cli.is_symlink() or not controller_cli.is_file()
            or hashlib.sha256(controller_cli.read_bytes()).hexdigest()!=plan['controller_cli']['sha256']):
        raise ValueError('Durable reviewed controller CLI differs')
    source = Path(plan['source']['source'])
    if hashlib.sha256(json.dumps(tree(source), sort_keys=True).encode()).hexdigest() != plan['source']['source_tree_sha256']:
        raise ValueError('Readonly original adapted source differs')
    for filename, expected in plan['host_dispatch_policy']['binding_sha256'].items():
        if hashlib.sha256((CODE/filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Reviewed binding source differs')
    if plan['controller_user'] != f'{os.getuid()}:{os.getgid()}':
        raise ValueError('Concrete controller UID/GID differs from this host')
    required = {'container.enabled=true', 'container.network=none', 'container.image='+plan['image_id'],
                'agent.name=codex', 'agent.model=null', 'agent.reasoning_effort=null',
                'execution.phases=task_drafting,investigation,ablations,final_evaluation,posthoc,paper'}
    if not required.issubset(plan['pipeline_argv']): raise ValueError('Original full phase/container/native contract differs')
    return plan


def owned_children(client, plan, ledger):
    ids = client.run(['ps', '-aq', '--filter', 'label=nstack.research.owner='+plan['owner']]).stdout.split()
    verified = []
    for ident in ids:
        info = json.loads(client.run(['inspect', ident]).stdout)[0]
        labels = info['Config'].get('Labels') or {}; launch = labels.get('nstack.research.launch', '')
        if labels.get('nstack.research.owner') != plan['owner'] or not re.fullmatch('[0-9a-f]{32}', launch):
            raise ValueError('Child cleanup ownership differs')
        record = queue.read_object(ledger/(launch+'.json'))
        if record.get('owner') != plan['owner'] or record.get('launch') != launch:
            raise ValueError('Child cleanup private launch differs')
        verified.append(info['Id'])
    return verified


class Client:
    def __init__(self, native): self.binary, self.env = native.binary, native.env
    def run(self, arguments, *, timeout=30, check=True):
        return subprocess.run([self.binary, *arguments], env=self.env, capture_output=True,
                              text=True, timeout=timeout, check=check)


async def run_original(client, plan, state, controller_id):
    dispatch = module('nstack_ais_native_dispatch', CODE/'native_dispatch.py')
    settings = dict(plan['host_dispatch_policy'])
    settings['deadline_at'] = time.time()+settings['deadline_seconds_after_launch']
    settings['receipt_root'] = str(state/'requests'); settings['ledger'] = str(state/'queue/ledger')
    dispatcher = dispatch.HostDispatcher(settings, client.binary, client.env)
    command = [client.binary, 'exec', controller_id, *plan['pipeline_argv']]
    process = await asyncio.create_subprocess_exec(*command, env=client.env,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async def retain(stream, path):
        count = 0
        with path.open('wb') as output:
            while chunk := await stream.read(65536):
                count += len(chunk)
                if count > 16*1024*1024: raise RuntimeError('Original controller output exceeded bound')
                output.write(chunk); output.flush()
        return count
    readers = [asyncio.create_task(retain(process.stdout,state/'controller.stdout.log')),
               asyncio.create_task(retain(process.stderr,state/'controller.stderr.log'))]
    completed = set(); deadline = time.monotonic()+settings['deadline_seconds_after_launch']
    try:
        while process.returncode is None:
            if time.monotonic() >= deadline: raise TimeoutError('Authorized original campaign deadline reached')
            for reader in readers:
                if reader.done() and reader.exception(): raise reader.exception()
            for request in queue.pending(state/'queue', completed):
                try:
                    answer, usage = await dispatcher.dispatch(request, allow_inference=True)
                except BaseException:
                    queue.finish(state/'queue', request, success=False)
                    # An uncertain or rejected dispatch never becomes an implicit
                    # upstream retry/provider fallback. Stop this owned campaign.
                    raise
                queue.finish(state/'queue', request, success=True, answer=answer, usage=usage)
                completed.add(request['request_id'])
            await asyncio.sleep(.1)
        await asyncio.gather(*readers)
        return {'controller_exit': await process.wait(), 'completed_native_requests': len(completed)}
    finally:
        if process.returncode is None:
            client.run(['stop', '--time', '10', controller_id], check=False)
            try: await asyncio.wait_for(process.wait(), 15)
            except TimeoutError: process.kill(); await process.wait()
        await asyncio.gather(*readers, return_exceptions=True)


def archive_artifacts(client, ident, root, state, *, timeout=120, max_bytes=4*1024**3):
    """Retain exact raw Docker tar bytes without mode-sensitive host extraction."""
    archive=state/'artifacts.tar';stderr=state/'artifact-export.stderr.log'
    receipt={'archive':str(archive),'verified':False,'extracted':False};process=None
    started=time.monotonic()
    try:
        with archive.open('xb') as output, stderr.open('xb') as errors:
            process=subprocess.Popen([client.binary,'cp',ident+':'+root,'-'],env=client.env,
                                     stdout=output,stderr=errors,start_new_session=True)
            while process.poll() is None:
                if (time.monotonic()-started>timeout or archive.stat().st_size>max_bytes
                        or stderr.stat().st_size>16*1024**2):
                    raise TimeoutError('Bounded artifact archive transfer stopped')
                time.sleep(.1)
            receipt['producer_exit']=process.wait()
        if receipt['producer_exit']!=0:raise ValueError('Artifact archive producer failed')
        if stderr.stat().st_size>16*1024**2:raise ValueError('Artifact export stderr exceeded bound')
        if time.monotonic()-started>timeout:raise TimeoutError('Artifact export deadline reached')
        size=archive.stat().st_size
        if size<1024 or size>max_bytes or size%512:raise ValueError('Artifact archive size is invalid')
        with archive.open('rb') as stream:
            stream.seek(-1024,2)
            if stream.read()!=bytes(1024):raise ValueError('Artifact archive lacks complete tar footer')
        members=[]
        with tarfile.open(archive,'r:') as bundle:
            for member in bundle:
                name=PurePosixPath(member.name)
                if (name.is_absolute() or '..' in name.parts or len(members)>=200000
                        or time.monotonic()-started>timeout):
                    raise ValueError('Artifact archive member bounds/path invalid')
                row={'name':member.name,'mode':member.mode,'size':member.size,
                     'type':member.type.decode('ascii','replace'),'linkname':member.linkname}
                if member.isfile():
                    digest=hashlib.sha256();stream=bundle.extractfile(member)
                    while chunk:=stream.read(1024**2):
                        if time.monotonic()-started>timeout:raise TimeoutError('Artifact member hash deadline reached')
                        digest.update(chunk)
                    row['sha256']=digest.hexdigest()
                members.append(row)
        digest=hashlib.sha256()
        with archive.open('rb') as stream:
            while chunk:=stream.read(1024**2):
                if time.monotonic()-started>timeout:raise TimeoutError('Artifact archive hash deadline reached')
                digest.update(chunk)
        if time.monotonic()-started>timeout:raise TimeoutError('Artifact verification deadline reached')
        receipt['sha256']=digest.hexdigest()
        receipt.update(bytes=size,members=members,verified=True)
    except (OSError,ValueError,TimeoutError,tarfile.TarError) as error:
        receipt['failure_type']=type(error).__name__
    finally:
        if process and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        if stderr.exists():
            receipt['stderr_bytes']=stderr.stat().st_size
            with stderr.open('rb') as stream:receipt['stderr_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        save(state/'ARTIFACTS.json',receipt)
    return receipt


def execute(plan, inputs, state, endpoint):
    if state.exists() or state.is_symlink(): raise ValueError('Preserve prior run; select fresh private state')
    inputs = inputs.resolve(strict=True)
    if any(path.name == 'setup.py' for path in inputs.rglob('*')): raise ValueError('This binding requires genuinely absent setup.py')
    if (not re.fullmatch('[a-z0-9][a-z0-9_-]*',plan['task_name'])
            or state.expanduser().absolute()!=state.resolve()
            or next(row['source'] for row in plan['controller_mounts']
                    if row['destination']=='/run/nstack-native-bridge') != str(state/'queue')):
        raise ValueError('Concrete run state or task name differs')
    actual_inputs = tree(inputs)
    if actual_inputs != plan['input_sha256']: raise ValueError('Frozen explicit input view differs')
    state.mkdir(mode=0o700, parents=True)
    for directory in ['queue','queue/requests','queue/responses','queue/ledger','requests']:
        (state/directory).mkdir(mode=0o700)
    queue._atomic.atomic_json(state/'queue/queue.json', {'owner':plan['owner'],
                'request_timeout_seconds':plan['host_dispatch_policy']['turn_timeout_seconds']})
    queue._atomic.atomic_json(state/'queue/guard.json',plan['guard_policy'])
    receipt = {'state':'preparing','owner':plan['owner'],'input_sha256':actual_inputs,
               'launch_sha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
               'inference':'not_requested','artifact_exported':False}
    with LocalDocker(endpoint) as native:
        client = Client(native); volume = plan['volume']; controller = plan['controller_name']
        ident = None; created_volume = False
        try:
            # Creation has no replacement fallback. Never adopt an existing
            # volume/container merely because its name matches the launch file.
            exists = client.run(['volume','inspect',volume],check=False)
            if exists.returncode == 0: raise ValueError('Owned volume name already exists; preserve it')
            client.run(['volume','create','--label','nstack.research.owner='+plan['owner'],volume]); created_volume=True
            meta=json.loads(client.run(['volume','inspect',volume]).stdout)[0]
            if meta['Mountpoint'] != plan['volume_mountpoint'] or meta['Labels'].get('nstack.research.owner') != plan['owner']:
                raise ValueError('Actual daemon volume path/owner differs')
            command=['run','-d','--pull=never','--name',controller,'--label','nstack.research.controller='+plan['owner'],
                    '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                    '--user',plan['controller_user'],'--group-add',str(plan['controller_socket_gid']),
                    '--cpus','2','--memory','2147483648','--pids-limit','4096',
                    '--tmpfs','/tmp:rw,nosuid,nodev,size=268435456,mode=1777']
            for row in plan['controller_mounts']:
                value='type='+row['type']+',src='+row['source']+',dst='+row['destination']
                if not row['writable']: value+=',readonly'
                command+=['--mount',value]
            for key,value in plan['controller_environment'].items():command+=['--env',key+'='+value]
            command+=['--workdir',plan['source']['source'],plan['image_id'],'/bin/sleep',str(plan['host_dispatch_policy']['deadline_seconds_after_launch']+300)]
            receipt['controller_argv']=[client.binary,*command]
            ident=client.run(command).stdout.strip()
            if not re.fullmatch('[0-9a-f]{64}',ident):raise ValueError('Owned controller ID absent')
            # The daemon's ordinary archive copy preserves actual caller UID/GID.
            # No chown/capability/privileged/native-permission relaxation is used.
            staging=state/'initial/run';staging.mkdir(mode=0o700,parents=True)
            for name in ['tasks','results','work','empty-mask','private-control/home','private-control/docker-config']:
                (staging/name).mkdir(mode=0o700,parents=True)
            shutil.copytree(inputs,staging/'tasks'/plan['task_name'])
            (staging/'private-control/docker-config/config.json').write_text('{"auths":{}}\n')
            (staging/'private-control/empty.env').write_text('')
            client.run(['cp','-a',str(staging),ident+':'+plan['volume_mountpoint']])
            proof="import os,json;from pathlib import Path, PurePosixPath;p=Path(os.environ['NSTACK_RUN_ROOT']);s=p.stat();assert os.getuid()==s.st_uid and s.st_mode&511==448;assert Path('/var/run/docker.sock').stat().st_gid==int(os.environ['NSTACK_SOCKET_GID']);print(json.dumps({'uid':os.getuid(),'run_mode':oct(s.st_mode&511),'socket_gid':Path('/var/run/docker.sock').stat().st_gid}))"
            receipt['initialization']=json.loads(client.run(['exec',ident,'/usr/local/bin/python','-I','-B','-c',proof]).stdout)
            receipt.update(asyncio.run(run_original(client,plan,state,ident)))
            receipt['state']='original_pipeline_completed' if receipt['controller_exit']==0 else 'original_pipeline_failed'
        except BaseException as error:
            receipt['state']='failed_or_interrupted';receipt['failure_type']=type(error).__name__
            raise
        finally:
            # Preserve full owned run artifacts before removing any storage.
            try:
                if ident:
                    export=archive_artifacts(client,ident,plan['linux_root'],state)
                    receipt['artifact_export_exit']=export.get('producer_exit')
                    receipt['artifact_exported']=export['verified']
                    receipt['artifact_archive_sha256']=export.get('sha256')
                    receipt['artifact_export_failure_type']=export.get('failure_type')
                    children=owned_children(client,plan,state/'queue/ledger')
                    if children:receipt['child_cleanup_exit']=client.run(['rm','-f',*children],check=False).returncode
                    info=json.loads(client.run(['inspect',ident]).stdout)[0]
                    if info['Config']['Labels'].get('nstack.research.controller') != plan['owner']:raise ValueError('Controller cleanup ownership differs')
                    receipt['controller_cleanup_exit']=client.run(['rm','-f',info['Id']],check=False).returncode
                if created_volume and receipt['artifact_exported']:
                    receipt['volume_cleanup_exit']=client.run(['volume','rm',volume],check=False).returncode
                elif created_volume:receipt['volume_retained_for_recovery']=volume
            except (ValueError,OSError,subprocess.SubprocessError) as cleanup_error:
                receipt['cleanup_failure_type']=type(cleanup_error).__name__
                if created_volume:receipt['volume_retained_for_recovery']=volume
            finally:
                # Per-request attempted/sent/unknown/completed journals are the
                # authority for inference/usage, including interrupted native turns.
                receipt['inference']='consult_per_request_native_journals'
                receipt['overall_exit']=overall_exit(receipt)
                receipt['delivery_complete']=receipt['overall_exit']==0
                if receipt.get('controller_exit')==0 and not receipt['delivery_complete']:
                    receipt['state']='incomplete_artifact_or_cleanup'
                save(state/'RUN.json',receipt)
    return receipt


def overall_exit(receipt):
    """Preserve scientific exit while refusing incomplete delivery/cleanup."""
    scientific = receipt.get('controller_exit', 1)
    if scientific: return scientific
    complete = (receipt.get('artifact_exported') is True
                and receipt.get('controller_cleanup_exit') == 0
                and receipt.get('volume_cleanup_exit') == 0
                and receipt.get('child_cleanup_exit', 0) == 0
                and not receipt.get('cleanup_failure_type')
                and not receipt.get('volume_retained_for_recovery'))
    return 0 if complete else 2


def report_directory(path):
    """Report only explicit canonical private state; never follow a state alias."""
    info = path.stat()
    if (not path.is_absolute() or path.resolve() != path or path.is_symlink()
            or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077):
        raise ValueError('Report requires a canonical private owner-controlled directory')


def report_object(path, *, optional=False):
    if optional and not path.exists() and not path.is_symlink():
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_nlink != 1
                or info.st_size > queue.MAX_BYTES):
            raise ValueError('Report receipt must be a bounded private regular file without aliases')
        with os.fdopen(descriptor, 'r', closefd=False) as stream:
            value = json.load(stream)
    finally:
        os.close(descriptor)
    if not isinstance(value, dict):
        raise ValueError('Report receipt must be a JSON object')
    return value


REPORT_COUNTERS = ('inputTokens', 'outputTokens', 'totalTokens',
                   'cachedInputTokens', 'reasoningOutputTokens')


def reported_usage(value):
    if value is None:
        return None
    if (not isinstance(value, dict)
            or any(type(value.get(k)) is not int or value[k] < 0 for k in REPORT_COUNTERS)
            or value['totalTokens'] != value['inputTokens'] + value['outputTokens']
            or value['cachedInputTokens'] > value['inputTokens']
            or value['reasoningOutputTokens'] > value['outputTokens']):
        raise ValueError('Invalid native cumulative token counters')
    return {key: value[key] for key in REPORT_COUNTERS}


def report_label(value, choices=None):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', value):
        raise ValueError('Invalid receipt status or exception type')
    if choices is not None and value not in choices:
        raise ValueError('Unrecognized recorded status')
    return value


def report_exit(value):
    if value is not None and type(value) is not int:
        raise ValueError('Invalid recorded exit status')
    return value


def report_flag(value):
    if value is not None and type(value) is not bool:
        raise ValueError('Invalid recorded boolean status')
    return value


def report_retained_volume(value):
    # execute retains the actual volume name, not a boolean. Project its
    # presence only; recovery identities are not part of this public summary.
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,254}', value):
        raise ValueError('Invalid retained recovery volume identity')
    return True


def report_request(directory, ident):
    report_directory(directory)
    path = directory/'receipt.json'
    receipt = report_object(path, optional=True)
    journal = report_object(directory/'turn-state.json', optional=True)
    if receipt is not None and receipt.get('request_id') != ident:
        raise ValueError('Native request receipt identity differs')
    receipt = receipt or {}
    embedded = receipt.get('turn_state')
    if embedded is not None and not isinstance(embedded, dict):
        raise ValueError('Invalid embedded native turn journal')
    journals = [value for value in (journal, embedded) if value is not None]
    complete = receipt.get('native_turn')
    partial = receipt.get('partial_native')
    if complete is not None and partial is not None:
        raise ValueError('Ambiguous complete and partial native receipt')
    native = complete if complete is not None else partial
    if native is not None and not isinstance(native, dict):
        raise ValueError('Invalid native evidence object')
    native = native or {}
    # A matching usage snapshot does not bind two journals to the same turn.
    # Early producer states legitimately have no turn ID. Reconcile every
    # present identity before accepting any completed-turn proof.
    turn_ids = set()
    for value in [receipt, native, *journals]:
        if value.get('request_id') is not None and value['request_id'] != ident:
            raise ValueError('Native evidence request identity differs')
        turn_id = value.get('turn_id')
        if turn_id is not None:
            if not isinstance(turn_id, str) or not turn_id or len(turn_id) > 256:
                raise ValueError('Invalid native turn identity')
            turn_ids.add(turn_id)
    if len(turn_ids) > 1:
        raise ValueError('Conflicting native turn identities')
    usage = reported_usage(native.get('usage'))
    completion = 'unknown'
    if complete is not None:
        if (not complete.get('turn_id')
                or complete.get('status') != 'completed' or complete.get('error_present') is not False
                or usage is None or not isinstance(complete.get('answer_sha256'), str)
                or not re.fullmatch('[0-9a-f]{64}', complete['answer_sha256'])):
            raise ValueError('Invalid completed native turn proof')
        completion = 'recorded_completed'
    journal_states = []
    for value in journals:
        state = report_label(value.get('state'), {
            'attempted', 'sent_to_native', 'accepted_by_native', 'interruption_unavailable',
            'interruption_attempted', 'interruption_acknowledged', 'native_turn_completed',
            'native_turn_failed', 'native_turn_interrupted', 'completed'})
        if state and state not in journal_states:
            journal_states.append(state)
        if state == 'completed':
            measured = reported_usage(value.get('measured_usage'))
            if (not value.get('turn_id') or measured is None
                    or usage is not None and measured != usage):
                raise ValueError('Completed native journal lacks consistent turn/usage evidence')
            usage = measured
            completion = 'recorded_completed'
    items = native.get('items')
    counts = None
    if items is not None:
        if not isinstance(items, list):
            raise ValueError('Invalid native item projection')
        counts = {'completed_item_projections': len(items), 'command_executions': 0,
                  'agent_messages': 0, 'reasoning_items': 0, 'command_exits': {}}
        for item in items:
            if (not isinstance(item, dict) or not isinstance(item.get('type'), str)
                    or set(item) - {'type', 'id', 'status', 'exitCode', 'text_sha256'}):
                raise ValueError('Invalid privacy-safe native item projection')
            kind = item['type']
            if kind == 'commandExecution':
                counts['command_executions'] += 1
                exit_code = report_exit(item.get('exitCode'))
                if exit_code is not None:
                    key = str(exit_code)
                    counts['command_exits'][key] = counts['command_exits'].get(key, 0) + 1
            elif kind == 'agentMessage':
                counts['agent_messages'] += 1
            elif kind == 'reasoning':
                counts['reasoning_items'] += 1
    declared = report_label(receipt.get('inference'),
                            {'unknown', 'not_requested', 'occurred', 'occurred_or_unknown'})
    positive = (completion == 'recorded_completed' or declared == 'occurred'
                or usage is not None and any(usage.values())
                or counts is not None and any(counts[k] for k in
                    ('command_executions', 'agent_messages', 'reasoning_items')))
    inference = 'occurred' if positive else ('not_requested' if declared == 'not_requested' else 'unknown')
    return {'request_id': ident, 'receipt': str(path),
            'receipt_status': 'present' if path.exists() else 'missing',
            'dispatch_state': report_label(receipt.get('state'), {'preparing', 'prepared_no_inference',
                'failed_before_inference', 'failed_or_uncertain', 'completed'}),
            'failure_type': report_label(receipt.get('failure_type')),
            'journal_states': journal_states, 'journal_inference': declared,
            'inference_evidence': inference, 'native_completion': completion,
            'usage_status': ('reported_for_completed_turn' if completion == 'recorded_completed'
                             else 'partial_snapshot') if usage is not None else 'unknown',
            'reported_cumulative_usage': usage, 'items': counts,
            'final_usage': 'not_independently_established', 'billing': 'unknown'}


def report_state(state):
    """Read retained native evidence only, without loading a launch or any runtime."""
    report_directory(state)
    run = report_object(state/'RUN.json')
    if not isinstance(run.get('owner'), str) or not re.fullmatch('[0-9a-f]{32}', run['owner']):
        raise ValueError('Invalid owned run receipt identity')
    rows = []
    requests = state/'requests'
    if requests.exists() or requests.is_symlink():
        report_directory(requests)
        entries = sorted(requests.glob('request-*'))
        if len(entries) > 40:
            raise ValueError('Native request receipt count exceeds the recorded driver contract')
        for directory in entries:
            ident = directory.name.removeprefix('request-')
            if not re.fullmatch('[0-9a-f]{32}', ident):
                raise ValueError('Invalid native request directory identity')
            row = report_request(directory, ident)
            response_root = state/'queue/responses'
            if response_root.exists() or response_root.is_symlink():
                report_directory(response_root)
                response = report_object(response_root/(ident+'.json'), optional=True)
                if response is not None:
                    if (type(response.get('schema_version')) is not int or response['schema_version'] != 1
                            or response.get('owner') != run['owner']
                            or response.get('request_id') != ident or type(response.get('success')) is not bool):
                        raise ValueError('Queue response identity or status differs')
                    row['queue_response'] = {'success': response['success'],
                                             'usage_present': response.get('usage') is not None}
            rows.append(row)
    measured = [row for row in rows if row['reported_cumulative_usage'] is not None]
    subtotal = {key: sum(row['reported_cumulative_usage'][key] for row in measured)
                for key in REPORT_COUNTERS} if measured else None
    cleanup = {key: report_exit(run.get(key)) for key in
               ('child_cleanup_exit', 'controller_cleanup_exit', 'volume_cleanup_exit')}
    cleanup['failure_type'] = report_label(run.get('cleanup_failure_type'))
    cleanup['volume_retained_for_recovery'] = report_retained_volume(run.get('volume_retained_for_recovery'))
    cleanup['status'] = ('recorded_failure' if cleanup['failure_type'] or any(
        cleanup[key] not in (None, 0) for key in ('child_cleanup_exit', 'controller_cleanup_exit', 'volume_cleanup_exit'))
        else 'recorded_success_for_reported_steps' if any(cleanup[key] == 0 for key in
            ('child_cleanup_exit', 'controller_cleanup_exit', 'volume_cleanup_exit')) else 'unknown')
    artifacts = report_object(state/'ARTIFACTS.json', optional=True)
    artifact_summary = {'exported_in_run_receipt': report_flag(run.get('artifact_exported')),
                        'producer_exit': report_exit(run.get('artifact_export_exit')),
                        'failure_type': report_label(run.get('artifact_export_failure_type')),
                        'manifest_present': artifacts is not None}
    if artifacts is not None:
        if type(artifacts.get('verified')) is not bool:
            raise ValueError('Invalid artifact verification receipt')
        artifact_summary['verified_in_manifest'] = artifacts['verified']
        artifact_summary['verification_scope'] = 'retained receipt; archive not revalidated by report'
    return {'scope': 'Offline read-only native journal reconciliation; no launch/runtime execution',
            'run_receipt': str(state/'RUN.json'), 'run_state': report_label(run.get('state'),
                {'preparing', 'failed_or_interrupted', 'original_pipeline_completed',
                 'original_pipeline_failed', 'incomplete_artifact_or_cleanup'}),
            'failure_type': report_label(run.get('failure_type')),
            'overall_exit': report_exit(run.get('overall_exit')),
            'controller_exit': report_exit(run.get('controller_exit')),
            'delivery_complete': report_flag(run.get('delivery_complete')), 'cleanup': cleanup,
            'artifacts': artifact_summary, 'requests': rows,
            'inference_evidence': ('occurred' if any(row['inference_evidence'] == 'occurred' for row in rows)
                                   else 'not_requested' if rows and all(row['inference_evidence'] == 'not_requested' for row in rows)
                                   else 'unknown'),
            'reported_usage_subtotal': subtotal, 'requests_with_usage': len(measured),
            'requests_without_usage': len(rows) - len(measured),
            'usage_scope': 'One cumulative snapshot per request; cached/reasoning counts are included components, not added to total',
            'final_completion_and_usage': 'Consult per-request evidence; missing completion/usage remains unknown',
            'billing': 'unknown; no charges inferred from counters or upstream missing usage'}


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['plan','run','report'])
    parser.add_argument('--launch',type=Path)
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--state',type=Path)
    parser.add_argument('--docker-host',help='Existing local Unix socket only; no daemon startup')
    args=parser.parse_args()
    if args.operation != 'report' and args.launch is None:
        parser.error('plan and run require --launch')
    try:
        if args.operation == 'report':
            if args.state is None or args.launch is not None or args.inputs is not None or args.docker_host is not None:
                parser.error('report requires only --state EXPLICIT_OWNED_STATE')
            print(json.dumps(report_state(args.state), indent=2))
            return 0
        plan=load_plan(args.launch)
        if args.operation=='plan':
            print(json.dumps({'source':plan['source'],'image':plan['image_id'],'pipeline_argv':plan['pipeline_argv'],
                              'max_requests':plan['host_dispatch_policy']['max_requests'],
                              'deadline_seconds':plan['host_dispatch_policy']['deadline_seconds_after_launch'],
                              'scope':'Plan only, no model/auth/Docker launch'},indent=2));return 0
        if not args.inputs or not args.state:parser.error('run requires exact --inputs and fresh --state')
        receipt=execute(plan,args.inputs,args.state,args.docker_host)
        return overall_exit(receipt)
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        message = str(error).strip() or type(error).__name__
        if args.operation == 'run' and args.state is not None:
            receipt_path = args.state/'RUN.json'
            if receipt_path.is_file() and not receipt_path.is_symlink():
                message += '; inspect owning receipt ' + str(receipt_path)
        parser.error(message)
    return 1


if __name__=='__main__':raise SystemExit(main())
