from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook")
async def universal_webhook(request: Request):
    """
    Universal webhook for ANY social media platform.
    For now, we simply receive data and acknowledge it.
    Later, this will be used for AI DM booking integrations.
    """

    payload = await request.json()
    print("📥 Incoming webhook data:", payload)

    # 👇 Validation placeholder (we will map this to DB later)
    technician_email = payload.get("technician_email")
    client_name = payload.get("client_name") or payload.get("name")

    if not technician_email or not client_name:
        return {
            "status": "error",
            "message": "Missing required fields"
        }

    # Just acknowledge for now
    return {
        "status": "success",
        "message": "Webhook received successfully"
    }