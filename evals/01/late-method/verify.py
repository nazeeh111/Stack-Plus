"""Verify the calculator ledger and retained sign in a completed synthetic project."""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path


def verify(project):
    offers = project / "offers.csv"
    if (project / "label.txt").read_text().strip() != "North Gallery":
        raise ValueError("The initial edit was lost")
    if not (project / "booking.md").is_file():
        raise ValueError("Missing registrar handoff")
    ledger = json.loads((project / "release-ledger.json").read_text())
    if ledger["source_sha256"] != hashlib.sha256(offers.read_bytes()).hexdigest():
        raise ValueError("The ledger is for a different offer sheet")
    expected = []
    with offers.open(newline="") as stream:
        for offer in csv.DictReader(stream):
            hold = 20 + 3 * int(offer["amber_minutes"]) + 8 * int(offer["seal_events"])
            while hold % 15:
                hold += 1
            ready = datetime.strptime(offer["arrival"], "%H:%M") + timedelta(minutes=hold + 10)
            expected.append({"route":offer["route"], "price_usd":int(offer["price_usd"]),
                             "holding_minutes":hold, "wall_ready":ready.strftime("%H:%M")})
    if ledger["terms"] != "T14" or ledger["routes"] != expected:
        raise ValueError("The source sheet and lender terms do not reproduce the ledger")
    qualified = sorted((row for row in expected if row["wall_ready"] <= "11:00"), key=lambda row:row["price_usd"])
    return {"preferred":qualified[0], "backup":qualified[1], "late":[row for row in expected if row["wall_ready"]>"11:00"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    print(json.dumps(verify(parser.parse_args().project), indent=2))
