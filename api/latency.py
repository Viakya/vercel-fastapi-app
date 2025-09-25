import json
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pathlib import Path

app = FastAPI()

# ✅ Enable CORS globally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change "*" to your frontend domain if you want to restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH, "r") as f:
    telemetry = json.load(f)


@app.options("/api/latency")
async def options_latency():
    """Handle preflight OPTIONS request for browsers"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.post("/api/latency")
async def get_latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    response = {}

    for region in regions:
        region_data = [r for r in telemetry if r["region"] == region]

        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(sum(l > threshold_ms for l in latencies))

        response[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches,
        }

    # ✅ Explicitly include CORS header in response
    return JSONResponse(
        content=response,
        headers={"Access-Control-Allow-Origin": "*"}
    )
