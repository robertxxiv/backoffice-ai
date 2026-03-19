from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64


@dataclass(slots=True)
class TokenPayload:
    user_id: str
    role: str
    expires_at: datetime


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f"scrypt${_urlsafe_encode(salt)}${_urlsafe_encode(derived)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_part, digest_part = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "scrypt":
        return False
    salt = _urlsafe_decode(salt_part)
    expected = _urlsafe_decode(digest_part)
    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)


def create_access_token(*, user_id: str, role: str, secret_key: str, ttl_minutes: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    payload_bytes = json.dumps(
        {
            "sub": user_id,
            "role": role,
            "exp": int(expires_at.timestamp()),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload_part = _urlsafe_encode(payload_bytes)
    signature = hmac.new(secret_key.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_part}.{_urlsafe_encode(signature)}"


def verify_access_token(token: str, secret_key: str) -> TokenPayload:
    try:
        payload_part, signature_part = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed access token.") from exc
    expected_signature = hmac.new(secret_key.encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).digest()
    actual_signature = _urlsafe_decode(signature_part)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise ValueError("Invalid access token signature.")
    payload = json.loads(_urlsafe_decode(payload_part))
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise ValueError("Access token has expired.")
    user_id = str(payload["sub"])
    role = str(payload["role"])
    return TokenPayload(user_id=user_id, role=role, expires_at=expires_at)


def _urlsafe_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _urlsafe_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")
