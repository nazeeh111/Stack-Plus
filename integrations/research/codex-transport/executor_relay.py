"""One-request loopback WebSocket to official executor stdio relay.

No model, tools, path mapping or credentials are implemented here. The trusted
caller supplies a fixed reviewed child argv/environment. Endpoint capability
bytes remain in memory and must be redacted before any caller log is persisted.
Requires the separately reviewed pinned websockets runtime, never auto-installs.
"""
from __future__ import annotations

import asyncio
import hmac
import http
import os
import secrets
import signal

from websockets.asyncio.server import serve


class ExecutorRelay:
    def __init__(self, command: list[str], environment: dict[str, str], *,
                 timeout_seconds: int = 60, max_bytes: int = 16 * 1024 * 1024):
        if not command or not os.path.isabs(command[0]):
            raise ValueError('trusted child executable must be absolute')
        self.command = command
        self.environment = environment
        self.timeout = timeout_seconds
        self.maximum = max_bytes
        self._capability = secrets.token_urlsafe(32)
        self._claimed = False
        self.process = None
        self.stderr = b''
        self.events = {'accepted_connections': 0, 'rejected_connections': 0,
                       'child_started': False, 'forwarded_bytes': 0}
        self._server = None
        self.done = asyncio.Event()

    def redact(self, value: str) -> str:
        return value.replace(self._capability, '<ephemeral-relay-capability>')

    async def _authorize(self, connection, request):
        valid = (not request.headers.get_all('Origin')
                 and hmac.compare_digest(request.path, '/' + self._capability)
                 and not self._claimed)
        if not valid:
            self.events['rejected_connections'] += 1
            return connection.respond(http.HTTPStatus.FORBIDDEN, 'refused\n')
        # No await between checking and claiming: one event-loop atomic claim.
        self._claimed = True
        return None

    def _account(self, size: int):
        self.events['forwarded_bytes'] += size
        if self.events['forwarded_bytes'] > self.maximum:
            raise ValueError('executor relay exceeded declared byte bound')

    async def _connection(self, websocket):
        self.events['accepted_connections'] += 1
        try:
            async with asyncio.timeout(self.timeout):
                self.process = await asyncio.create_subprocess_exec(
                    *self.command, stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    env=self.environment, start_new_session=True,
                    limit=self.maximum + 1)
                self.events['child_started'] = True

                async def incoming():
                    async for frame in websocket:
                        if not isinstance(frame, str) or '\n' in frame or '\r' in frame:
                            raise ValueError('executor relay requires one JSON message per text frame')
                        data = frame.encode()
                        self._account(len(data))
                        self.process.stdin.write(data + b'\n')
                        await self.process.stdin.drain()

                async def outgoing():
                    while line := await self.process.stdout.readline():
                        self._account(len(line))
                        await websocket.send(line.rstrip(b'\r\n').decode())

                async def stderr():
                    while data := await self.process.stderr.read(4096):
                        self._account(len(data))
                        if len(self.stderr) < 16384:
                            self.stderr += data[:16384 - len(self.stderr)]

                tasks = [asyncio.create_task(f()) for f in (incoming, outgoing, stderr)]
                try:
                    complete, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in complete:
                        task.result()
                finally:
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as error:
            # Record only a type; exception text could include the endpoint URL.
            self.events['failure_type'] = type(error).__name__
        finally:
            await self._stop_child()
            await websocket.close()
            self.done.set()

    async def _stop_child(self):
        if self.process is None:
            return
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.returncode is None:
            try:
                await asyncio.wait_for(self.process.wait(), 2)
            except asyncio.TimeoutError:
                os.killpg(self.process.pid, signal.SIGTERM)
                try:
                    await asyncio.wait_for(self.process.wait(), 3)
                except asyncio.TimeoutError:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    await self.process.wait()
        self.events['child_returncode'] = self.process.returncode

    async def __aenter__(self):
        self._server = await serve(
            self._connection, '127.0.0.1', 0, process_request=self._authorize,
            compression=None, max_size=self.maximum, max_queue=4,
            open_timeout=10, close_timeout=2)
        port = self._server.sockets[0].getsockname()[1]
        self.url = f'ws://127.0.0.1:{port}/{self._capability}'
        return self

    async def __aexit__(self, *unused):
        self._server.close()
        await self._server.wait_closed()
        await self._stop_child()
