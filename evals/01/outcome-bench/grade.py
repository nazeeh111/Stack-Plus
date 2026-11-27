"""Grade one frozen response and, independently, its optional on-disk artifact."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations
import json
from pathlib import Path


CASES_FILE = Path(__file__).with_name("cases.json")
CASES_SHA256 = "ae40b5887c5582b8f18f521233a48b2c0e80e0c5d5db8a41569dd9650b469624"
assert hashlib.sha256(CASES_FILE.read_bytes()).hexdigest() == CASES_SHA256
CASES = {case["id"]: case for case in json.loads(CASES_FILE.read_text())["cases"]}


def object_without_duplicates(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate JSON key")
    return obj


def read_object(raw):
    """Allow one code fence for content inspection. Score the fence separately."""
    text = raw.strip()
    fenced = text.startswith(("```json\n", "```\n")) and text.endswith("\n```")
    if fenced:
        text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
    item = json.loads(text, object_pairs_hook=object_without_duplicates)
    if not isinstance(item, dict):
        raise ValueError("expected a JSON object")
    return item, not fenced


def equal_values(actual, expected, *, allow_additions=False):
    # JSON booleans and floats must not satisfy an integer field via Python equality.
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        keys_ok = expected.keys() <= actual.keys() if allow_additions else expected.keys() == actual.keys()
        return keys_ok and all(equal_values(actual[k], v, allow_additions=allow_additions) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(equal_values(a, b, allow_additions=allow_additions) for a, b in zip(actual, expected))
    return actual == expected


def fits_shape(actual, example):
    if type(actual) is not type(example):
        return False
    if isinstance(example, dict):
        return actual.keys() == example.keys() and all(fits_shape(actual[k], v) for k, v in example.items())
    if isinstance(example, list):
        return all(fits_shape(item, example[0]) for item in actual)
    return True


def schedule(case, revised):
    sheet = case["fixture"]["jobs.txt"].split("id,minutes,participants\n", 1)[1]
    jobs = {}
    for row in sheet.splitlines():
        name, duration, seats = row.split(",")
        jobs[name] = (int(duration), int(seats))
    options = []
    for count in range(1, len(jobs) + 1):
        for order in permutations(jobs, count):
            if revised and order[0] != "A":
                continue
            timeline = []
            end = participants = 0
            for name in order:
                duration, seats = jobs[name]
                start = end
                if revised and start < 50 and start + duration > 44:
                    start = 50
                end = start + duration
                if end > 90:
                    break
                timeline.append({"id": name, "start": start, "end": end})
                participants += seats
            else:
                options.append(((-count, -participants, end, order), timeline, participants))
    _, timeline, participants = min(options)
    return {"jobs": timeline, "participants": participants}


def courier(case):
    packet = case["fixture"]["transfer.txt"]
    table = packet.split("path,content ID,size in GiB\n", 1)[1].split("Available drives", 1)[0]
    paths = [line.split(",") for line in table.strip().splitlines()]
    sizes = {identity: Fraction(gib) * 2**30 for _, identity, gib in paths}
    drives = [(0, "Pocket", 3_000_000_000), (12, "Field", 3_500_000_000), (26, "Studio", 6_000_000_000)]

    def plan(verified):
        missing = sorted(sizes.keys() - verified)
        required = sum((sizes[i] for i in missing), Fraction(50_000_000))
        assert required.denominator == 1
        price, name, _ = min(d for d in drives if d[2] >= required)
        return {"drive": name, "cost_usd": price, "bytes": int(required),
                "transmit_ids": missing, "path_count": len(paths)}

    guaranteed = plan({"C"})
    alternate = plan({"B", "C"})
    opportunity = {"verify_id": "B", "if_verified_drive": alternate["drive"],
                   "if_verified_bytes": alternate["bytes"], "saving_usd": guaranteed["cost_usd"] - alternate["cost_usd"]}
    return guaranteed, opportunity


def grade(case_id, turn, raw, *, text_artifact=False):
    case = CASES[case_id]
    if turn < 1 or turn > len(case["turns"]):
        raise ValueError(f"no turn {turn} for {case_id}")
    opportunity = None
    if case_id == "export-help":
        original = case["fixture"]["help.txt"]
        expected = {"text": original.replace("Export table: rows.tvs", "Export table: rows.tsv", 1)}
    elif case_id == "archive-courier":
        expected, opportunity = courier(case)
    else:
        expected = schedule(case, turn == 2)

    try:
        response, plain = ({"text": raw}, True) if text_artifact else read_object(raw)
    except (ValueError, TypeError) as error:
        return {"content_pass": False, "format_pass": False, "error": str(error)}

    schema = dict(expected)
    if opportunity is not None and "opportunity" in response:
        schema["opportunity"] = opportunity
    format_pass = plain and fits_shape(response, schema)
    checks = {}
    for key, value in expected.items():
        actual = response.get(key)
        if key == "transmit_ids" and isinstance(actual, list) and all(isinstance(i, str) for i in actual):
            actual = sorted(actual)
        checks[key] = equal_values(actual, value, allow_additions=True)
    result = {"content_pass": all(checks.values()), "format_pass": format_pass, "checks": checks}
    if opportunity is not None:
        if "opportunity" not in response:
            result["opportunity"] = "omitted"
        else:
            result["opportunity"] = "correct" if equal_values(response["opportunity"], opportunity, allow_additions=True) else "incorrect"
    return result


def delivery_matches(case_id, reply, artifact):
    try:
        submitted, _ = read_object(reply)
        if case_id == "export-help":
            return submitted.get("text") == artifact
        saved, _ = read_object(artifact)
        return equal_values(saved, submitted)
    except (ValueError, TypeError):
        return False


def selftest():
    help_expected = "Export table: rows.tsv\nImport legacy capture: rows.tvs\n"
    assert grade("export-help", 1, help_expected, text_artifact=True)["content_pass"]
    assert not grade("export-help", 1, help_expected.rstrip(), text_artifact=True)["content_pass"]
    assert not grade("export-help", 1, help_expected.replace(".tvs", ".tsv"), text_artifact=True)["content_pass"]
    guaranteed, opportunity = courier(CASES["archive-courier"])
    assert guaranteed == {"drive": "Field", "cost_usd": 12, "bytes": 3_002_790_016,
                          "transmit_ids": ["A", "B"], "path_count": 4}
    assert opportunity["if_verified_bytes"] == 1_660_612_736
    check = lambda obj: grade("archive-courier", 1, json.dumps(obj))
    assert check(guaranteed)["opportunity"] == "omitted"
    assert check({**guaranteed, "opportunity": opportunity})["opportunity"] == "correct"
    assert check({**guaranteed, "opportunity": {**opportunity, "saving_usd": 26}})["opportunity"] == "incorrect"
    assert not check({**guaranteed, "drive": "Pocket", "cost_usd": 0})["content_pass"]
    assert not check({**guaranteed, "cost_usd": True})["content_pass"]
    assert not check({**guaranteed, "transmit_ids": ["B", "B"]})["content_pass"]
    old, new = [schedule(CASES["cutter-handoff"], revised) for revised in (False, True)]
    assert [j["id"] for j in old["jobs"]] == ["A", "B", "D"] and old["participants"] == 16
    assert [j["start"] for j in new["jobs"]] == [0, 50, 71] and new["participants"] == 11
    assert grade("cutter-handoff", 2, json.dumps(new))["content_pass"]
    assert not grade("cutter-handoff", 2, json.dumps(old))["content_pass"]
    assert not grade("cutter-handoff", 2, json.dumps({**new, "jobs": new["jobs"][1:]}))["content_pass"]
    annotated = {**new, "jobs": [{**new["jobs"][0], "note": "already filed"}, *new["jobs"][1:]]}
    annotated_grade = grade("cutter-handoff", 2, json.dumps(annotated))
    assert annotated_grade["content_pass"] and not annotated_grade["format_pass"]
    missing = {**new, "jobs": [{"id": "A", "start": 0}, *new["jobs"][1:]]}
    missing_grade = grade("cutter-handoff", 2, json.dumps(missing))
    assert not missing_grade["content_pass"] and not missing_grade["format_pass"]
    fenced = grade("cutter-handoff", 2, "```json\n" + json.dumps(new) + "\n```")
    assert fenced["content_pass"] and not fenced["format_pass"]
    assert not grade("export-help", 1, '{"text":"first","text":"second"}')["format_pass"]
    assert delivery_matches("export-help", json.dumps({"text": help_expected}), help_expected)
    assert not delivery_matches("archive-courier", json.dumps(guaranteed), json.dumps({**guaranteed, "opportunity": opportunity}))
    print("Frozen cases and positive and negative controls passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES, nargs="?")
    parser.add_argument("turn", type=int, nargs="?")
    parser.add_argument("--reply", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if not args.case or not args.turn or args.reply is None:
        parser.error("supply CASE TURN --reply FILE, or --selftest")
    reply = args.reply.read_bytes().decode()
    response = grade(args.case, args.turn, reply)
    artifact = {"status": "unassessed"}
    if args.artifact is not None:
        if args.artifact.is_file():
            saved = args.artifact.read_bytes().decode()
            artifact = grade(args.case, args.turn, saved, text_artifact=args.case == "export-help")
            artifact["status"] = "observed"
            artifact["matches_reply"] = delivery_matches(args.case, reply, saved)
        else:
            artifact = {"status": "missing", "content_pass": False, "format_pass": False}
    print(json.dumps({"case": args.case, "turn": args.turn, "answer": response, "artifact": artifact}, indent=2))


if __name__ == "__main__":
    main()
