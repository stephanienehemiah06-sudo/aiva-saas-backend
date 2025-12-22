from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# ==========================
# 👩‍🎨 TECHNICIAN MODEL
# ==========================
class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)

    # ======================
    # BASIC ACCOUNT INFO
    # ======================
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    business_name = Column(String, nullable=False)

    # ======================
    # LOCATION & WEB
    # ======================
    country = Column(String)
    city = Column(String)
    address = Column(String)
    website = Column(String)

    # ======================
    # AI PERSONALITY
    # ======================
    assistant_name = Column(String)
    tone = Column(String)
    brand_voice_style = Column(String)
    welcome_message = Column(Text)

    # ======================
    # POLICIES
    # ======================
    policies = Column(Text)
    cancellation_policy = Column(Text)
    lateness_policy = Column(Text)

    # ======================
    # PAYMENTS
    # ======================
    deposit_required = Column(Boolean, default=False)
    deposit_amount = Column(Float, default=0)
    payment_provider = Column(String)
    payout_email = Column(String)

    # ======================
    # WORK SCHEDULE
    # ======================
    work_schedule = Column(Text)

    # ======================
    # RELATIONSHIPS
    # ======================
    services = relationship(
        "Service",
        back_populates="technician",
        cascade="all, delete-orphan"
    )



# ==========================
# 💅 SERVICE MODEL
# ==========================
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    technician_id = Column(Integer, ForeignKey("technicians.id"))

    # ----------------------
    # Core info
    # ----------------------
    name = Column(String, nullable=False)
    category = Column(String)
    description = Column(Text)

    # ----------------------
    # Pricing & time
    # ----------------------
    price = Column(Float, nullable=False)
    currency = Column(String, default="NGN")
    duration_minutes = Column(Integer, default=60)

    deposit_required = Column(Boolean, default=False)
    deposit_amount = Column(Float)

    # ----------------------
    # Status
    # ----------------------
    active = Column(Boolean, default=True)

    # ----------------------
    # Relationships
    # ----------------------
    technician = relationship(
        "Technician",
        back_populates="services"
    )



# ==========================
# 📅 BOOKING MODEL
# ==========================
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    technician_id = Column(Integer, ForeignKey("technicians.id"))
    service_id = Column(Integer, ForeignKey("services.id"))

    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)

    appointment_date = Column(String, nullable=False)   # e.g. "2025-12-01"
    appointment_time = Column(String, nullable=False)   # e.g. "15:00"

    status = Column(
        String,
        default="PENDING_PAYMENT"
    )
    # statuses:
    # - PENDING_PAYMENT
    # - CONFIRMED
    # - CANCELLED

    payment_reference = Column(String, nullable=True)

    # ======================
    # RELATIONSHIPS
    # ======================
    technician = relationship("Technician")
    service = relationship("Service")



# ==================================================
# 🧠 PHASE C — AI CONVERSATION MEMORY MODEL
# ==================================================
class ConversationState(Base):
    __tablename__ = "conversation_states"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(String, unique=True, nullable=False)

    # Current step of conversation:
    # GREETING
    # SERVICE_SELECTION
    # CLIENT_INFO
    # SLOT_INPUT
    # AVAILABILITY_CHECK
    # CONFIRM_BOOKING
    # PAYMENT_LINK
    # DONE
    stage = Column(String, default="GREETING")

    # Client information
    client_name = Column(String, nullable=True)
    client_email = Column(String, nullable=True)

    # Booking selections
    service_id = Column(Integer, nullable=True)
    appointment_date = Column(String, nullable=True)
    appointment_time = Column(String, nullable=True)
    