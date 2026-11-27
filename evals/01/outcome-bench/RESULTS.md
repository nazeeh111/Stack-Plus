# Results on the three frozen cases

Both arms returned all four required answers in the requested JSON format. Both identified the conditional $12 saving in the archive case. Stack+ also saved all four requested artifact snapshots, including the two successive cutter plans. Each matched its corresponding reply. The text-only control had no file-delivery assignment.

| Case and turn | Independently checked outcome | Native text-only | Stack+ | Stack+ tool calls |
|---|---|---:|---:|---:|
| Export help | Only the export extension changed. Both lines and the final newline were preserved. | 2.875 s | 12.988 s | 2 |
| Archive courier | Field, $12, 3,002,790,016 bytes. Verifying blob B would make the free Pocket drive feasible at 1,660,612,736 bytes. | 24.794 s | 20.945 s | 2 |
| Cutter, initial | A, B, D served 16 participants and finished at minute 86. | 4.608 s | 17.434 s | 2 |
| Cutter, revised | A’s completed 0–34 minute run was preserved. D started at minute 50, E at 71. The new plan served 11 and ended at minute 89. | 3.915 s | 11.692 s | 1 |
| **Total** | **4/4 required answers in each arm** | **36.192 s** | **63.059 s** | **7** |

These are six native Codex sessions with matched caller inference settings, one session per arm per case. Each arm received identical decision inputs and the same one scripted correction. No extra user steering was needed. The table counts outer native tool calls; a call can contain multiple operations. Times run from native task start to completion and exclude client startup, grading and resume overhead. The first-running arm alternated by case.

The native control was instructed to answer from text and received no Stack+ guide, 01 or skill catalog. Its traces contained **zero executed tool calls**. The client still advertised three built-in namespaces (`functions`, `clock`, `collaboration`). An API run with zero tool definitions remains untested. The isolation check reproduced the client's expected diagnostic when access to the personal guide was denied. A settings bookkeeping event in the courier control required recovering the original turn from its native record. Its effective settings matched the caller’s settings.

The prompts and decision criteria were frozen before execution. An independent review corrected the grader's handling of extra nested schedule fields so answer content and JSON format are scored separately. The final grader was applied to the saved answers without rerunning the participants. One trial per arm per case establishes the observed answers, delivery and timing. There was no answer-quality advantage on this sample. The optional opportunity was invited by the prompt.

[Prompts and inputs](cases.json) · [Grader and negative controls](grade.py) · [Method](README.md)
