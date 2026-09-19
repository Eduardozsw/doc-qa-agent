import logging

from core.security import hash_password, verify_password
from db.postgres import get_conn

logger = logging.getLogger(__name__)


def create_user(email: str, password: str, name: str = "") -> dict:
    password_hash = hash_password(password)
    with get_conn() as conn:
        row = conn.execute(
            """
            INSERT INTO users (email, password_hash, name)
            VALUES (%s, %s, %s)
            RETURNING id, email, name, plan
            """,
            (email, password_hash, name),
        ).fetchone()
        conn.commit()
    row["id"] = str(row["id"])
    return row


def get_user_by_email(email: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, name, plan FROM users WHERE email = %s",
            (email,),
        ).fetchone()
    if row:
        row["id"] = str(row["id"])
    return row


def get_user_by_id(user_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, name, plan FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
    if row:
        row["id"] = str(row["id"])
    return row


def authenticate(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def update_user(user_id: str, name: str | None = None, password: str | None = None) -> dict:
    fields: list[str] = []
    params: list = []

    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if password is not None:
        fields.append("password_hash = %s")
        params.append(hash_password(password))

    with get_conn() as conn:
        if fields:
            params.append(user_id)
            conn.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = %s",
                params,
            )
        row = conn.execute(
            "SELECT id, email, name, plan FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
        conn.commit()
    row["id"] = str(row["id"])
    return row


def get_user_plan(user_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT plan FROM users WHERE id = %s", (user_id,)).fetchone()
    return row["plan"] if row else "free"


def get_user_info(user_id: str) -> tuple[str, str]:
    with get_conn() as conn:
        row = conn.execute("SELECT email, name FROM users WHERE id = %s", (user_id,)).fetchone()
    if not row:
        return "", ""
    return row["email"] or "", row["name"] or ""
