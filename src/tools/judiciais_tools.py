import os
import re
import json
from typing import Union, Optional
from src.app import mcp
from src.core.config import CACHE_DIR
from src.core.security import normalizar_cnpj
from src.providers import escavador, bigdatacorp, dossie_builder

@mcp.tool()
async def escavador_buscar_processos_oab(
    oab_numero: Union[str, int], 
    oab_estado: str = "", 
    oab_tipo: str = "ADVOGADO",
    max_paginas: int = 50,
    ignore_cache: bool = False
) -> dict:
    """
    ATENÇÃO: Esta é a ÚNICA ferramenta para consultar processos judiciais de um advogado por NÚMERO DE OAB e ESTADO (UF).
    NÃO use ferramentas de BigDataCorp/CPF para busca por OAB. Use esta ferramenta.
    
    Busca processos de um advogado a partir da OAB (API Escavador / Veridian).
    
    Args:
        oab_numero: Número da OAB (ex: 7008, '5485', '7008/MS' ou 'OAB/MS 7008').
        oab_estado: Sigla do Estado da OAB (ex: 'MS', 'SP', 'RJ'). Opcional se informado junto ao número.
        oab_tipo: Tipo de inscrição OAB (opcional, padrão 'ADVOGADO').
        max_paginas: Máximo de páginas a baixar (cada página = 20 processos, padrão 50 = até 1000 processos).
        ignore_cache: Se True, força nova busca na API ignorando o cache.
    """
    return await escavador.buscar_processos_oab(oab_numero, oab_estado, oab_tipo, max_paginas, ignore_cache)

@mcp.tool()
async def bigdata_consultar_processo(numero_processo: Union[str, int], dataset_code: str = "bdclawsuitbasicdata") -> dict:
    """
    Consulta os detalhes completos de um processo judicial a partir de seu número CNJ único.
    
    Args:
        numero_processo: O número CNJ do processo (ex: '1415618-82.2026.8.12.0000').
        dataset_code: O código do dataset desejado (padrão 'bdclawsuitbasicdata').
    """
    return await bigdatacorp.consultar_processo(numero_processo, dataset_code)

@mcp.tool()
async def bigdata_cnpj_alteracoes(cnpj: Union[str, int]) -> dict:
    """
    Consulta as ALTERAÇÕES HISTÓRICAS de um CNPJ na BigDataCorp (datasets de evolução e
    histórico cadastral) e retorna uma TIMELINE cronológica das mudanças: razão social,
    situação cadastral, capital social, natureza jurídica, endereço, nº de funcionários, etc.

    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    cnpj_limpo = normalizar_cnpj(cnpj)
    dados = await bigdatacorp.consultar_cnpj(cnpj_limpo, datasets="bdccompanyevolution,bdccompanyhistorical")
    if isinstance(dados, dict) and dados.get("error"):
        return dados

    # Lê cache para construir a timeline detalhada
    chave_cache = f"bigdata_cnpj_{cnpj_limpo}"
    cache_path = os.path.join(CACHE_DIR, f"{chave_cache}.json")
    if not os.path.exists(cache_path):
        return {"error": f"Dados brutos não encontrados para timeline do CNPJ {cnpj_limpo}"}

    with open(cache_path, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)

    nome = ""
    try:
        r0 = (dados_brutos.get("Result") or [{}])[0]
        nome = (r0.get("BasicData") or {}).get("OfficialName") or ""
    except Exception:
        pass

    timeline = dossie_builder.construir_timeline_cnpj(dados_brutos)
    md = dossie_builder.timeline_para_markdown(cnpj_limpo, nome, timeline)

    try:
        with open(os.path.join(CACHE_DIR, f"timeline_cnpj_{cnpj_limpo}.md"), "w", encoding="utf-8") as f:
            f.write(md)
    except Exception:
        pass

    return {
        "status": "sucesso",
        "cnpj": cnpj_limpo,
        "nome": nome,
        "total_alteracoes": len(timeline),
        "timeline": timeline,
        "timeline_markdown": md,
    }
