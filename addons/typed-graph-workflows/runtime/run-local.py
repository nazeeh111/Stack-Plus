#!/usr/bin/env python3
"""Run the pinned CLI inside one explicitly selected local project.

This enforces provenance and filesystem/network scope, not permission to perform
an arbitrary data mutation. The calling host still needs task authorization.
"""
import hashlib
import json
import os
import pwd
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

BINARY_SHA256 = "d93baf802106252313d66fbd861145f21f1e1520d7f8c36ff54a1840ba319e33"
VERBS = {"version", "skill", "lint", "init", "schema", "query", "mutate",
         "load", "branch", "snapshot", "export", "diff", "commit", "changes"}
FORBIDDEN = {"--operator-config", "--profile", "--graph", "--config", "--api",
             "--base", "--as", "--yes"}
PATH_FLAGS = {"--schema", "--query", "--data", "--params-file", "--file", "--out"}

def fail(message):
    raise SystemExit("omnigraph-local: " + message)

def under(path, root):
    return path == root or path.is_relative_to(root)

def project_path(value, workspace):
    parsed = urlsplit(value)
    if parsed.scheme:
        if parsed.scheme != "file" or parsed.netloc or parsed.query or parsed.fragment:
            fail("only a local path or file:// path is supported")
        value = unquote(parsed.path)
    path = Path(value)
    path = (path if path.is_absolute() else workspace / path).resolve()
    if not under(path, workspace):
        fail("input, output and graph paths must stay inside --workspace")
    return str(path)

def sandbox_profile(runtime, workspace, session):
    home = Path(pwd.getpwuid(os.geteuid()).pw_dir).resolve()
    quote = lambda p: json.dumps(str(p))
    return f'''(version 1)
(allow default)
(deny file-write*)
(deny network*)
(deny file-read* file-write* (subpath {quote(home)}))
(allow file-read* (subpath {quote(runtime)}))
(allow file-read* file-write* (subpath {quote(workspace)}))
(allow file-read* file-write* (subpath {quote(session)}))
(deny file-read* file-write* (subpath "/Library/Keychains") (subpath "/System/Library/Keychains") (literal "/private/var/db/SystemKey") (subpath {quote(home / "Library/Keychains")}))
(deny mach-lookup (global-name "com.apple.securityd") (global-name "com.apple.securityd.xpc") (global-name "com.apple.SecurityServer") (global-name "com.apple.SecurityAgent") (global-name "com.apple.security.agent") (global-name "com.apple.trustd.agent"))
(deny appleevent-send)
(deny process-exec (literal "/System/Library/CoreServices/SecurityAgent.app/Contents/MacOS/SecurityAgent"))
'''

def main(argv):
    if len(argv) < 4 or argv[0] != "--workspace" or argv[2] != "--":
        fail("usage: run-local.py --workspace /absolute/project -- COMMAND [ARGS]")
    runtime = Path(__file__).resolve().parent
    workspace_arg = Path(argv[1])
    if not workspace_arg.is_absolute():
        fail("--workspace must be an absolute existing project directory")
    workspace = workspace_arg.resolve(strict=True)
    home = Path(pwd.getpwuid(os.geteuid()).pw_dir).resolve()
    protected = [home, runtime, Path("/System"), Path("/usr"), Path("/bin"),
                 Path("/sbin"), Path("/Library"), Path("/private/var")]
    if not workspace.is_dir() or workspace.stat().st_uid != os.geteuid():
        fail("--workspace must be a directory owned by the invoking user")
    if workspace == Path("/private/tmp") or any(under(p, workspace) for p in protected):
        fail("--workspace cannot contain the real home, runtime or system paths")
    private_roots = [home / "Knowledge", home / "Library", home / ".ssh",
                     home / ".aws", home / ".codex", home / ".config", home / ".local",
                     home / ".agents", home / ".docker", home / ".cache",
                     home / ".Trash", home / ".gnupg"]
    private_roots = [p.resolve() for p in private_roots]
    if any(under(workspace, p) for p in protected[1:] + private_roots):
        fail("runtime, system and private host directories are not graph workspaces")
    args = list(argv[3:])
    if not args or args[0] not in VERBS | {"--help", "-h"}:
        fail("only the supported local graph commands are available")
    if args[0] == "skill" and (len(args) < 2 or args[1] != "show"):
        fail("skill is limited to show; no installed skill export")
    target_count = 0
    i = 1
    while i < len(args):
        key, equals, inline = args[i].partition("=")
        if args[0] == "init" and not key.startswith("-"):
            fail("init uses --target; positional backend addresses are unavailable")
        if key in FORBIDDEN:
            fail("operator, account, cluster and clone overrides are unavailable")
        if key == "--target" or key in PATH_FLAGS:
            if not equals:
                if i + 1 >= len(args):
                    fail("missing path after " + key)
                value = args[i + 1]
            else:
                value = inline
            path = project_path(value, workspace)
            if key == "--target":
                target_count += 1
                graph = Path(path)
                if any((p / "__cluster").exists() for p in [graph, *graph.parents]):
                    fail("cluster-managed storage is outside this standalone runner")
            if equals:
                args[i] = key + "=" + path
            else:
                args[i + 1] = path
                i += 1
        i += 1
    backend = args[0] not in {"version", "skill", "lint", "--help", "-h"}
    if backend and "--help" not in args and "-h" not in args and target_count != 1:
        fail("graph operations require exactly one explicit --target inside --workspace")
    if target_count > 1:
        fail("only one graph target is allowed")
    binary = runtime / "bin/omnigraph"
    sandbox = Path("/usr/bin/sandbox-exec")
    if not sandbox.is_file() or binary.is_symlink() or not binary.is_file():
        fail("pinned binary or native sandbox is unavailable")
    digest = hashlib.sha256()
    with binary.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    if digest.hexdigest() != BINARY_SHA256:
        fail("pinned binary hash differs; no execution attempted")
    with tempfile.TemporaryDirectory(prefix="omnigraph-local-", dir="/private/tmp") as session:
        session = Path(session)
        for name in ("home", "operator", "tmp"):
            (session / name).mkdir()
        operator = session / "operator/config.yaml"
        operator.write_text("version: 1\n")
        profile = sandbox_profile(runtime, workspace, session)
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(session / "home"),
               "CFFIXED_USER_HOME": str(session / "home"), "OMNIGRAPH_HOME": str(session / "operator"),
               "TMPDIR": str(session / "tmp") + "/", "RUST_BACKTRACE": "0", "LANG": "en_US.UTF-8"}
        return subprocess.run([str(sandbox), "-p", profile, str(binary),
                               "--operator-config", str(operator), *args],
                              cwd=workspace, env=env).returncode

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
