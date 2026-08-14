import os
import hashlib
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import SOCIAVAULT_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

SOCIAVAULT_BASE_URL = "https://api.sociavault.com"

def _get_headers() -> dict:
    key = os.environ.get("SOCIAVAULT_API_KEY", "")
    return {
        "X-API-Key": key,
        "Accept": "application/json"
    }

async def buscar_perfil(handle: str) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    chave_cache = f"tiktok_profile_{handle_limpo}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/profile",
                headers=_get_headers(),
                params={"handle": handle_limpo}
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (perfil): {str(e)}"}

async def listar_videos(handle: str, user_id: Optional[Union[str, int]] = None, sort_by: str = "latest", max_cursor: Optional[str] = None, trim: bool = False) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    cursor_str = max_cursor or "initial"
    trim_str = "trimmed" if trim else "full"
    chave_cache = f"tiktok_videos_{handle_limpo}_{sort_by}_{cursor_str}_{trim_str}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {
        "handle": handle_limpo,
        "sort_by": sort_by,
        "trim": str(trim).lower()
    }
    if user_id: params["user_id"] = str(user_id)
    if max_cursor: params["max_cursor"] = str(max_cursor)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/videos",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (vídeos): {str(e)}"}

async def listar_comentarios(url: str, cursor: Optional[int] = None, trim: bool = False) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    url_limpa = url.split("?")[0].strip()
    url_hash = hashlib.md5(url_limpa.encode("utf-8")).hexdigest()
    trim_str = "trimmed" if trim else "full"
    chave_cache = f"tiktok_comments_{url_hash}_{cursor or 0}_{trim_str}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"url": url_limpa, "trim": str(trim).lower()}
    if cursor is not None: params["cursor"] = str(cursor)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/comments",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (comentários): {str(e)}"}

async def listar_respostas_comentario(comment_id: str, url: str, cursor: Optional[int] = None) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    comment_id_str = str(comment_id).strip()
    chave_cache = f"tiktok_comment_replies_{comment_id_str}_{cursor or 0}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"comment_id": comment_id_str, "url": url.split("?")[0].strip()}
    if cursor is not None: params["cursor"] = str(cursor)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/comment-replies",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (respostas de comentário): {str(e)}"}

async def listar_seguindo(handle: str, min_time: Optional[int] = None, trim: bool = False) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    chave_cache = f"tiktok_following_{handle_limpo}_{min_time or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"handle": handle_limpo, "trim": str(trim).lower()}
    if min_time is not None: params["min_time"] = str(min_time)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/following",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (seguindo): {str(e)}"}

async def listar_seguidores(handle: Optional[str] = None, user_id: Optional[Union[str, int]] = None, min_time: Optional[int] = None, trim: bool = False) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    if not handle and not user_id:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'handle' ou 'user_id'."}
        
    identificador = (handle.strip().replace("@", "")) if handle else str(user_id)
    chave_cache = f"tiktok_followers_{identificador}_{min_time or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"trim": str(trim).lower()}
    if handle: params["handle"] = handle.strip().replace("@", "")
    if user_id: params["user_id"] = str(user_id)
    if min_time is not None: params["min_time"] = str(min_time)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/followers",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (seguidores): {str(e)}"}

async def buscar_usuarios(query: str, cursor: Optional[int] = None, trim: bool = False) -> dict:
    if not os.environ.get("SOCIAVAULT_API_KEY"):
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    query_limpa = query.strip()
    query_cache = query_limpa.replace(" ", "_")
    chave_cache = f"tiktok_search_{query_cache}_{cursor or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"query": query_limpa, "trim": str(trim).lower()}
    if cursor is not None: params["cursor"] = str(cursor)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/search/users",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na API SociaVault (buscar usuários): {str(e)}"}
