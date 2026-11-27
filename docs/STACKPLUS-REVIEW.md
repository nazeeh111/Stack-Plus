# Review a consequential handoff

Use Elephant–Goldfish when an independent interpretation could change a design, proof, interface, or delivery decision. The Elephant carries project history and owns the decision. A Goldfish receives a neutral question and a pinned set of inputs. Routine edits can finish with their ordinary consumer check.

## Define the result

Identify the recipient, the action they need to take, the relevant constraints and the observation that would settle a disagreement. Distinguish requirements from proposed implementations. Record assumptions that could change the choice.

## Pin the inputs

From the project directory, name the files the reviewer needs. The command returns a content-based packet ID. Use a target-only packet for an independent reading of a proposal.

```sh
packet=$(stack+ review pack --requirements brief.md --artifact design.md --evidence sample.csv)
stack+ review show "$packet"
stack+ review show "$packet" --file sample.csv
stack+ review verify "$packet" --current
```

The packet contains copies of the named files in the project’s `.stackplus-review/` directory. Choose inputs the recipient may read. Preserve confidential inputs in their project. The reader opens project-relative regular files, and rejects symlinks and traversal. The host controls reviewer access to the rest of the workspace. A local packet can also be read by a human.

## Seek an independent reading

Give a fresh reader the packet ID, project path, scope, budget and the decision to assess. Keep the author’s favored conclusion out of the brief. Ask the reader to reconstruct the intended use, identify ambiguous directions or unsupported claims and cite the relevant file. The lead compares the interpretation to the artifact. A timeout, missing file or absent review leaves that part unverified.

## Resolve and verify

Record accepted findings, their evidence, the resulting decision and any unresolved trade-off in the project. Give changes to one owner. Verify through the interface the recipient uses. When the leading alternatives are close, check whether a credible change to an input reverses their ordering and communicate what should trigger a recheck.

```sh
revised=$(stack+ review pack --parent "$packet" --requirements brief.md \
  --artifact design.md --finding review.md --resolution decision.md)
stack+ review verify "$revised" --current
```

`verify ID` checks stored contents and ancestry. `verify ID --current` also checks current named project files and exits nonzero on drift. `show` reads the pinned bytes regardless of subsequent edits. Compare the revised result in the consuming interface and retain the decision with its evidence. Keep earlier reviews separately when commissioning a genuinely fresh second opinion.

The optional design-specification skill includes the full upstream brainstorm, draft, review, review-loop, resolve, bootstrap and drift-report methods with their original source and license. [Included source and notices](../addons/design-specification-workflow/NOTICE.md) · [Google’s Elephant–Goldfish model](https://github.com/google/elephant-goldfish-model)
