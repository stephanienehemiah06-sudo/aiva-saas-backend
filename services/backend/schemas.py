from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from pydanti import BaseModel


class LoginSchema(BaseModel):
    email: str
    password: str


class ServiceSchema(BaseModel):
    technician_id: int
    name: str
    price: float
    duration: int


class AvailabilitySchema(BaseModel):
    technician_id: int
    day: str
    start_time: str
    end_time: str


class AppointmentSchema(BaseModel):
    technician_id: int
    service_id: int
    staff_id: Optional[int] = None
    date: str
    start_time: str
    end_time: str
    client_name: str
    client_phone: str


class StaffCreateSchema(BaseModel):
    technician_id: int
    full_name: str
    role: Optional[str] = None


class StaffUpdateSchema(BaseModel):
    technician_id: int
    full_name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class StaffResponseSchema(BaseModel):
    id: int
    technician_id: int
    full_name: str
    role: Optional[str] = None
    active: bool
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentSettingsCreate(BaseModel):
    technician_id: int
    provider: str

    public_key: Optional[str] = None
    secret_key: Optional[str] = None

    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    auto_confirm_proofs: Optional[bool] = False


    class TokenResponse(BaseModel):
        access_token: str
        token_type: str = "bearer"


# ==========================
# SUBSCRIPTION SCHEMA (NEW)
# ==========================

class SubscriptionCreate(BaseModel):
    technician_id: int
    plan: str
    start_date: str
    end_date: str


# ==========================
# SOCIAL MEDIA SCHEMAS
# ==========================

class SocialAccountBase(BaseModel):
    platform: str
    account_name: str


class SocialAccountCreate(SocialAccountBase):
    technician_id: int
    account_id: Optional[str] = None
    phone_number: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None


class SocialAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    is_active: Optional[bool] = None


class SocialAccountResponse(SocialAccountBase):
    id: int
    technician_id: int
    account_id: Optional[str] = None
    phone_number: Optional[str] = None
    connected_at: str
    is_active: bool
    webhook_verified: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


# ==========================
# OAUTH SCHEMAS
# ==========================

class OAuthInitiateRequest(BaseModel):
    technician_id: int
    redirect_uri: str


class OAuthInitiateResponse(BaseModel):
    auth_url: str
    platform: str
    state: str


class OAuthCallbackRequest(BaseModel):
    platform: str
    code: str
    technician_id: int
    redirect_uri: str
    state: str


class OAuthCallbackResponse(BaseModel):
    success: bool
    account_name: Optional[str] = None
    platform: str
    message: Optional[str] = None


# ==========================
# WHATSAPP SCHEMAS
# ==========================

class WhatsAppQRRequest(BaseModel):
    technician_id: int


class WhatsAppQRResponse(BaseModel):
    qr_code: str
    session_id: str
    expires_in: int  # seconds


class WhatsAppStatusResponse(BaseModel):
    connected: bool
    phone_number: Optional[str] = None
    account_name: Optional[str] = None
    connected_at: Optional[str] = None


class WhatsAppWebhookConfigRequest(BaseModel):
    technician_id: int
    phone_id: str
    access_token: str


class WhatsAppWebhookConfigResponse(BaseModel):
    success: bool
    message: str
    webhook_url: Optional[str] = None


# ==========================
# SOCIAL MEDIA STATUS
# ==========================

class SocialStatusResponse(BaseModel):
    connected: bool
    platform: str
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    phone_number: Optional[str] = None
    connected_at: Optional[str] = None
    expires_at: Optional[str] = None


class SocialAccountsListResponse(BaseModel):
    accounts: List[SocialAccountResponse]


# ==========================
# CHAT / AI SCHEMAS
# ==========================

class ChatSettingsBase(BaseModel):
    tone: str = "friendly"
    custom_prompt: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7


class ChatSettingsCreate(ChatSettingsBase):
    technician_id: int


class ChatSettingsUpdate(ChatSettingsBase):
    pass


class ChatSettingsResponse(ChatSettingsBase):
    technician_id: int
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================
# CHAT SESSION SCHEMAS
# ==========================

class ChatMessageRequest(BaseModel):
    technician_id: int
    message: str
    session_id: Optional[str] = None
    platform: Optional[str] = None
    account_id: Optional[str] = None
    
    # Optional pre-filled data
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    requested_service_id: Optional[int] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    confirm: Optional[bool] = False


class ChatMessageResponse(BaseModel):
    reply: str
    session_id: str
    booking_id: Optional[int] = None
    need: Optional[str] = None  # client_name | service | datetime | contact | confirm
    step: Optional[str] = None
    services: Optional[List[dict]] = None
    price: Optional[float] = None
    available_suggestions: Optional[List[str]] = None
    payment_instructions: Optional[dict] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    technician_id: int
    platform: Optional[str] = None
    step: str
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    service_id: Optional[int] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    booking_id: Optional[int] = None
    created_at: str
    updated_at: str
    expires_at: str

    model_config = ConfigDict(from_attributes=True)


# ==========================
# PAYMENT PROOF SCHEMAS
# ==========================

class PaymentProofBase(BaseModel):
    booking_id: int
    technician_id: int


class PaymentProofCreate(PaymentProofBase):
    filename: str


class PaymentProofResponse(PaymentProofBase):
    id: int
    filename: str
    uploaded_at: str
    status: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentProofConfirmRequest(BaseModel):
    proof_id: int
    approve: bool = True


# ==========================
# BOOKING SCHEMAS
# ==========================

class ClientBookingRequest(BaseModel):
    technician_id: int
    service_id: int
    client_name: str
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    date: str
    time: str


class ClientBookingResponse(BaseModel):
    success: bool
    booking_id: int
    message: str
    service_price: float


class ConfirmPaymentRequest(BaseModel):
    booking_id: int
    payment_method: str = "bank"  # bank | stripe | manual


class BookingResponse(BaseModel):
    id: int
    client_name: str
    client_phone: Optional[str] = None
    service_name: Optional[str] = None
    appointment_date: str
    appointment_time: str
    payment_status: str

    model_config = ConfigDict(from_attributes=True)


class BookingsListResponse(BaseModel):
    bookings: List[BookingResponse]


# ==========================
# MESSAGE LOG SCHEMAS
# ==========================

class MessageLogBase(BaseModel):
    technician_id: int
    platform: str
    direction: str  # incoming | outgoing
    sender_id: Optional[str] = None
    recipient_id: Optional[str] = None
    message_content: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "sent"


class MessageLogCreate(MessageLogBase):
    pass


class MessageLogResponse(MessageLogBase):
    id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


# ==========================
# WEBHOOK SCHEMAS
# ==========================

class WebhookVerificationResponse(BaseModel):
    challenge: Optional[int] = None
    status: Optional[str] = None


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[Any]  # Can be more specific based on WhatsApp webhook structure


class InstagramWebhookPayload(BaseModel):
    object: str
    entry: List[Any]  # Can be more specific based on Instagram webhook structure


# ==========================
# TEST MESSAGE SCHEMAS
# ==========================

class TestMessageRequest(BaseModel):
    technician_id: int
    platform: str  # whatsapp | instagram
    recipient: str  # phone for WhatsApp, user_id for Instagram
    message: str = "Test message from AIVA Beauty AI"


class TestMessageResponse(BaseModel):
    success: bool
    message: str


class ComplaintCreateSchema(BaseModel):
    technician_id: int
    booking_id: Optional[int] = None
    client_name: str
    client_contact: Optional[str] = None
    complaint_text: str


class NotificationMarkReadSchema(BaseModel):
    technician_id: int
    notification_id: Optional[int] = None
    mark_all: bool = False