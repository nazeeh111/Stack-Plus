# Native FPGA operation

The complete MIT source leaf, references, templates, RTL, testbench and checker
are retained. `SOURCE.json` records exact originals and the only body addition,
a link to this binding. No controller or vendor-tool installation is implied.

Use current native source, shell and file tools. Discover the optional FPGA
runtime through the native runtime index and inspect its acceptance evidence.
The isolated Icarus/Yosys CPU fixture tests a one-entry synchronous ready/valid
buffer at widths 1 and 8, and a deliberate data-loss mutation. It is not a board
project, CDC proof, placement/routing result, static timing signoff or hardware
commissioning. Yosys generic synthesis is not a substitute for a target vendor's
primitive models, implementation flow or timing constraints.

Run the source checker in an owned new output directory with the named tools
actually available. Missing stages remain incomplete. Retain exact source,
constraint and tool versions with real checks. No global PATH modification,
daemon or connected hardware access is required by this local workflow.

The source's `esp32-development` and `electronics` collection siblings are not
bundled here. Use the installed embedded-systems skill for firmware, and the
KiCad, datasheet, SPICE and EMC skills where applicable. This routing does not
claim those methods replace every absent sibling capability.

Preserve current user authority, model and effort. Programming, resetting or
erasing hardware retains the original target/scope/rollback requirement. Source
commands do not authorize commits, publishing, spending or credential changes.
