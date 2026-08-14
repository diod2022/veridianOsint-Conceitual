import os
import urllib.parse
import httpx
from typing import Optional, Dict, Any
from src.core.config import HARVEST_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

def _get_token() -> str:
    return os.environ.get("HARVEST_API_KEY") or os.environ.get("HARVEST_API_TOKEN", "")

def _get_headers() -> dict:
    return {
        "X-API-Key": _get_token(),
        "Accept": "application/json"
    }

async def buscar_perfil(linkedin_url: str) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    parsed_url = urllib.parse.urlparse(linkedin_url)
    perfil_id = parsed_url.path.strip("/").split("/")[-1] if "/" in parsed_url.path else "alvo"
    cache_key = f"li_perfil_{perfil_id}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/profile",
                headers=_get_headers(),
                params={"url": linkedin_url}
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro na Harvest API (buscar perfil do LinkedIn): {str(e)}"}

async def consultar_endpoint(endpoint_name: str, target_url: str) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    endpoint = f"https://api.harvest-api.com/linkedin/{endpoint_name}"
    cache_id = f"li_endpoint_{endpoint_name.replace('/', '_')}"
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                endpoint,
                headers=_get_headers(),
                params={"url": target_url}
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_id, response.json())
        except Exception as e:
            return {"error": f"Erro na Harvest API ({endpoint_name}): {str(e)}"}

async def buscar_pessoas_por_nome(nome_completo: str, nome: Optional[str] = None, sobrenome: Optional[str] = None) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    params = {"search": nome_completo}
    if nome: params["firstName"] = nome
    if sobrenome: params["lastName"] = sobrenome
    
    cache_key = f"li_search_{nome_completo.replace(' ', '_')}"
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/profile-search",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro na Harvest API (buscar pessoas por nome): {str(e)}"}

async def ver_comentarios_post(post_url: str, sort_by: str = "relevance", page: int = 1) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    parsed = urllib.parse.urlparse(post_url)
    post_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "post"
    cache_key = f"li_post_comments_{post_id}_p{page}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    params = {"post": post_url, "sortBy": sort_by, "page": page}
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/post-comments",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar comentários do post na Harvest API: {str(e)}"}

async def ver_reacoes_post(post_url: str, page: int = 1) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    parsed = urllib.parse.urlparse(post_url)
    post_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "post"
    cache_key = f"li_post_reactions_{post_id}_p{page}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    params = {"post": post_url, "page": page}
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/post-reactions",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar reações do post na Harvest API: {str(e)}"}

async def buscar_posts(termo_busca: str, profile_url: Optional[str] = None, company_url: Optional[str] = None, posted_limit: Optional[str] = None, page: int = 1) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    params = {"search": termo_busca, "page": page}
    if profile_url: params["profile"] = profile_url
    if company_url: params["company"] = company_url
    if posted_limit: params["postedLimit"] = posted_limit
    
    termo_limpo = termo_busca.replace(" ", "_").replace("\"", "")
    cache_key = f"li_post_search_{termo_limpo}_p{page}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/post-search",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar posts na Harvest API: {str(e)}"}

async def ver_posts_usuario(profile_url: str, posted_limit: Optional[str] = None, page: int = 1) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    parsed = urllib.parse.urlparse(profile_url)
    perfil_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "alvo"
    cache_key = f"li_user_posts_{perfil_id}_p{page}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    params = {"profile": profile_url, "page": page}
    if posted_limit: params["postedLimit"] = posted_limit
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/profile-posts",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar posts do perfil na Harvest API: {str(e)}"}

async def buscar_email_perfil(profile_url: str, skip_smtp: bool = False) -> dict:
    token = _get_token()
    if not token:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    parsed = urllib.parse.urlparse(profile_url)
    perfil_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "alvo"
    cache_key = f"li_email_{perfil_id}"
    
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    params = {"url": profile_url, "findEmail": "true"}
    if skip_smtp: params["skipSmtp"] = "true"
    
    async with get_semaphore("social"):
        try:
            response = await resilient_request(
                "GET",
                "https://api.harvest-api.com/linkedin/profile",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(cache_key, response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar e-mail do perfil no LinkedIn: {str(e)}"}
