# Stack+ and plain-chat comparison

Three original synthetic cases test different kinds of work. Both arms receive the exact same messages, including every fact needed to answer. The cutter case has a second turn in the same chat. The checked-in project files repeat the inline inputs. Work in fresh directories outside this checkout so the tested lead cannot read the grader or another arm’s outputs. [Measured results](RESULTS.md)

| Case | Required answer | Additional observation |
|---|---|---|
| Export help | Return both lines byte-for-byte, with only the requested extension corrected. | A tool-enabled lead can save the edit directly. Record any delegation on this routine task. |
| Archive courier | Choose the lowest-cost drive guaranteed by the confirmed contents, including full path reconstruction, exact byte count and manifest overhead. | Score a concrete, conditional cost-saving check separately. Omitting this optional contribution leaves a correct guaranteed answer intact. |
| Cutter handoff | Produce the optimum executable schedule at each turn under the published priority order. | The revised plan must preserve the completed job exactly once and respect the new inspection window. |

## Run both arms

1. Freeze the revision and the SHA-256 of `cases.json` before either arm starts. Give each arm the same lead, effort and identity-independent task instructions where the host permits it. Record actual settings and any differences. Establish separate, fresh sessions and projects for each case and arm.
2. Give the Stack+ arm its normal authorized toolkit. Select 01 once before the first message. For the native text-only control, exclude Stack+ and its instructions, direct the lead to use only the supplied text, and audit both advertised namespaces and executed tools. A strict zero-declaration comparison requires evidence that the provider received an empty tool list. Use the exact `prompt` values, with no coaching, search suggestions or corrections beyond the scripted second turn.
3. Save each original reply. In the Stack+ arm independently snapshot the named artifact after each turn, before sending the next prompt. The plain-chat arm is graded on the same answer, with file delivery inapplicable. Record elapsed time, tool or specialist activity, and additional user interventions. Alternate which arm goes first across cases. Record repeats and failures.
4. Grade each turn in a separate process. Turn numbers start at one. Use `--artifact` only when checking file delivery. A missing file passed to that option is a failed delivery. Control file delivery is reported as unassessed. For the help case the artifact is plain text. The other artifacts contain the requested JSON.

```sh
python3 grade.py export-help 1 --reply /path/to/answer.txt --artifact /path/to/help.txt
python3 grade.py archive-courier 1 --reply /path/to/answer.txt
python3 grade.py cutter-handoff 2 --reply /path/to/answer.txt --artifact /path/to/plan.json
python3 grade.py --selftest
```

**Scoring.** Report the four turns individually. Required content, reply format, the optional contribution and on-disk delivery have separate results. Report extra user turns, specialist activity and elapsed times alongside correctness. The text-only control is scored on its reply. Its file-delivery column is inapplicable. Tool count by itself says little about efficiency. This small sample can establish a measured difference on these cases. It cannot estimate overall success rates. The grader computes byte totals using exact fractions and enumerates feasible schedules and tie-breaks independently. Its self-test includes incorrect submissions which must fail.
