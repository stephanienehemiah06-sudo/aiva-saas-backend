# This file will be merged into models.py
# Showing ChatSession model code:

from sqlalchemy import Column, Integer, String, ForeignKey

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)  # unique session ID token
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=False)
    platform = Column(String, nullable=True)  # instagram | whatsapp | facebook | telegram | web
    account_id = Column(String, nullable=True)  # social account or client identifier

    # Step tracking: name -> service -> datetime -> contact -> confirm -> booking_created
    step = Column(String, default="start")  # start | name | service | datetime | contact | price | confirm | booking_created | completed
    
    # Collected data (JSON-like; stored as text)
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    service_id = Column(Integer, nullable=True)
    appointment_date = Column(String, nullable=True)
    appointment_time = Column(String, nullable=True)
    booking_id = Column(Integer, nullable=True)  # created booking ID
    
    # Metadata
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    expires_at = Column(String, nullable=True)  # session expires after 24 hours or inactivity
