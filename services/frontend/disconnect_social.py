# disconnect_social.py
from database import SessionLocal
from models import SocialAccount

# Replace with your actual technician_id (from the logs, it's 4)
technician_id = 4

db = SessionLocal()
try:
    accounts = db.query(SocialAccount).filter(SocialAccount.technician_id == technician_id).all()
    if accounts:
        print(f"Found {len(accounts)} connected account(s):")
        for acc in accounts:
            print(f"  - {acc.platform}: {acc.account_name}")
        confirm = input("Delete all these connections? (yes/no): ")
        if confirm.lower() == 'yes':
            db.query(SocialAccount).filter(SocialAccount.technician_id == technician_id).delete()
            db.commit()
            print("All social accounts disconnected.")
        else:
            print("Aborted.")
    else:
        print("No connected accounts found for this technician.")
finally:
    db.close()