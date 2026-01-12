import json
import math
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent.parent / "data" / "telemetry.json"

with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)


@app.post("/")
async def compute_metrics(payload: dict):
    regions = payload.get("regions")
    threshold = payload.get("threshold_ms")

    if not isinstance(regions, list) or not isinstance(threshold, (int, float)):
        return {"error": "Invalid input"}

    response = {}

    for region in regions:
        records = [r for r in TELEMETRY if r["region"] == region]
        if not records:
            continue

        latencies = sorted(r["latency_ms"] for r in records)
        uptimes = [r["uptime_pct"] for r in records]

        p95_index = math.ceil(0.95 * len(latencies)) - 1

        response[region] = {
            "avg_latency": round(sum(latencies) / len(latencies), 2),
            "p95_latency": round(latencies[p95_index], 2),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
            "breaches": sum(1 for r in records if r["latency_ms"] > threshold),
        }

    return response

handler = Mangum(app)