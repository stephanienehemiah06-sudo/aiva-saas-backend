from typing import Optional
from pydantic import BaseModel


# ==========================
# 🔑 AUTH SCHEMAS
# ==========================
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    technician: dict


class TechnicianResponse(BaseModel):
    id: int
    email: str
    full_name: str
    business_name: str


# ==========================
# 💅 SERVICES
# ==========================
class ServiceCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: float
    currency: Optional[str] = "NGN"
    duration_minutes: Optional[int] = 60
    deposit_required: Optional[bool] = False
    deposit_amount: Optional[float] = None


class ServiceResponse(ServiceCreate):
    id: int
    technician_id: int
    active: bool


# ==========================
# 📅 BOOKINGS
# ==========================
class BookingRequest(BaseModel):
    service_id: int
    client_name: str
    client_email: str
    appointment_date: str
    appointment_time: str


class BookingResponse(BookingRequest):
    id: int
    technician_id: int
    status: str
    payment_link: Optional[str] = None


# ==========================
# 🤖 CHAT AI SCHEMAS
# ==========================
class ChatRequest(BaseModel):
    chat_id: str
    text: str


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = "NONE"