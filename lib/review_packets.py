#!/usr/bin/env python3
"""Build and read local, versioned Elephant–Goldfish review packets."""
from contextlib import contextmanager, ExitStack, suppress
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import zipfile


STORE = ".stackplus-review"
FORMAT = "stackplus-review-v1"
REQUIRED = ("artifact",)
ROLES = ("requirements", "artifact", "evidence", "finding", "resolution")
DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def check_id(value):
    if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
        raise ValueError("Expected a 64-character lowercase SHA-256 packet ID.")
    return value


def path_parts(name):
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts) or parts[0] == STORE:
        raise ValueError(f"Expected a project-relative input file path: {name!r}")
    return parts


@contextmanager
def directory(name, parent=None):
    fd = os.open(name, DIRECTORY, dir_fd=parent)
    try:
        yield fd
    finally:
        os.close(fd)


@contextmanager
def regular_file(parent, parts):
    # Open each component relative to a held directory. Renames and symlink swaps
    # cannot cause traversal through a different directory during this read.
    with ExitStack() as stack:
        for component in parts[:-1]:
            parent = stack.enter_context(directory(component, parent))
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError(f"Expected a regular file: {'/'.join(parts)}")
            yield stream


def fingerprint(stream, target=None):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
        if target is not None:
            target.write(chunk)
    return digest.hexdigest()


def source_hash(project, name, target=None):
    with regular_file(project, path_parts(name)) as stream:
        before = os.fstat(stream.fileno())
        digest = fingerprint(stream, target)
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_ctime_ns) != (after.st_size, after.st_ctime_ns):
            raise ValueError(f"Input changed during read: {name}")
        return digest


def load_manifest(archive, packet_id):
    raw = archive.read("manifest.json")
    if hashlib.sha256(raw).hexdigest() != packet_id:
        raise ValueError(f"Manifest does not match packet ID {packet_id}")
    manifest = json.loads(raw)
    if set(manifest) != {"format", "parent", "files"} or manifest["format"] != FORMAT:
        raise ValueError("Unsupported review manifest")
    if manifest["parent"] is not None:
        check_id(manifest["parent"])
    files = manifest["files"]
    if not isinstance(files, list):
        raise ValueError("Invalid file list")
    seen = set()
    roles = set()
    members = ["manifest.json"]
    for i, record in enumerate(files):
        if set(record) != {"path", "roles", "sha256"}:
            raise ValueError("Invalid file record")
        name = record["path"]
        path_parts(name)
        if name in seen or not record["roles"] or not set(record["roles"]) <= set(ROLES):
            raise ValueError(f"Invalid review input: {name}")
        seen.add(name)
        roles.update(record["roles"])
        check_id(record["sha256"])
        member = f"inputs/{i}"
        members.append(member)
        with archive.open(member) as stream:
            if fingerprint(stream) != record["sha256"]:
                raise ValueError(f"Snapshot differs from manifest: {name}")
    if not set(REQUIRED) <= roles or sorted(archive.namelist()) != sorted(members):
        raise ValueError("Missing required inputs or unexpected archive members")
    return manifest


@contextmanager
def snapshot(store, packet_id):
    name = check_id(packet_id) + ".zip"
    with regular_file(store, [name]) as stream, zipfile.ZipFile(stream) as archive:
        yield archive, load_manifest(archive, packet_id)


def ancestors(store, packet_id):
    visited = set()
    while packet_id is not None:
        if packet_id in visited:
            raise ValueError("Circular packet history")
        visited.add(packet_id)
        with snapshot(store, packet_id) as (_, manifest):
            packet_id = manifest["parent"]
    return len(visited)


def stale_inputs(project, manifest):
    stale = {}
    for record in manifest["files"]:
        name = record["path"]
        try:
            if source_hash(project, name) != record["sha256"]:
                stale[name] = "contents changed"
        except (ValueError, OSError) as error:
            stale[name] = str(error)
    return stale


def pack(project, store, args):
    ancestors(store, args.parent)
    paths = {}
    for role in ROLES:
        for name in getattr(args, role):
            path_parts(name)
            paths.setdefault(name, set()).add(role)

    # Publish a completed archive under its content address with an exclusive
    # link. Concurrent producers can reuse a verified winner; no file is replaced.
    temporary = ".pending-" + secrets.token_hex(16)
    fd = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=store)
    try:
        with os.fdopen(fd, "w+b") as stream:
            files = []
            with zipfile.ZipFile(stream, "w") as archive:
                for i, (name, roles) in enumerate(sorted(paths.items())):
                    with archive.open(f"inputs/{i}", "w", force_zip64=True) as target:
                        digest = source_hash(project, name, target)
                    files.append({"path": name, "roles": sorted(roles), "sha256": digest})
                manifest = {"format": FORMAT, "parent": args.parent, "files": files}
                raw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
                packet_id = hashlib.sha256(raw).hexdigest()
                archive.writestr("manifest.json", raw)
            stream.flush()
            os.fsync(stream.fileno())
        if stale := stale_inputs(project, manifest):
            raise ValueError(f"Inputs changed while packing: {json.dumps(stale)}")
        with suppress(FileExistsError):
            os.link(temporary, packet_id + ".zip", src_dir_fd=store, dst_dir_fd=store)
        with snapshot(store, packet_id):
            pass
        print(packet_id)
    finally:
        os.unlink(temporary, dir_fd=store)


def add_arguments(cli):
    commands = cli.add_subparsers(dest="action", required=True)
    commands.add_parser("guide", help="read the lead, implementer and reviewer workflow")
    make = commands.add_parser("pack", help="pin the listed files and print their packet ID")
    for role in ROLES:
        make.add_argument("--" + role, action="append", default=[], required=role in REQUIRED,
                          metavar="PATH", help="project-relative file (repeatable)")
    make.add_argument("--parent", metavar="ID", help="link a previously verified packet")
    check = commands.add_parser("verify", help="check packet integrity and revision history")
    check.add_argument("--current", action="store_true", help="also compare the current project files")
    show = commands.add_parser("show", help="read a manifest or a pinned file")
    show.add_argument("--file", metavar="PATH", help="write exact snapshot bytes to stdout")
    for command in (make, check, show):
        command.add_argument("--project", type=Path, default=Path("."), help="project root (default: cwd)")
    for command in (check, show):
        command.add_argument("id", metavar="PACKET_ID")
    return cli


def run(args):
    if args.action == "guide":
        guide = Path(__file__).resolve().parents[1] / "docs" / "STACKPLUS-REVIEW.md"
        print(guide.read_text(), end="")
        return 0
    with directory(args.project.resolve(strict=True)) as project:
        if args.action == "pack":
            with suppress(FileExistsError):
                os.mkdir(STORE, 0o700, dir_fd=project)
        with directory(STORE, project) as store:
            if args.action == "pack":
                pack(project, store, args)
                return 0
            with snapshot(store, args.id) as (archive, manifest):
                if args.action == "verify":
                    depth = ancestors(store, manifest["parent"])
                    stale = stale_inputs(project, manifest) if args.current else None
                    print(json.dumps({"id": args.id, "integrity": "verified", "ancestors": depth,
                                      "stale": stale}, sort_keys=True))
                    return 1 if stale else 0
                if args.file is None:
                    print(json.dumps(manifest, indent=2))
                    return 0
                for i, record in enumerate(manifest["files"]):
                    if record["path"] == args.file:
                        with archive.open(f"inputs/{i}") as stream:
                            shutil.copyfileobj(stream, sys.stdout.buffer)
                        return 0
                raise ValueError(f"File is absent from this packet: {args.file}")


def command(args):
    try:
        return run(args)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        raise ValueError(f"Review packet: {error}") from error
