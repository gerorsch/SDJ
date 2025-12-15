# gunicorn_conf.py
import os

# ───────────────────────── Parâmetros base ─────────────────────────
cpu_count = os.cpu_count() or 4
# Regra prática: I/O-bound → N–2N workers. Pode sobrescrever com env.
workers = int(os.getenv("GUNICORN_WORKERS", str(min(2 * cpu_count, max(cpu_count, 4)))))
worker_class = "uvicorn.workers.UvicornWorker"
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8001")

# Timeouts generosos por causa de SSE e geração de sentença
timeout = int(os.getenv("GUNICORN_TIMEOUT", "1200"))           # 20 min máx por request longo
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL", "30"))   # tempo p/ encerrar com graça
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Logs
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")
accesslog = "-"
errorlog = "-"

# 🩺 Ciclagem de workers (evita vazamento de memória a longo prazo)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "2000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# ─────────────────────── Hooks do Gunicorn (mestre) ───────────────────────
# gunicorn_conf.py
def on_starting(server):
    import asyncio
    from preprocessing.sentence_indexing_rag import setup_elasticsearch
    from services.auth import ensure_auth_schema

    print("🚀 EXECUTANDO SETUP ÚNICO NO PROCESSO MESTRE...")
    try:
        setup_elasticsearch()
        asyncio.run(ensure_auth_schema())
    except Exception as e:
        print(f"❌ Falha no setup: {e}")
    print("✅ SETUP ÚNICO CONCLUÍDO.")


# (Opcional) Mensagens quando os workers sobem — bom para depuração
def post_fork(server, worker):
    print(f"👶 Worker PID={worker.pid} iniciado")

def pre_fork(server, worker):
    # ponto para limpar/fechar algo do mestre se precisasse (não é o caso)
    pass
