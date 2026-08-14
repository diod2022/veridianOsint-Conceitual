import os
import json
import glob
import re
import sys
from typing import Optional, Any
from src.core.config import CACHE_DIR
from src.core.security import validar_caminho_seguro

def obter_caminho_cache_seguro(cache_id: str) -> Optional[str]:
    """
    Sanitiza o cache_id e resolve o caminho absoluto, garantindo que o arquivo
    esteja estritamente dentro do diretório de cache (evita Path Traversal).
    Oferece busca resiliente para variações de nomes (ex: escavador_oab_7008_MS -> escavador_oab_ms_7008).
    Retorna None se o caminho for inválido ou tentar sair do CACHE_DIR.
    """
    if not cache_id:
        return None
        
    if "/" in cache_id or "\\" in cache_id or ".." in cache_id:
        return None
        
    cache_id_seguro = os.path.basename(cache_id).strip()
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return None
        
    caminho_absoluto = os.path.abspath(os.path.join(CACHE_DIR, f"{cache_id_seguro}.json"))
    caminho_limite = os.path.abspath(CACHE_DIR)
    
    if os.path.exists(caminho_absoluto) and validar_caminho_seguro(caminho_limite, caminho_absoluto):
        return caminho_absoluto

    # Busca resiliente para variações de OAB / cache IDs informados por LLMs
    raw_upper = cache_id_seguro.upper()
    uf_match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', raw_upper)
    num_match = re.search(r'\b(\d{1,7})\b', raw_upper)
    
    if uf_match and num_match:
        uf = uf_match.group(1).lower()
        num = num_match.group(1).lower()
        resiliente_path = os.path.abspath(os.path.join(CACHE_DIR, f"escavador_oab_{uf}_{num}.json"))
        if os.path.exists(resiliente_path) and validar_caminho_seguro(caminho_limite, resiliente_path):
            return resiliente_path

    # Fallback genérico por palavra-chave se não encontrou exato
    keywords = [k.lower() for k in re.split(r'[\s_\-\/]+', cache_id_seguro) if k and k.lower() not in ['advogado', 'oab', 'json']]
    if keywords:
        for f in glob.glob(os.path.join(CACHE_DIR, "*.json")):
            fname = os.path.basename(f).lower()
            if all(kw in fname for kw in keywords):
                caminho_candidato = os.path.abspath(f)
                if validar_caminho_seguro(caminho_limite, caminho_candidato):
                    return caminho_candidato
                
    if caminho_absoluto.startswith(caminho_limite):
        return caminho_absoluto
    return None

def obter_caminho_cache_seguro_ext(cache_id: str, ext: str = ".json") -> Optional[str]:
    """
    Sanitiza o cache_id e resolve o caminho absoluto com a extensão informada,
    garantindo que o arquivo esteja estritamente dentro do diretório de cache.
    """
    if not cache_id:
        return None
        
    if "/" in cache_id or "\\" in cache_id or ".." in cache_id:
        return None
        
    cache_id_seguro = os.path.basename(cache_id).strip()
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return None
        
    caminho_absoluto = os.path.abspath(os.path.join(CACHE_DIR, f"{cache_id_seguro}{ext}"))
    caminho_limite = os.path.abspath(CACHE_DIR)
    
    if os.path.exists(caminho_absoluto) and validar_caminho_seguro(caminho_limite, caminho_absoluto):
        return caminho_absoluto

    if ext == ".json":
        return obter_caminho_cache_seguro(cache_id)

    if caminho_absoluto.startswith(caminho_limite):
        return caminho_absoluto
    return None

def gerar_resposta_enriquecida_cache(chave_identificadora: str, dados: Any) -> dict:
    """Gera resposta resumida e enriquecida para evitar estouro de tokens mas entregando amostra imediata útil."""
    if isinstance(dados, dict) and ("advogado_encontrado" in dados or "items" in dados):
        adv = dados.get("advogado_encontrado") or {}
        items = dados.get("items") or []
        items_ordenados = sorted(items, key=lambda x: str(x.get("data_inicio") or ""), reverse=True)
        
        tribunais = {}
        amostra = []
        for idx, p in enumerate(items_ordenados):
            fontes = p.get("fontes") or []
            sigla = "OUTROS"
            if fontes and (fontes[0].get("sigla") or fontes[0].get("nome")):
                sigla = fontes[0].get("sigla") or fontes[0].get("nome")
            elif p.get("unidade_origem", {}).get("tribunal_sigla"):
                sigla = p.get("unidade_origem", {}).get("tribunal_sigla")
            
            tribunais[sigla] = tribunais.get(sigla, 0) + 1
            
            if idx < 10:
                amostra.append({
                    "numero_cnj": p.get("numero_cnj") or "Sem número CNJ",
                    "polo_ativo": p.get("titulo_polo_ativo") or "Não informado",
                    "polo_passivo": p.get("titulo_polo_passivo") or "Não informado",
                    "tribunal": sigla,
                    "data_inicio": p.get("data_inicio") or "N/D",
                    "qtd_movimentacoes": p.get("quantidade_movimentacoes") or 0
                })
                
        oab_str = ""
        if adv.get("oab_numero") or adv.get("oab_estado"):
            oab_str = f"{adv.get('oab_numero', '')}/{adv.get('oab_estado', '')}".strip("/")
        elif adv.get("oab"):
            oab_str = str(adv.get("oab"))

        if not oab_str and chave_identificadora.startswith("escavador_oab_"):
            parts = chave_identificadora.replace("escavador_oab_", "").split("_")
            if len(parts) >= 2:
                oab_str = f"{parts[1].upper()}/{parts[0].upper()}"

        paginacao_em_andamento = bool(dados.get("_paginacao_em_andamento"))

        if len(items) == 0 and not adv.get("nome"):
            res = {
                "status": "sem_resultados",
                "advogado": {
                    "nome": None,
                    "oab": oab_str,
                    "cpf": None,
                    "total_processos_cadastrados": 0
                },
                "total_processos_baixados": 0,
                "resumo_tribunais": {},
                "amostra_10_processos_mais_recentes": [],
                "cache_id": chave_identificadora,
                "mensagem": "Nenhum advogado ou processo encontrado para esta OAB na API do Escavador.",
                "instrucao": f"A busca retornou 0 processos para a OAB {oab_str}."
            }
        else:
            instrucao_txt = (
                f"Exibindo amostra dos 10 processos mais recentes do total de {len(items)} baixados. "
                f"O arquivo completo com todos os {len(items)} processos está salvo localmente no cache '{chave_identificadora}'. "
                f"Para paginar o restante dos itens se o usuário pedir, use 'investigador_ler_cache' (cache_id='{chave_identificadora}', chave='items')."
            )
            if paginacao_em_andamento:
                instrucao_txt = (
                    f"Retornando os {len(items)} primeiros processos. A PAGINAÇÃO EM SEGUNDO PLANO ESTÁ EM ANDAMENTO no servidor. "
                    f"AGUARDE DE 30 A 60 SEGUNDOS e chame novamente esta ferramenta ou 'investigador_ler_cache' (cache_id='{chave_identificadora}', chave='items') "
                    f"para obter a lista completa de processos."
                )

            res = {
                "status": "sucesso",
                "advogado": {
                    "nome": adv.get("nome"),
                    "oab": oab_str,
                    "cpf": adv.get("cpf"),
                    "total_processos_cadastrados": adv.get("quantidade_processos") or len(items)
                },
                "total_processos_baixados": len(items),
                "resumo_tribunais": tribunais,
                "amostra_10_processos_mais_recentes": amostra,
                "cache_id": chave_identificadora,
                "instrucao": instrucao_txt
            }

        if paginacao_em_andamento:
            res["_paginacao_em_andamento"] = True

        return res

    if isinstance(dados, dict):
        resumo = {"tipo": "objeto", "chaves_disponiveis": list(dados.keys())}
    elif isinstance(dados, list):
        resumo = {"tipo": "lista", "tamanho_total": len(dados), "amostra_primeiros_3": dados[:3]}
    else:
        resumo = str(dados)[:500]

    return {
        "status": "sucesso",
        "cache_id": chave_identificadora,
        "mensagem": "Dados recuperados do cache local (crédito e tempo poupados!).",
        "resumo_dos_dados": resumo,
        "instrucao": f"Use a ferramenta 'investigador_ler_cache' com o cache_id '{chave_identificadora}' para explorar os dados."
    }

def checar_cache_universal(chave_identificadora: str) -> Optional[dict]:
    """Verifica se existe cache local e retorna o resumo imediatamente se existir (evita chamadas redundantes)."""
    cache_file = obter_caminho_cache_seguro(chave_identificadora)
    if not cache_file or not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        print(f"[CACHE HIT] '{chave_identificadora}' recuperado do cache local.", file=sys.stderr, flush=True)
        return gerar_resposta_enriquecida_cache(chave_identificadora, dados)
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao ler cache '{chave_identificadora}': {str(e)}", file=sys.stderr, flush=True)
    return None

def salvar_cache_universal(chave_identificadora: str, dados: Any) -> dict:
    """Helper que salva dados grandes localmente e retorna apenas um sumário pro LLM."""
    cache_file = obter_caminho_cache_seguro(chave_identificadora)
    if not cache_file:
        print(f"[CACHE ERROR] Chave de cache inválida ou insegura para salvar: {chave_identificadora}", file=sys.stderr, flush=True)
        return {"status": "erro", "mensagem": "Nome de cache inválido."}
        
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"[CACHE SAVED] Dados salvos localmente em '{cache_file}'.", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao salvar cache '{chave_identificadora}': {str(e)}", file=sys.stderr, flush=True)
        return {"status": "erro", "mensagem": f"Falha ao persistir cache: {str(e)}"}
        
    return gerar_resposta_enriquecida_cache(chave_identificadora, dados)
