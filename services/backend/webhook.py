from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import Response

router = APIRouter()

# ==================================================
# META / INSTAGRAM WEBHOOK CONFIG
# ==================================================

VERIFY_TOKEN = "aiva_saas_verify_token_2025"


# ==================================================
# WEBHOOK VERIFICATION (META calls this first)
# ==================================================

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    This endpoint is used by Meta to verify webhook ownership.
    MUST return hub.challenge as plain text.
    """

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ==================================================
# WEBHOOK RECEIVER (Instagram events will come here)
# ==================================================

@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receives Instagram / Meta webhook events.
    Always respond 200 OK so Meta doesn't retry.
    """

    payload = await request.json()
    print("📥 Instagram Webhook Event:", payload)

    return {"status": "received"}