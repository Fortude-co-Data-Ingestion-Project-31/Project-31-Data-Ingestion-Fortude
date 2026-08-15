"""
Authentication helpers and simple token store.

This module provides a minimal local authentication system used by the
demo application. It implements:

- user registration and password hashing
- simple token creation/verification (stored in a SQLite `tokens` table)
- basic TOTP (time-based one-time password) generation and verification
- lightweight MFA secret management persisted on the `users` table

Note: This is intentionally simple for the project demo. Do not use in
production without replacing the storage, token format, and secret
management with hardened, audited implementations.
"""

import base64
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
import struct
import time
import urllib.parse


DB_PATH = Path(__file__).resolve().parent / "users.db"


def _get_conn():
    return sqlite3.connect(str(DB_PATH))


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
        """
    )
    conn.commit()

    # tokens table for simple session tokens
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()

    # Ensure tokens table has a 'type' column for distinguishing
    # different token kinds (session vs mfa temporary tokens). This allows
    # the app to create short-lived MFA tokens that cannot be reused as a
    # session token until exchanged.
    try:
        cur.execute("ALTER TABLE tokens ADD COLUMN type TEXT DEFAULT 'session'")
        conn.commit()
    except Exception:
        # column probably already exists
        pass

    # Ensure users table has columns used to store MFA state: the base32
    # `mfa_secret` used to generate/verify TOTP codes and an integer
    # `mfa_enabled` flag to indicate whether MFA is active for a user.
    try:
        cur.execute("ALTER TABLE users ADD COLUMN mfa_secret TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        # columns may already exist
        pass

    # Ensure a default admin user exists (username: admin, password: password)
    try:
        register_user("admin", "password", role="admin")
    except Exception:
        # ignore if already exists
        pass

    conn.close()


def register_user(username: str, password: str, role: str = "user"):
    """Register a new user with a salted PBKDF2 password hash.

    Args:
        username: chosen username (must be unique)
        password: plaintext password (will be salted & hashed)
        role: optional role, defaults to 'user'

    Raises:
        sqlite3.IntegrityError: if the username already exists.
    """
    # Create a random salt and store a PBKDF2-derived hash of the
    # password. Storing the salt separately prevents rainbow-table attacks.
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, salt, role),
        )
        conn.commit()
    finally:
        conn.close()


def create_token(username: str, ttl: int = 3600) -> str:
    return create_token_with_type(username, ttl, token_type="session")


def create_token_with_type(username: str, ttl: int = 3600, token_type: str = "session") -> str:
    """Create and persist a random token for `username`.

    The token is stored in the `tokens` table with an expiration time
    and a `type` string that callers can check (e.g. 'mfa' or 'session').

    Returns:
        the generated token string
    """
    # Create a random token string, store it with an expiration timestamp
    # and the provided `type`. The `type` lets callers validate that a
    # token is the expected kind (for example, a short-lived "mfa" token
    # versus a longer-lived "session" token).
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + int(ttl)
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tokens (token, username, expires_at, type) VALUES (?, ?, ?, ?)", (token, username, expires_at, token_type))
        conn.commit()
        return token
    finally:
        conn.close()


def verify_token(token: str) -> str | None:
    """Verify a token exists and is not expired.

    Returns the username if valid, otherwise None.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, expires_at FROM tokens WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    username, expires_at = row
    if int(time.time()) > expires_at:
        return None
    return username


def verify_token_with_type(token: str, expected_type: str) -> str | None:
    """Verify a token exists, matches the expected type, and is not expired.

    Returns the username if valid, otherwise None.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, expires_at, type FROM tokens WHERE token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    username, expires_at, ttype = row
    if int(time.time()) > expires_at:
        return None
    if ttype != expected_type:
        return None
    return username


def delete_token(token: str):
    """Delete a token from the tokens table.

    Used to invalidate temporary MFA tokens once they've been exchanged
    for a session token.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM tokens WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


def generate_mfa_secret() -> str:
    # Generate a random 20-byte secret and return it in Base32 form
    # (compatible with common authenticator apps such as Google Authenticator
    # and Okta Verify). Padding is removed for compactness.
    """Generate a new 20-byte Base32-encoded secret for TOTP enrollment.

    The returned string is compatible with common authenticator apps.
    """
    raw = secrets.token_bytes(20)
    secret = base64.b32encode(raw).decode("ascii").rstrip("=")
    return secret


def _normalize_base32(secret: str) -> bytes:
    # Prepare a base32 secret for decoding: remove spaces, uppercase it,
    # and add the necessary padding before decoding.
    clean = secret.strip().replace(" ", "").upper()
    padding = (8 - len(clean) % 8) % 8
    return base64.b32decode(clean + "=" * padding)


def totp(secret: str, for_time: float | None = None, interval: int = 30, digits: int = 6) -> str:
    # Standard TOTP algorithm (RFC 6238) implemented with HMAC-SHA1 and
    # a moving counter based on the current time. Returns a zero-padded
    # numeric string of `digits` length.
    """Compute the TOTP code for `secret` at `for_time` (or now).

    Implements RFC 6238 using HMAC-SHA1.
    """
    key = _normalize_base32(secret)
    counter = int((for_time or time.time()) // interval)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code_int % (10 ** digits)).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1, interval: int = 30, digits: int = 6) -> bool:
    # Verify the provided `code` against the TOTP value at the current
    # time and nearby time steps determined by `window`. This allows for
    # small clock skew between server and client devices.
    """Verify a TOTP `code` allowing for `window` steps of clock skew.

    Returns True when a matching code is found, False otherwise.
    """
    normalized = str(code).zfill(digits)
    for step in range(-window, window + 1):
        if totp(secret, time.time() + step * interval, interval, digits) == normalized:
            return True
    return False


def generate_otpauth_url(secret: str, username: str, issuer: str) -> str:
    # Return an otpauth URL that can be converted into a QR code by the
    # frontend. This URL follows the Key URI Format used by authenticator
    # apps so scanning the resulting QR will enroll the secret.
    label = urllib.parse.quote(f"{issuer}:{username}", safe="")
    issuer_enc = urllib.parse.quote(issuer, safe="")
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer_enc}&algorithm=SHA1&digits=6&period=30"


def set_mfa_secret(username: str, secret: str):
    """Store a generated MFA secret for `username` and disable MFA until verified.

    The function clears the `mfa_enabled` flag so the user must verify the
    secret before MFA becomes active.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET mfa_secret = ?, mfa_enabled = 0 WHERE username = ?", (secret, username))
        conn.commit()
    finally:
        conn.close()

    # When setting a new secret we explicitly clear `mfa_enabled` so the
    # user must verify the new secret before the service treats MFA as
    # enabled. This prevents accidentally enabling MFA with an unverified
    # secret.


def enable_mfa(username: str):
    """Mark a user's MFA as enabled.

    Called after successful verification of the TOTP during setup.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET mfa_enabled = 1 WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()


def disable_mfa(username: str):
    """Disable MFA for a user and remove any stored secret.

    Useful for admin-driven recovery flows in the demo.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET mfa_enabled = 0, mfa_secret = NULL WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()


def get_mfa_secret(username: str) -> str | None:
    """Retrieve the stored MFA secret for `username`, or None if missing."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT mfa_secret FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return row[0]


def get_user_role(username: str) -> str | None:
    """Return the role string for `username` (e.g. 'admin' or 'user')."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return row[0]


def is_admin(username: str) -> bool:
    """Convenience: True when the user has the 'admin' role."""
    return get_user_role(username) == "admin"


def ensure_mfa_secret(username: str) -> str:
    """Return an existing MFA secret for the user or create one.

    If no secret exists a new one is generated and stored (MFA remains
    disabled until verified).
    """
    secret = get_mfa_secret(username)
    if not secret:
        secret = generate_mfa_secret()
        set_mfa_secret(username, secret)
    return secret


def is_mfa_enabled(username: str) -> bool:
    """Return True if the user has MFA enabled in the database."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT mfa_enabled FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return bool(row[0])



def verify_user(username: str, password: str) -> bool:
    """Verify username/password against stored salted PBKDF2 hash."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    stored_hash, salt = row
    return stored_hash == _hash_password(password, salt)


def update_user(old_username: str, new_username: str | None = None, new_password: str | None = None):
    """Update a user's username and/or password.

    If `new_username` is provided the user's username and related token
    ownership are updated. If `new_password` is provided the password is
    rehashed and stored.
    """
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # change username if provided
        if new_username and new_username != old_username:
            cur.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
            # update token ownerships too
            cur.execute("UPDATE tokens SET username = ? WHERE username = ?", (new_username, old_username))

        # change password if provided
        if new_password:
            salt = secrets.token_hex(16)
            password_hash = _hash_password(new_password, salt)
            target_username = new_username or old_username
            cur.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (password_hash, salt, target_username))

        conn.commit()
    finally:
        conn.close()
