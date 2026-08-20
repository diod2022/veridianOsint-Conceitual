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

async def consultar_processo_cnj(numero_cnj: Union[str, int]) -> dict:
    """
    Consulta os detalhes completos de um processo judicial por número CNJ na API Escavador v2.
    Retorna polos (ativo/passivo), advogados, OABs, tribunal e histórico de movimentações.
    """
    from src.core.security import normalizar_cnj, validar_cnj
    
    cnj_formatado, cnj_digitos = normalizar_cnj(numero_cnj)
    
    # Se tiver 20 dígitos, valida o DV matematicamente
    if len(cnj_digitos) == 20 and not validar_cnj(cnj_digitos):
        return {
            "status": "erro",
            "codigo_erro": "CNJ_INVALIDO",
            "etapa": "validacao_local",
            "fornecedor": "Veridian",
            "mensagem": f"Número CNJ '{numero_cnj}' é matematicamente inválido (dígitos verificadores incorretos segundo a Resolução CNJ nº 65/2008).",
            "retentavel": False,
            "detalhes": {"cnj_informado": str(numero_cnj)}
        }
        
    chave_cache = f"processo_cnj_{cnj_digitos if len(cnj_digitos) >= 10 else re.sub(r'[^a-zA-Z0-9]', '_', str(numero_cnj))}"
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    token = _get_token()
    if not token:
        return {
            "status": "erro",
            "codigo_erro": "CREDENCIAIS_AUSENTES",
            "etapa": "autenticacao",
            "fornecedor": "Escavador",
            "mensagem": "Chave ESCAVADOR_API_KEY não configurada no .env para consulta processual por CNJ.",
            "retentavel": False
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }

    # Tenta consultar pelo CNJ formatado e se 404 pelo CNJ puro
    cnj_busca = cnj_formatado if len(cnj_digitos) == 20 else str(numero_cnj).strip()
    url = f"https://api.escavador.com/api/v2/processos/numero_cnj/{urllib.parse.quote(cnj_busca)}"

    try:
        async with get_semaphore("escavador"):
            response = await resilient_request("GET", url, headers=headers)
    except Exception as e:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_CONEXAO",
            "etapa": "requisicao_api",
            "fornecedor": "Escavador",
            "mensagem": f"Falha de conexão com a API do Escavador: {str(e)}",
            "retentavel": True
        }

    if response.status_code == 404:
        # Se 404 com CNJ formatado, tenta com apenas dígitos
        if cnj_busca != cnj_digitos and len(cnj_digitos) == 20:
            url_alt = f"https://api.escavador.com/api/v2/processos/numero_cnj/{urllib.parse.quote(cnj_digitos)}"
            try:
                async with get_semaphore("escavador"):
                    resp_alt = await resilient_request("GET", url_alt, headers=headers)
                    if resp_alt.status_code == 200:
                        response = resp_alt
                        cnj_busca = cnj_digitos
            except Exception:
                pass

    if response.status_code == 404:
        return {
            "status": "sem_resultados",
            "codigo_erro": "PROCESSO_NAO_ENCONTRADO",
            "fornecedor": "Escavador",
            "mensagem": f"Processo CNJ {cnj_busca} não foi encontrado na base de dados.",
            "detalhes": {"numero_cnj": cnj_busca}
        }

    if response.status_code == 403:
        # Segredo de Justiça
        return {
            "status": "sucesso",
            "segredo_de_justica": True,
            "numero_cnj": cnj_busca,
            "mensagem": "Processo localizado, porém tramita em SEGREDO DE JUSTIÇA (acesso restrito aos autos).",
            "cache_id": chave_cache
        }

    if response.status_code != 200:
        return {
            "status": "erro",
            "codigo_erro": f"ESCAVADOR_HTTP_{response.status_code}",
            "etapa": "requisicao_api",
            "fornecedor": "Escavador",
            "mensagem": f"Erro na consulta à API Escavador: HTTP {response.status_code}",
            "detalhes": response.text
        }

    dados = response.json()
    
    # Extrai resumo estruturado
    partes = dados.get("partes") or []
    polo_ativo = dados.get("titulo_polo_ativo") or "Não informado"
    polo_passivo = dados.get("titulo_polo_passivo") or "Não informado"
    
    advogados_encontrados = []
    for parte in partes:
        for adv in (parte.get("advogados") or []):
            adv_nome = adv.get("nome")
            adv_oab = adv.get("oab") or f"{adv.get('oab_numero', '')}/{adv.get('oab_estado', '')}".strip("/")
            if adv_nome:
                advogados_encontrados.append({"nome": adv_nome, "oab": adv_oab})

    movimentacoes = dados.get("movimentacoes") or []
    ultimas_movs = []
    for m in movimentacoes[:5]:
        ultimas_movs.append({
            "data": m.get("data"),
            "conteudo": m.get("conteudo") or m.get("texto") or "Sem descrição"
        })

    dados_enriquecidos = {
        "status": "sucesso",
        "numero_cnj": dados.get("numero_cnj") or cnj_busca,
        "polo_ativo": polo_ativo,
        "polo_passivo": polo_passivo,
        "tribunal": (dados.get("unidade_origem") or {}).get("tribunal_sigla") or dados.get("tribunal") or "Não informado",
        "data_inicio": dados.get("data_inicio") or "Não informada",
        "total_movimentacoes": len(movimentacoes),
        "advogados": advogados_encontrados,
        "ultimas_movimentacoes": ultimas_movs,
        "dados_brutos": dados,
        "cache_id": chave_cache
    }

    return salvar_cache_universal(chave_cache, dados_enriquecidos)

