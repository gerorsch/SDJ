# auth.py
import os
import re
import smtplib
import ssl
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
import asyncpg

# 🚨 IMPORTANTE: agora usamos release_conn (pool)
from database.postgres import acquire_conn as get_postgres_conn, release_conn

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Configurações ---
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "240"))
JWT_ISSUER = os.getenv("JWT_ISSUER", "justino.api")
LOGIN_CODE_TTL_MIN = int(os.getenv("LOGIN_CODE_TTL_MIN", "10"))
LOGIN_CODE_LEN = int(os.getenv("LOGIN_CODE_LEN", "6"))
LOGIN_MIN_INTERVAL_SEC = int(os.getenv("LOGIN_MIN_INTERVAL_SEC", "60"))
ALLOWED_DOMAINS_STR = os.getenv("ALLOWED_EMAIL_DOMAINS", "tjpe.jus.br")
ALLOWED_DOMAINS = [domain.strip().lower() for domain in ALLOWED_DOMAINS_STR.split(',')]
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
APP_NAME = os.getenv("APP_NAME", "Justino")

# --- SQL para garantir o schema do DB ---
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS app_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_iat BIGINT DEFAULT 0
);
CREATE TABLE IF NOT EXISTS login_code (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    request_ip INET
);
CREATE INDEX IF NOT EXISTS login_code_user_idx ON login_code(user_id);
CREATE INDEX IF NOT EXISTS login_code_expires_idx ON login_code(expires_at);
"""

# async def ensure_auth_schema():
#     conn = await get_postgres_conn()
#     try:
#         await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
#         await conn.execute(CREATE_SQL)
#     finally:
#         await release_conn(conn)  # ← devolve ao pool
# no topo do arquivo
import asyncpg
import os

def _dsn_from_env() -> str:
    dsn = os.getenv("POSTGRES_DSN")
    if dsn:
        return dsn
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "rag_user")
    password = os.getenv("POSTGRES_PASSWORD", "rag_password")
    database = os.getenv("POSTGRES_DB", "rag_database")
    return f"postgres://{user}:{password}@{host}:{port}/{database}"

async def ensure_auth_schema():
    """⚠️ Usar APENAS conexão efêmera aqui (sem pool). Roda no mestre."""
    conn = await asyncpg.connect(dsn=_dsn_from_env())
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        await conn.execute(CREATE_SQL)
    finally:
        await conn.close()

# --- Funções Auxiliares ---

def _validate_allowed_email(email: str) -> str:
    email = email.strip().lower()
    if not any(email.endswith(f"@{domain}") for domain in ALLOWED_DOMAINS):
        allowed_domains_formatted = ", ".join([f"*@{d}" for d in ALLOWED_DOMAINS])
        raise HTTPException(status_code=400, detail=f"Domínio de e-mail não autorizado. Use: {allowed_domains_formatted}.")
    return email

async def _get_user_by_email(conn: asyncpg.Connection, email: str) -> Optional[asyncpg.Record]:
    return await conn.fetchrow(
        "SELECT id, last_login_iat FROM app_user WHERE email=$1 AND is_active=TRUE",
        email
    )

def _gen_code(n: int = LOGIN_CODE_LEN) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(n))

async def _recent_request_block(conn: asyncpg.Connection, user_id: str) -> bool:
    q = "SELECT created_at FROM login_code WHERE user_id=$1 ORDER BY created_at DESC LIMIT 1"
    row = await conn.fetchrow(q, user_id)
    if not row:
        return False
    delta = datetime.now(timezone.utc) - row["created_at"]
    return delta.total_seconds() < LOGIN_MIN_INTERVAL_SEC

async def _insert_login_code(conn: asyncpg.Connection, user_id: str, code: str, ip: Optional[str]) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=LOGIN_CODE_TTL_MIN)
    await conn.execute(
        "INSERT INTO login_code(user_id, code, expires_at, request_ip) VALUES ($1, $2, $3, $4)",
        user_id, code, expires_at, ip
    )

def _send_email_code(to_email: str, code: str):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"✅ [MODO DEV] Código para {to_email} é: {code}")
        return
    body = f"Seu código de acesso ao {APP_NAME} é: {code}\nEle expira em {LOGIN_CODE_TTL_MIN} minutos."
    msg = f"From: {MAIL_FROM}\r\nTo: {to_email}\r\nSubject: [{APP_NAME}] Código de acesso\r\n\r\n{body}".encode("utf-8")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(MAIL_FROM, [to_email], msg)
    except Exception as e:
        print(f"❌ Falha ao enviar e-mail para {to_email}. Erro: {e}")

def _issue_jwt(user_id: str, email: str, iat: int) -> str:
    payload = {
        "sub": user_id, "email": email, "iss": JWT_ISSUER,
        "iat": iat,
        "exp": iat + (JWT_EXPIRES_MIN * 60),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# --- Schemas ---
class RequestCodeIn(BaseModel):
    email: EmailStr

class VerifyCodeIn(BaseModel):
    email: EmailStr
    code: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Endpoints ---

@router.post("/request-code")
async def request_code(payload: RequestCodeIn, request: Request):
    email = _validate_allowed_email(payload.email)
    conn = await get_postgres_conn()
    try:
        user = await _get_user_by_email(conn, email)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não cadastrado no sistema.")

        user_id = str(user["id"])
        if await _recent_request_block(conn, user_id):
            raise HTTPException(status_code=429, detail="Aguarde antes de pedir outro código.")

        code = _gen_code()
        await _insert_login_code(conn, user_id, code, request.client.host if request.client else None)
        _send_email_code(email, code)
        return {"ok": True}
    finally:
        await release_conn(conn)  # ← devolve ao pool

@router.post("/verify-code", response_model=TokenOut)
async def verify_code(payload: VerifyCodeIn):
    email = _validate_allowed_email(payload.email)
    code = payload.code.strip()
    if not re.fullmatch(r"\d{" + str(LOGIN_CODE_LEN) + r"}", code):
        raise HTTPException(status_code=400, detail="Código inválido")

    conn = await get_postgres_conn()
    try:
        user = await _get_user_by_email(conn, email)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado.")
        user_id = str(user["id"])

        row = await conn.fetchrow(
            "SELECT id, expires_at, consumed_at FROM login_code "
            "WHERE user_id=$1 AND code=$2 ORDER BY created_at DESC LIMIT 1",
            user_id, code
        )
        if not row:
            raise HTTPException(status_code=400, detail="Código incorreto")
        if row["consumed_at"]:
            raise HTTPException(status_code=400, detail="Código já utilizado")
        if datetime.now(timezone.utc) > row["expires_at"]:
            raise HTTPException(status_code=400, detail="Código expirado")

        await conn.execute("UPDATE login_code SET consumed_at=now() WHERE id=$1", row["id"])

        # Invalida sessões antigas e cria a nova.
        iat = int(datetime.now(timezone.utc).timestamp())
        await conn.execute("UPDATE app_user SET last_login_iat = $1 WHERE id = $2", iat, user_id)

        token = _issue_jwt(user_id, email, iat)
        return TokenOut(access_token=token)
    finally:
        await release_conn(conn)  # ← devolve ao pool

# --- Dependência de Autenticação (para endpoints protegidos) ---
@router.get("/health")  # opcional: util para testes
async def health():
    return {"ok": True}

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Credenciais ausentes")
    token = authorization.split(" ", 1)[1]

    conn = await get_postgres_conn()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
        user_id = payload.get("sub")
        token_iat = payload.get("iat")
        if not user_id or not token_iat:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Verifica se o token é o mais recente gerado para o usuário.
        user = await conn.fetchrow("SELECT last_login_iat FROM app_user WHERE id = $1", user_id)
        if not user or user["last_login_iat"] > token_iat:
            raise HTTPException(status_code=401, detail="Sessão inválida. Por favor, faça login novamente.")

        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    finally:
        await release_conn(conn)  # ← devolve ao pool
