from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Direct Argon2 hasher avoids passlib dependency issues in some environments.
pwd_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False