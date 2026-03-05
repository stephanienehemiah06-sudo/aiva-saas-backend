# social_utils.py
import os
import requests
import uuid
from datetime import datetime, timedelta
from datetime import timezone
from typing import Dict, Optional, Tuple

# Store OAuth states (in production use Redis)
oauth_states: Dict[str, Dict] = {}

def generate_oauth_state(technician_id: int, platform: str) -> str:
    """Generate and store OAuth state for CSRF protection"""
    state = str(uuid.uuid4())
    oauth_states[state] = {
        "technician_id": technician_id,
        "platform": platform,
        "expires": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    }
    return state

def verify_oauth_state(state: str, technician_id: int, platform: str) -> bool:
    """Verify OAuth state"""
    if state not in oauth_states:
        return False
    
    stored = oauth_states[state]
    if stored["technician_id"] != technician_id or stored["platform"] != platform:
        return False
    
    # Check expiration
    expiry = datetime.fromisoformat(stored["expires"])
    now_utc = datetime.now(timezone.utc)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if now_utc > expiry:
        del oauth_states[state]
        return False
    
    # Clean up after verification
    del oauth_states[state]
    return True

def get_instagram_auth_url(redirect_uri: str, state: str) -> str:
    """Build Instagram OAuth URL"""
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    if not client_id:
        raise ValueError("INSTAGRAM_CLIENT_ID not set")
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "scope": "instagram_business_basic,instagram_business_manage_messages"
    }
    
    import urllib.parse
    return f"https://api.instagram.com/oauth/authorize?{urllib.parse.urlencode(params)}"

def get_facebook_auth_url(redirect_uri: str, state: str) -> str:
    """Build Facebook OAuth URL"""
    app_id = os.getenv("FACEBOOK_APP_ID")
    if not app_id:
        raise ValueError("FACEBOOK_APP_ID not set")
    
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "scope": "pages_messaging,pages_manage_metadata,pages_read_engagement"
    }
    
    import urllib.parse
    return f"https://www.facebook.com/v18.0/dialog/oauth?{urllib.parse.urlencode(params)}"

def exchange_instagram_code(code: str, redirect_uri: str) -> Optional[Dict]:
    """Exchange Instagram code for access token"""
    client_id = os.getenv("INSTAGRAM_CLIENT_ID")
    client_secret = os.getenv("INSTAGRAM_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return None
    
    token_url = "https://api.instagram.com/oauth/access_token"
    response = requests.post(token_url, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": code
    })
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    access_token = data.get("access_token")
    
    # Get long-lived token (60 days)
    long_token_url = "https://graph.instagram.com/access_token"
    long_response = requests.get(long_token_url, params={
        "grant_type": "ig_exchange_token",
        "client_secret": client_secret,
        "access_token": access_token
    })
    
    if long_response.status_code == 200:
        long_data = long_response.json()
        access_token = long_data.get("access_token", access_token)
    
    # Get user info
    user_url = "https://graph.instagram.com/me"
    user_response = requests.get(user_url, params={
        "fields": "id,username",
        "access_token": access_token
    })
    
    user_data = {}
    if user_response.status_code == 200:
        user_data = user_response.json()
    
    return {
        "access_token": access_token,
        "account_id": user_data.get("id"),
        "account_name": user_data.get("username", "Instagram Account"),
        "expires_in": 5184000  # 60 days in seconds
    }

def exchange_facebook_code(code: str, redirect_uri: str) -> Optional[Dict]:
    """Exchange Facebook code for access token"""
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    
    if not app_id or not app_secret:
        return None
    
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    response = requests.get(token_url, params={
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code
    })
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    access_token = data.get("access_token")
    
    # Get pages
    pages_url = "https://graph.facebook.com/v18.0/me/accounts"
    pages_response = requests.get(pages_url, params={
        "access_token": access_token
    })
    
    account_name = "Facebook Page"
    account_id = None
    
    if pages_response.status_code == 200:
        pages_data = pages_response.json()
        if pages_data.get("data"):
            page = pages_data["data"][0]
            access_token = page.get("access_token", access_token)
            account_name = page.get("name", account_name)
            account_id = page.get("id")
    
    return {
        "access_token": access_token,
        "account_id": account_id,
        "account_name": account_name,
        "expires_in": data.get("expires_in", 5184000)
    }

def generate_whatsapp_qr(technician_id: int) -> Tuple[str, str]:
    """Generate WhatsApp QR code for pairing"""
    session_id = str(uuid.uuid4())
    
    # In production, integrate with WhatsApp Business API
    # For demo, use QR code API
    qr_data = f"https://wa.me/?text=connect_{technician_id}_{session_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}"
    
    return qr_url, session_id