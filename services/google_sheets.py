import os
import json
import gspread
from google.oauth2 import service_account
from dotenv import load_dotenv
from datetime import datetime

# Load env
load_dotenv()

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
SHEET_ID = os.getenv("SHEET_ID")


# ==============================
# CONNECT TO GOOGLE SHEETS
# ==============================
def get_sheet(tab_name: str):
    """Authorize and return the specific worksheet tab."""
    try:
        # Load service account credentials
        with open(GOOGLE_CREDENTIALS_FILE, "r") as f:
            creds_json = json.load(f)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        credentials = service_account.Credentials.from_service_account_info(
            creds_json, scopes=scopes
        )

        client = gspread.authorize(credentials)

        # Open using Sheet ID
        sheet = client.open_by_key(SHEET_ID).worksheet(tab_name)
        return sheet

    except Exception as e:
        print(f"❌ Error loading Google Sheet: {e}")
        return None


# ==============================
# SAVE BOOKING TO SHEET
# ==============================
def save_booking_to_sheet(booking):
    """Save booking into Google Sheets."""
    sheet = get_sheet("Sheet1")   # Make sure this matches your tab name

    if not sheet:
        print("❌ Could not connect to Google Sheet")
        return False

    row = [
        booking.technician_email,
        booking.client_name,
        booking.service,
        booking.date,
        booking.time,
        booking.email,
        booking.phone
    ]

    sheet.append_row(row)
    return True


# ==============================
# SAVE TECHNICIAN SIGNUP
# ==============================
def add_technician_signup(data: dict):
    """Save technician signup into Google Sheets."""
    try:
        sheet = get_sheet("Technicians_Sheet")

        if not sheet:
            print("❌ Could not connect to Technician_Sheet")
            return False

        row = [
            data.get("full_name"),
            data.get("email"),
            data.get("password"),
            data.get("business_name"),
            data.get("assistant_name"),
            data.get("country"),
            data.get("city"),
            data.get("website"),
            data.get("tone"),
            data.get("services"),
            data.get("payment_provider"),
            data.get("payout_email"),
            data.get("notes"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]

        sheet.append_row(row)
        return True

    except Exception as e:
        print("❌ Error saving technician:", e)
        return False


# ==============================
# OLD TECH APPEND (KEEP IF NEEDED)
# ==============================
def append_technician(data: dict):
    """Append technician registration into Google Sheets."""
    sheet = get_sheet("Technician_Sheet")

    if not sheet:
        print("❌ Could not connect to Technician_Sheet")
        return False

    row = [
        data.get("name", ""),
        data.get("email", ""),
        data.get("phone", ""),
        data.get("business_name", ""),
        data.get("platform", ""),
        data.get("username", ""),
        data.get("webhook_url", "")
    ]

    sheet.append_row(row)
    return True
