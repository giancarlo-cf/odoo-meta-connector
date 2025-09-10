from fastapi import FastAPI, Query, Request, Response, HTTPException, Depends
from fastapi.security import APIKeyHeader
import os
import parser
import odoo_api
import json

app = FastAPI()
header_scheme = APIKeyHeader(name="X-Api-Key")
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "invalid_token")
API_KEY = os.getenv("API_KEY")


@app.get("/webhooks/", status_code=200)
async def subscribe(
        hub_mode: str = Query(..., alias="hub.mode"),
        hub_challenge: str = Query(..., alias="hub.challenge"),
        hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhooks/", status_code=200)
async def create_lead(body: dict):
    parsed_body = await parser.parse_leadgen(body)
    lead_id = await odoo_api.create_lead(parsed_body)
    return {"Created lead id": lead_id}


@app.get("/webhooks/cec/", status_code=200)
async def subscribe(
        hub_mode: str = Query(..., alias="hub.mode"),
        hub_challenge: str = Query(..., alias="hub.challenge"),
        hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=hub_challenge, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhooks/cec/", status_code=200)
async def create_lead(body: dict):
    parsed_body = await parser.parse_leadgen(body)
    lead_id = await odoo_api.create_lead(parsed_body)
    return {"Created lead id": lead_id}


@app.post("/cec/", status_code=200)
async def create_lead(request: Request, key: str = Depends(header_scheme)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

    form_data = await request.form()
    print(form_data)
    print(json.dumps(dict(form_data), indent=4))
    return {"status": "ok", "message": "Form data received and printed"}


@app.get("/health/")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Service is running"}
