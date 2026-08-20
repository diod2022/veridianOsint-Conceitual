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

import glob
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.security import normalizar_cnpj, normalizar_cnj, validar_cnj

def _buscar_processo_em_caches_locais(cnj_formatado: str, cnj_digitos: str) -> Optional[dict]:
    """Varre os caches locais de CPFs/CNPJs e OABs buscando os detalhes do processo já baixado."""
    if not os.path.exists(CACHE_DIR):
        return None
        
    alvos_busca = {cnj_formatado, cnj_digitos}
    candidatos_encontrados = []
    
    for fpath in glob.glob(os.path.join(CACHE_DIR, "*.json")):
        fname = os.path.basename(fpath)
        if fname.startswith("processo_cnj_"):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                
            # 1. Verifica em BigDataCorp CPF/CNPJ (Result[0].Processes.Lawsuits)
            if isinstance(d, dict) and "Result" in d and len(d["Result"]) > 0:
                r0 = d["Result"][0]
                proc_obj = r0.get("Processes") or r0.get("Lawsuits") or {}
                if isinstance(proc_obj, dict):
                    lawsuits = proc_obj.get("Lawsuits") or []
                    for l in lawsuits:
                        num = str(l.get("Number") or l.get("LawsuitCNJ") or l.get("LawsuitCNJNumber") or "")
                        num_digitos = re.sub(r'\D', '', num)
                        if (num and num in alvos_busca) or (num_digitos and num_digitos == cnj_digitos and len(cnj_digitos) >= 10):
                            partes = l.get("Parties") or []
                            polo_ativo = "Não informado"
                            polo_passivo = "Não informado"
                            advs = []
                            for p in partes:
                                papel = str(p.get("Role") or p.get("Type") or "").upper()
                                nome_p = p.get("Name") or "Não informado"
                                if any(termo in papel for termo in ("ATIVO", "AUTOR", "REQUERENTE", "EXEQUENTE", "IMPETRANTE", "RECLAMANTE")):
                                    polo_ativo = nome_p
                                elif any(termo in papel for termo in ("PASSIVO", "REU", "RÉU", "REQUERIDO", "EXECUTADO", "IMPETRADO", "RECLAMADO")):
                                    polo_passivo = nome_p
                                for adv in (p.get("Lawyers") or []):
                                    adv_nome = adv.get("Name") or adv.get("Nome")
                                    adv_oab = adv.get("OAB") or adv.get("Oab") or ""
                                    if adv_nome:
                                        advs.append({"nome": adv_nome, "oab": adv_oab})
                                        
                            updates = l.get("Updates") or l.get("Steps") or []
                            ultimas_movs = [{"data": u.get("Date") or u.get("PublicationDate"), "conteudo": u.get("Description") or u.get("Content") or "Sem descrição"} for u in updates[:5]]
                            
                            candidatos_encontrados.append({
                                "status": "sucesso",
                                "numero_cnj": num or cnj_formatado,
                                "polo_ativo": polo_ativo,
                                "polo_passivo": polo_passivo,
                                "tribunal": l.get("Court") or l.get("CourtName") or l.get("CourtType") or "Não informado",
                                "data_inicio": l.get("DistributionDate") or l.get("StartDate") or "Não informada",
                                "total_movimentacoes": len(updates),
                                "advogados": advs,
                                "ultimas_movimentacoes": ultimas_movs,
                                "dados_brutos": l,
                                "origem_cache": fname,
                                "_score": 10 + (5 if polo_ativo != "Não informado" else 0) + len(advs)
                            })

            # 2. Verifica em Escavador OAB (items)
            if isinstance(d, dict) and "items" in d:
                for item in d.get("items", []):
                    num = str(item.get("numero_cnj") or "")
                    num_digitos = re.sub(r'\D', '', num)
                    if (num and num in alvos_busca) or (num_digitos and num_digitos == cnj_digitos and len(cnj_digitos) >= 10):
                        polo_ativo = item.get("titulo_polo_ativo") or "Não informado"
                        polo_passivo = item.get("titulo_polo_passivo") or "Não informado"
                        advs = []
                        
                        fontes = item.get("fontes") or []
                        for fonte in fontes:
                            for env in fonte.get("envolvidos", []):
                                p_polo = str(env.get("polo") or "").upper()
                                p_tipo = str(env.get("tipo") or "").upper()
                                if "ATIVO" in p_polo and polo_ativo == "Não informado":
                                    polo_ativo = env.get("nome") or polo_ativo
                                elif "PASSIVO" in p_polo and polo_passivo == "Não informado":
                                    polo_passivo = env.get("nome") or polo_passivo
                                if "ADVOGADO" in p_polo or "ADVOGADO" in p_tipo:
                                    adv_nome = env.get("nome")
                                    oabs = env.get("oabs") or []
                                    adv_oab = f"{oabs[0].get('numero')}/{oabs[0].get('uf')}" if oabs else ""
                                    if adv_nome and not any(a["nome"] == adv_nome for a in advs):
                                        advs.append({"nome": adv_nome, "oab": adv_oab})

                        candidatos_encontrados.append({
                            "status": "sucesso",
                            "numero_cnj": num or cnj_formatado,
                            "polo_ativo": polo_ativo,
                            "polo_passivo": polo_passivo,
                            "tribunal": (item.get("unidade_origem") or {}).get("tribunal_sigla") or item.get("tribunal") or "Não informado",
                            "data_inicio": item.get("data_inicio") or "Não informada",
                            "total_movimentacoes": item.get("quantidade_movimentacoes") or 0,
                            "advogados": advs,
                            "ultimas_movimentacoes": [],
                            "dados_brutos": item,
                            "origem_cache": fname,
                            "_score": 5 + (5 if polo_ativo != "Não informado" else 0) + len(advs)
                        })
        except Exception:
            continue
            
    if candidatos_encontrados:
        melhor = max(candidatos_encontrados, key=lambda x: x.get("_score", 0))
        melhor.pop("_score", None)
        salvar_cache_universal(f"processo_cnj_{cnj_digitos}", melhor)
        return melhor

    return None

@mcp.tool()
async def bigdata_consultar_processo(numero_processo: Union[str, int], dataset_code: str = "bdclawsuitbasicdata") -> dict:
    """
    Consulta os detalhes completos de um processo judicial a partir de seu número CNJ único.
    Retorna polos (ativo/passivo), advogados, OABs, tribunal e histórico de movimentações.
    
    Args:
        numero_processo: O número CNJ do processo (ex: '1415618-82.2026.8.12.0000').
        dataset_code: O código do dataset desejado (padrão 'bdclawsuitbasicdata').
    """
    cnj_formatado, cnj_digitos = normalizar_cnj(numero_processo)
    
    # 1. Tenta recuperar de cache pré-existente de processo
    chave_cache = f"processo_cnj_{cnj_digitos if len(cnj_digitos) >= 10 else re.sub(r'[^a-zA-Z0-9]', '_', str(numero_processo))}"
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    # 2. Varre caches locais de investigações anteriores (CPF, CNPJ, OAB)
    cache_local = _buscar_processo_em_caches_locais(cnj_formatado, cnj_digitos)
    if cache_local:
        return cache_local

    # 3. Tenta consultar via Escavador (especialista em processos por CNJ individual)
    res_escavador = await escavador.consultar_processo_cnj(numero_processo)
    if res_escavador.get("status") == "sucesso" or res_escavador.get("codigo_erro") == "CNJ_INVALIDO":
        return res_escavador
        
    # 4. Fallback para BigDataCorp
    res_bdc = await bigdatacorp.consultar_processo(numero_processo, dataset_code)
    if res_bdc.get("status") == "sucesso":
        return res_bdc
        
    # Se ambos falharem, retorna diagnóstico estruturado claro
    return res_escavador if res_escavador.get("status") == "erro" else res_bdc

