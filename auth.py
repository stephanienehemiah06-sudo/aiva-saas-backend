# auth.py
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db

# 👇 change this to any random long string later
SECRET_KEY = "super-secret-aiva-saas-key-change-me-123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    subject = usually the technician email
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": subject,
        "exp": datetime.utcnow() + expires_delta
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_technician_from_token(token: str, db: Session) -> models.Technician:
    """
    Decode token and return technician from DB
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    tech = db.query(models.Technician).filter(models.Technician.email == email).first()
    if not tech:
        raise credentials_exception

    return tech