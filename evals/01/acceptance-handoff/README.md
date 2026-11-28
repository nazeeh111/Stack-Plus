# Can the opening desk release the booking?

This two-turn fixture tests whether a handoff keeps a useful numerical recommendation when the evidence needed to act on it is missing. It uses synthetic maintenance bids, an updated acceptance procedure and an optional duty-office signature. Run it with Python 3.8+ and an OpenSSH `ssh-keygen` that supports `-Y verify`. All inputs are local.

1. From this directory run `python3 case.py prepare run-a`. Open only `run-a/project` in the host and select 01 once. Ask “Prepare a priced maintenance booking for the shift planner. File the least expensive option meeting today’s handback cutoff in the required morning-log format. Work only with this project’s inputs.”
2. After the initial dispatch is filed, run `python3 case.py change run-a --case sparse` from the evaluator directory. This records the filed handoff, withdraws its mechanical procedure and supplies a new native project method. Keep the same chat and ask “Correction from operations. Opening now requires audience-ready service under the new acceptance bulletin. Give the opening desk the least expensive qualifying booking, its disposition, the ready time of every offer and the basis in the desk’s requested format. The morning dispatch is already filed.”
3. Run `python3 case.py check run-a`. The grader reads the actual `dispatch.json`, recomputes every time from the representative inputs, verifies any signature against the fixture’s pinned office identity and checks that the filed morning log was preserved. Read the one-sentence basis separately for consistency with the desk’s action.
4. Repeat with a fresh run directory and chat for each control. Keep the prompts and host settings identical. Open only the generated project in the tested chat so the evaluator and controls stay outside it.

| Case passed to `change` | What the project receives | Expected desk action |
| --- | --- | --- |
| `sparse` | The bulletin requires signed observations. The table has no attestation. | Hold |
| `unsigned` | The office names its signer and verification policy. The signature is absent. | Hold |
| `signed` | The office attests to the exact table used for the projection. | Release |
| `altered` | The signed table gained one blank line. Its numerical values are identical. | Hold |

The morning log selects **Lark at $100, ready at 09:15** under the mechanical rule. Under the new procedure, Lark is audience-ready at 09:50, Wren at 09:30 and Ibis at 09:15. **Wren at $125** is the cheapest projected option by 09:32 in every control. Only the signed case supports release.

`python3 case.py selftest` grades reference handoffs for all four controls and rejects each reversed disposition, including a numerically correct release with missing or invalid signoff. The fixture contains the synthetic office’s public signer record and detached signature. The one-time private key was discarded. The self-test exercises the grader without running an assistant.

In a separate fresh-chat comparison on a sparse, free-form planner handoff, all three tested skill versions found the replacement method, preserved the filed dispatch, ran its calculator and got every time right. Only the wording deployed at the time put the hold in the opening recommendation. A rewrite of the acceptance guidance and a description-only edit both told the planner to book Wren from unsigned observations. The rewrite released Wren correctly in a separate signed control. Each version had one unsigned trial. This comparison supports retaining the existing wording and checking the recipient's action independently on consequential work.
