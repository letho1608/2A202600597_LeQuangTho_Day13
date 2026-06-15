"""Verify traces are visible in Langfuse by calling the public API."""
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import httpx

host = os.environ["LANGFUSE_HOST"].rstrip("/")
pk = os.environ["LANGFUSE_PUBLIC_KEY"]
sk = os.environ["LANGFUSE_SECRET_KEY"]
auth = "Basic " + base64.b64encode(f"{pk}:{sk}".encode()).decode()

url = host + "/api/public/traces?limit=20"
r = httpx.get(url, headers={"Authorization": auth}, timeout=15.0)
print("status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    traces = data.get("data", [])
    print(f"total returned: {len(traces)}")
    for t in traces[:5]:
        print(
            f"  id={t.get('id')[:24]}... user={t.get('userId')} session={t.get('sessionId')} tags={t.get('tags')} createdAt={t.get('createdAt')}"
        )
    print(f"\nJSON_SAMPLE_PATH: {os.getcwd()}\\evidence\\langfuse_traces.json")
    with open("evidence/langfuse_traces.json", "w", encoding="utf-8") as f:
        json.dump({"status": r.status_code, "count": len(traces), "first_5": traces[:5]}, f, indent=2, ensure_ascii=False)
    print("Wrote evidence/langfuse_traces.json")
else:
    print(r.text[:500])
    sys.exit(1)
