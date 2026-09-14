"""Read competition records and serialize predictions safely."""
from dataclasses import asdict
import csv
import gzip
import json
from pathlib import Path


def read_records(path, limit=None):
    opener = gzip.open if str(path).endswith(".gz") else open
    records, seen = [], set()
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if (not isinstance(record.get("id"), str) or not record["id"]
                    or record["id"] in seen or not isinstance(record.get("meta"), dict)
                    or not isinstance(record.get("docs"), list) or not record["docs"]
                    or any(not isinstance(d.get("text"), str)
                           or "type" not in d or "doc_id" not in d for d in record["docs"])
                    or not any(d["type"] == "공고문" for d in record["docs"])):
                raise ValueError("Invalid or duplicate input record")
            seen.add(record["id"])
            records.append(record)
            if limit is not None and len(records) >= limit:
                break
    return records


def write_submission(results, path):
    if any(result.error or result.judgments is None for result in results):
        raise ValueError("Prediction failures: see trace.jsonl; submission was not written")
    items = [f"v{i}" for i in range(1, 25)]
    for result in results:
        if set(result.judgments) != set(items):
            raise ValueError(f"Incomplete judgment: {result.record_id}")
    path = Path(path)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id"] + items + [f"e{i}" for i in range(1, 25)])
        writer.writeheader()
        for result in results:
            row = {"id": result.record_id}
            for key, value in result.judgments.items():
                row[key] = value["위반여부"]
                row["e" + key[1:]] = value["근거문구"] or ""
            writer.writerow(row)
    temporary.replace(path)


def prediction_payload(prediction):
    """Return a serializable prediction with invalid raw model output omitted."""
    payload = asdict(prediction)
    for task in payload["trace"]:
        for event in task["events"]:
            if event["event"] == "model":
                try:
                    json.loads(event["response"])
                except (ValueError, TypeError):
                    event["response"] = "[invalid non-JSON response omitted]"
    return payload
