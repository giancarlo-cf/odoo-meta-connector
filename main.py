from fastapi import FastAPI, Query, Response, HTTPException
import os

app = FastAPI()
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "invalid_token")


@app.get("/webhooks/", status_code=200)
async def subscribe(
        hub_mode: str = Query(..., alias="hub.mode"),
        hub_challenge: int = Query(..., alias="hub.challenge"),
        hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhooks/", status_code=200)
async def create_lead(body: dict):
    print(f"Received Meta Lead body")
    print(body)
