"""Bounded native turn protocol. Call only after the independent setup gate.

No provider, model, effort, environment, auth, or policy defaults. The owner
must validate live host context and the entire outer boundary before calling.
No raw native replies, configuration, tool output or stderr are persisted.
"""
from __future__ import annotations
import asyncio
import hashlib
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'nstack_native_setup', Path(__file__).with_name('app_server_no_model.py'))
_setup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_setup)


class NativeTurnClient(_setup.NoModelClient):
    allowed_methods = _setup.ALLOWED | {'turn/start', 'turn/interrupt'}
    allow_turn_notifications = True

    def __init__(self, *args, journal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.journal = journal
        self.turn_journal = None
        self.turns = {}
        self.items = []
        self.usage = None
        self.final_answer = None

    def record_turn(self, state, **fields):
        self.turn_journal = {**(self.turn_journal or {}), 'state': state, **fields}
        self.journal(dict(self.turn_journal))

    def request_sent(self, method):
        if method == 'turn/start':
            self.record_turn('sent_to_native', inference='unknown')

    def observe_notification(self, method, params):
        if method == 'turn/completed':
            turn = params.get('turn', {})
            self.turns[turn.get('id')] = {
                'status': turn.get('status'), 'error_present': turn.get('error') is not None}
            if self.journal is not None:
                self.record_turn('native_turn_' + str(turn.get('status')),
                                 turn_id=turn.get('id'), inference='occurred_or_unknown')
        elif method == 'thread/tokenUsage/updated':
            # Token counts only, never account/billing/auth metadata.
            raw = params.get('tokenUsage', {}).get('total', {})
            names = ('totalTokens', 'inputTokens', 'cachedInputTokens',
                     'outputTokens', 'reasoningOutputTokens')
            if all(type(raw.get(n)) is int and raw[n] >= 0 for n in names):
                self.usage = {n: raw[n] for n in names}
        elif method == 'item/completed':
            item = params.get('item', {})
            kind = item.get('type')
            proof = {'type': kind, 'id': item.get('id')}
            for name in ('status', 'exitCode'):
                if name in item:
                    proof[name] = item[name]
            if kind == 'agentMessage':
                text = item.get('text', '')
                proof['text_sha256'] = hashlib.sha256(text.encode()).hexdigest()
                if item.get('phase') == 'final_answer':
                    self.final_answer = text
            self.items.append(proof)

    async def complete_turn(self, params: dict, *, timeout_seconds: int):
        if not 1 <= timeout_seconds <= 600:
            raise _setup.NativeSetupRefusal('native turn timeout is outside its reviewed bound')
        required = ('threadId', 'input', 'model', 'effort', 'approvalPolicy',
                    'sandboxPolicy', 'environments')
        if any(name not in params for name in required):
            raise _setup.NativeSetupRefusal('native turn lacks explicit reviewed settings')
        if not callable(self.journal) or self.turn_journal is not None:
            raise _setup.NativeSetupRefusal('native turn requires a fresh private state journal')
        # Persist BEFORE writing turn/start. A crash between pipe write and its
        # acknowledgement is uncertain inference, never evidence of zero use.
        self.record_turn('attempted', inference='unknown', turn_id=None)
        rpc_timeout = self.timeout
        turn_id = None
        try:
            async with asyncio.timeout(timeout_seconds) as deadline:
                # Sending/acknowledging turn/start already can initiate inference.
                # It shares the outer deadline and retains a separate RPC cap;
                # notifications during the acknowledgement cannot restart either.
                async with asyncio.timeout(rpc_timeout):
                    response = await self.request('turn/start', params)
                turn_id = response['turn']['id']
                self.record_turn('accepted_by_native', turn_id=turn_id, inference='unknown')
                while turn_id not in self.turns:
                    # Reasoning/tools can be silent longer than a setup RPC.
                    # Every notification read shares this one turn deadline;
                    # receiving an item never resets the inference budget.
                    self.timeout = max(0, deadline.when() - asyncio.get_running_loop().time())
                    await self._message()
        except BaseException:
            self.timeout = rpc_timeout
            if turn_id is None:
                # Request bytes may have reached native even without an ack.
                # The owner must close its client; never guess an interrupt ID.
                self.record_turn('interruption_unavailable', inference='unknown', turn_id=None,
                                 interruption_reason='turn_id_unknown')
                raise
            self.record_turn('interruption_attempted', inference='unknown')
            # Native cancellation first; owner still tears down only its own
            # client process and container if native cancellation fails.
            try:
                # Cleanup has its own bounded RPC grace after inference ends.
                # Continuous notifications cannot prolong cancellation forever.
                async with asyncio.timeout(rpc_timeout):
                    await self.request('turn/interrupt', {
                        'threadId': params['threadId'], 'turnId': turn_id})
                if turn_id not in self.turns:
                    self.record_turn('interruption_acknowledged', inference='unknown')
            except Exception:
                pass
            raise
        finally:
            self.timeout = rpc_timeout
        proof = self.turns[turn_id]
        if proof['status'] != 'completed' or proof['error_present']:
            raise _setup.NativeSetupRefusal('native turn did not complete successfully')
        if self.final_answer is None or self.usage is None:
            raise _setup.NativeSetupRefusal('native turn lacks final answer or measured usage')
        self.record_turn('completed', inference='occurred', measured_usage=self.usage)
        return {'turn_id': turn_id, **proof, 'items': self.items,
                'usage': self.usage, 'dollar_cost': None,
                'answer_sha256': hashlib.sha256(self.final_answer.encode()).hexdigest()}
