"""End-to-end Langfuse verification: send N requests, wait for flush, query API, write evidence."""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_BASE = os.environ.get("VERIFY_API_BASE", "http://127.0.0.1:8000")
N_REQUESTS = int(os.environ.get("VERIFY_N", "10"))
TAG_PREFIX = os.environ.get("VERIFY_TAG_PREFIX", "req-verify-v3")
USER_ID = os.environ.get("VERIFY_USER_ID", "u_team_01")
SESSION_ID = os.environ.get("VERIFY_SESSION_ID", "s_verify_01")
FEATURE = os.environ.get("VERIFY_FEATURE", "qa")
FLUSH_WAIT_S = int(os.environ.get("VERIFY_FLUSH_WAIT", "12"))
EVIDENCE_PATH = ROOT / "evidence" / "langfuse_traces.json"


def _post_chat(client: httpx.Client, idx: int) -> tuple[int, str]:
    request_id = f"{TAG_PREFIX}-{idx:02d}"
    body = {
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "feature": FEATURE,
        "message": f"verify message {idx} - tell me about PII handling",
    }
    r = client.post(
        f"{API_BASE}/chat",
        json=body,
        headers={"x-request-id": request_id},
        timeout=30.0,
    )
    return r.status_code, request_id


def _query_traces() -> tuple[int, dict]:
    host = os.environ["LANGFUSE_HOST"].rstrip("/")
    pk = os.environ["LANGFUSE_PUBLIC_KEY"]
    sk = os.environ["LANGFUSE_SECRET_KEY"]
    auth = "Basic " + base64.b64encode(f"{pk}:{sk}".encode()).decode()
    url = host + f"/api/public/traces?limit={N_REQUESTS + 5}"
    r = httpx.get(url, headers={"Authorization": auth}, timeout=15.0)
    return r.status_code, r.json() if r.status_code == 200 else {"raw": r.text[:500]}


def main() -> int:
    print(f"[verify] POST {N_REQUESTS} requests to {API_BASE}/chat (tag={TAG_PREFIX}-XX)")
    with httpx.Client() as client:
        sent = 0
        for i in range(N_REQUESTS):
            try:
                code, rid = _post_chat(client, i)
                print(f"  [{i:02d}] {code} {rid}")
                if code == 200:
                    sent += 1
            except Exception as exc:
                print(f"  [{i:02d}] ERROR {type(exc).__name__}: {exc}")
        print(f"[verify] {sent}/{N_REQUESTS} sent OK")

    print(f"[verify] sleeping {FLUSH_WAIT_S}s for Langfuse SDK flush...")
    time.sleep(FLUSH_WAIT_S)

    print("[verify] querying Langfuse public API...")
    code, payload = _query_traces()
    print(f"  status: {code}")
    if code != 200:
        print(json.dumps(payload, indent=2)[:500])
        return 1

    traces = payload.get("data", [])
    print(f"  total traces returned: {len(traces)}")

    matched = [t for t in traces if t.get("sessionId") == SESSION_ID or SESSION_ID in (t.get("sessionId") or "")]
    print(f"  matching sessionId={SESSION_ID}: {len(matched)}")
    print()
    print("  id (truncated) | userId | sessionId | tags | createdAt")
    print("  " + "-" * 100)
    for t in traces[: min(N_REQUESTS + 2, len(traces))]:
        tid = (t.get("id") or "")[:24]
        uid = t.get("userId")
        sid = t.get("sessionId")
        tags = t.get("tags") or []
        ts = t.get("createdAt")
        print(f"  {tid:24s} | {uid} | {sid} | {tags} | {ts}")

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": code,
                "count": len(traces),
                "session_id": SESSION_ID,
                "matched": len(matched),
                "all_traces": traces,
                "first_n": traces[: N_REQUESTS + 2],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\n[verify] wrote {EVIDENCE_PATH}")
    return 0 if matched else 2


if __name__ == "__main__":
    sys.exit(main())
