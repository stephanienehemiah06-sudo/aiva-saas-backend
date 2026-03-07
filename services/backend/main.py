# =======================
# AIVA BEAUTY SAAS BACKEND
# =======================

from typing import List
import os
import pathlib
from fastapi import FastAPI, Depends, HTTPException, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from services.backend import models, schemas
from services.backend.database import engine, get_db
from services.password_service import hash_password, verify_password
from services.backend.auth import create_access_token, get_technician_from_token
from services.backend.webhook import router as webhook_router

# =======================
# CREATE DATABASE
# =======================

models.Base.metadata.create_all(bind=engine)

# =======================
# CREATE APP ✅ FIRST
# =======================

app = FastAPI(
    title="AIVA SaaS Agent Backend 🪄✨",
    version="1.1.0"
)

app.include_router(webhook_router)

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]

# Support both layouts:
# 1) services/frontend (current)
# 2) frontend (if moved out of services)
candidate_frontend_dirs = [
    ROOT_DIR / "services" / "frontend",
    ROOT_DIR / "frontend",
]
FRONTEND_DIR = next((p for p in candidate_frontend_dirs if p.exists()), candidate_frontend_dirs[0])

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/signup")
def signup_page():
    return FileResponse(str(FRONTEND_DIR / "signup.html"))


@app.get("/login")
def login_page():
    return FileResponse(str(FRONTEND_DIR / "login.html"))


@app.get("/dashboard")
def dashboard_page():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))

# =======================
# CORS
# =======================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =======================
# META WEBHOOK CONFIG ✅
# =======================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# =======================
# AUTH HELPER ✅
# =======================

def get_current_technician(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth header")

    token = authorization.replace("Bearer ", "").strip()
    tech = get_technician_from_token(token, db)

    if not tech:
        raise HTTPException(status_code=401, detail="Invalid token")

    return tech


# =======================
# SIGNUP
# =======================

@app.post("/signup-technician")
async def signup_technician(request: Request, db: Session = Depends(get_db)):

    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(400, "Email & password required")

    if db.query(models.Technician).filter(models.Technician.email == email).first():
        raise HTTPException(409, "Email already exists")

    new_tech = models.Technician(
        full_name=data.get("full_name") or data.get("business_name", ""),
        email=email,
        password_hash=hash_password(password),
        phone=data.get("phone", ""),
        business_name=data.get("business_name", ""),
        country=data.get("country"),
    )

    db.add(new_tech)
    db.commit()
    db.refresh(new_tech)

    return {
        "status": "success",
        "message": "Account created successfully",
        "technician_id": new_tech.id,
    }


# =======================
# LOGIN ✅
# =======================

@app.post("/login", response_model=schemas.TokenResponse)
async def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):

    tech = db.query(models.Technician).filter(
        models.Technician.email == data.email
    ).first()

    if not tech or not verify_password(data.password, tech.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token(subject=tech.email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "technician": {
            "id": tech.id,
            "full_name": tech.full_name,
            "email": tech.email,
            "phone": tech.phone,
            "business_name": tech.business_name,
            "country": tech.country,
            "payment_provider": tech.payment_provider,
            "deposit_required": bool(tech.deposit_required),
            "deposit_amount": float(tech.deposit_amount or 0.0),
        }
    }


# =======================
# CURRENT USER
# =======================

@app.get("/me", response_model=schemas.TechnicianResponse)
def get_me(current=Depends(get_current_technician)):
    return current


# =======================
# 💅 SERVICES
# =======================

@app.post("/services", response_model=schemas.ServiceResponse)
def create_service(
    service: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    s = models.Service(
        technician_id=technician.id,
        name=service.name,
        category=service.category,
        description=service.description,
        price=service.price,
        currency=service.currency,
        duration_minutes=service.duration_minutes,
        active=True,
    )

    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@app.get("/services/me", response_model=List[schemas.ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    return db.query(models.Service).filter(
        models.Service.technician_id == technician.id
    ).all()


# =======================
# 📅 BOOKINGS
# =======================

try:
    from services.backend.models import Booking
except ImportError:
    Booking = models.Appointment

@app.post("/check-availability")
def check_availability(
    appointment_date: str,
    appointment_time: str,
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    taken = db.query(Booking).filter(
        Booking.technician_id == technician.id,
        Booking.appointment_date == appointment_date,
        Booking.appointment_time == appointment_time,
        Booking.status == "CONFIRMED",
    ).first()

    return {"available": taken is None}


@app.post("/book", response_model=schemas.BookingResponse)
def create_booking(
    data: schemas.BookingRequest,
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    occupied = db.query(Booking).filter(
        Booking.technician_id == technician.id,
        Booking.appointment_date == data.appointment_date,
        Booking.appointment_time == data.appointment_time,
        Booking.status == "CONFIRMED",
    ).first()

    if occupied:
        raise HTTPException(409, "Time slot already booked")

    booking = Booking(
        technician_id=technician.id,
        service_id=data.service_id,
        client_name=data.client_name,
        client_email=data.client_email,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        status="PENDING_PAYMENT",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


# =======================
# 🤖 AI CHAT ENGINE
# =======================

try:
    from services.backend.models import ConversationState
except ImportError:
    ConversationState = models.ChatSession

@app.post("/chat", response_model=schemas.ChatResponse)
def chat_with_client(
    data: schemas.ChatRequest,
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    session = db.query(ConversationState).filter(
        ConversationState.chat_id == data.chat_id
    ).first()

    if not session:
        session = ConversationState(chat_id=data.chat_id, stage="GREETING")
        db.add(session)
        db.commit()
        db.refresh(session)

    if session.stage == "GREETING":
        session.stage = "SERVICE_SELECTION"
        db.commit()

        return {
            "reply": f"Hi 👋 I'm {technician.assistant_name or 'your booking assistant'} for {technician.business_name}. What service would you like to book?",
            "action": "ASK_SERVICE",
        }

    return {
        "reply": "Type BOOK to begin booking ❤️",
        "action": "UNKNOWN",
    }


# =======================
# 📡 META / INSTAGRAM WEBHOOK
# =======================

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("📥 Instagram Webhook Event:", payload)
    return {"status": "received"}


# =======================
# PRIVACY POLICY (META)
# =======================

@app.get("/privacy")
def privacy_policy():
    return {
        "privacy_policy": """
AIVA Beauty SaaS Privacy Policy

AIVA Beauty SaaS ("we", "our", "us") provides booking automation tools for beauty professionals.

Information We Collect:
- Business name
- Email address
- Phone number
- Services and booking details
- Messages sent through connected platforms (Instagram)

How We Use Data:
- To enable appointment booking
- To respond to customer messages
- To manage schedules and payments

Data Sharing:
- We do not sell or share personal data with third parties.
- Data is only used to provide our services.

Data Security:
- All data is stored securely.
- Access is restricted to authorized users only.

User Control:
- Users can request data deletion by contacting support.

Contact:
Email: support@aivabeauty.app
"""
    }

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>AIVA AI Agent</title>
        </head>
        <body style="font-family: Arial; text-align:center; margin-top:100px;">
            <h1>✨ AIVA AI Booking Assistant</h1>
            <p>Instagram AI Agent for Lash & Nail Technicians</p>

            <h3>Status</h3>
            <p>Backend Server Running ✅</p>

            <h3>Available Routes</h3>
            <p>/webhook</p>
            <p>/privacy</p>

            <p style="margin-top:40px;">Built by Stephanie</p>
        </body>
    </html>
    """


# =======================
# ROOT
# =======================

@app.get("/")
def root():
    return {"message": "AIVA backend running ✅"}
