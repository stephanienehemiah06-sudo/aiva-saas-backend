# create_test_user.py
from services.backend.database import SessionLocal
from services.backend.models import Technician
from services.backend.auth import hash_password

db = SessionLocal()

print("🔍 Checking for existing test user...")

# Check if test user exists
user = db.query(Technician).filter(Technician.email == "test@example.com").first()
if not user:
    test_user = Technician(
        full_name="Test User",
        business_name="Test Beauty Salon",
        email="test@example.com",
        password=hash_password("password123")
    )
    db.add(test_user)
    db.commit()
    print("✅ Test user created successfully!")
    print("📧 Email: test@example.com")
    print("🔑 Password: password123")
else:
    print("✅ Test user already exists")
    print("📧 Email: test@example.com")
    print("🔑 Password: password123")
    print(f"👤 User ID: {user.id}")

# Also create some sample services
from services.backend.models import Service

services = db.query(Service).filter(Service.technician_id == user.id).count()
if services == 0 and user:
    sample_services = [
        Service(technician_id=user.id, name="Haircut", price=5000, duration=60),
        Service(technician_id=user.id, name="Manicure", price=3000, duration=45),
        Service(technician_id=user.id, name="Pedicure", price=4000, duration=60),
        Service(technician_id=user.id, name="Facial", price=8000, duration=90),
    ]
    for service in sample_services:
        db.add(service)
    db.commit()
    print("💅 Sample services created!")

db.close()
print("✨ Done!")