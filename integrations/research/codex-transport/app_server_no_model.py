"""Bounded stock native metadata/setup client. Model-turn methods are excluded.

Full native replies remain in memory for allowlisted projection by the caller.
No raw reply, configuration, environment or stderr text is persisted here.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import signal


ALLOWED = frozenset({
    'initialize', 'modelProvider/list', 'config/read', 'configRequirements/read',
    'experimentalFeature/list', 'environment/add', 'environment/info',
    'environment/status', 'thread/start', 'thread/settings/update', 'thread/read',
    'mcpServerStatus/list', 'hooks/list', 'plugin/list',
})


class NativeSetupRefusal(RuntimeError):
    pass


class NoModelClient:
    allowed_methods = ALLOWED
    allow_turn_notifications = False
    def __init__(self, command: list[str], environment: dict[str, str], cwd: Path,
                 *, timeout_seconds: int = 45, max_bytes: int = 16 * 1024 * 1024):
        if not command or not Path(command[0]).is_absolute():
            raise NativeSetupRefusal('native executable must be absolute')
        self.command = command
        self.environment = environment
        self.cwd = cwd
        self.timeout = timeout_seconds
        self.maximum = max_bytes
        self.sequence = 0
        self.methods = []
        self.notification_counts = {}
        self.thread_settings = {}
        self.stderr_bytes = 0
        self.stderr_hash = hashlib.sha256()
        self.received_bytes = 0

    async def __aenter__(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.command, env=self.environment, cwd=self.cwd,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, limit=self.maximum + 1,
            start_new_session=True)

        async def drain():
            while data := await self.process.stderr.read(4096):
                self.stderr_bytes += len(data)
                self.stderr_hash.update(data)
        self._stderr_task = asyncio.create_task(drain())
        return self

    async def _message(self):
        line = await asyncio.wait_for(self.process.stdout.readline(), self.timeout)
        if not line:
            raise NativeSetupRefusal('native setup process ended before its response')
        self.received_bytes += len(line)
        if self.received_bytes > self.maximum or self.stderr_bytes > self.maximum:
            raise NativeSetupRefusal('native setup output bound exceeded')
        message = json.loads(line)
        if 'method' in message:
            method = message['method']
            self.notification_counts[method] = self.notification_counts.get(method, 0) + 1
            if 'id' in message:
                raise NativeSetupRefusal('unexpected reverse request during native setup')
            if method == 'thread/settings/updated':
                value = message.get('params', {})
                settings = value.get('threadSettings', {})
                fields = ('model', 'effort', 'modelProvider', 'approvalPolicy',
                          'sandboxPolicy', 'environments')
                self.thread_settings[value.get('threadId')] = {
                    key: settings.get(key) for key in fields}
            if method.startswith('turn/') and not self.allow_turn_notifications:
                raise NativeSetupRefusal('unexpected model turn during metadata-only setup')
            self.observe_notification(method, message.get('params', {}))
        return message

    def observe_notification(self, method, params):
        """Subclass hook; the no-model client retains no notification bodies."""

    def request_sent(self, method):
        """Called only after the request bytes have drained to native stdin."""

    async def request(self, method: str, params: dict, *, expect_error: bool = False):
        if method not in self.allowed_methods:
            raise NativeSetupRefusal('method is outside the no-model setup allowlist')
        self.sequence += 1
        ident = self.sequence
        self.methods.append(method)
        payload = json.dumps({'jsonrpc': '2.0', 'id': ident,
                              'method': method, 'params': params}).encode() + b'\n'
        if len(payload) > self.maximum:
            raise NativeSetupRefusal('native setup request exceeds its bound')
        self.process.stdin.write(payload)
        await self.process.stdin.drain()
        self.request_sent(method)
        while True:
            response = await self._message()
            if response.get('id') != ident:
                continue
            if expect_error:
                if 'error' not in response:
                    raise NativeSetupRefusal('forbidden environment unexpectedly exists')
                return {'rejected': True, 'code': response['error'].get('code')}
            if 'error' in response:
                # Never include native error text; it may quote configuration.
                raise NativeSetupRefusal('native setup RPC refused: ' + method
                                         + ' code ' + str(response['error'].get('code')))
            return response['result']

    async def initialize(self):
        await self.request('initialize', {
            'clientInfo': {'name': 'nstack_research_no_model_gate', 'version': '0.1.0'},
            'capabilities': {'experimentalApi': True}})
        self.process.stdin.write(b'{"jsonrpc":"2.0","method":"initialized"}\n')
        await self.process.stdin.drain()

    async def wait_settings(self, thread_id: str):
        while thread_id not in self.thread_settings:
            await self._message()
        return self.thread_settings[thread_id]

    async def __aexit__(self, *unused):
        if self.process.stdin:
            self.process.stdin.close()
        try:
            await asyncio.wait_for(self.process.wait(), 5)
        except asyncio.TimeoutError:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(self.process.wait(), 5)
            except asyncio.TimeoutError:
                os.killpg(self.process.pid, signal.SIGKILL)
                await self.process.wait()
        await self._stderr_task
