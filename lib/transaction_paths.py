"""Bind a transaction target to its directory, not just matching leaf bytes."""
import contextlib
import errno
import os
from pathlib import Path
from typing import NamedTuple


class Parent(NamedTuple):
    fd: int
    path: Path
    identity: dict


class BoundEntry(NamedTuple):
    path: Path
    parent_fd: int

    def __fspath__(self):
        return os.fspath(self.path)


def directory_identity(path, fd):
    status = os.fstat(fd)
    return {"path": str(path), "device": status.st_dev, "inode": status.st_ino}


@contextlib.contextmanager
def open_parent(path, expected=None, *, create=False):
    """Open without following any ancestor links; optionally create missing dirs.

    A binding may name the nearest existing ancestor when staging an absent
    parent. Validate that ancestor before creating any descendants. Keep the
    directory handle open until the final directory-relative mutation finishes.
    Private journal/staging storage is trusted, as in the transaction engine.
    """
    path = Path(path).absolute()
    if ".." in path.parts:
        raise ValueError("Non-canonical transaction target parent: " + str(path))
    parent = path.parent
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("No-follow transaction parent opening is unavailable")
    if expected is not None:
        if (not isinstance(expected, dict) or set(expected) != {"path", "device", "inode"}
                or not isinstance(expected["path"], str)
                or not Path(expected["path"]).is_absolute()
                or ".." in Path(expected["path"]).parts
                or not parent.is_relative_to(Path(expected["path"]))):
            raise ValueError("Invalid transaction parent binding: " + str(path))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with contextlib.ExitStack() as stack:
        def opened(name, **kwargs):
            descriptor = os.open(name, flags, **kwargs)
            stack.callback(os.close, descriptor)
            return descriptor

        current = Path(parent.anchor)
        fd = opened(str(current))
        matched = expected is None

        def check():
            nonlocal matched
            identity = directory_identity(current, fd)
            if expected is not None and str(current) == expected["path"]:
                if identity != expected:
                    raise ValueError("Changed transaction target parent: " + str(path))
                matched = True
            return identity

        identity = check()
        for part in parent.parts[1:]:
            try:
                child = opened(part, dir_fd=fd)
            except FileNotFoundError:
                if not matched:
                    raise ValueError("Missing transaction target parent: " + str(path)) from None
                if not create:
                    break
                os.mkdir(part, dir_fd=fd)
                child = opened(part, dir_fd=fd)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ValueError("Linked or non-directory transaction target parent: " + str(path)) from exc
                raise
            current /= part
            fd = child
            identity = check()
        if not matched:
            raise ValueError("Missing transaction target parent: " + str(path))
        yield Parent(fd, current, identity)


def parent_identity(path, expected=None):
    with open_parent(path, expected) as parent:
        return parent.identity
