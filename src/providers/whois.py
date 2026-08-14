import os
import sys
import httpx
from typing import Optional, Dict, Any
from src.core.config import WHOIS_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

def _get_api_key() -> str:
    return os.environ.get("WHOIS_API_KEY") or os.environ.get("WHOISXML_API_KEY", "")

async def whois_consultar(target: str, ignore_raw_text: bool = True, hard_refresh: bool = False) -> dict:
    key = _get_api_key()
    if not key:
        return {"error": "WHOISXML_API_KEY não configurada no .env"}
        
    target_clean = target.strip()
    if "@" in target_clean:
        parts = target_clean.split("@")
        if len(parts) > 1:
            target_clean = parts[-1].strip()
            
    cache_id = target_clean.lower().replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
    chave_cache = f"whois_{cache_id}"
    
    if not hard_refresh:
        cache_hit = checar_cache_universal(chave_cache)
        if cache_hit:
            return cache_hit

    headers = {"Content-Type": "application/json"}
    payload = {
        "domainName": target_clean,
        "apiKey": key,
        "outputFormat": "JSON",
        "ignoreRawTexts": 1 if ignore_raw_text else 0,
        "_hardRefresh": 1 if hard_refresh else 0
    }
    
    async with get_semaphore("whois"):
        try:
            response = await resilient_request(
                "POST",
                "https://www.whoisxmlapi.com/whoisserver/WhoisService",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            dados = response.json()
            
            if isinstance(dados, dict) and "ErrorMessage" in dados:
                msg = dados["ErrorMessage"].get("msg", "Erro retornado pela API WhoisXML")
                return {"error": f"Erro retornado pela API WhoisXML: {msg}"}
                
            return salvar_cache_universal(chave_cache, dados)
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API WhoisXML", "detalhes": detalhes}
        except Exception as e:
            return {"error": f"Erro de rede ao consultar WhoisXML: {str(e)}"}
