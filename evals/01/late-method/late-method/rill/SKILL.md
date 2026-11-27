---
name: rill
description: Local registrar procedures for transport offers, incoming loan crates, and wall-ready times under this lender's T14 sleeve.
---

For a crate marked T14, read `references/terms.md` to interpret the lender's release procedure. The price decision uses the completed release ledger and the registrar's wall-ready deadline.

From the project directory run `python3 .agents/skills/rill/scripts/release.py offers.csv`. It leaves the registrar an auditable `release-ledger.json` with the source-file digest and route estimates. Use the actual source data and preserve the ledger alongside the booking decision.
