# A skill introduced after the first turn

This synthetic museum case tests whether a newly relevant method changes a real decision. Use a fresh project per arm. Keep the lender terms and verification script outside the tested project until indicated.

1. Copy the contents of `fixture/` into a fresh project. Select 01 once in the host. Ask “Fix the spelling on label.txt so the room name reads North Gallery. Leave the other files alone.” Time the edit and inspect the saved sign.
2. Add the complete `late-method/rill` directory as `.agents/skills/rill` in that project. The lending rule is in its supporting file. The initial prompt and project inventory did not include it.
3. In the same conversation ask “Change of plan. The registrar needs a transport decision for the loaned print. Which is the least expensive offer that will get it on the gallery wall by 11:00? Use the local project material. Leave a concise booking.md with the chosen route, price, wall-ready time, a backup and any reason a cheaper offer misses. Keep this to a recommendation.”
4. Inspect the native transcript for the actual calculator call. Run `python3 verify.py /path/to/test-project` from this directory and compare its independently reconstructed result with the registrar’s handoff. The preferred carrier is Cedar at $265, ready at 10:40. Flint is the backup. Sable costs less and reaches the wall at 11:45.
5. Repeat on the same inputs with 01 unselected and the method present. In a third fresh project, select 01 but withhold the method. Inspect whether the answer signals that a definitive release time cannot be established. Compare actual artifacts, discovery and steering effort, and elapsed time.

In one matched native evaluation, both method-present chats ran the calculator and made the verified booking recommendation. The method-absent chat provisionally favored Cedar and could not rule out Sable. The contribution was enough evidence to act; the winning carrier’s name alone did not distinguish the outcomes. All three initial edits were direct. These observations concern one task.
