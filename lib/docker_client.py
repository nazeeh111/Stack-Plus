"""A private Docker CLI context for an existing local Unix-socket engine."""
from pathlib import Path
import os
import shutil
import stat
import tempfile

DOCKER_SEARCH_PATH = os.pathsep.join(('/usr/local/bin', '/Applications/Docker.app/Contents/Resources/bin'))


def docker_binary():
    binary = shutil.which('docker') or shutil.which('docker', path=DOCKER_SEARCH_PATH)
    if not binary:
        raise ValueError('Existing Docker CLI required; no installation or daemon startup fallback')
    return str(Path(binary).absolute())


class LocalDocker:
    """Ignore inherited Docker settings and remove only this client's temporary files."""
    def __init__(self, endpoint=None):
        self.binary = docker_binary()
        if endpoint is None:
            candidates = [Path.home() / '.docker/run/docker.sock', Path('/var/run/docker.sock')]
            sockets = [p for p in candidates if p.exists() and stat.S_ISSOCK(p.stat().st_mode)]
            if not sockets:
                raise ValueError('Existing local Docker socket required; select --docker-host unix:///absolute/socket')
            endpoint = 'unix://' + str(sockets[0])
        if not isinstance(endpoint, str) or not endpoint.startswith('unix:///') or any(x in endpoint for x in ('\n', '\r', '\0')):
            raise ValueError('Only an existing absolute local Unix Docker socket is supported')
        socket = Path(endpoint[7:])
        if not socket.exists() or not stat.S_ISSOCK(socket.stat().st_mode):
            raise ValueError('Docker endpoint is not an existing local Unix socket')
        # Resolve socket aliases only, without opening user Docker configuration.
        self.endpoint = 'unix://' + str(socket.resolve())
        self._temporary = tempfile.TemporaryDirectory(prefix='nstack-docker-client-',
            dir='/private/tmp' if Path('/private/tmp').is_dir() else None)
        self.root = Path(self._temporary.name)
        home, config = self.root / 'home', self.root / 'config'
        home.mkdir(mode=0o700); config.mkdir(mode=0o700)
        # Docker autodetects native credential helpers even with empty config.
        # Resolve its absolute CLI first; keep helper installation dirs off PATH.
        self.env = {'PATH': '/usr/bin:/bin',
                    'HOME': str(home), 'DOCKER_CONFIG': str(config),
                    'DOCKER_HOST': self.endpoint, 'LANG': 'C.UTF-8'}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._temporary.cleanup()
