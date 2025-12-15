# database/postgres.py
import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

# Permite DSN completo (opcional) ou variáveis separadas
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

async def init_postgres_pool():
    """Chamar no startup do FastAPI (cada worker cria seu próprio pool)."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_dsn_from_env(),
            min_size=int(os.getenv("PGPOOL_MIN", "1")),
            max_size=int(os.getenv("PGPOOL_MAX", "5")),
            max_inactive_connection_lifetime=float(os.getenv("PGPOOL_IDLE", "300")),
            statement_cache_size=int(os.getenv("PG_STMT_CACHE", "1000")),
        )

async def close_postgres_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def acquire_conn() -> asyncpg.Connection:
    """Pega uma conexão do pool (lembre de dar release)."""
    if _pool is None:
        await init_postgres_pool()
    return await _pool.acquire()

async def release_conn(conn: asyncpg.Connection):
    if _pool is not None and conn is not None:
        await _pool.release(conn)

# # Compat: se você quiser manter a assinatura antiga,
# # pode expor um helper com 'async with':
# class _ConnCtx:
#     def __init__(self, pool): self.pool = pool
#     async def __aenter__(self):
#         if self.pool is None:
#             await init_postgres_pool()
#         return await _pool.acquire()
#     async def __aexit__(self, exc_type, exc, tb):
#         await _pool.release(self.conn)  # noqa

# # Mantém a função antiga como alias para facilitar migração
# # (mas recomendo usar acquire/release diretamente)
# async def get_postgres_conn():
#     return await acquire_conn()
