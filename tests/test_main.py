import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import uuid
import hashlib
import hmac
import json as jsonlib
import os

from services.backend.main import app, get_db
from services.backend import models
from services.backend.database import Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # keep same in-memory DB across connections
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ====== FIXTURES ======
@pytest.fixture
def test_technician():
    """Create a test technician in DB."""
    db = TestingSessionLocal()
    tech = models.Technician(
        full_name="Test Tech",
        business_name="Test Beauty",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password="hashed_pwd_123"
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)
    yield tech
    db.close()

@pytest.fixture
def test_service(test_technician):
    """Create a test service."""
    db = TestingSessionLocal()
    svc = models.Service(
        technician_id=test_technician.id,
        name="Haircut",
        price=5000.0,
        duration=30
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    yield svc
    db.close()

@pytest.fixture
def test_payment_setting(test_technician):
    """Create a test payment setting."""
    db = TestingSessionLocal()
    ps = models.PaymentSetting(
        technician_id=test_technician.id,
        provider="manual",
        bank_name="Test Bank",
        account_name="Test Account",
        account_number="1234567890",
        auto_confirm_proofs=False
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    yield ps
    db.close()

# ====== BOOKING TESTS ======
def test_create_client_booking(test_technician, test_service):
    """Test creating a booking from client request."""
    response = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "client_name": "John Doe",
            "client_phone": "+2348012345678",
            "client_email": "john@example.com",
            "date": "2026-02-20",
            "time": "14:00"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["booking_id"] is not None
    assert data["service_price"] == 5000.0


def test_client_booking_creates_dashboard_notification(test_technician, test_service):
    """Booking creation should add a dashboard notification."""
    response = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "client_name": "Jane Doe",
            "client_phone": "+2348010000000",
            "date": "2026-02-22",
            "time": "10:00"
        }
    )
    assert response.status_code == 200

    db = TestingSessionLocal()
    notifications = db.query(models.DashboardNotification).filter(
        models.DashboardNotification.technician_id == test_technician.id,
        models.DashboardNotification.event_type == "booking_created"
    ).all()
    db.close()

    assert len(notifications) >= 1


def test_create_complaint_creates_notification(test_technician):
    """Complaint creation should add complaint and dashboard notification."""
    response = client.post(
        "/complaints",
        json={
            "technician_id": test_technician.id,
            "client_name": "Client A",
            "complaint_text": "Service was delayed by 30 minutes"
        }
    )
    assert response.status_code == 200
    assert response.json().get("success") is True

    db = TestingSessionLocal()
    complaint = db.query(models.Complaint).filter(
        models.Complaint.technician_id == test_technician.id
    ).first()
    notification = db.query(models.DashboardNotification).filter(
        models.DashboardNotification.technician_id == test_technician.id,
        models.DashboardNotification.event_type == "complaint_created"
    ).first()
    db.close()

    assert complaint is not None
    assert notification is not None


def test_notifications_read_flow(test_technician):
    """Unread count should decrease when notification is marked read."""
    db = TestingSessionLocal()
    n1 = models.DashboardNotification(
        technician_id=test_technician.id,
        event_type="booking_created",
        title="New Booking",
        message="Booking one",
        related_id=1,
        is_read=False,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(n1)
    db.commit()
    db.refresh(n1)
    notification_id = n1.id
    db.close()

    list_res = client.get(f"/notifications/{test_technician.id}")
    assert list_res.status_code == 200
    assert list_res.json().get("unread_count", 0) >= 1

    mark_res = client.post(
        f"/notifications/{notification_id}/read",
        json={"technician_id": test_technician.id}
    )
    assert mark_res.status_code == 200

    list_res_after = client.get(f"/notifications/{test_technician.id}")
    assert list_res_after.status_code == 200
    assert list_res_after.json().get("unread_count", 0) == 0

def test_create_booking_slot_unavailable(test_technician, test_service):
    """Test booking fails when slot is taken."""
    # Create first booking
    db = TestingSessionLocal()
    booking1 = models.Appointment(
        technician_id=test_technician.id,
        service_id=test_service.id,
        client_name="Client 1",
        date="2026-02-20",
        time="14:00",
        payment_status="confirmed"
    )
    db.add(booking1)
    db.commit()
    db.close()
    
    # Try to create booking at same slot
    response = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "client_name": "Client 2",
            "client_phone": "+2348012345678",
            "date": "2026-02-20",
            "time": "14:00"
        }
    )
    assert response.status_code == 400
    assert "unavailable" in response.json()["detail"].lower()

def test_get_technician_bookings(test_technician, test_service):
    """Test retrieving technician's bookings."""
    # Create a booking
    db = TestingSessionLocal()
    booking = models.Appointment(
        technician_id=test_technician.id,
        service_id=test_service.id,
        client_name="Test Client",
        client_phone="+2348012345678",
        date="2026-02-20",
        time="14:00",
        payment_status="confirmed"
    )
    db.add(booking)
    db.commit()
    db.close()
    
    # Fetch bookings
    response = client.get(f"/bookings/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert "bookings" in data
    assert len(data["bookings"]) >= 1


def test_staff_crud_premium_success(test_technician):
    """Premium users can create, list, update, and delete staff members."""
    db = TestingSessionLocal()
    premium_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="premium",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(premium_sub)
    db.commit()
    db.close()

    create_res = client.post(
        "/staff",
        json={
            "technician_id": test_technician.id,
            "full_name": "Ada Stylist",
            "role": "Senior Technician"
        }
    )
    assert create_res.status_code == 200
    staff_id = create_res.json()["staff"]["id"]

    list_res = client.get(f"/staff/{test_technician.id}")
    assert list_res.status_code == 200
    assert len(list_res.json().get("staff", [])) >= 1

    update_res = client.put(
        f"/staff/{staff_id}",
        json={
            "technician_id": test_technician.id,
            "role": "Team Lead",
            "active": True
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["staff"]["role"] == "Team Lead"

    delete_res = client.delete(f"/staff/{staff_id}?technician_id={test_technician.id}")
    assert delete_res.status_code == 200
    assert delete_res.json().get("success") is True


def test_staff_list_forbidden_for_pro_plan(test_technician):
    """Pro plan should be blocked from Premium-only staff management endpoints."""
    db = TestingSessionLocal()
    pro_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="pro",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(pro_sub)
    db.commit()
    db.close()

    response = client.get(f"/staff/{test_technician.id}")
    assert response.status_code == 403
    assert "premium" in response.json().get("detail", "").lower()


def test_client_booking_allows_parallel_slots_for_different_staff(test_technician, test_service):
    """Same time slot should be allowed across different staff, but not same staff."""
    db = TestingSessionLocal()
    premium_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="premium",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(premium_sub)
    db.commit()
    db.close()

    s1 = client.post("/staff", json={"technician_id": test_technician.id, "full_name": "Staff One", "role": "Lash"})
    s2 = client.post("/staff", json={"technician_id": test_technician.id, "full_name": "Staff Two", "role": "Nails"})
    assert s1.status_code == 200
    assert s2.status_code == 200
    staff1_id = s1.json()["staff"]["id"]
    staff2_id = s2.json()["staff"]["id"]

    booking1 = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "staff_id": staff1_id,
            "client_name": "Client One",
            "client_phone": "+2348011111111",
            "date": "2026-03-10",
            "time": "11:00"
        }
    )
    assert booking1.status_code == 200

    booking2 = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "staff_id": staff2_id,
            "client_name": "Client Two",
            "client_phone": "+2348022222222",
            "date": "2026-03-10",
            "time": "11:00"
        }
    )
    assert booking2.status_code == 200

    booking3 = client.post(
        "/client-booking",
        json={
            "technician_id": test_technician.id,
            "service_id": test_service.id,
            "staff_id": staff1_id,
            "client_name": "Client Three",
            "client_phone": "+2348033333333",
            "date": "2026-03-10",
            "time": "11:00"
        }
    )
    assert booking3.status_code == 400
    assert "unavailable" in booking3.json().get("detail", "").lower()

def test_confirm_payment(test_technician, test_service):
    """Test confirming payment for a booking."""
    # Create booking
    db = TestingSessionLocal()
    booking = models.Appointment(
        technician_id=test_technician.id,
        service_id=test_service.id,
        client_name="Test Client",
        date="2026-02-20",
        time="14:00",
        payment_status="unpaid"
    )
    db.add(booking)
    db.commit()
    booking_id = booking.id
    db.close()
    
    # Confirm payment
    response = client.post(
        "/confirm-payment",
        json={
            "booking_id": booking_id,
            "payment_method": "bank"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify booking is confirmed
    db = TestingSessionLocal()
    updated = db.query(models.Appointment).filter(models.Appointment.id == booking_id).first()
    assert updated.payment_status == "confirmed"
    db.close()

# ====== PAYMENT SETTINGS TESTS ======
def test_save_payment_settings(test_technician):
    """Test saving payment settings."""
    response = client.post(
        "/payments/settings",
        json={
            "technician_id": test_technician.id,
            "provider": "manual",
            "bank_name": "Test Bank",
            "account_name": "Test Account",
            "account_number": "9876543210",
            "auto_confirm_proofs": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_payment_account(test_technician, test_payment_setting):
    """Test retrieving payment account details."""
    response = client.get(f"/payment-account/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "manual"
    assert data["bank_name"] == "Test Bank"
    assert data["account_number"] == "1234567890"

# ====== SUBSCRIPTION TESTS ======
def test_get_subscription_status(test_technician):
    """Test retrieving subscription status."""
    response = client.get(f"/subscription/status/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert "status" in data
# ====== SOCIAL / CHAT TESTS ======

def test_instagram_webhook_and_chat(test_technician, test_service):
    """Simulate an incoming Instagram message and ensure the chat reply is sent."""
    # create social account record for the technician
    db = TestingSessionLocal()
    sa = models.SocialAccount(
        technician_id=test_technician.id,
        platform="instagram",
        account_name="ig_business",
        account_id="PAGE123",
        access_token="FAKE_TOKEN",
        connected_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(sa)
    db.commit()
    db.close()

    # monkeypatch the send function to capture output
    sent = {}
    def fake_send(recipient_id, message_text, access_token):
        sent['recipient'] = recipient_id
        sent['text'] = message_text
        sent['token'] = access_token
        return True
    import main as main_module
    main_module.send_instagram_message = fake_send

    # incoming webhook payload from a user
    payload = {"entry":[{"messaging":[{"sender":{"id":"USER456"},"recipient":{"id":"PAGE123"},"message":{"text":"Hello"}}]}]}
    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
    assert sent.get('recipient') == "USER456"
    assert "name" in sent.get('text','').lower()
    assert sent.get('token') == "FAKE_TOKEN"


def test_social_automation_settings_persist(test_technician):
    """Save and fetch social automation settings."""
    save_res = client.post(
        "/social/automation-settings",
        json={
            "technician_id": test_technician.id,
            "auto_reply_enabled": False,
            "welcome_dm_template": "Welcome from test"
        }
    )
    assert save_res.status_code == 200
    saved = save_res.json()
    assert saved["success"] is True
    assert saved["auto_reply_enabled"] is False

    get_res = client.get(f"/social/automation-settings/{test_technician.id}")
    assert get_res.status_code == 200
    fetched = get_res.json()
    assert fetched["auto_reply_enabled"] is False
    assert fetched["welcome_dm_template"] == "Welcome from test"


def test_instagram_webhook_respects_auto_reply_toggle(test_technician):
    """Webhook should not send reply when auto reply is disabled."""
    db = TestingSessionLocal()
    db.add(models.SocialAccount(
        technician_id=test_technician.id,
        platform="instagram",
        account_name="ig_business",
        account_id="PAGE_AUTOREPLY_OFF",
        access_token="FAKE_TOKEN",
        connected_at=datetime.now(timezone.utc).isoformat()
    ))
    db.add(models.SocialAutomationSetting(
        technician_id=test_technician.id,
        auto_reply_enabled=False,
        welcome_dm_template="",
        updated_at=datetime.now(timezone.utc).isoformat()
    ))
    db.commit()
    db.close()

    sent = {"count": 0}
    def fake_send(recipient_id, message_text, access_token):
        sent["count"] += 1
        return True
    import main as main_module
    main_module.send_instagram_message = fake_send

    payload = {"entry":[{"messaging":[{"sender":{"id":"USER_OFF"},"recipient":{"id":"PAGE_AUTOREPLY_OFF"},"message":{"text":"Hello"}}]}]}
    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 200
    assert sent["count"] == 0


def test_recent_social_messages_endpoint(test_technician):
    """Recent message endpoint should return latest logs."""
    db = TestingSessionLocal()
    db.add(models.MessageLog(
        technician_id=test_technician.id,
        platform="instagram",
        direction="incoming",
        sender_id="user_1",
        recipient_id="biz_1",
        message_content="Hi, I want lashes",
        session_id="sess_1",
        status="received",
        created_at=datetime.now(timezone.utc).isoformat()
    ))
    db.add(models.MessageLog(
        technician_id=test_technician.id,
        platform="instagram",
        direction="outgoing",
        sender_id="biz_1",
        recipient_id="user_1",
        message_content="Hi! What's your name please?",
        session_id="sess_1",
        status="sent",
        created_at=datetime.now(timezone.utc).isoformat()
    ))
    db.commit()
    db.close()

    response = client.get(f"/social/messages/{test_technician.id}?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) >= 2
    assert any(item.get("direction") == "incoming" for item in data["messages"])
    assert any(item.get("direction") == "outgoing" for item in data["messages"])


def test_session_messages_endpoint_returns_timeline(test_technician):
    """Session timeline endpoint should return session metadata and messages."""
    db = TestingSessionLocal()
    session = models.ChatSession(
        session_id="timeline_sess_1",
        technician_id=test_technician.id,
        platform="instagram",
        account_id="timeline_user",
        step="name",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    )
    db.add(session)
    db.add(models.MessageLog(
        technician_id=test_technician.id,
        platform="instagram",
        direction="incoming",
        sender_id="timeline_user",
        recipient_id="biz_1",
        message_content="Hello there",
        session_id="timeline_sess_1",
        status="received",
        created_at=datetime.now(timezone.utc).isoformat()
    ))
    db.commit()
    db.close()

    response = client.get(f"/social/session/{test_technician.id}/timeline_sess_1/messages?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert data.get("session", {}).get("session_id") == "timeline_sess_1"
    assert len(data.get("messages", [])) >= 1


def test_manual_reply_endpoint_sends_and_logs(test_technician):
    """Manual reply endpoint should call sender and log outgoing message."""
    db = TestingSessionLocal()
    db.add(models.SocialAccount(
        technician_id=test_technician.id,
        platform="instagram",
        account_name="ig_business",
        account_id="BIZ_IG",
        access_token="FAKE_TOKEN",
        connected_at=datetime.now(timezone.utc).isoformat()
    ))
    db.commit()
    db.close()

    sent = {"count": 0}
    def fake_send(recipient_id, message_text, access_token):
        sent["count"] += 1
        return True
    import main as main_module
    main_module.send_instagram_message = fake_send

    response = client.post(
        "/social/manual-reply",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_id": "USER_MANUAL_1",
            "session_id": "timeline_sess_1",
            "message": "Thanks, we are on it."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert sent["count"] == 1


def test_instagram_webhook_signature_enforced_rejects_missing_header(test_technician, monkeypatch):
    """When signature enforcement is enabled, missing signature must be rejected."""
    monkeypatch.setenv("INSTAGRAM_WEBHOOK_ENFORCE_SIGNATURE", "true")
    monkeypatch.setenv("INSTAGRAM_CLIENT_SECRET", "test_secret_123")

    payload = {
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "SENDER_A"},
                        "recipient": {"id": "RECIPIENT_A"},
                        "message": {"text": "hello"}
                    }
                ]
            }
        ]
    }

    response = client.post("/webhooks/instagram", json=payload)
    assert response.status_code == 403


def test_instagram_webhook_signature_enforced_accepts_valid_header(test_technician, monkeypatch):
    """When signature enforcement is enabled, valid signature should pass."""
    monkeypatch.setenv("INSTAGRAM_WEBHOOK_ENFORCE_SIGNATURE", "true")
    monkeypatch.setenv("INSTAGRAM_CLIENT_SECRET", "test_secret_123")

    db = TestingSessionLocal()
    db.add(models.SocialAccount(
        technician_id=test_technician.id,
        platform="instagram",
        account_name="ig_test",
        account_id="PAGE_SIG_TEST",
        access_token="FAKE_TOKEN",
        connected_at=datetime.now(timezone.utc).isoformat()
    ))
    db.commit()
    db.close()

    sent = {"count": 0}
    def fake_send(recipient_id, message_text, access_token):
        sent["count"] += 1
        return True
    import main as main_module
    main_module.send_instagram_message = fake_send

    payload = {
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "USER_SIG_OK"},
                        "recipient": {"id": "PAGE_SIG_TEST"},
                        "message": {"text": "hello"}
                    }
                ]
            }
        ]
    }
    raw = jsonlib.dumps(payload).encode("utf-8")
    sig = "sha256=" + hmac.new(
        os.getenv("INSTAGRAM_CLIENT_SECRET", "").encode("utf-8"),
        raw,
        hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhooks/instagram",
        data=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig
        }
    )
    assert response.status_code == 200
    assert sent["count"] == 1


def test_handoff_pause_and_resume_flow(test_technician):
    """Pause and resume AI handoff on a session."""
    first = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_id": "handoff_user_1",
            "message": "Hello"
        }
    )
    assert first.status_code == 200
    session_id = first.json().get("session_id")
    assert session_id

    pause = client.post(
        "/social/handoff/pause",
        json={
            "technician_id": test_technician.id,
            "session_id": session_id,
            "note": "manual pricing"
        }
    )
    assert pause.status_code == 200
    assert pause.json().get("success") is True

    while_paused = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_id": "handoff_user_1",
            "message": "Need update"
        }
    )
    assert while_paused.status_code == 200
    paused_data = while_paused.json()
    assert paused_data.get("handoff_paused") is True

    resume = client.post(
        "/social/handoff/resume",
        json={
            "technician_id": test_technician.id,
            "session_id": session_id
        }
    )
    assert resume.status_code == 200
    assert resume.json().get("success") is True

    after_resume = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_id": "handoff_user_1",
            "message": "Back again"
        }
    )
    assert after_resume.status_code == 200
    assert after_resume.json().get("handoff_paused") is not True


def test_handoff_pause_creates_session_when_missing(test_technician):
    """Pausing by platform/account should create a handoff session if none exists yet."""
    response = client.post(
        "/social/handoff/pause",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_id": "new_user_without_session",
            "note": "manual handoff"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert data.get("handoff_paused") is True
    assert data.get("session_id")

def test_upgrade_subscription(test_technician):
    """Test upgrading to a paid plan."""
    response = client.post(
        "/subscription/upgrade",
        json={
            "technician_id": test_technician.id,
            "plan": "starter"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"].lower().startswith("starter")


def test_chat_receive_blocked_after_trial_expiry(test_technician):
    """Expired trial users should be prompted to upgrade before using AI chat."""
    db = TestingSessionLocal()
    expired_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="trial",
        status="active",
        start_date=(datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
        end_date=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    )
    db.add(expired_sub)
    db.commit()
    db.close()

    response = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "message": "Hello there"
        }
    )

    assert response.status_code == 403
    detail = response.json().get("detail", "").lower()
    assert "upgrade" in detail
    assert "pro" in detail


def test_chat_receive_requires_pro_for_starter_plan(test_technician):
    """Starter plan should not access full AI booking assistant (Pro+)."""
    db = TestingSessionLocal()
    starter_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="starter",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(starter_sub)
    db.commit()
    db.close()

    response = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "message": "I want to book"
        }
    )

    assert response.status_code == 403
    detail = response.json().get("detail", "").lower()
    assert "pro" in detail


def test_revenue_dashboard_premium_success(test_technician):
    """Premium users should receive revenue dashboard aggregates."""
    db = TestingSessionLocal()

    svc1 = models.Service(technician_id=test_technician.id, name="Volume Set", price=75.0, duration=90)
    svc2 = models.Service(technician_id=test_technician.id, name="Refill", price=45.0, duration=60)
    db.add_all([svc1, svc2])
    db.commit()
    db.refresh(svc1)
    db.refresh(svc2)

    premium_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="premium",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(premium_sub)

    today = datetime.now(timezone.utc).date().isoformat()
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    bookings = [
        models.Appointment(
            technician_id=test_technician.id,
            service_id=svc1.id,
            client_name="A",
            date=today,
            time="10:00",
            service_price=75.0,
            payment_status="confirmed"
        ),
        models.Appointment(
            technician_id=test_technician.id,
            service_id=svc2.id,
            client_name="B",
            date=today,
            time="12:00",
            service_price=45.0,
            payment_status="paid"
        ),
        models.Appointment(
            technician_id=test_technician.id,
            service_id=svc2.id,
            client_name="C",
            date=yesterday,
            time="09:00",
            service_price=45.0,
            payment_status="unpaid"
        )
    ]
    db.add_all(bookings)
    db.commit()
    db.close()

    response = client.get(f"/dashboard/revenue/{test_technician.id}?days=7")
    assert response.status_code == 200
    data = response.json()

    assert data["currency"] == "GBP"
    assert data["period_days"] == 7
    assert data["totals"]["confirmed_revenue"] == 120.0
    assert data["totals"]["confirmed_bookings"] == 2
    assert data["totals"]["average_ticket"] == 60.0
    assert data["totals"]["pending_revenue"] == 45.0
    assert len(data["trend"]) == 7
    assert len(data["top_services"]) >= 1


def test_revenue_dashboard_pro_forbidden(test_technician):
    """Pro users should be blocked from premium revenue dashboard endpoint."""
    db = TestingSessionLocal()
    pro_sub = models.Subscription(
        technician_id=test_technician.id,
        plan="pro",
        status="active",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    )
    db.add(pro_sub)
    db.commit()
    db.close()

    response = client.get(f"/dashboard/revenue/{test_technician.id}")
    assert response.status_code == 403
    assert "premium" in response.json().get("detail", "").lower()

# ====== CHAT SESSION TESTS ======
def test_chat_receive_initial_message(test_technician):
    """Test receiving initial chat message."""
    response = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "message": "Hi, what services do you offer?"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_id" in data

def test_chat_receive_with_session(test_technician, test_service):
    """Test continuing chat with session_id."""
    # First message
    res1 = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "message": "Hi, I want to book"
        }
    )
    session_id = res1.json()["session_id"]
    
    # Continue with session
    res2 = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "session_id": session_id,
            "message": "My name is Alice"
        }
    )
    assert res2.status_code == 200
    data = res2.json()
    assert data["session_id"] == session_id
    assert "reply" in data

def test_chat_list_services(test_technician, test_service):
    """Test listing services via chat."""
    response = client.post(
        "/chat/receive",
        json={
            "technician_id": test_technician.id,
            "message": "show services"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert len(data["services"]) > 0

# ====== PAYMENT PROOF TESTS ======
def test_list_payment_proofs(test_technician):
    """Test listing payment proofs."""
    response = client.get(f"/payments/proofs/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert "proofs" in data
    assert isinstance(data["proofs"], list)

def test_confirm_payment_proof(test_technician, test_service):
    """Test confirming a payment proof."""
    # Create booking
    db = TestingSessionLocal()
    booking = models.Appointment(
        technician_id=test_technician.id,
        service_id=test_service.id,
        client_name="Test Client",
        date="2026-02-20",
        time="15:00",
        payment_status="unpaid"
    )
    db.add(booking)
    db.commit()
    booking_id = booking.id
    
    # Create proof
    proof = models.PaymentProof(
        booking_id=booking_id,
        technician_id=test_technician.id,
        filename="test_proof.jpg",
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        status="pending"
    )
    db.add(proof)
    db.commit()
    proof_id = proof.id
    db.close()
    
    # Confirm proof
    response = client.post(
        "/payments/proof/confirm",
        json={
            "proof_id": proof_id,
            "approve": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "approved"
    
    # Verify booking is confirmed
    db = TestingSessionLocal()
    updated_booking = db.query(models.Appointment).filter(models.Appointment.id == booking_id).first()
    assert updated_booking.payment_status == "confirmed"
    db.close()

# ====== CHAT SETTINGS TESTS ======
def test_save_chat_settings(test_technician):
    """Test saving chat settings."""
    response = client.post(
        "/chat-settings",
        json={
            "technician_id": test_technician.id,
            "tone": "professional",
            "custom_prompt": "Be formal and concise"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tone"] == "professional"

def test_get_chat_settings(test_technician):
    """Test retrieving chat settings."""
    # Save settings first
    client.post(
        "/chat-settings",
        json={
            "technician_id": test_technician.id,
            "tone": "cozy"
        }
    )
    
    # Retrieve settings
    response = client.get(f"/chat-settings/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["tone"] == "cozy"

# ====== SOCIAL ACCOUNTS TESTS ======
def test_connect_social_account(test_technician):
    """Test connecting a social account."""
    response = client.post(
        "/social-accounts/connect",
        json={
            "technician_id": test_technician.id,
            "platform": "instagram",
            "account_name": "test_beauty_salon",
            "access_token": "test_token_123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_get_social_accounts(test_technician):
    """Test retrieving connected social accounts."""
    # Connect account first
    client.post(
        "/social-accounts/connect",
        json={
            "technician_id": test_technician.id,
            "platform": "whatsapp",
            "account_name": "+2348012345678"
        }
    )
    
    # Retrieve accounts
    response = client.get(f"/social-accounts/{test_technician.id}")
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert len(data["accounts"]) > 0

def test_disconnect_social_account(test_technician):
    """Test disconnecting a social account."""
    # Connect account first
    res1 = client.post(
        "/social-accounts/connect",
        json={
            "technician_id": test_technician.id,
            "platform": "facebook",
            "account_name": "test_page"
        }
    )
    account_id = res1.json().get("account_id")
    
    # Disconnect
    response = client.delete(f"/social-accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
