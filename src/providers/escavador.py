import os
import sys
import re
import asyncio
import urllib.parse
import httpx
from typing import Union, Optional, Dict, Any, Set
from src.core.config import ESCAVADOR_API_KEY
from src.core.cache import checar_cache_universal, salvar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

_oab_bg_tasks: Set[str] = set()

def _get_token() -> str:
    return os.environ.get("ESCAVADOR_API_KEY") or os.environ.get("ESCAVADOR_API_TOKEN", "")

async def _background_fetch_all_pages(
    oab_num: str,
    oab_est: str,
    oab_tipo: str,
    max_paginas: int,
    chave_cache: str,
    initial_items: list = None,
    first_next_url: str = None,
    first_page_data: dict = None
):
    token = _get_token()
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json"
        }
        base_params = {"oab_numero": oab_num, "oab_estado": oab_est, "oab_tipo": oab_tipo}
        
        todos_items = list(initial_items) if initial_items else []
        dados_finais = dict(first_page_data) if first_page_data else None
        next_url = first_next_url
        
        if not initial_items:
            async with get_semaphore("escavador"):
                resp = await resilient_request(
                    "GET",
                    "https://api.escavador.com/api/v2/advogado/processos",
                    headers=headers,
                    params=base_params
                )
            if resp.status_code != 200:
                return
            dados_finais = resp.json()
            todos_items.extend(dados_finais.get("items", []))
            next_url = (dados_finais.get("links") or {}).get("next")
        
        pagina = 1
        while next_url and pagina < max_paginas:
            parsed = urllib.parse.urlparse(next_url)
            qp = urllib.parse.parse_qs(parsed.query)
            params_next = dict(base_params)
            if "cursor" in qp:
                params_next["cursor"] = qp["cursor"][0]
            if "li" in qp:
                params_next["li"] = qp["li"][0]
            
            try:
                async with get_semaphore("escavador"):
                    resp = await resilient_request(
                        "GET",
                        "https://api.escavador.com/api/v2/advogado/processos",
                        headers=headers,
                        params=params_next
                    )
            except Exception:
                break
                
            if resp.status_code != 200:
                break
            dados_pag = resp.json()
            items_pag = dados_pag.get("items", [])
            if not items_pag:
                next_url = None
                break
            todos_items.extend(items_pag)
            next_url = (dados_pag.get("links") or {}).get("next")
            pagina += 1
            await asyncio.sleep(0.3)
        
        if dados_finais is None:
            dados_finais = {}
        dados_finais["items"] = todos_items
        dados_finais["_paginacao_em_andamento"] = False
        if "links" not in dados_finais:
            dados_finais["links"] = {}
        dados_finais["links"]["next"] = next_url
        salvar_cache_universal(chave_cache, dados_finais)
    except Exception as e:
        print(f"[ESCAVADOR BG ERROR] {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
    finally:
        _oab_bg_tasks.discard(chave_cache)

async def buscar_processos_oab(
    oab_numero: Union[str, int],
    oab_estado: str = "",
    oab_tipo: str = "ADVOGADO",
    max_paginas: int = 50,
    ignore_cache: bool = False
) -> dict:
    token = _get_token()
    if not token:
        return {"error": "ESCAVADOR_API_KEY não configurada no .env"}
        
    raw_str = f"{oab_numero} {oab_estado}".strip().upper()
    uf_match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', raw_str)
    oab_est_clean = uf_match.group(1) if uf_match else str(oab_estado).strip().upper()
    
    num_match = re.search(r'\b(\d{1,7})\b', raw_str)
    oab_num_clean = num_match.group(1) if num_match else re.sub(r'\D', '', str(oab_numero))
    oab_tipo_clean = oab_tipo.strip().upper() if oab_tipo else "ADVOGADO"
    
    if not oab_num_clean or not oab_est_clean:
        return {"error": "Número da OAB e Estado são obrigatórios (ex: oab_numero='7008', oab_estado='MS')."}
        
    cache_id = f"oab_{oab_est_clean.lower()}_{oab_num_clean.lower()}"
    chave_cache = f"escavador_{cache_id}"
    
    if not ignore_cache:
        cache_hit = checar_cache_universal(chave_cache)
        if cache_hit:
            if cache_hit.get("_paginacao_em_andamento") and chave_cache not in _oab_bg_tasks:
                _oab_bg_tasks.add(chave_cache)
                asyncio.create_task(_background_fetch_all_pages(
                    oab_num_clean, oab_est_clean, oab_tipo_clean, max_paginas, chave_cache
                ))
            return cache_hit

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }
    params = {
        "oab_numero": oab_num_clean,
        "oab_estado": oab_est_clean,
        "oab_tipo": oab_tipo_clean
    }
    
    try:
        async with get_semaphore("escavador"):
            response = await resilient_request(
                "GET",
                "https://api.escavador.com/api/v2/advogado/processos",
                headers=headers,
                params=params
            )
    except Exception as e:
        if chave_cache not in _oab_bg_tasks:
            _oab_bg_tasks.add(chave_cache)
            asyncio.create_task(_background_fetch_all_pages(oab_num_clean, oab_est_clean, oab_tipo_clean, max_paginas, chave_cache))
        return {
            "status": "processando_em_segundo_plano",
            "_paginacao_em_andamento": True,
            "cache_id": chave_cache,
            "mensagem": "A API do Escavador demorou para responder. A busca foi iniciada em segundo plano.",
            "instrucao": f"AGUARDE DE 30 A 60 SEGUNDOS e chame novamente esta ferramenta ou 'investigador_ler_cache' com cache_id='{chave_cache}'."
        }
    
    if response.status_code != 200:
        try:
            detalhes = response.json()
        except Exception:
            detalhes = response.text
        return {"error": f"API do Escavador retornou status {response.status_code}", "detalhes": detalhes}
    
    dados_p1 = response.json()
    items_p1 = dados_p1.get("items", [])
    next_url = (dados_p1.get("links") or {}).get("next")
    
    if next_url and max_paginas > 1:
        if chave_cache not in _oab_bg_tasks:
            _oab_bg_tasks.add(chave_cache)
            asyncio.create_task(_background_fetch_all_pages(
                oab_num_clean, oab_est_clean, oab_tipo_clean, max_paginas, chave_cache,
                initial_items=items_p1, first_next_url=next_url, first_page_data=dados_p1
            ))
        
        return salvar_cache_universal(chave_cache, {
            **dados_p1,
            "_paginacao_em_andamento": True,
            "_instrucao_paginacao": (
                f"Retornando os primeiros {len(items_p1)} processos da OAB {oab_num_clean}/{oab_est_clean}. "
                f"O download de TODAS as páginas foi iniciado em segundo plano no servidor. "
                f"AGUARDE DE 30 A 60 SEGUNDOS e chame novamente esta ferramenta (sem ignore_cache) "
                f"ou 'investigador_ler_cache' com cache_id='{chave_cache}' para obter o resultado completo."
            )
        })
    else:
        return salvar_cache_universal(chave_cache, dados_p1)
