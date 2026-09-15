"""Password hashing and verification using Argon2 (via Passlib)."""
from passlib.context import CryptContext

# Argon2 is the recommended modern default; bcrypt kept as a legacy verifier
# so existing bcrypt hashes (if migrating from another system) still validate.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plaintext passwords."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash. Constant-time comparison."""
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """True if the stored hash uses outdated parameters and should be re-hashed on next login."""
    return pwd_context.needs_update(hashed_password)
