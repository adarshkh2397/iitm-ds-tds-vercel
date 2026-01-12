import json
import math
from http.server import BaseHTTPRequestHandler
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "telemetry.json"

with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)


class handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body)

            regions = payload.get("regions")
            threshold = payload.get("threshold_ms")

            if not isinstance(regions, list) or not isinstance(threshold, (int, float)):
                raise ValueError("Invalid input")

            response = {}

            for region in regions:
                records = [r for r in TELEMETRY if r["region"] == region]
                if not records:
                    continue

                latencies = sorted(r["latency_ms"] for r in records)
                uptimes = [r["uptime_pct"] for r in records]

                avg_latency = sum(latencies) / len(latencies)
                avg_uptime = sum(uptimes) / len(uptimes)

                p95_index = math.ceil(0.95 * len(latencies)) - 1
                p95_latency = latencies[p95_index]

                breaches = sum(
                    1 for r in records if r["latency_ms"] > threshold
                )

                response[region] = {
                    "avg_latency": round(avg_latency, 2),
                    "p95_latency": round(p95_latency, 2),
                    "avg_uptime": round(avg_uptime, 3),
                    "breaches": breaches,
                }

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(400)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())