from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.core.config import Settings
from app.db.models import User


def ensure_initial_admin(session: Session, settings: Settings) -> None:
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return
    existing = session.scalar(select(User).where(User.email == settings.initial_admin_email.lower()))
    if existing is not None:
        if existing.role != "admin" or not existing.is_active:
            existing.role = "admin"
            existing.is_active = True
            session.commit()
        return
    session.add(
        User(
            email=settings.initial_admin_email.lower(),
            password_hash=hash_password(settings.initial_admin_password),
            role="admin",
            is_active=True,
        )
    )
    session.commit()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(session: Session, *, email: str, password: str, role: str = "user") -> User:
    normalized_email = email.strip().lower()
    normalized_role = role.strip().lower()
    if normalized_role not in {"admin", "user"}:
        raise ValueError("role must be either 'admin' or 'user'.")
    existing = session.scalar(select(User).where(User.email == normalized_email))
    if existing is not None:
        raise ValueError("A user with that email already exists.")
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role=normalized_role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
