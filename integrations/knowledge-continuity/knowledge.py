#!/usr/bin/env python3
"""Curated local knowledge capture. Invoke through the lead's normal native tool.

Hooks only call `event`; that operation cannot read sources/notes or write notes.
No model, network, transcript, credential or generated-memory access exists here.
"""
from __future__ import annotations

import argparse
import builtins
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import types

MAX_INPUT = 65536
MAX_NOTE = 131072
ID = re.compile(r"[A-Za-z0-9_-]{1,160}\Z")
NOTE_ID = re.compile(r"[a-z0-9][a-z0-9-]{1,100}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
SECRET = re.compile(r"(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
FORBIDDEN = {".ssh", ".aws", ".docker", ".gnupg", "memories_v2", "keychains", "credentials", "credential"}
CUE = "If a durable decision, correction or lesson emerges, follow the existing Knowledge guidance."


class Rejected(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_enabled(cfg: dict) -> None:
    if cfg["enabled"] is not True or os.environ.get("NSTACK_KNOWLEDGE_DISABLED") == "1":
        raise Rejected("capture disabled")


def filesystem_tools():
    """Bind the writer's utilities to this release without changing Python's import path."""
    library = Path(__file__).resolve().parents[2] / "lib"
    paths = types.ModuleType("nstack_knowledge_transaction_paths")
    transaction = types.ModuleType("nstack_knowledge_transaction")

    def release_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "transaction_paths" and level == 0:
            return paths
        return builtins.__import__(name, globals, locals, fromlist, level)

    # transaction.py imports its sibling by its standalone name. Scope that
    # binding to this module so callers' import paths and module caches stay intact.
    transaction.__dict__["__builtins__"] = {**vars(builtins), "__import__": release_import}
    for module, filename in ((paths, "transaction_paths.py"), (transaction, "transaction.py")):
        source = safe_absolute(str(library / filename))
        module.__file__ = str(source)
        exec(compile(regular_bytes(source, 1024 * 1024), str(source), "exec"), module.__dict__)
    return transaction


def regular_bytes(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise Rejected("expected a bounded regular file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise Rejected("input exceeds bound")
        return data
    finally:
        os.close(fd)


def safe_absolute(raw: str, *, exists: bool = True) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise Rejected("invalid path")
    path = Path(raw)
    if not path.is_absolute() or ".." in path.parts:
        raise Rejected("absolute canonical path required")
    if any(part.lower() in FORBIDDEN for part in path.parts):
        raise Rejected("private host/credential paths are excluded")
    if path.resolve(strict=exists) != path:
        raise Rejected("symlink/noncanonical path is excluded")
    return path


def load_json(path: Path, limit: int = MAX_INPUT) -> dict:
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise Rejected("duplicate JSON key")
            out[key] = value
        return out
    data = json.loads(regular_bytes(path, limit), object_pairs_hook=unique)
    if not isinstance(data, dict):
        raise Rejected("JSON object required")
    return data


def settings(path: Path) -> dict:
    cfg = load_json(path)
    required = {"version", "enabled", "owner", "vault", "vault_name", "state", "obsidian", "git"}
    if set(cfg) - required - {"excluded_source_roots"} or not required <= set(cfg) or type(cfg["version"]) is not int or cfg["version"] != 1 or type(cfg["enabled"]) is not bool:
        raise Rejected("unsupported settings schema")
    roots = cfg.get("excluded_source_roots", [])
    if not isinstance(roots, list) or len(roots) > 32 or any(not isinstance(p, str) or not Path(p).is_absolute() or ".." in Path(p).parts for p in roots):
        raise Rejected("invalid excluded source roots")
    if not isinstance(cfg["owner"], str) or not 1 <= len(cfg["owner"]) <= 100 or any(ord(c) < 32 for c in cfg["owner"]):
        raise Rejected("invalid owner")
    for key in ("vault", "state", "obsidian", "git"):
        if not isinstance(cfg[key], str):
            raise Rejected("invalid settings path")
        # Event code checks lexical paths only, never opens vault, binaries or sources.
        if not Path(cfg[key]).is_absolute() or ".." in Path(cfg[key]).parts:
            raise Rejected("absolute settings paths required")
    if Path(cfg["state"]).is_relative_to(Path(cfg["vault"])):
        raise Rejected("private state must remain outside the vault")
    if not isinstance(cfg["vault_name"], str) or not re.fullmatch(r"[\w -]{1,80}", cfg["vault_name"]):
        raise Rejected("invalid vault name")
    return cfg


def identity(host: str, session: str, event: str) -> str:
    if host not in {"codex", "opencode"} or not isinstance(session, str) or not ID.fullmatch(session) or not isinstance(event, str) or not ID.fullmatch(event):
        raise Rejected("invalid event identity")
    return digest(f"{host}\0{session}\0{event}".encode())


def receipt_path(cfg: dict, key: str) -> Path:
    state = safe_absolute(cfg["state"])
    folder = state / "receipts"
    if folder.exists() and folder.resolve() != folder:
        raise Rejected("unsafe receipt directory")
    return folder / (key + ".json")


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".knowledge-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def receipt(cfg: dict, host: str, session: str, event: str, status: str, **extra) -> dict:
    require_enabled(cfg)
    key = identity(host, session, event)
    if status not in {"saved", "skip", "blocked", "missing"}:
        raise Rejected("invalid receipt status")
    existing = read_receipt(cfg, key)
    if existing and existing["status"] == "saved":
        raise Rejected("saved event receipt is immutable")
    data = {"version": 1, "key": key, "host": host, "status": status, "observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), **extra}
    atomic_json(receipt_path(cfg, key), data)
    folder = receipt_path(cfg, key).parent
    entries = sorted((p for p in folder.iterdir() if re.fullmatch(r"[0-9a-f]{64}\.json", p.name) and p.is_file() and not p.is_symlink()), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    for old in entries[512:]:
        item = load_json(old, 4096)
        if item.get("version") == 1 and item.get("key") == old.stem and item.get("host") in {"codex", "opencode"}:
            old.unlink()
    return data


def read_receipt(cfg: dict, key: str) -> dict | None:
    path = receipt_path(cfg, key)
    if not path.exists():
        return None
    item = load_json(path, 4096)
    if item.get("version") != 1 or item.get("key") != key or item.get("status") not in {"saved", "skip", "blocked", "missing"}:
        raise Rejected("invalid receipt")
    return item


def event(cfg: dict, payload: dict) -> dict:
    """Passive native identity; no state lookup, receipt, vault read or continuation."""
    if not cfg["enabled"] or os.environ.get("NSTACK_KNOWLEDGE_DISABLED") == "1":
        return {}
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return {}  # Stop remains inert for old bindings.
    if "agent_id" in payload or "agent_type" in payload:
        return {}
    cwd = safe_absolute(payload.get("cwd", ""))
    if not cwd.is_dir() or not os.access(cwd, os.R_OK | os.W_OK):
        return {}
    session, turn = payload.get("session_id"), payload.get("turn_id")
    identity("codex", session, turn)  # Validate real IDs without reading state.
    marker = f"Knowledge event: host=codex session={session} event={turn}."
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": marker + "\n" + CUE}}


def metadata(data: bytes) -> tuple[dict, str]:
    text = data.decode("utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise Rejected("Markdown frontmatter required")
    header, body = text[4:].split("\n---\n", 1)
    values = {}
    for line in header.splitlines():
        match = re.fullmatch(r"([A-Za-z_][\w-]*):(?: (.*))?", line)
        if match:
            name, value = match.groups()
            if name in values:
                raise Rejected("duplicate frontmatter field")
            value = value or ""
            if value.startswith('"'):
                value = json.loads(value)
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            values[name] = value
    return values, body


def note_path(vault: Path, raw: str) -> Path:
    if not isinstance(raw, str) or len(raw) > 240 or "\\" in raw or any(ord(c) < 32 for c in raw):
        raise Rejected("invalid note path")
    rel = Path(raw)
    if rel.is_absolute() or rel.suffix != ".md" or any(x in {"", ".", ".."} or x.startswith(".") for x in rel.parts):
        raise Rejected("vault-relative Markdown path required")
    target = vault / rel
    safe_absolute(str(target), exists=target.exists())
    return target


def stable_id_available(vault: Path, target: Path, note_id: str) -> None:
    """Inspect bounded frontmatter IDs only, never aggregate note bodies."""
    for other in vault.rglob("*.md"):
        if other == target or any(part.startswith(".") for part in other.relative_to(vault).parts):
            continue
        safe_absolute(str(other))
        fd = os.open(other, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise Rejected("nonregular vault note")
            prefix = os.read(fd, 4)
            if prefix == b"---\n":
                while len(prefix) < 8192 and not prefix.endswith(b"\n---\n"):
                    byte = os.read(fd, 1)
                    if not byte:
                        break
                    prefix += byte
        finally:
            os.close(fd)
        if not prefix.startswith(b"---\n"):
            continue
        if b"\n---\n" not in prefix:
            raise Rejected("note frontmatter exceeds verification bound")
        values, _ = metadata(prefix.split(b"\n---\n", 1)[0] + b"\n---\n")
        if values.get("note_id") == note_id:
            raise Rejected("stable note ID already belongs to another path")


def run(argv: list[str], *, cwd: Path, timeout: int = 30) -> bytes:
    result = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        # Never expose possibly private command output or environment.
        raise Rejected(f"native command failed (exit {result.returncode})")
    if len(result.stdout) > 2 * MAX_NOTE:
        raise Rejected("native output exceeds bound")
    return result.stdout


def git_preflight(cfg: dict, vault: Path, rel: str) -> str:
    git = str(safe_absolute(cfg["git"]))
    if Path(run([git, "rev-parse", "--show-toplevel"], cwd=vault).decode().strip()) != vault:
        raise Rejected("vault must own its Git repository")
    if run([git, "remote"], cwd=vault).strip():
        raise Rejected("private vault must have no remotes")
    if run([git, "--literal-pathspecs", "diff", "--cached", "--name-only", "-z", "--", rel], cwd=vault).strip():
        raise Rejected("target has pre-existing staged work")
    # Git honors its normal config, hooks and native execution policy.
    return run([git, "rev-parse", "HEAD"], cwd=vault).decode().strip()


def transaction_root(state: Path) -> Path:
    folder = state / "transactions"
    if folder.is_symlink():
        raise Rejected("linked transaction parent is excluded")
    if not folder.exists():
        folder.mkdir(mode=0o700)
    safe_absolute(str(folder))
    if not folder.is_dir():
        raise Rejected("transaction parent must be a directory")
    return folder


def prepare_journal(path: Path) -> None:
    """The writer lock is held. Only an empty, private pre-write journal is reusable."""
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        safe_absolute(str(path))
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700
                    or os.listdir(fd)):
                raise Rejected("existing event journal requires reviewed recovery")
        finally:
            os.close(fd)
    safe_absolute(str(path))


def require_completed_duplicate(cfg: dict, vault: Path, target: Path, before: bytes, transactions: Path) -> None:
    rel = str(target.relative_to(vault))
    git_preflight(cfg, vault, rel)
    git = str(safe_absolute(cfg["git"]))
    if run([git, "show", f"HEAD:{rel}"], cwd=vault) != before:
        raise Rejected("duplicate bytes lack matching checkpoint; reviewed recovery required")
    children = list(transactions.iterdir())
    if len(children) > 10000:
        raise Rejected("transaction inventory exceeds verification bound")
    for child in children:
        if child.is_symlink() or not child.is_dir() or not HASH.fullmatch(child.name):
            raise Rejected("unknown transaction entry")
        safe_absolute(str(child))
        record = load_json(child / "transaction.json", 16384)
        if record.get("note") == rel:
            phase = load_json(child / "stage.json", 4096) if (child / "stage.json").exists() else {}
            if phase.get("stage") != "checkpointed":
                raise Rejected("unresolved transaction requires reviewed recovery")


def source_path_allowed(raw: str, cfg: dict) -> None:
    """Reject known host stores lexically, before any source open/read."""
    if not isinstance(raw, str):
        raise Rejected("invalid source path")
    path = Path(raw)
    parts = [part.lower() for part in path.parts]
    stores = {"sessions", "archived_sessions", "memories", "memories_v2", "memory", "rollout_summaries", "memory_summary.md"}
    for n, part in enumerate(parts[:-1]):
        if part in {".codex", ".opencode"} and parts[n + 1] in stores:
            raise Rejected("host transcripts/generated memory cannot be file evidence")
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    roots = [codex_home / name for name in stores]
    roots.extend(Path(root) for root in cfg.get("excluded_source_roots", []))
    roots.extend([Path(os.environ.get("XDG_DATA_HOME", str(home / ".local/share"))) / "opencode", Path(os.environ.get("XDG_STATE_HOME", str(home / ".local/state"))) / "opencode", home / "Library/Application Support/opencode"])
    if any(root.is_absolute() and (path == root or path.is_relative_to(root)) for root in roots):
        raise Rejected("host transcripts/generated memory cannot be file evidence")


def late_checkpoint_result(expected: dict, observed: dict) -> str:
    """One final observation, after mutation/checkpoint; never a mutation gate."""
    if expected == observed:
        return "exact"
    if sys.platform != "darwin" or getattr(stat, "UF_TRACKED", None) != 0x40:
        return "rejected"
    if expected.get("kind") != "file" or observed.get("kind") != "file":
        return "rejected"
    before_flags = expected.get("metadata", {}).get("flags")
    after_flags = observed.get("metadata", {}).get("flags")
    if type(before_flags) is not int or type(after_flags) is not int or before_flags < 0 or after_flags < 0 or after_flags == before_flags or after_flags != (before_flags | 0x40):
        return "rejected"
    comparison = copy.deepcopy(observed)
    comparison["metadata"]["flags"] = before_flags
    return "darwin-uf-tracked-added" if comparison == expected else "rejected"


def verify_late_checkpoint(fs, target: Path, expected: dict, journal: Path) -> tuple[dict, str]:
    # Exactly one actual fingerprint is captured and returned unmodified.
    observed = fs.fingerprint(target)
    outcome = late_checkpoint_result(expected, observed)
    atomic_json(journal / "late-verification.json", {
        "version": 1, "phase": "post-checkpoint", "platform": sys.platform,
        "observed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expected": expected, "observed": observed, "result": outcome,
        "expected_metadata_sha256": digest(json.dumps(expected.get("metadata"), sort_keys=True).encode()),
        "observed_metadata_sha256": digest(json.dumps(observed.get("metadata"), sort_keys=True).encode()),
    })
    if outcome == "rejected":
        raise Rejected("post-checkpoint fingerprint mismatch; reviewed recovery required")
    return observed, outcome


def prepare(cfg: dict, candidate: dict, host: str, session: str, event_id: str) -> tuple[Path, bytes, bytes, dict]:
    fields = {"version", "note", "note_id", "scope", "source_kind", "source", "source_sha256", "source_revision", "event_date", "expected_sha256", "expected_generation", "body", "reason"}
    if set(candidate) != fields or type(candidate["version"]) is not int or candidate["version"] != 1:
        raise Rejected("unsupported candidate schema")
    identity(host, session, event_id)
    for key in ("note_id", "scope", "source_revision", "event_date", "body", "reason"):
        if not isinstance(candidate[key], str) or not candidate[key].strip():
            raise Rejected("empty candidate field")
    if not NOTE_ID.fullmatch(candidate["note_id"]):
        raise Rejected("invalid stable ID/source hash")
    if len(candidate["scope"]) > 240 or len(candidate["reason"]) > 500 or len(candidate["source_revision"]) > 240 or len(candidate["body"].encode()) > 32768 or SECRET.search(json.dumps(candidate)):
        raise Rejected("candidate exceeds bounds or contains a credential pattern")
    dt.date.fromisoformat(candidate["event_date"])
    vault = safe_absolute(cfg["vault"])
    if not vault.is_dir():
        raise Rejected("vault unavailable")
    target = note_path(vault, candidate["note"])
    stable_id_available(vault, target, candidate["note_id"])
    source = None
    if candidate["source_kind"] == "file":
        if not isinstance(candidate["source_sha256"], str) or not HASH.fullmatch(candidate["source_sha256"]):
            raise Rejected("invalid file source hash")
        source_path_allowed(candidate["source"], cfg)
        source = safe_absolute(candidate["source"])
        source_name = source.name.lower()
        if source_name in {"auth.json", "credentials.json", "opencode.json", "opencode.jsonc", "config.toml"} or source_name.startswith((".env", "credentials", "secrets")) or source.suffix.lower() in {".key", ".pem"}:
            raise Rejected("credential/config sources excluded")
        if digest(regular_bytes(source, 64 * 1024 * 1024)) != candidate["source_sha256"]:
            raise Rejected("source hash changed")
        if source == target:
            raise Rejected("owning source must be separate from note")
    elif candidate["source_kind"] == "current-context":
        if candidate["source"] != f"{host}:{session}:{event_id}" or candidate["source_sha256"] is not None or candidate["source_revision"] != "current-context":
            raise Rejected("current-context attribution must match this event without invented file hash")
    else:
        raise Rejected("unknown source kind")
    before = regular_bytes(target, MAX_NOTE) if target.exists() else b""
    generation = candidate["expected_generation"]
    if type(generation) is not int or generation < 0:
        raise Rejected("invalid expected generation")
    if before:
        old, old_body = metadata(before)
        if not isinstance(candidate["expected_sha256"], str) or not HASH.fullmatch(candidate["expected_sha256"]) or digest(before) != candidate["expected_sha256"] or old.get("note_id") != candidate["note_id"] or old.get("generation") != str(generation) or old.get("scope") != candidate["scope"] or old.get("owner") != cfg["owner"] or old.get("state") not in {"draft", "current", "historical", "retired"}:
            raise Rejected("note ID/scope/generation/hash precondition failed")
        # Same supported content is already knowledge; host origin need not create duplication.
        if old_body.rstrip() == candidate["body"].rstrip() and (candidate["source_kind"] == "current-context" or old.get("source_sha256") == candidate["source_sha256"]):
            return target, before, before, {"duplicate": True}
        header = before.decode().split("\n---\n", 1)[0][4:]
        blocks = re.split(r"(?m)(?=^[A-Za-z_][\w-]*:)", header)
        replace = {"note_id", "owner", "scope", "state", "generation", "source_kind", "source", "source_sha256", "source_revision", "source_verification", "event_date", "observed_date", "supersedes", "correction_reason", "correction_path", "capture_host", "capture_event"}
        preserved = [b.rstrip() for b in blocks if b.strip() and b.split(":", 1)[0] not in replace]
    else:
        if target.exists() or generation != 0 or candidate["expected_sha256"] is not None:
            raise Rejected("new note requires absent target and generation zero")
        preserved = []
    values = {"note_id": candidate["note_id"], "owner": cfg["owner"], "scope": candidate["scope"], "state": "current", "generation": generation + 1, "source_kind": candidate["source_kind"], "source": candidate["source"], "source_sha256": candidate["source_sha256"], "source_revision": candidate["source_revision"], "source_verification": "file bytes/hash verified; claim meaning remains lead-reviewed" if source else "lead current-context attribution; no independent file verification", "event_date": candidate["event_date"], "observed_date": dt.date.today().isoformat(), "supersedes": f"{candidate['note_id']} generation {generation}" if generation else "none", "correction_reason": candidate["reason"], "correction_path": candidate["note"], "capture_host": host, "capture_event": identity(host, session, event_id)}
    header = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in values.items())
    if preserved:
        header += "\n" + "\n".join(preserved)
    after = ("---\n" + header + "\n---\n" + candidate["body"].rstrip() + "\n").encode()
    return target, before, after, {"duplicate": False, "generation": generation + 1, "source": str(source) if source else None, "source_sha256": candidate["source_sha256"]}


def capture(cfg: dict, candidate: dict, host: str, session: str, event_id: str, *, verify_obsidian: bool = False) -> dict:
    require_enabled(cfg)
    key = identity(host, session, event_id)
    state = safe_absolute(cfg["state"])
    vault = safe_absolute(cfg["vault"])
    if state == vault or state.is_relative_to(vault):
        raise Rejected("private state must remain outside the vault")
    lockpath = state / "writer.lock"
    fd = os.open(lockpath, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Rejected("invalid writer lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        existing = read_receipt(cfg, key)
        if existing and existing["status"] == "saved":
            if existing.get("candidate_sha256") != digest(json.dumps(candidate, sort_keys=True).encode()):
                raise Rejected("event already assessed with different candidate")
            return existing
        transactions = transaction_root(state)
        target, before, after, info = prepare(cfg, candidate, host, session, event_id)
        if info["duplicate"]:
            require_completed_duplicate(cfg, vault, target, before, transactions)
            return receipt(cfg, host, session, event_id, "skip", reason="duplicate", note=candidate["note"], note_sha256=digest(before), candidate_sha256=digest(json.dumps(candidate, sort_keys=True).encode()))
        vault = safe_absolute(cfg["vault"])
        head_before = git_preflight(cfg, vault, candidate["note"])
        fs = filesystem_tools()
        journal = transactions / key
        prepare_journal(journal)
        baseline = fs.fingerprint(target)
        if (before and (baseline.get("kind") != "file" or baseline.get("sha256") != digest(before))) or (not before and baseline.get("kind") != "absent"):
            raise Rejected("note changed before backup")
        # Preserve actual bytes and supported metadata, then independently restore both.
        if before:
            fs.copy(target, journal / "before.md")
            fs.same(journal / "before.md", baseline)
            fs.same(target, baseline)
        else:
            (journal / "before.md").write_bytes(before)
        restored = journal / "restore-rehearsal.md"
        if before:
            fs.copy(journal / "before.md", restored)
            fs.same(restored, baseline)
        else:
            restored.write_bytes(before)
        if regular_bytes(restored, MAX_NOTE) != before:
            raise Rejected("restoration rehearsal mismatch")
        (journal / "candidate.md").write_bytes(after)
        atomic_json(journal / "transaction.json", {"version": 1, "key": key, "note": candidate["note"], "before_sha256": digest(before) if before else None, "before_fingerprint": baseline, "after_sha256": digest(after), "stage": "prepared", **info})
        # Recheck source and target after all preparation. No fallback on conflict/denial.
        if info["source"] and digest(regular_bytes(Path(info["source"]), 64 * 1024 * 1024)) != info["source_sha256"]:
            raise Rejected("source changed during preparation")
        if (regular_bytes(target, MAX_NOTE) if target.exists() else b"") != before:
            raise Rejected("note changed during preparation")
        fs.same(target, baseline)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        safe_absolute(str(target.parent))
        if before:
            temp_fd, tmp = tempfile.mkstemp(prefix=".knowledge-", dir=target.parent)
            os.close(temp_fd)
            try:
                stage = Path(tmp)
                fs.copy(target, stage)
                fs.same(stage, baseline)
                mode = baseline["metadata"]["mode"]
                stage.chmod(mode | stat.S_IWUSR)
                with stage.open("wb") as stream:
                    stream.write(after); stream.flush(); os.fsync(stream.fileno())
                stage.chmod(mode)
                desired = fs.fingerprint(stage)
                if desired["metadata"] != baseline["metadata"]:
                    raise Rejected("note metadata cannot be preserved")
                if regular_bytes(target, MAX_NOTE) != before:
                    raise Rejected("note changed before replacement")
                fs.same(target, baseline)
                os.replace(tmp, target)
                fs.same(target, desired)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        else:
            new_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(new_fd, "wb") as stream:
                stream.write(after); stream.flush(); os.fsync(stream.fileno())
            desired = fs.fingerprint(target)
        atomic_json(journal / "stage.json", {"stage": "written", "after_sha256": digest(after), "after_fingerprint": desired})
        if regular_bytes(target, MAX_NOTE) != after:
            raise Rejected("independent file readback mismatch; recovery retained")
        indexing = "deferred"
        if verify_obsidian:
            # Explicit acceptance option when the operator knows the app is open.
            # Normal future captures never call/autolaunch Obsidian.
            try:
                obsidian = str(safe_absolute(cfg["obsidian"]))
                observed = run([obsidian, f"vault={cfg['vault_name']}", "read", f"path={candidate['note']}"], cwd=vault)
                indexing = "verified" if observed.rstrip(b"\n") == after.rstrip(b"\n") else "failed"
            except (OSError, ValueError, subprocess.SubprocessError):
                indexing = "failed"
        if regular_bytes(target, MAX_NOTE) != after:
            raise Rejected("note changed before checkpoint")
        git = str(safe_absolute(cfg["git"]))
        # commit --only honors normal hooks and preserves unrelated staged entries.
        run([git, "--literal-pathspecs", "add", "--", candidate["note"]], cwd=vault)
        run([git, "--literal-pathspecs", "commit", "--only", "-m", f"Update knowledge: {candidate['note_id']}", "--", candidate["note"]], cwd=vault, timeout=60)
        if regular_bytes(target, MAX_NOTE) != after:
            raise Rejected("note changed during checkpoint")
        checkpoint = run([git, "rev-parse", "HEAD"], cwd=vault).decode().strip()
        parents = run([git, "rev-list", "--parents", "-n", "1", checkpoint], cwd=vault).decode().split()
        changed = run([git, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", checkpoint], cwd=vault).split(b"\0")
        if parents != [checkpoint, head_before] or [p for p in changed if p] != [os.fsencode(candidate["note"])]:
            raise Rejected("checkpoint changed-path/parent scope mismatch")
        committed = run([git, "show", f"HEAD:{candidate['note']}"], cwd=vault)
        if committed != after:
            raise Rejected("checkpoint bytes mismatch")
        final_observation, late_result = verify_late_checkpoint(fs, target, desired, journal)
        atomic_json(journal / "stage.json", {"stage": "checkpointed", "after_sha256": digest(after), "after_fingerprint": final_observation, "checkpoint": checkpoint, "late_verification": late_result})
        return receipt(cfg, host, session, event_id, "saved", note=candidate["note"], note_sha256=digest(after), generation=info["generation"], checkpoint=checkpoint, candidate_sha256=digest(json.dumps(candidate, sort_keys=True).encode()), obsidian_index=indexing, late_verification=late_result)
    finally:
        os.close(fd)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="nstack-knowledge")
    parser.add_argument("--settings", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("event")
    for name in ("capture", "skip", "blocked", "status"):
        item = sub.add_parser(name)
        item.add_argument("--host", choices=("codex", "opencode"), required=True)
        item.add_argument("--session", required=True)
        item.add_argument("--event", required=True)
        if name == "capture":
            item.add_argument("--candidate", type=Path, required=True)
            item.add_argument("--verify-obsidian", action="store_true")
        if name in {"skip", "blocked"}:
            item.add_argument("--reason", choices=("no-useful-knowledge", "duplicate", "native-denial", "unavailable", "conflict"), required=True)
    args = parser.parse_args(argv)
    try:
        cfg = settings(args.settings)
        if args.command == "event":
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise Rejected("hook input exceeds bound")
            payload = json.loads(raw)
            result = event(cfg, payload) if isinstance(payload, dict) else {}
        elif args.command == "capture":
            result = capture(cfg, load_json(args.candidate), args.host, args.session, args.event, verify_obsidian=args.verify_obsidian)
        elif args.command == "status":
            result = read_receipt(cfg, identity(args.host, args.session, args.event)) or {"status": "missing"}
        else:
            require_enabled(cfg)
            result = receipt(cfg, args.host, args.session, args.event, "skip" if args.command == "skip" else "blocked", reason=args.reason)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        # No input, candidate, command stdout/stderr, environment or traceback in logs.
        if args.command == "event":
            print("{}")
            return 0
        print(json.dumps({"status": "blocked", "error": str(error) if isinstance(error, Rejected) else type(error).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
