"""Local Docker selection cannot inherit remote targets or credential configuration."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import docker_client


class DockerClientBoundary(unittest.TestCase):
    def test_existing_desktop_binary_is_found_without_global_path_edits(self):
        def find(name, path=None):
            return '/Applications/Docker.app/Contents/Resources/bin/docker' if path == docker_client.DOCKER_SEARCH_PATH else None
        with patch.object(docker_client.shutil, 'which', side_effect=find):
            self.assertEqual(docker_client.docker_binary(), '/Applications/Docker.app/Contents/Resources/bin/docker')

    def test_remote_or_non_socket_endpoint_is_rejected_before_temporary_state(self):
        with patch.object(docker_client, 'docker_binary', return_value='/existing/docker'), \
                patch.object(docker_client.tempfile, 'TemporaryDirectory', side_effect=AssertionError('No client state before endpoint validation')):
            for endpoint in ('tcp://remote:2375', 'ssh://remote', 'unix://relative', 'unix:///tmp/missing-socket', 'unix:///tmp/a\nother'):
                with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                    docker_client.LocalDocker(endpoint)

    def test_explicit_local_socket_uses_fresh_empty_config_and_removes_owned_files(self):
        with tempfile.TemporaryDirectory(prefix='docker-boundary-', dir='/private/tmp' if Path('/private/tmp').is_dir() else None) as tmp:
            endpoint = str(Path(tmp) / 'engine.sock')
            with socket.socket(socket.AF_UNIX) as engine:
                engine.bind(endpoint)
                inherited = {'DOCKER_HOST': 'tcp://synthetic-remote:2375', 'DOCKER_CONTEXT': 'synthetic-context',
                             'DOCKER_CONFIG': str(Path(tmp) / 'do-not-read-config'), 'DOCKER_AUTH_CONFIG': 'synthetic-only',
                             'AWS_ACCESS_KEY_ID': 'synthetic-only', 'HTTP_PROXY': 'http://synthetic-proxy',
                             'HOME': str(Path(tmp) / 'do-not-read-home')}
                with patch.dict(os.environ, inherited), patch.object(docker_client, 'docker_binary', return_value=sys.executable):
                    with docker_client.LocalDocker('unix://' + endpoint) as client:
                        owned = client.root
                        self.assertEqual(client.env['DOCKER_HOST'], 'unix://' + str(Path(endpoint).resolve()))
                        self.assertEqual(list(Path(client.env['DOCKER_CONFIG']).iterdir()), [])
                        self.assertEqual(list(Path(client.env['HOME']).iterdir()), [])
                        observed = subprocess.run([client.binary, '-c', 'import json,os; print(json.dumps(dict(os.environ)))'],
                                                  env=client.env, check=True, capture_output=True, text=True)
                        environment = json.loads(observed.stdout)
                        for key in ('DOCKER_CONTEXT', 'DOCKER_AUTH_CONFIG', 'AWS_ACCESS_KEY_ID', 'HTTP_PROXY'):
                            self.assertNotIn(key, environment)
                        self.assertNotEqual(environment['HOME'], inherited['HOME'])
                        Path(client.env['DOCKER_CONFIG'], 'owned-buildx').write_text('owned')
                    self.assertFalse(owned.exists())
                self.assertFalse(Path(inherited['DOCKER_CONFIG']).exists())
                self.assertFalse(Path(inherited['HOME']).exists())

    def test_empty_configs_cannot_discover_inherited_native_credential_helpers(self):
        # Docker's owning source auto-detects osxkeychain from PATH even when
        # config.json is empty. Exercise the actual four client environments.
        with tempfile.TemporaryDirectory(prefix='docker-helper-discovery-',
                dir='/private/tmp' if Path('/private/tmp').is_dir() else None) as tmp:
            root = Path(tmp).resolve(); binaries = root / 'bin'; binaries.mkdir()
            for name in ('docker', 'docker-credential-osxkeychain', 'docker-credential-desktop',
                         'docker-credential-pass', 'docker-credential-secretservice'):
                file = binaries / name
                file.write_text('#!/bin/sh\nexit 97\n'); file.chmod(0o700)
            home = root / 'host-home'; socket_dir = home / '.docker/run'
            socket_dir.mkdir(parents=True); endpoint = socket_dir / 'docker.sock'
            with socket.socket(socket.AF_UNIX) as engine:
                engine.bind(str(endpoint))
                with patch.dict(os.environ, {'PATH': str(binaries)}), \
                        patch.object(Path, 'home', return_value=home):
                    self.assertIsNotNone(shutil.which('docker-credential-osxkeychain'))
                    with docker_client.LocalDocker('unix://' + str(endpoint)) as client:
                        environments = [client.env]
                        for name in ('workflows', 'n8n_mcp', 'ai_workflows'):
                            spec = importlib.util.spec_from_file_location('private_' + name,
                                    ROOT / 'recipes' / (name + '.py'))
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            if name == 'workflows':
                                env = module.docker_env(root / name, 'unix://' + str(endpoint))
                            elif name == 'n8n_mcp':
                                env = module.environment(root / name)
                            else:
                                env = module.Runtime(root / name, 'unix://' + str(endpoint)).env
                            environments.append(env)
                        for env in environments:
                            for helper in ('osxkeychain', 'desktop', 'pass', 'secretservice'):
                                self.assertIsNone(shutil.which('docker-credential-' + helper,
                                                              path=env['PATH']))
                            self.assertNotEqual(env['PATH'], str(binaries))

    def test_both_controllers_capture_with_private_environment(self):
        client = type('Client', (), {'env': {'HOME': '/synthetic/private', 'DOCKER_HOST': 'unix:///synthetic/socket'}})()
        for name, path in (('rea_private_docker', ROOT / 'recipes/rea_linux.py'), ('fpga_private_docker', ROOT / 'integrations/fpga/runtime.py')):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            with self.subTest(controller=name), patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'ok', '')) as run:
                self.assertEqual(module.capture(client, ['/existing/docker', 'info']), 'ok')
                self.assertIs(run.call_args.kwargs['env'], client.env)


if __name__ == '__main__': unittest.main()
