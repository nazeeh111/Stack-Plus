# Profile transaction ownership and recovery

The shared transaction engine protects each recorded file, link or directory
with both its contents/metadata and the identity of its containing directory.
It is used by the profile installers, host adapters, project configuration and
runtime registration. It is not an all-or-nothing filesystem snapshot.

## Directory ownership

New journal rows record a `parent` binding with the original directory's
absolute path, device and inode. An inode identifies a filesystem object, not
its contents. Replacing a directory with a byte-identical copy does not transfer
the transaction's authority to that copy.

Staged files retain their parent binding until replacement. Missing parent
directories can be created beneath a checked existing ancestor. Ancestor
symlinks are refused; a target leaf may itself be a symlink, with the original
link retained for recovery.

Apply, retry and rollback validate bindings without following ancestor links.
Final replacement, retirement and restoration operate relative to an opened
directory handle. Unlike-type directory/link replacements still use the native
atomic exchange, not delete-then-create.

When applying through an opened directory, journal preparation carries that
same directory binding and the caller's original baseline. It does not acquire
new authority from a pathname that may already name a substitute. Drift before
backup completion leaves an original-bound `backup-preparing` intent. Retrying
cannot adopt the substitute. Restoring the original directory permits retry;
rollback may instead cancel this untouched intent without changing either
directory. No target-entry replacement, retirement or removal is possible until
the prepared row is saved. Empty parents created during staging are retained,
as before; cancellation does not remove them.

Before rollback restores its first entry, it checks every pending parent. A
known changed parent therefore cannot leave an otherwise valid profile partly
restored. Later leaf-content conflicts and filesystem failures can still stop a
rollback partway through, as before; the journal records progress for retry.
Backup-preparing intents are the exception: they have no live changes to
restore and can be canceled without resolving the target.

Nested active targets are refused within one run. Replacing or retiring a
directory and independently changing its descendants cannot preserve one stable
parent identity. Use separately recoverable runs in reverse recovery order, or
manage the directory as one target.

## If recovery reports a changed, missing or linked parent

Do not edit the journal, copy its recorded inode into a new row, or remove the
foreign directory to force recovery. Keep the private run, backups, stages and
all current user bytes. Inspect what moved and who owns both directories.

If the original directory was renamed, retain the replacement separately and
restore the original directory to its recorded location. Then retry the saved
per-run recovery helper. Renaming the original back preserves its identity;
recreating it from copied files does not. If the original directory is gone,
manual, explicitly scoped reconciliation is required.

## Native removed-link repair

Repair of a removed native skill-root link uses the original applied journal
row's parent binding and publishes a metadata-preserving staged link relative to
the verified open directory without overwriting an occupied destination. Repair
requires a same-volume filesystem that supports hard links to symlinks; an
unsupported operation fails without replacing the destination.
A replacement or linked parent is refused; preserve it separately and rename
the original directory back before retrying. The original journal and rollback
baseline do not change. Legacy native rows without a parent binding cannot use
this automatic repair and require manual reconciliation. An already pinned
older helper does not gain this protection from a source update alone.

## Compatibility and limits

- Existing journal rows without a `parent` field remain recoverable. They gain
  ancestor-link refusal, but cannot retrospectively detect a byte-identical
  replacement directory. No identity is silently invented for those rows.
- Existing saved helpers execute their pinned code release. Updating source
  alone does not upgrade old recovery helpers or activate this protection.
- The private journal and staging directory remain trusted. This is not a
  sandbox against hostile processes or forged recovery records. Leaf-content
  checks are still point-in-time observations; non-cooperating writers can race
  them. A concurrent directory rename after a check can affect the originally
  opened directory, but cannot redirect the final operation into its substitute.
- This change adds no power-loss durability guarantee. It retains existing
  metadata-copy, same-volume, write-ahead and process-interruption behavior.
- No new dependency is required. The engine already requires Unix locking and
  native metadata support. No-follow directory handles are required; native
  atomic exchange must be available for unlike-type replacements.
