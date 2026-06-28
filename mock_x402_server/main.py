"""Mock x402 data source for Buildathon demo.

Simulates a paid API that returns RWA yield data.
Requires x402 payment proof in X-Payment header.
"""

import json
import random
import time

from fastapi import FastAPI, Request, Response

app = FastAPI(title="Mock x402 RWA Data Source")

# Simulated data with base values and volatility
MOCK_DATA = {
    "us_treasury_10y": {"base": 425, "volatility": 10, "cost": 500},
    "t_bill_3m": {"base": 520, "volatility": 15, "cost": 300},
    "t_bill_6m": {"base": 505, "volatility": 12, "cost": 300},
}


@app.get("/api/{data_type}")
async def get_data(data_type: str, request: Request):
    """Return RWA data. Requires x402 payment proof."""

    if data_type not in MOCK_DATA:
        return Response(status_code=404, content="Unknown data type")

    config = MOCK_DATA[data_type]

    # Check for payment proof
    x_payment = request.headers.get("X-Payment")
    if not x_payment:
        # Return 402 Payment Required
        payment_response = {
            "x402Version": 1,
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "casper-testnet",
                    "maxAmountRequired": str(config["cost"]),
                    "resource": f"/api/{data_type}",
                    "description": f"RWA data: {data_type}",
                    "payTo": "01a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef12345678",
                    "asset": "CSPR",
                }
            ],
        }
        return Response(
            status_code=402,
            content=json.dumps(payment_response),
            media_type="application/json",
        )

    # Payment present — return data
    value = config["base"] + random.randint(-config["volatility"], config["volatility"])
    confidence = random.randint(80, 99)

    data = {
        "data_type": data_type,
        "value": value,
        "unit": "basis_points",
        "source": "mock_source",
        "confidence": confidence,
        "timestamp": int(time.time()),
    }

    return data


@app.get("/health")
async def health():
    return {"status": "ok", "data_sources": list(MOCK_DATA.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
