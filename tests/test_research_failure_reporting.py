"""Offline receipt reconciliation and CLI diagnostics; no model or daemon."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

SOURCE = Path(__file__).resolve().parents[1]/'integrations/research/ai_scientist.py'
spec = importlib.util.spec_from_file_location('ais_failure_report', SOURCE)
ais = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ais)
turn_source = ais.module('ais_report_producer_turn', ais.CODE/'app_server_turn.py')
COUNTS = {'inputTokens': 132174, 'outputTokens': 17795, 'totalTokens': 149969,
          'cachedInputTokens': 116096, 'reasoningOutputTokens': 7930}


class FailureReportTests(unittest.TestCase):
    def setUp(self):
        previous_umask = os.umask(0o077)
        self.addCleanup(os.umask, previous_umask)
        self.tmp = tempfile.TemporaryDirectory(prefix='nstack-ais-report-', dir='/private/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)/'owned-state'
        self.state.mkdir(mode=0o700)
        self.put(self.state/'RUN.json', {'owner': 'a'*32, 'state': 'failed_or_interrupted',
            'failure_type': 'TimeoutError', 'overall_exit': 1, 'delivery_complete': False,
            'artifact_exported': True, 'artifact_export_exit': 0,
            'controller_cleanup_exit': 0, 'volume_cleanup_exit': 0,
            'controller_argv': ['PRIVATE_SENTINEL'], 'historical_driver_hash': '0'*64})
        self.put(self.state/'ARTIFACTS.json', {'verified': True, 'producer_exit': 0,
            'members': [{'name': 'PRIVATE_SENTINEL'}]})

    def put(self, path, value):
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    def request(self, ident='b'*32, *, usage=COUNTS, items=None, complete=False):
        directory = self.state/'requests'/('request-'+ident)
        data = {'request_id': ident, 'state': 'failed_or_uncertain', 'inference': 'unknown',
                'failure_type': 'TimeoutError', 'native_argv': ['PRIVATE_SENTINEL'],
                'context': {'account': 'PRIVATE_SENTINEL'}}
        if items is None:
            items = [{'type': 'commandExecution', 'id': str(n), 'status': 'completed',
                      'exitCode': 0 if n < 9 else 127} for n in range(10)]
        if complete:
            data.update(state='completed', inference='occurred', failure_type=None,
                        native_turn={'turn_id': 'fixture-turn', 'status': 'completed', 'error_present': False,
                                     'answer_sha256': 'f'*64, 'items': items, 'usage': usage,
                                     'dollar_cost': None})
        else:
            data['partial_native'] = {'usage': usage, 'items': items, 'dollar_cost': None}
            data['turn_state'] = self.producer_journal('interruption_acknowledged', 'fixture-turn')
            self.put(directory/'turn-state.json', data['turn_state'])
        self.put(directory/'receipt.json', data)
        return directory

    def producer_journal(self, state, turn_id, *, usage=None):
        """Use the real no-I/O journal writer, without entering a native client."""
        recorded = []
        client = turn_source.NativeTurnClient(['/not-executed/native'], {}, self.state,
                                             journal=recorded.append)
        client.record_turn('attempted', inference='unknown', turn_id=None)
        if turn_id is not None:
            client.record_turn('accepted_by_native', inference='unknown', turn_id=turn_id)
        fields = {'inference': 'occurred' if state == 'completed' else 'unknown'}
        if state == 'completed':
            fields['measured_usage'] = usage
        client.record_turn(state, **fields)
        return recorded[-1]

    def snapshot(self):
        return {str(p.relative_to(self.state)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.state.rglob('*') if p.is_file()}

    def test_actual_failed_request_pattern_reports_positive_partial_without_rewrite(self):
        self.request()
        self.put(self.state/'queue/responses'/('b'*32+'.json'),
                 {'schema_version': 1, 'owner': 'a'*32, 'request_id': 'b'*32,
                  'success': False, 'usage': None, 'answer': 'PRIVATE_SENTINEL'})
        before = self.snapshot()
        result = ais.report_state(self.state)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(result['inference_evidence'], 'occurred')
        self.assertEqual(result['reported_usage_subtotal'], COUNTS)
        row = result['requests'][0]
        self.assertEqual((row['journal_inference'], row['native_completion'], row['usage_status']),
                         ('unknown', 'unknown', 'partial_snapshot'))
        self.assertEqual(row['items']['command_executions'], 10)
        self.assertEqual(row['items']['command_exits'], {'0': 9, '127': 1})
        self.assertFalse(row['queue_response']['usage_present'])
        self.assertEqual(result['cleanup']['status'], 'recorded_success_for_reported_steps')
        self.assertFalse(result['delivery_complete'])
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(result))
        self.assertIn('unknown', result['billing'])

    def test_unknown_usage_is_not_reported_as_zero(self):
        self.request(usage=None, items=[])
        result = ais.report_state(self.state)
        self.assertIsNone(result['reported_usage_subtotal'])
        self.assertEqual(result['requests_without_usage'], 1)
        self.assertEqual(result['inference_evidence'], 'unknown')

    def test_command_completion_proves_work_even_without_token_counters(self):
        self.request(usage=None)
        row = ais.report_state(self.state)['requests'][0]
        self.assertEqual(row['inference_evidence'], 'occurred')
        self.assertIsNone(row['reported_cumulative_usage'])

    def test_complete_and_partial_snapshots_count_once_per_request(self):
        self.request()
        small = {'inputTokens': 10, 'outputTokens': 2, 'totalTokens': 12,
                 'cachedInputTokens': 4, 'reasoningOutputTokens': 1}
        self.request('c'*32, usage=small, items=[], complete=True)
        result = ais.report_state(self.state)
        self.assertEqual(result['reported_usage_subtotal']['totalTokens'], 149981)
        self.assertEqual(result['requests'][1]['usage_status'], 'reported_for_completed_turn')
        self.assertIn('not_independently', result['requests'][1]['final_usage'])

    def test_measured_completed_journal_does_not_duplicate_snapshot(self):
        directory = self.request()
        self.put(directory/'turn-state.json', self.producer_journal('completed', 'fixture-turn', usage=COUNTS))
        result = ais.report_state(self.state)
        self.assertEqual(result['reported_usage_subtotal'], COUNTS)
        self.assertEqual(result['requests'][0]['native_completion'], 'recorded_completed')

    def test_missing_request_receipt_remains_unknown(self):
        directory = self.request()
        (directory/'receipt.json').unlink()
        result = ais.report_state(self.state)
        self.assertEqual(result['requests'][0]['receipt_status'], 'missing')
        self.assertIsNone(result['reported_usage_subtotal'])

    def test_conflicting_completed_evidence_is_refused(self):
        directory = self.request(complete=True)
        self.put(directory/'turn-state.json', self.producer_journal('completed', 'fixture-turn',
            usage={**COUNTS, 'cachedInputTokens': 0}))
        with self.assertRaises(ValueError):
            ais.report_state(self.state)
        (directory/'turn-state.json').unlink()
        data = json.loads((directory/'receipt.json').read_text())
        data['partial_native'] = {'usage': COUNTS, 'items': []}
        self.put(directory/'receipt.json', data)
        with self.assertRaises(ValueError):
            ais.report_state(self.state)

    def test_foreign_or_loosely_typed_queue_identity_is_refused(self):
        self.request()
        response = {'schema_version': 1, 'owner': 'a'*32, 'request_id': 'b'*32,
                    'success': False, 'usage': None}
        for key, value in (('owner', 'c'*32), ('request_id', 'c'*32),
                           ('schema_version', True), ('success', 0)):
            with self.subTest(key=key):
                self.put(self.state/'queue/responses'/('b'*32+'.json'), {**response, key: value})
                with self.assertRaises(ValueError):
                    ais.report_state(self.state)

    def test_missing_cleanup_is_unknown_and_invalid_retention_identity_is_refused(self):
        run = {'owner': 'a'*32, 'state': 'failed_or_interrupted'}
        self.put(self.state/'RUN.json', run)
        result = ais.report_state(self.state)
        self.assertEqual(result['cleanup']['status'], 'unknown')
        self.assertIsNone(result['cleanup']['volume_retained_for_recovery'])
        for invalid in (False, True, '', '/private/invalid', 'invalid volume'):
            with self.subTest(invalid=invalid):
                self.put(self.state/'RUN.json', {**run, 'volume_retained_for_recovery': invalid})
                with self.assertRaises(ValueError):
                    ais.report_state(self.state)

    def test_real_execute_retains_volume_name_and_report_projects_only_presence(self):
        """Exercise both producer recovery branches with entirely fake I/O."""
        inputs = self.state.parent/'inputs'
        inputs.mkdir(mode=0o700)
        (inputs/'fixture.txt').write_text('synthetic input')
        volume = 'nstack-ais-wine-744724836482'
        for failure in ('failed-export', 'cleanup-error'):
            with self.subTest(failure=failure):
                produced = self.state.parent/failure
                plan = {'owner': 'a'*32, 'task_name': 'fixture', 'volume': volume,
                        'controller_name': 'not-created', 'volume_mountpoint': '/expected-owned-mount',
                        'controller_mounts': [{'type': 'bind', 'destination': '/run/nstack-native-bridge',
                                               'source': str(produced/'queue'), 'writable': True}],
                        'input_sha256': ais.tree(inputs), 'guard_policy': {},
                        'host_dispatch_policy': {'turn_timeout_seconds': 1, 'deadline_seconds_after_launch': 1},
                        'controller_user': '1:1', 'controller_socket_gid': 1,
                        'controller_environment': {}, 'source': {'source': '/not-executed-source'},
                        'image_id': 'sha256:'+'f'*64, 'linux_root': '/expected-owned-mount/run'}
                calls = []

                def fake_run(argv, **kwargs):
                    calls.append(argv)
                    if argv[:2] == ['volume', 'inspect']:
                        if len(calls) == 1:
                            return SimpleNamespace(returncode=1, stdout='')
                        output = json.dumps([{'Mountpoint': plan['volume_mountpoint'],
                                              'Labels': {'nstack.research.owner': plan['owner']}}])
                    elif argv[0] == 'run':
                        output = 'c'*64
                    elif argv[0] == 'exec':
                        output = '{}'
                    elif argv[0] == 'inspect':
                        output = json.dumps([{'Id': 'c'*64, 'Config': {
                            'Labels': {'nstack.research.controller': plan['owner']}}}])
                    elif argv[0] in ('cp', 'rm') or argv[:2] == ['volume', 'create']:
                        output = ''
                    else:
                        raise AssertionError('Unexpected fake daemon operation')
                    return SimpleNamespace(returncode=0, stdout=output)

                with patch.object(ais, 'LocalDocker'), patch.object(ais, 'Client') as client, \
                        patch.object(ais, 'run_original', new=AsyncMock(return_value={'controller_exit': 0})), \
                        patch.object(ais, 'owned_children', return_value=[]), \
                        patch.object(ais, 'archive_artifacts') as export, \
                        patch.object(ais.subprocess, 'run', side_effect=AssertionError('no native subprocess')):
                    client.return_value.binary = '/not-executed/docker'
                    client.return_value.run.side_effect = fake_run
                    if failure == 'failed-export':
                        export.return_value = {'producer_exit': 1, 'verified': False, 'failure_type': 'ValueError'}
                    else:
                        export.side_effect = OSError('synthetic cleanup error')
                    ais.execute(plan, inputs, produced, '/not-a-real-socket')
                raw = json.loads((produced/'RUN.json').read_text())
                self.assertEqual(raw['volume_retained_for_recovery'], volume)
                before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in produced.rglob('*') if p.is_file()}
                result = ais.report_state(produced)
                self.assertIs(result['cleanup']['volume_retained_for_recovery'], True)
                self.assertEqual(result['cleanup']['status'], 'recorded_success_for_reported_steps'
                                 if failure == 'failed-export' else 'recorded_failure')
                self.assertFalse(result['artifacts']['exported_in_run_receipt'])
                self.assertFalse(result['delivery_complete'])
                self.assertEqual(result['overall_exit'], 2)
                self.assertNotIn(volume, json.dumps(result))
                self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in produced.rglob('*') if p.is_file()})
                self.assertNotIn(['volume', 'rm', volume], calls)

    def test_conflicting_external_completed_turn_never_promotes_partial_receipt(self):
        directory = self.request()
        self.put(directory/'turn-state.json',
                 self.producer_journal('completed', 'different-foreign-turn', usage=COUNTS))
        with self.assertRaisesRegex(ValueError, 'Conflicting native turn identities'):
            ais.report_state(self.state)

    def test_completed_native_proof_must_agree_with_journal_turn(self):
        directory = self.request(complete=True)
        self.put(directory/'turn-state.json',
                 self.producer_journal('completed', 'different-foreign-turn', usage=COUNTS))
        with self.assertRaisesRegex(ValueError, 'Conflicting native turn identities'):
            ais.report_state(self.state)

    def test_optional_journal_request_identity_must_match_owning_request(self):
        directory = self.request()
        journal = self.producer_journal('completed', 'fixture-turn', usage=COUNTS)
        journal['request_id'] = 'c'*32
        self.put(directory/'turn-state.json', journal)
        with self.assertRaisesRegex(ValueError, 'request identity differs'):
            ais.report_state(self.state)

    def test_early_unknown_turn_can_be_reported_and_later_bound_to_same_request(self):
        directory = self.request(usage=None, items=[])
        early = self.producer_journal('interruption_unavailable', None)
        data = json.loads((directory/'receipt.json').read_text())
        data['turn_state'] = early
        self.put(directory/'receipt.json', data)
        self.put(directory/'turn-state.json', early)
        self.assertEqual(ais.report_state(self.state)['requests'][0]['native_completion'], 'unknown')
        self.put(directory/'turn-state.json', self.producer_journal('completed', 'later-turn', usage=COUNTS))
        self.assertEqual(ais.report_state(self.state)['requests'][0]['native_completion'], 'recorded_completed')

    def test_completed_evidence_without_turn_identity_is_not_accepted(self):
        directory = self.request(complete=True)
        data = json.loads((directory/'receipt.json').read_text())
        data['native_turn'].pop('turn_id')
        self.put(directory/'receipt.json', data)
        with self.assertRaises(ValueError):
            ais.report_state(self.state)
        data.pop('native_turn')
        data.update(state='failed_or_uncertain', inference='unknown',
                    partial_native={'usage': COUNTS, 'items': []})
        self.put(directory/'receipt.json', data)
        self.put(directory/'turn-state.json', self.producer_journal('completed', None, usage=COUNTS))
        with self.assertRaises(ValueError):
            ais.report_state(self.state)

    def test_nonregular_receipt_is_refused_without_waiting_for_writer(self):
        directory = self.request()
        (directory/'receipt.json').unlink()
        os.mkfifo(directory/'receipt.json', mode=0o600)
        with self.assertRaises(ValueError):
            ais.report_state(self.state)

    def test_report_cli_uses_no_launch_hash_docker_subprocess_or_execution(self):
        self.request()
        output = io.StringIO()
        with patch('sys.argv', ['ai_scientist.py', 'report', '--state', str(self.state)]), \
                patch.object(ais, 'load_plan', side_effect=AssertionError('no launch read')), \
                patch.object(ais, 'execute', side_effect=AssertionError('no execution')), \
                patch.object(ais, 'LocalDocker', side_effect=AssertionError('no daemon')), \
                patch.object(ais.subprocess, 'run', side_effect=AssertionError('no subprocess')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(ais.main(), 0)
        self.assertEqual(json.loads(output.getvalue())['inference_evidence'], 'occurred')

    def test_plan_and_run_still_require_launch(self):
        for operation in ('plan', 'run'):
            with self.subTest(operation=operation), patch('sys.argv', ['ai_scientist.py', operation]), \
                    contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as stop:
                ais.main()
            self.assertEqual(stop.exception.code, 2)
            self.assertIn('--launch', stderr.getvalue())

    def test_blank_timeout_cli_error_names_type_and_owning_receipt(self):
        before = (self.state/'RUN.json').read_bytes()
        with patch('sys.argv', ['ai_scientist.py', 'run', '--launch', '/not-read',
                               '--inputs', '/not-read', '--state', str(self.state)]), \
                patch.object(ais, 'load_plan', return_value={}), \
                patch.object(ais, 'execute', side_effect=TimeoutError()), \
                contextlib.redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as stop:
            ais.main()
        self.assertEqual(stop.exception.code, 2)
        self.assertIn('TimeoutError', stderr.getvalue())
        self.assertIn(str(self.state/'RUN.json'), stderr.getvalue())
        self.assertEqual((self.state/'RUN.json').read_bytes(), before)

    def test_invalid_counter_types_missing_fields_and_component_totals_are_refused(self):
        directory = self.request()
        for bad in ({**COUNTS, 'totalTokens': True}, {**COUNTS, 'inputTokens': -1},
                    {k: v for k, v in COUNTS.items() if k != 'outputTokens'},
                    {**COUNTS, 'totalTokens': 1}, {**COUNTS, 'cachedInputTokens': 999999}):
            with self.subTest(bad=bad):
                data = json.loads((directory/'receipt.json').read_text())
                data['partial_native']['usage'] = bad
                self.put(directory/'receipt.json', data)
                with self.assertRaises(ValueError):
                    ais.report_state(self.state)

    def test_raw_item_fields_and_invalid_boolean_are_not_echoed(self):
        directory = self.request(items=[{'type': 'commandExecution', 'id': 'x',
                                        'command': 'PRIVATE_SENTINEL'}])
        with self.assertRaises(ValueError):
            ais.report_state(self.state)
        data = json.loads((directory/'receipt.json').read_text())
        data['partial_native']['items'] = []
        self.put(directory/'receipt.json', data)
        run = json.loads((self.state/'RUN.json').read_text())
        run['delivery_complete'] = 'PRIVATE_SENTINEL'
        self.put(self.state/'RUN.json', run)
        with self.assertRaises(ValueError):
            ais.report_state(self.state)

    def test_state_receipt_and_request_aliases_are_refused(self):
        directory = self.request()
        alias = self.state.parent/'alias'
        alias.symlink_to(self.state, target_is_directory=True)
        with self.assertRaises(ValueError):
            ais.report_state(alias)
        path = directory/'receipt.json'
        original = directory/'original.json'
        path.rename(original)
        path.symlink_to(original)
        with self.assertRaises((ValueError, OSError)):
            ais.report_state(self.state)
        path.unlink()
        os.link(original, path)
        with self.assertRaises(ValueError):
            ais.report_state(self.state)


if __name__ == '__main__':
    unittest.main()
