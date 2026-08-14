import os
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import HIKER_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

HIKER_BASE_URL = "https://api.hikerapi.com"

def _get_token() -> str:
    return os.environ.get("HIKER_API_KEY") or os.environ.get("HIKER_API_TOKEN", "")

def _get_headers() -> dict:
    return {
        "x-access-key": _get_token(),
        "Accept": "application/json"
    }

async def buscar_usuario(username: str) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    usr = username.strip().lstrip("@")
    cache_hit = checar_cache_universal(f"ig_user_{usr}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{HIKER_BASE_URL}/v2/user/by/username",
                headers=_get_headers(),
                params={"username": usr}
            )
            response.raise_for_status()
            return salvar_cache_universal(f"ig_user_{usr}", response.json())
        except Exception as e:
            return {"error": f"Erro na HikerAPI (buscar usuário): {str(e)}"}

async def pesquisar_perfis(query: str) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    q = query.strip()
    cache_key = f"ig_search_{q.replace(' ', '_')}"
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{HIKER_BASE_URL}/v2/fbsearch/accounts",
                headers=_get_headers(),
                params={"query": q}
            )
            response.raise_for_status()
            data = response.json()
            perfis = []
            lista_usuarios = data.get("users", []) if isinstance(data, dict) else data
            if not isinstance(lista_usuarios, list):
                lista_usuarios = []
                
            for user_wrapper in lista_usuarios:
                user = user_wrapper.get("user", {}) if isinstance(user_wrapper, dict) and "user" in user_wrapper else user_wrapper
                if not isinstance(user, dict):
                    continue
                perfis.append({
                    "username": user.get("username"),
                    "nome_completo": user.get("full_name"),
                    "user_id": user.get("pk") or user.get("pk_id"),
                    "is_private": user.get("is_private"),
                    "is_verified": user.get("is_verified"),
                    "profile_pic_url": user.get("profile_pic_url"),
                    "byline": user.get("byline")
                })
                
            resultado = {
                "termo_pesquisado": q,
                "total_resultados": len(perfis),
                "perfis": perfis
            }
            return salvar_cache_universal(cache_key, resultado)
        except Exception as e:
            return {"error": f"Erro na HikerAPI (pesquisa de contas): {str(e)}"}

async def ver_seguidores(
    user_id: Union[str, int],
    page_id: Optional[str] = None,
    tipo: str = "ambos",
    page_id_followers: Optional[str] = None,
    page_id_following: Optional[str] = None,
    cursor: Optional[str] = None,
    max_id: Optional[str] = None
) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    uid = str(user_id).strip()
    fol_cursor = page_id_followers or page_id or cursor or max_id
    fll_cursor = page_id_following or page_id or cursor or max_id
    tipo_normalizado = (tipo or "ambos").lower().strip()
    
    chave_cache = f"ig_followers_{uid}_{tipo_normalizado}_pfol_{fol_cursor or '1'}_pfll_{fll_cursor or '1'}"
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            resultado = {}
            if tipo_normalizado in ["ambos", "followers", "seguidores"]:
                params_fol = {"user_id": uid}
                if fol_cursor:
                    params_fol["page_id"] = str(fol_cursor)
                resp_fol = await resilient_request(
                    "GET",
                    f"{HIKER_BASE_URL}/v2/user/followers",
                    headers=_get_headers(),
                    params=params_fol
                )
                if resp_fol.status_code == 200:
                    resultado["followers"] = resp_fol.json()
            
            if tipo_normalizado in ["ambos", "following", "seguindo"]:
                params_fll = {"user_id": uid}
                if fll_cursor:
                    params_fll["page_id"] = str(fll_cursor)
                resp_fll = await resilient_request(
                    "GET",
                    f"{HIKER_BASE_URL}/v2/user/following",
                    headers=_get_headers(),
                    params=params_fll
                )
                if resp_fll.status_code == 200:
                    resultado["following"] = resp_fll.json()
                
            if not resultado:
                return {"error": "Falha ao obter seguidores e seguindo"}
                
            return salvar_cache_universal(chave_cache, resultado)
        except Exception as e:
            return {"error": f"Erro na HikerAPI (seguidores): {str(e)}"}

async def ver_posts(
    user_id: Union[str, int],
    page_id: Optional[str] = None,
    end_cursor: Optional[str] = None
) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    uid = str(user_id).strip()
    cursor_usado = end_cursor or page_id
    chave_cache = f"ig_posts_{uid}_p_{cursor_usado or '1'}"
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    params = {"user_id": uid}
    if cursor_usado:
        params["end_cursor"] = str(cursor_usado)
        
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{HIKER_BASE_URL}/v1/user/medias/chunk",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na HikerAPI (ver posts): {str(e)}"}

async def ver_stories(user_id: Union[str, int]) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    uid = str(user_id).strip()
    chave_cache = f"ig_stories_{uid}"
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                f"{HIKER_BASE_URL}/v2/user/stories",
                headers=_get_headers(),
                params={"user_id": uid}
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except Exception as e:
            return {"error": f"Erro na HikerAPI (ver stories): {str(e)}"}
