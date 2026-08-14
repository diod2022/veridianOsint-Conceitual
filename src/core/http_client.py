import httpx
import asyncio
import contextlib
import sys
from typing import Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception

# Shared HTTPX client com connection pooling persistente
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=10.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
)

# Semáforos assíncronos por provedor para proteção contra excesso de concorrência / 429
_provider_semaphores: Dict[str, asyncio.Semaphore] = {
    "bigdata": asyncio.Semaphore(5),
    "csint": asyncio.Semaphore(5),
    "escavador": asyncio.Semaphore(3),
    "unitfour": asyncio.Semaphore(4),
    "social": asyncio.Semaphore(4),
    "lighthouse": asyncio.Semaphore(3),
    "whois": asyncio.Semaphore(5),
    "web": asyncio.Semaphore(5)
}

def get_semaphore(provider: str) -> asyncio.Semaphore:
    """Retorna o semáforo de taxa para o provedor solicitado."""
    return _provider_semaphores.get(provider, _provider_semaphores["web"])

def _is_transient_http_error(exception: BaseException) -> bool:
    """Identifica falhas de rede transitórias ou 429/5xx elegíveis para retry."""
    if isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in (429, 502, 503, 504)
    return False

@retry(
    retry=retry_if_exception(_is_transient_http_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=8, jitter=0.5),
    reraise=True
)
async def resilient_request(method: str, url: str, **kwargs) -> httpx.Response:
    """Executa requisição HTTP com connection pooling persistente e retentativas com jitter."""
    return await http_client.request(method, url, **kwargs)

@contextlib.asynccontextmanager
async def server_lifespan(server):
    """Lifespan do FastMCP para gerenciamento limpo do pool HTTP."""
    print("[MCP] Servidor 'veridianOsint-Conceitual' iniciado com pool de conexões e resiliência ativas.", file=sys.stderr, flush=True)
    try:
        yield
    finally:
        print("[MCP] Fechando conexões do pool HTTP de forma limpa...", file=sys.stderr, flush=True)
        await http_client.aclose()
