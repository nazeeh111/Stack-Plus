# Read-only discovery: task → component → route

This session was run from the public source recorded below on November 17, 2026,
using Python 3.14. The state path was absent before and after all three commands.
It did not read the user's deployed state, fetch source, build a skill, install a
runtime, alter host configuration or contact a model provider.

Use an absent temporary path of your choice for `NSTACK_STATE`:

```sh
NSTACK_STATE=/tmp/nstack-discovery-example python3 nstack.py search web-ui-design --brief
NSTACK_STATE=/tmp/nstack-discovery-example python3 nstack.py show L010
NSTACK_STATE=/tmp/nstack-discovery-example python3 nstack.py route L010
```

| Raw output | Useful evidence |
| --- | --- |
| [search.json](search.json) | L010 selects `web-ui-design` and `mcp-builder` |
| [show.json](show.json) | Pinned upstream revision, selected paths and distinct rights |
| [route.json](route.json) | Explicit prerequisites, task checks and retirement guidance |

The route says preparation is not target runtime acceptance. `staged_builds` was
empty in this isolated session. This is not a check of installed native discovery,
macOS permissions, optional runtimes or a live activation/rollback. Follow
[onboarding](../ONBOARDING.md), [source fidelity](../SOURCE_FIDELITY.md) and
[transactions](../TRANSACTIONS.md) for those separate workflows.

## Source identity

Repository: `nazeeh111/nstack`

Default-branch head: `c7f6c73bb3ae7fd5aba7c9bd41d8514a932926b7`

The presentation changes only documentation and its assets. This record does
not assert that an unpublished engineering successor is merged into the default.

## Reading the illustration

The [editable registry card](discovery.svg) depicts one search result. Its
component identifier and two native names come from `search.json`. The
seven-character revision is the prefix of the full `show.json` revision.
The rights label covers the two selected source paths only. The original
vector artwork uses system fonts and is distributed under the repository's
[MIT license](../../LICENSE). No upstream artwork or font files are bundled.
