#!/usr/bin/env python3
"""Scoped native Codex transport; never reads, copies or changes auth files.

Implements the reviewed Shinka/HEADLESS_BIN executable contract. The manifest is
trusted task configuration, not model input. Native login status is captured
and reduced to one boolean, never printed or persisted (API status may contain
a masked key). No inference occurs for --check or --plan.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

REVIEWED_CLI_VERSION = "codex-cli 0.169.0"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")
DISABLED_FEATURES = (
    "apps", "plugins", "plugin_hooks", "hooks",
    "computer_use", "multi_agent", "multi_agent_v2", "multi_agent_v2_dynamic_tools",
    "code_mode", "code_mode_only", "enable_mcp_apps", "recommended_plugins",
    "memories", "external_agent_memory_import", "executor_capability_discovery_v2",
)
# Preserve host-owned auth routing context without copying credentials or
# passing provider keys to either the client or its tools.
CLIENT_ENV = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "TMP", "TEMP",
              "LANG", "LC_ALL", "LC_CTYPE", "CODEX_HOME")


class TransportError(RuntimeError):
    pass


def trusted_file(path: Path) -> Path:
    path = path.absolute()
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise TransportError("configuration/metadata must be an owner-controlled regular file")
    if path.resolve() != path:
        raise TransportError("configuration/metadata path must be canonical, without symlinks")
    return path


def read_object(path: Path) -> dict:
    path = trusted_file(path)
    if path.stat().st_size > 1024 * 1024:
        raise TransportError("configuration object too large")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TransportError("configuration must be an object")
    return value


def current_context(reference: Path) -> dict:
    """Extract metadata records only; no transcript text leaves this function."""
    ref = read_object(reference)
    if any(not isinstance(ref.get(key), str) or not ref[key] for key in
           ("source", "thread_id", "expected_turn_id")):
        raise TransportError("metadata reference identity is incomplete")
    source = trusted_file(Path(ref["source"]))
    session = None
    latest = None
    # Filter raw record types before JSON decoding non-metadata payloads.
    with source.open("rb") as stream:
        for line in stream:
            if not (b'"turn_context"' in line or b'"session_meta"' in line):
                continue
            record = json.loads(line)
            kind = record.get("type")
            payload = record.get("payload", {})
            if kind == "session_meta":
                session = {k: payload.get(k) for k in ("id", "model_provider")}
            elif kind == "turn_context":
                latest = {k: payload.get(k) for k in ("turn_id", "model", "effort")}
    if not session or session["id"] != ref.get("thread_id"):
        raise TransportError("native metadata thread identity mismatch")
    if session["model_provider"] != "openai":
        raise TransportError("this transport requires the current native OpenAI provider")
    if not latest or latest["turn_id"] != ref.get("expected_turn_id"):
        raise TransportError("native metadata turn is absent or has advanced; refresh reference")
    if not isinstance(latest["model"], str) or not SAFE_NAME.fullmatch(latest["model"]):
        raise TransportError("native model metadata is missing or invalid")
    if not isinstance(latest["effort"], str) or not SAFE_NAME.fullmatch(latest["effort"]):
        raise TransportError("native reasoning effort is missing or unsupported; no substitution")
    return {"thread_id": session["id"], **latest}


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def canonical_root(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute() or not path.exists() or path.is_symlink():
        raise TransportError("permission roots must exist and be absolute non-symlinks")
    resolved = path.resolve()
    if resolved == Path("/"):
        raise TransportError("whole-filesystem roots are forbidden")
    return resolved


def load_manifest(path: Path) -> dict:
    manifest_path = trusted_file(path)
    value = read_object(manifest_path)
    required = {"schema_version", "context_reference", "workspace", "read_roots",
                "write_roots", "deny_roots", "receipt_dir", "timeout_seconds"}
    if set(value) - required - {"web_search", "max_output_bytes"} or required - set(value):
        raise TransportError("manifest fields do not match schema")
    if value["schema_version"] != 1:
        raise TransportError("unsupported manifest schema")
    for key in ("read_roots", "write_roots", "deny_roots"):
        if not isinstance(value[key], list) or not all(isinstance(x, str) for x in value[key]):
            raise TransportError("permission roots must be string lists")
        value[key] = [canonical_root(x) for x in value[key]]
    value["workspace"] = canonical_root(value["workspace"])
    value["receipt_dir"] = canonical_root(value["receipt_dir"])
    value["context_reference"] = trusted_file(Path(value["context_reference"]))
    for key, low, high in (("timeout_seconds", 1, 7200), ("max_output_bytes", 1024, 67108864)):
        value.setdefault(key, 16777216)
        if type(value[key]) is not int or not low <= value[key] <= high:
            raise TransportError("invalid transport resource bound")
    value.setdefault("web_search", "disabled")
    if value["web_search"] not in {"disabled", "live"}:
        raise TransportError("web_search must be disabled or explicitly live")
    if not any(inside(value["workspace"], p) for p in value["read_roots"] + value["write_roots"]):
        raise TransportError("workspace is outside all allowed roots")
    if any(inside(value["receipt_dir"], p) for p in value["write_roots"]):
        raise TransportError("trusted receipts must be outside model-writable roots")
    if any(inside(protected, root) for protected in (manifest_path, value["context_reference"])
           for root in value["write_roots"]):
        raise TransportError("manifest and metadata reference must be outside model-writable roots")
    info = value["receipt_dir"].stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise TransportError("receipt directory must be private and owner-controlled")
    for root in value["read_roots"] + value["write_roots"]:
        if any(inside(root, d) for d in value["deny_roots"]):
            raise TransportError("allowed root conflicts with a denied root")
    value["_manifest_path"] = manifest_path
    return value


def policy(manifest: dict, *, read_only: bool) -> dict:
    fs = {":minimal": "read"}
    for path in manifest["read_roots"]:
        fs[str(path)] = "read"
    for path in manifest["write_roots"]:
        fs[str(path)] = "read" if read_only else "write"
    # Native filesystem helpers re-exec this trusted binary under the same
    # profile. Grant that exact executable, not its enclosing home/tool tree.
    if manifest.get("_binary_path"):
        fs[str(manifest["_binary_path"])] = "read"
    home = Path.home()
    # Deny model tools, not the trusted native client's own ordinary auth.
    protected = [home / ".codex", home / ".docker", home / ".ssh", home / ".aws",
                 Path("/var/run/docker.sock"), Path("/private/var/run/docker.sock"),
                 manifest["receipt_dir"], manifest["context_reference"],
                 manifest["_manifest_path"],
                 *manifest["deny_roots"]]
    if os.environ.get("CODEX_HOME"):
        protected.append(Path(os.environ["CODEX_HOME"]).absolute())
    for path in protected:
        fs[str(path)] = "deny"
    return {"filesystem": fs, "network": {"enabled": False,
            "dangerously_allow_all_unix_sockets": False}}


def toml(value) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + "=" + toml(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(toml(x) for x in value) + "]"
    return json.dumps(value)


def clean_environment() -> dict:
    return {name: os.environ[name] for name in CLIENT_ENV if name in os.environ}


def config_arguments(manifest: dict, *, read_only: bool, context: dict) -> list[str]:
    settings = {
        "model_provider": "openai", "model_reasoning_effort": context["effort"],
        "approval_policy": "never", "default_permissions": "nstack_research",
        "permissions.nstack_research": policy(manifest, read_only=read_only),
        "web_search": manifest["web_search"], "mcp_servers": {},
        "plugins._default.enabled": False, "apps._default.enabled": False,
        "agents.enabled": False, "cloud.skills.enabled": False,
        "skills.bundled.enabled": False, "skills.include_instructions": False,
        "shell_environment_policy.inherit": "none",
        "shell_environment_policy.set": {k: v for k, v in clean_environment().items()
                                         if k in {"PATH", "HOME", "LANG", "TMPDIR"}},
        "analytics.enabled": False, "feedback.enabled": False, "allow_login_shell": False,
        "memories.generate_memories": False, "memories.use_memories": False,
        "memories.dedicated_tools": False,
    }
    settings.update({"features." + name: False for name in DISABLED_FEATURES})
    # Mark source roots untrusted so project configuration cannot enable hooks,
    # MCP tools or broader environment access. User/system exec rules stay active.
    # CLI dotted keys aren't a TOML quoted-key parser. Quote paths inside the
    # inline table value instead, so the actual path receives the trust rule.
    settings["projects"] = {str(manifest["workspace"]): {"trust_level": "untrusted"}}
    result = []
    for key, value in settings.items():
        result.extend(["-c", key + "=" + toml(value)])
    return result


def build_command(binary: str, manifest: dict, context: dict, work_dir: Path,
                  *, read_only: bool) -> list[str]:
    if not inside(work_dir, manifest["workspace"]):
        raise TransportError("requested workdir is outside the declared workspace")
    manifest["_binary_path"] = str(Path(binary).resolve())
    return [binary, "exec", "--ignore-user-config", "--strict-config", "--ephemeral",
            "--json", "--skip-git-repo-check", "--color", "never", "-C", str(work_dir),
            "--model", context["model"],
            *config_arguments(manifest, read_only=read_only, context=context), "-"]


def check_binary(binary: str) -> None:
    result = subprocess.run([binary, "--version"], env=clean_environment(),
                            capture_output=True, text=True, timeout=15, check=False)
    if result.returncode or result.stdout.strip() != REVIEWED_CLI_VERSION:
        raise TransportError("CLI version differs from reviewed native permission implementation")


def subscription_ready(binary: str) -> bool:
    # Do not log output: native API-mode status can contain a masked key.
    result = subprocess.run([binary, "login", "status"], env=clean_environment(),
                            capture_output=True, text=True, timeout=30, check=False)
    return result.returncode == 0 and (result.stdout + result.stderr).strip() == "Logged in using ChatGPT"


def parse_events(text: str, context: dict) -> tuple[str, dict]:
    final = None
    usage = None
    for line in text.splitlines():
        event = json.loads(line)
        if event.get("type") in {"turn.failed", "error"}:
            raise TransportError("native model turn failed; details retained privately")
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            final = item.get("text")
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
    if not isinstance(final, str) or not final.strip() or not isinstance(usage, dict):
        raise TransportError("native response lacks final answer or measured usage")
    fields = ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens")
    if any(type(usage.get(k)) is not int or usage[k] < 0 for k in fields):
        raise TransportError("native token accounting is incomplete")
    return final, {"agent": "codex", "provider": "openai", "model": context["model"],
                   "usageStatus": "reported", "costBasis": None, "cost": None,
                   "pricingSource": None, "pricingStatus": "missing", **usage}


def write_private(path: Path, value: dict) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def execute(command: list[str], prompt: str, manifest: dict, context: dict,
            *, read_only: bool) -> tuple[str, dict]:
    run_id = uuid.uuid4().hex
    root = manifest["receipt_dir"] / run_id
    root.mkdir(mode=0o700)
    receipt = {"status": "starting", "context": context, "command": command,
               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
               "policy": policy(manifest, read_only=read_only),
               "billing": "native ChatGPT preflight; no paid fallback; external auth-change race remains"}
    write_private(root / "request.json", receipt)
    if not subscription_ready(command[0]):
        raise TransportError("native ChatGPT subscription login not confirmed; no inference launched")
    # Validate metadata again at dispatch; an advanced parent turn is not an
    # invitation to use stale model/effort or continue after the user steers it.
    if current_context(manifest["context_reference"]) != context:
        raise TransportError("native parent context changed before dispatch")
    out = root / "native-events.jsonl"
    err = root / "native-stderr.log"
    deadline = time.monotonic() + manifest["timeout_seconds"]
    with out.open("xb") as stdout, err.open("xb") as stderr:
        os.chmod(out, 0o600)
        os.chmod(err, 0o600)
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                env=clean_environment(), start_new_session=True)
        try:
            proc.stdin.write(prompt.encode())
            proc.stdin.close()
            while proc.poll() is None:
                if time.monotonic() >= deadline or out.stat().st_size + err.stat().st_size > manifest["max_output_bytes"]:
                    raise TransportError("native model process exceeded its declared resource bound")
                time.sleep(0.1)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)
    if proc.returncode:
        raise TransportError("native Codex failed; private events retained; no provider/model fallback")
    if out.stat().st_size + err.stat().st_size > manifest["max_output_bytes"]:
        raise TransportError("native model process exceeded its declared output bound")
    final, usage = parse_events(out.read_text(), context)
    write_private(root / "completion.json", {"status": "completed", "context": context,
                  "usage": usage, "events_sha256": hashlib.sha256(out.read_bytes()).hexdigest()})
    return final, usage


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("agent", nargs="?", choices=["codex"])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--allow", choices=["read-only", "yolo"], default="read-only")
    parser.add_argument("--usage", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--reasoning-effort")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        context = current_context(manifest["context_reference"])
        if args.model is not None and args.model != context["model"]:
            raise TransportError("requested model differs from current native parent")
        if args.reasoning_effort is not None and args.reasoning_effort != context["effort"]:
            raise TransportError("requested effort differs from current native parent")
        discovered_binary = shutil.which("codex")
        if discovered_binary is None:
            raise TransportError("native Codex CLI is absent")
        binary = str(Path(discovered_binary).resolve())
        check_binary(binary)
        if args.check:
            print(json.dumps({"available": True, "cli": REVIEWED_CLI_VERSION,
                              "context": context, "inference": False, "auth_checked": False}))
            return 0
        work_dir = (args.work_dir or Path.cwd()).resolve()
        command = build_command(binary, manifest, context, work_dir,
                                read_only=args.allow == "read-only")
        if args.plan:
            print(json.dumps({"command": command, "policy": policy(manifest, read_only=args.allow == "read-only"),
                              "context": context, "inference": False}, indent=2))
            return 0
        if bool(args.prompt_file) == bool(args.prompt):
            raise TransportError("provide exactly one prompt or prompt-file")
        prompt = args.prompt if args.prompt is not None else args.prompt_file.read_text()
        if not prompt.strip() or len(prompt.encode()) > 2097152:
            raise TransportError("prompt is empty or exceeds bound")
        final, usage = execute(command, prompt, manifest, context, read_only=args.allow == "read-only")
        print(final)
        print(json.dumps({"usage": usage}))
        return 0
    except (TransportError, OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print("research transport refused: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
