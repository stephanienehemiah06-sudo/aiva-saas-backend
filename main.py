# =======================
# AIVA BEAUTY SAAS BACKEND
# =======================

from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas

from database import engine, get_db
from services.password_service import hash_password, verify_password
from auth import create_access_token, get_technician_from_token

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

VERIFY_TOKEN = "aiva_verify_token_2025"

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

from models import Booking

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

    return {
        "id": booking.id,
        "technician_id": technician.id,
        "service_id": data.service_id,
        "client_name": booking.client_name,
        "client_email": booking.client_email,
        "appointment_date": booking.appointment_date,
        "appointment_time": booking.appointment_time,
        "status": booking.status,
        "payment_link": technician.payment_provider or "",
    }


@app.post("/payment-webhook")
async def payment_webhook(payload: dict, db: Session = Depends(get_db)):

    ref = payload.get("reference")
    if not ref:
        return {"status": "ignored"}

    booking = db.query(Booking).filter(
        Booking.payment_reference == ref
    ).first()

    if not booking:
        return {"status": "booking_not_found"}

    booking.status = "CONFIRMED"
    db.commit()
    return {"status": "confirmed"}


@app.get("/bookings/me", response_model=list[schemas.BookingResponse])
def list_my_bookings(
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):
    return db.query(Booking).filter(
        Booking.technician_id == technician.id
    ).all()


# ==================================================
# 🤖 AI CHAT ENGINE ✅
# ==================================================

from models import ConversationState

@app.post("/chat", response_model=schemas.ChatResponse)
def chat_with_client(
    data: schemas.ChatRequest,
    db: Session = Depends(get_db),
    technician=Depends(get_current_technician),
):

    message = data.text.lower().strip()

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
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("📥 Instagram Webhook Event:", payload)
    return {"status": "received"}


# =======================
# ROOT
# =======================

@app.get("/")
def root():
    return {"message": "AIVA backend running ✅"}