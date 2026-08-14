import os
import sys
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import CSINT_API_KEY
from src.core.http_client import resilient_request, get_semaphore
from src.core.cache import checar_cache_universal, salvar_cache_universal

CSINT_BASE_URL = "https://csint.pro/api"

async def consultar_ip(ip: str) -> dict:
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with get_semaphore("csint"):
        try:
            response = await resilient_request(
                "POST",
                f"{CSINT_BASE_URL}/iplookup",
                headers=headers,
                json={"ip": ip}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except Exception as e:
            return {"error": f"Erro ao consultar IP no CSINT: {str(e)}"}

async def busca_universal(query: Union[str, int], tipo: str = "auto") -> dict:
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    query_str = str(query).strip()
    cache_id = query_str.replace('@', '').replace('.', '').replace('+', '').replace('-', '').replace(' ', '')
    chave_cache = f"csint_busca_{cache_id}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with get_semaphore("csint"):
        try:
            response = await resilient_request(
                "POST",
                f"{CSINT_BASE_URL}/search",
                headers=headers,
                json={"query": query_str, "type": tipo}
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except Exception as e:
            return {"error": f"Erro na busca universal CSINT: {str(e)}"}

async def consultar_telefone(telefone: Union[str, int]) -> dict:
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    tel_str = str(telefone).strip()
    cache_id = tel_str.replace('+', '').replace('-', '').replace(' ', '')
    chave_cache = f"csint_seon_phone_{cache_id}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with get_semaphore("csint"):
        try:
            response = await resilient_request(
                "POST",
                f"{CSINT_BASE_URL}/seon/phone",
                headers=headers,
                json={"phone": tel_str}
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except Exception as e:
            return {"error": f"Erro ao consultar telefone no CSINT: {str(e)}"}

async def consultar_email(email: Union[str, int]) -> dict:
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    email_str = str(email).strip()
    cache_id = email_str.replace("@", "_at_").replace(".", "_").replace("+", "").replace("-", "")
    chave_cache = f"csint_seon_email_{cache_id}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with get_semaphore("csint"):
        try:
            response = await resilient_request(
                "POST",
                f"{CSINT_BASE_URL}/seon/email",
                headers=headers,
                json={"email": email_str}
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except Exception as e:
            return {"error": f"Erro ao consultar e-mail no CSINT: {str(e)}"}
