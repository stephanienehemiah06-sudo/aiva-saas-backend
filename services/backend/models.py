from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from services.backend.database import Base


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    business_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    services = relationship(
        "Service",
        back_populates="technician",
        cascade="all, delete"
    )
   
    social_accounts = relationship("SocialAccount", back_populates="technician", cascade="all, delete-orphan")
    social_automation_setting = relationship("SocialAutomationSetting", back_populates="technician", uselist=False, cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)

    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    duration = Column(Integer, nullable=False)

    technician = relationship("Technician", back_populates="services")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(String, nullable=True)


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, nullable=False, index=True)
    day = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, nullable=False, index=True)
    service_id = Column(Integer, nullable=False)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | payment_sent | confirmed | completed
    service_price = Column(Float, nullable=True)
    payment_status = Column(String, default="unpaid")  # unpaid | pending | confirmed | paid
    payment_method = Column(String, nullable=True)  # bank | manual | stripe
    booking_source = Column(String, default="website")  # website | ai
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    created_at = Column(String, nullable=True)


class PaymentSetting(Base):
    __tablename__ = "payment_settings"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)

    provider = Column(String, nullable=False)

    public_key = Column(String, nullable=True)
    secret_key = Column(String, nullable=True)

    bank_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    auto_confirm_proofs = Column(Boolean, default=False)


# ==========================
# SUBSCRIPTION SYSTEM
# ==========================

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)

    plan = Column(String, default="trial")   # trial | starter | pro | premium | free
    status = Column(String, default="active")

    start_date = Column(String)
    end_date = Column(String)

    stripe_subscription_id = Column(String, nullable=True)


# ==========================
# SOCIAL MEDIA ACCOUNTS
# ==========================

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    platform = Column(String, nullable=False)  # instagram, whatsapp, facebook, telegram
    account_name = Column(String, nullable=False)
    
    # Platform-specific identifiers
    account_id = Column(String, nullable=True)  # For storing platform-specific IDs (Instagram/Facebook page ID)
    phone_number = Column(String, nullable=True)  # For WhatsApp business phone number
    
    # Token management
    access_token = Column(Text, nullable=True)  # OAuth access token
    refresh_token = Column(Text, nullable=True)  # For refreshing expired tokens
    token_expires_at = Column(String, nullable=True)  # ISO format expiry datetime
    
    # Metadata
    connected_at = Column(String, nullable=False)  # ISO format connection timestamp
    is_active = Column(Boolean, default=True)  # Whether the connection is active
    
    # Webhook/subscription info
    webhook_verified = Column(Boolean, default=False)  # Whether webhook is verified
    webhook_url = Column(String, nullable=True)  # Custom webhook URL if needed
    
    # Relationship back to technician
    technician = relationship("Technician", back_populates="social_accounts")


class SocialAutomationSetting(Base):
    __tablename__ = "social_automation_settings"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False, unique=True)
    auto_reply_enabled = Column(Boolean, default=True)
    welcome_dm_template = Column(Text, nullable=True)
    updated_at = Column(String, nullable=False)

    technician = relationship("Technician", back_populates="social_automation_setting")


# ==========================
# WHATSAPP SESSIONS (for QR pairing)
# ==========================

class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    session_id = Column(String, unique=True, nullable=False, index=True)
    qr_code_data = Column(Text, nullable=True)  # QR code data or URL
    status = Column(String, default="pending")  # pending | scanning | connected | expired
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    connected_at = Column(String, nullable=True)
    
    # Relationship
    technician = relationship("Technician")


# ==========================
# OAUTH STATES (for CSRF protection)
# ==========================

class OAuthState(Base):
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, nullable=False, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    platform = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relationship
    technician = relationship("Technician")


# ==========================
# CHAT / AI SETTINGS
# ==========================

class ChatSetting(Base):
    __tablename__ = "chat_settings"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False, unique=True)

    tone = Column(String, default="friendly")  # friendly | professional | cozy | custom
    custom_prompt = Column(Text, nullable=True)
    updated_at = Column(String, nullable=True)
    
    # AI model settings
    model_name = Column(String, default="gpt-3.5-turbo")  # AI model to use
    temperature = Column(Float, default=0.7)  # AI temperature setting
    
    technician = relationship("Technician")


# ==========================
# PAYMENT PROOFS
# ==========================

class PaymentProof(Base):
    __tablename__ = "payment_proofs"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | approved | rejected
    reviewed_at = Column(String, nullable=True)
    reviewed_by = Column(String, nullable=True)  # "technician" or "auto"
    
    # Relationships
    booking = relationship("Appointment")
    technician = relationship("Technician")


# ==========================
# CHAT SESSIONS (STATEFUL) - FIXED VERSION
# ==========================

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    platform = Column(String, nullable=True)  # instagram | whatsapp | facebook | telegram | web
    account_id = Column(String, nullable=True)  # Platform-specific user ID

    # Step tracking
    step = Column(String, default="start")  # start | name | service | datetime | contact | price | confirm | booking_created | completed
    
    # Collected data
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    service_id = Column(Integer, nullable=True)
    appointment_date = Column(String, nullable=True)
    appointment_time = Column(String, nullable=True)
    booking_id = Column(Integer, nullable=True)
    
    # Conversation context
    last_message = Column(Text, nullable=True)
    message_count = Column(Integer, default=0)
    handoff_paused = Column(Boolean, default=False)
    handoff_note = Column(String, nullable=True)
    handoff_updated_at = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    
    # Relationships - FIXED: Removed the problematic booking relationship
    technician = relationship("Technician")
    # Removed: booking = relationship("Appointment", foreign_keys=[booking_id]) - this was causing the error


# ==========================
# MESSAGE LOGS (for debugging)
# ==========================

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    platform = Column(String, nullable=False)
    direction = Column(String)  # incoming | outgoing
    sender_id = Column(String, nullable=True)
    recipient_id = Column(String, nullable=True)
    message_content = Column(Text, nullable=True)
    session_id = Column(String, nullable=True)
    status = Column(String, default="sent")  # sent | delivered | read | failed
    created_at = Column(String, nullable=False)
    
    # Relationship
    technician = relationship("Technician")


class DashboardNotification(Base):
    __tablename__ = "dashboard_notifications"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # booking_created | complaint_created | others
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(String, nullable=False)

    technician = relationship("Technician")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False, index=True)
    booking_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=False)
    client_contact = Column(String, nullable=True)
    complaint_text = Column(Text, nullable=False)
    status = Column(String, default="open")
    created_at = Column(String, nullable=False)

    technician = relationship("Technician")