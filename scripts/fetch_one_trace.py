"""Fetch one trace's full observation tree from Langfuse for waterfall rendering."""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
EVIDENCE = ROOT / "evidence"


def main() -> int:
    traces = json.loads((EVIDENCE / "langfuse_traces.json").read_text(encoding="utf-8"))
    matched = [t for t in traces["all_traces"] if t.get("sessionId") == traces["session_id"]]
    if not matched:
        print("no matched trace")
        return 1
    sample = matched[0]
    trace_id = sample["id"]

    host = os.environ["LANGFUSE_HOST"].rstrip("/")
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    auth = "Basic " + base64.b64encode(f"{pk}:{sk}".encode()).decode()

    r = httpx.get(
        f"{host}/api/public/observations",
        params={"traceId": trace_id, "limit": 50},
        headers={"Authorization": auth},
        timeout=15.0,
    )
    if r.status_code != 200:
        print("observations fetch failed:", r.status_code, r.text[:200])
        return 1

    obs = r.json().get("data", [])
    out = {"trace": sample, "observations": obs, "fetched_at": r.headers.get("date")}
    out_path = EVIDENCE / "langfuse_one_trace.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"trace_id={trace_id}")
    print(f"observations={len(obs)}")
    for o in obs:
        print(f"  - {o.get('type'):8s} {o.get('name'):24s} start={o.get('startTime')} duration={o.get('duration')} ms")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
