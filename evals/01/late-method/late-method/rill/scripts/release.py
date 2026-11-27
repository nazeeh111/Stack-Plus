"""Issue the registrar's T14 route release ledger in the current project."""

import csv
import hashlib
import json
from pathlib import Path
import sys


def release(row):
    hour, minute = map(int, row["arrival"].split(":"))
    raw = 20 + 3 * int(row["amber_minutes"]) + 8 * int(row["seal_events"])
    slot = ((raw + 14) // 15) * 15
    hour, minute = divmod(hour * 60 + minute + slot + 10, 60)
    return {"route": row["route"], "price_usd": int(row["price_usd"]),
            "holding_minutes": slot, "wall_ready": f"{hour:02d}:{minute:02d}"}


if __name__ == "__main__":
    source = Path(sys.argv[1])
    with source.open() as stream:
        routes = [release(row) for row in csv.DictReader(stream)]
    ledger = {"terms": "T14", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "routes": routes}
    Path("release-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(routes))
