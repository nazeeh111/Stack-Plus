# Stack+ selections

Select **01** once in a conversation and describe the finished outcome. The lead can use the host’s enabled skills and tools, look for a technique inside supporting files, and try an additional method when it could change the result. Elephant–Goldfish also works directly through `./stack+ review`. Existing grants and project-specific constraints apply throughout.

[The selection catalog](../registry/stackplus-selections.json) lists 219 methods and their intended scopes, plus 15 skill identities managed by their hosts. A source record gives the originating repository, commit and path. A checked-in adaptation identifies its directory in this checkout. Files shipped by a third party retain their own license and notices. Host-provided tools, account connections, large runtimes, project data and physical instruments have their own installation and access requirements.

## Choose and stage one method

From the Stack+ checkout, search by native name, publisher, source path or scope:

```sh
./stack+ selections review-pcba --json
./stack+ selections google-drive --json
```

Use `--stage` with an exact name and a new directory to obtain a bundle without changing either host’s configuration. The destination’s parent must exist. To prepare an on-demand method in the local Stack+ library:

```sh
library="${XDG_DATA_HOME:-$HOME/.local/share}/stackplus/library"
mkdir -p "$library"
./stack+ selections --stage repository-docs "$library/repository-docs"
```

For a project-specific method, stage it inside the project. For example, run these commands from the checkout with `project` set to an existing project you own:

```sh
project=/absolute/path/to/your/project
mkdir -p "$project/.stackplus" "$project/.agents/skills"
./stack+ selections --stage review-pcba-package "$project/.stackplus/review-pcba-package"
ln -s ../../.stackplus/review-pcba-package/bundle/skills/review-pcba-package "$project/.agents/skills/review-pcba-package"
```

The new link exposes that one method in the project. Use the host’s normal skill inventory to check eligibility there. The assembly method can open its publisher’s shared workflow and run the referenced project tool. Routine requests can use their direct project operations. To revert this opt-in, unlink the one project link you created. A staged bundle can remain available for inspection. A later stage requires a new destination and preserves existing files.

The staging routes use one normal source of truth per method:

- **122 base methods** use the public native builder, selecting the exact native ID in a temporary home. It applies the repository’s source-closure and naming adaptations.
- **23 methods** copy a complete checked-in bundle. The defensive review methods use static source inspection and conventional project tests.
- **74 publisher leaves** fetch an exact public Git commit and export the selected leaf, its declared shared support and available root notices. With a local Git object store, use `--source-checkout PATH` to select the pinned commit from it. Git may fetch missing objects in a partial clone.

The result has a `bundle/skills/NAME` entry, its `bundle/package/` material, and a `bundle/bundle.json` receipt with its source, scope and per-file digests. The instructions can be inspected without executing anything in the downloaded bundle. Five methods have outcome-oriented descriptions that retain their existing native IDs. A publisher bundle can require an application, service or library for an actual operation. Check that operation against the project’s data in its consuming interface.

The catalog records the selected source and intended activation. Earlier broader profiles retain their original compatibility paths. The 219-method catalog is an on-demand library. Only deliberately chosen project or recurring entries belong in a host’s native list.

The release check built the 122 base methods together in a clean temporary home, staged the 23 checked-in bundles, and compared every selected Git file for the 74 direct leaves against twelve publisher revisions. A representative assembly package also ran its shared command and produced a handoff whose placement CSV was reopened independently. The [late-method evaluation](../evals/01/late-method/README.md) exercises a separate question: what happens to the completed work when a skill becomes useful after the first turn?

The [acceptance handoff evaluation](../evals/01/acceptance-handoff/README.md) checks whether the desk can act on a calculated recommendation. Its controls cover signed, unsigned and subsequently altered evidence.
