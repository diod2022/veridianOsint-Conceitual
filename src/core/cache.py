import os
import json
import glob
import re
import sys
import time
import urllib.parse
from typing import Optional, Any
from src.core.config import CACHE_DIR
from src.core.security import validar_caminho_seguro

def obter_caminho_cache_seguro(cache_id: str) -> Optional[str]:
    """
    Sanitiza o cache_id e resolve o caminho absoluto, garantindo que o arquivo
    esteja estritamente dentro do diretório de cache (evita Path Traversal).
    Suporta:
    - Nomes com caminhos parciais (ex: 'cache_consultas/bigdata_xxx.json')
    - IDs informados com ou sem extensão (.json, .md, .zip)
    - CPFs formatados ('233.022.348-05') ou puros ('23302234805')
    - CNPJs formatados ou puros
    - Variações de prefixos de provedor ('unitfour_ligados_...', 'bigdata_...')
    - Buscas nominais ('Miguel Dau' -> 'unitfour_busca_nome_miguel_dau')
    - Números de processo CNJ
    - Variações de OAB ('OAB/MS 7008' -> 'escavador_oab_ms_7008')
    """
    if not cache_id or not isinstance(cache_id, str):
        return None
        
    cache_id_raw = urllib.parse.unquote(str(cache_id)).strip()
    if ".." in cache_id_raw:
        return None
        
    # Extrai o nome do arquivo se o cliente passou caminho completo ou relativo
    cache_id_seguro = os.path.basename(cache_id_raw).strip()
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return None

    caminho_limite = os.path.abspath(CACHE_DIR)
    
    # 1. Verifica se o nome informado já existe diretamente em CACHE_DIR
    caminho_direto = os.path.abspath(os.path.join(CACHE_DIR, cache_id_seguro))
    if os.path.exists(caminho_direto) and validar_caminho_seguro(caminho_limite, caminho_direto):
        return caminho_direto

    # 2. Normaliza removendo extensões conhecidas para montar o .json canônico
    clean_id = re.sub(r'\.(json|md|zip)$', '', cache_id_seguro, flags=re.IGNORECASE).strip()
    if not clean_id:
        return None

    caminho_json = os.path.abspath(os.path.join(CACHE_DIR, f"{clean_id}.json"))
    if os.path.exists(caminho_json) and validar_caminho_seguro(caminho_limite, caminho_json):
        return caminho_json

    clean_lower = clean_id.lower()

    # 2.5 Resolução para prefixos Veridian gerados pelo white-label
    if clean_lower.startswith("veridian_") or clean_lower.startswith("veridian"):
        sub = re.sub(r'^veridian_?', '', clean_lower)
        sub_digitos = re.sub(r'\D', '', sub)
        
        candidatos_veridian = []
        if "ligado" in sub or "socio" in sub or "parente" in sub:
            if sub_digitos:
                candidatos_veridian.append(f"unitfour_ligados_{sub_digitos}.json")
        elif "mandado" in sub:
            if sub_digitos:
                candidatos_veridian.append(f"unitfour_mandados_{sub_digitos}.json")
        elif "antecedente" in sub or "criminal" in sub:
            if sub_digitos:
                candidatos_veridian.append(f"unitfour_antecedentes_{sub_digitos}.json")
        elif "pep" in sub:
            if sub_digitos:
                candidatos_veridian.append(f"unitfour_pep_{sub_digitos}.json")
        elif "busca_nome_" in sub or "nome_" in sub:
            nome_slug = re.sub(r'^(busca_)?(avancada_)?nome_', '', sub)
            candidatos_veridian.append(f"unitfour_busca_nome_{nome_slug}.json")
        elif "oab" in sub:
            uf_m = re.search(r'\b(ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)\b', sub)
            num_m = re.search(r'\b(\d{1,7})\b', sub)
            if uf_m and num_m:
                candidatos_veridian.append(f"escavador_oab_{uf_m.group(1)}_{num_m.group(1)}.json")
        elif "processo" in sub or "cnj" in sub:
            if sub_digitos:
                candidatos_veridian.append(f"processo_cnj_{sub_digitos}.json")
        elif "cnpj" in sub:
            if sub_digitos:
                candidatos_veridian.extend([
                    f"bigdata_cnpj_{sub_digitos}.json",
                    f"unitfour_cnpj_{sub_digitos}.json",
                    f"unitfour_tomadores_{sub_digitos}.json",
                    f"unitfour_empresas_ligadas_{sub_digitos}.json"
                ])
        elif "cpf" in sub or len(sub_digitos) == 11:
            if sub_digitos:
                candidatos_veridian.extend([
                    f"bigdata_{sub_digitos}.json",
                    f"unitfour_cpf_{sub_digitos}.json",
                    f"unitfour_ligados_{sub_digitos}.json"
                ])
                
        # Tenta também sub direto com prefixos de provedor
        candidatos_veridian.extend([
            f"unitfour_{sub}.json",
            f"bigdata_{sub}.json",
            f"escavador_{sub}.json",
            f"{sub}.json"
        ])
        
        for cand in candidatos_veridian:
            p = os.path.abspath(os.path.join(CACHE_DIR, cand))
            if os.path.exists(p) and validar_caminho_seguro(caminho_limite, p):
                return p

    # 3. Resolução por dígitos (CPF, CNPJ, CNJ)
    digitos = re.sub(r'\D', '', clean_id)
    prefixos_conhecidos = (
        "bigdata_cnpj_", "bigdata_", "unitfour_cpf_", "unitfour_ligados_", "unitfour_mandados_",
        "unitfour_pep_", "unitfour_antecedentes_", "unitfour_tomadores_", "unitfour_empresas_ligadas_",
        "unitfour_cnpj_", "unitfour_veiculo_", "unitfour_busca_tel_", "unitfour_busca_cep_",
        "processo_cnj_", "escavador_oab_"
    )
    
    # Se o nome possui prefixo conhecido com dígitos formatados (ex: 'unitfour_ligados_233.022.348-05')
    for pref in prefixos_conhecidos:
        if clean_lower.startswith(pref):
            sufixo_digitos = re.sub(r'\D', '', clean_lower[len(pref):])
            if sufixo_digitos:
                candidato_com_prefixo = os.path.abspath(os.path.join(CACHE_DIR, f"{pref}{sufixo_digitos}.json"))
                if os.path.exists(candidato_com_prefixo) and validar_caminho_seguro(caminho_limite, candidato_com_prefixo):
                    return candidato_com_prefixo

    tem_prefixo_especifico = any(clean_lower.startswith(p) for p in prefixos_conhecidos)

    if len(digitos) == 11 and not tem_prefixo_especifico:
        # Bare CPF (sem prefixo): tenta na ordem de relevância
        candidatos_cpf = [
            f"bigdata_{digitos}.json",
            f"unitfour_cpf_{digitos}.json",
            f"unitfour_ligados_{digitos}.json",
            f"unitfour_mandados_{digitos}.json",
            f"unitfour_pep_{digitos}.json",
            f"unitfour_antecedentes_{digitos}.json",
            f"cpf_{digitos}.json"
        ]
        for cand in candidatos_cpf:
            p = os.path.abspath(os.path.join(CACHE_DIR, cand))
            if os.path.exists(p) and validar_caminho_seguro(caminho_limite, p):
                return p

    elif len(digitos) == 14 and not tem_prefixo_especifico:
        # Bare CNPJ (sem prefixo)
        candidatos_cnpj = [
            f"bigdata_cnpj_{digitos}.json",
            f"unitfour_cnpj_{digitos}.json",
            f"unitfour_tomadores_{digitos}.json",
            f"unitfour_empresas_ligadas_{digitos}.json",
            f"cnpj_{digitos}.json"
        ]
        for cand in candidatos_cnpj:
            p = os.path.abspath(os.path.join(CACHE_DIR, cand))
            if os.path.exists(p) and validar_caminho_seguro(caminho_limite, p):
                return p

    elif len(digitos) == 20 and not tem_prefixo_especifico:
        # Bare Processo CNJ
        p_cnj = os.path.abspath(os.path.join(CACHE_DIR, f"processo_cnj_{digitos}.json"))
        if os.path.exists(p_cnj) and validar_caminho_seguro(caminho_limite, p_cnj):
            return p_cnj

    # 4. Resolução para buscas nominais (ex: 'unitfour_busca_nome_miguel_dau' ou 'Miguel Dau')
    nome_slug = re.sub(r'[^a-zA-Z0-9]', '_', clean_id.lower()).strip('_')
    nome_slug_sem_unit = re.sub(r'^unitfour_busca_nome_', '', nome_slug)
    if nome_slug_sem_unit and not tem_prefixo_especifico:
        candidatos_nome = [
            f"unitfour_busca_nome_{nome_slug_sem_unit}.json",
            f"unitfour_busca_nome_{nome_slug}.json",
            f"busca_nome_{nome_slug_sem_unit}.json"
        ]
        for cand in candidatos_nome:
            p = os.path.abspath(os.path.join(CACHE_DIR, cand))
            if os.path.exists(p) and validar_caminho_seguro(caminho_limite, p):
                return p

    # 5. Busca resiliente para variações de OAB (ex: escavador_oab_7008_MS -> escavador_oab_ms_7008)
    raw_upper = clean_id.upper()
    uf_match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', raw_upper)
    num_match = re.search(r'\b(\d{1,7})\b', raw_upper)
    
    if uf_match and num_match and not tem_prefixo_especifico:
        uf = uf_match.group(1).lower()
        num = num_match.group(1).lower()
        resiliente_path = os.path.abspath(os.path.join(CACHE_DIR, f"escavador_oab_{uf}_{num}.json"))
        if os.path.exists(resiliente_path) and validar_caminho_seguro(caminho_limite, resiliente_path):
            return resiliente_path

    # 6. Fallback genérico por palavra-chave se não encontrou exato
    if not tem_prefixo_especifico:
        keywords = [k.lower() for k in re.split(r'[\s_\-\/]+', clean_id) if k and k.lower() not in ['advogado', 'oab', 'json']]
        if keywords and os.path.exists(CACHE_DIR):
            for f in glob.glob(os.path.join(CACHE_DIR, "*.json")):
                fname = os.path.basename(f).lower()
                if all(kw in fname for kw in keywords):
                    caminho_candidato = os.path.abspath(f)
                    if validar_caminho_seguro(caminho_limite, caminho_candidato):
                        return caminho_candidato
                
    # 7. Se o arquivo ainda não existe (para gravação), retorna o caminho canônico esperado
    if caminho_json.startswith(caminho_limite):
        return caminho_json
    return None

def obter_caminho_cache_seguro_ext(cache_id: str, ext: str = ".json") -> Optional[str]:
    """
    Sanitiza o cache_id e resolve o caminho absoluto com a extensão informada,
    garantindo que o arquivo esteja estritamente dentro do diretório de cache.
    """
    if not cache_id or not isinstance(cache_id, str):
        return None
        
    cache_id_raw = urllib.parse.unquote(str(cache_id)).strip()
    if ".." in cache_id_raw:
        return None
        
    cache_id_seguro = os.path.basename(cache_id_raw).strip()
    clean_id = re.sub(r'\.(json|md|zip)$', '', cache_id_seguro, flags=re.IGNORECASE).strip()
    if not clean_id or clean_id in (".", ".."):
        return None
        
    caminho_absoluto = os.path.abspath(os.path.join(CACHE_DIR, f"{clean_id}{ext}"))
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
    clean_id = re.sub(r'\.(json|md|zip)$', '', chave_identificadora, flags=re.IGNORECASE).strip()
    
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

        if not oab_str and clean_id.startswith("escavador_oab_"):
            parts = clean_id.replace("escavador_oab_", "").split("_")
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
                "cache_id": clean_id,
                "mensagem": "Nenhum advogado ou processo encontrado para esta OAB na API do Escavador.",
                "instrucao": f"A busca retornou 0 processos para a OAB {oab_str}."
            }
        else:
            instrucao_txt = (
                f"Exibindo amostra dos 10 processos mais recentes do total de {len(items)} baixados. "
                f"O arquivo completo com todos os {len(items)} processos está salvo localmente no cache '{clean_id}'. "
                f"Para paginar o restante dos itens se o usuário pedir, use 'investigador_ler_cache' (cache_id='{clean_id}', chave='items')."
            )
            if paginacao_em_andamento:
                instrucao_txt = (
                    f"Retornando os {len(items)} primeiros processos. A PAGINAÇÃO EM SEGUNDO PLANO ESTÁ EM ANDAMENTO no servidor. "
                    f"AGUARDE DE 30 A 60 SEGUNDOS e chame novamente esta ferramenta ou 'investigador_ler_cache' (cache_id='{clean_id}', chave='items') "
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
                "cache_id": clean_id,
                "instrucao": instrucao_txt
            }

        if paginacao_em_andamento:
            res["_paginacao_em_andamento"] = True

        return res

    if isinstance(dados, dict) and ("polo_ativo" in dados or "polo_passivo" in dados or "numero_cnj" in dados):
        return {
            "status": "sucesso",
            "numero_cnj": dados.get("numero_cnj"),
            "polo_ativo": dados.get("polo_ativo"),
            "polo_passivo": dados.get("polo_passivo"),
            "tribunal": dados.get("tribunal"),
            "data_inicio": dados.get("data_inicio"),
            "total_movimentacoes": dados.get("total_movimentacoes") or len(dados.get("movimentacoes") or []),
            "advogados": dados.get("advogados") or [],
            "ultimas_movimentacoes": dados.get("ultimas_movimentacoes") or [],
            "cache_id": clean_id,
            "instrucao": f"Use 'investigador_ler_cache' (cache_id='{clean_id}', chave='dados_brutos') para ver o processo completo na íntegra."
        }

    if isinstance(dados, dict):
        chaves = [k for k in dados.keys() if not k.startswith("_")]
        resumo = {"tipo": "objeto", "chaves_disponiveis": chaves}
    elif isinstance(dados, list):
        resumo = {"tipo": "lista", "tamanho_total": len(dados), "amostra_primeiros_3": dados[:3]}
    else:
        resumo = str(dados)[:500]

    return {
        "status": "sucesso",
        "cache_id": clean_id,
        "mensagem": "Dados recuperados do cache local (crédito e tempo poupados!).",
        "resumo_dos_dados": resumo,
        "instrucao": f"Use a ferramenta 'investigador_ler_cache' com o cache_id '{clean_id}' para explorar os dados."
    }

def checar_cache_universal(chave_identificadora: str) -> Optional[dict]:
    """Verifica se existe cache local e retorna o resumo imediatamente se existir (evita chamadas redundantes)."""
    cache_file = obter_caminho_cache_seguro(chave_identificadora)
    if not cache_file or not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        clean_id = re.sub(r'\.(json|md|zip)$', '', chave_identificadora, flags=re.IGNORECASE).strip()
        print(f"[CACHE HIT] '{clean_id}' recuperado do cache local.", file=sys.stderr, flush=True)
        return gerar_resposta_enriquecida_cache(clean_id, dados)
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao ler cache '{chave_identificadora}': {str(e)}", file=sys.stderr, flush=True)
    return None

def salvar_cache_universal(chave_identificadora: str, dados: Any) -> dict:
    """
    Salva dados localmente de forma ATÔMICA (com tempfile + rename) e retorna sumário com cache_id.
    """
    clean_id = re.sub(r'\.(json|md|zip)$', '', chave_identificadora, flags=re.IGNORECASE).strip()
    cache_file = obter_caminho_cache_seguro(clean_id)
    if not cache_file:
        print(f"[CACHE ERROR] Chave de cache inválida ou insegura para salvar: {chave_identificadora}", file=sys.stderr, flush=True)
        return {"status": "erro", "mensagem": "Nome de cache inválido."}
        
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp_file = f"{cache_file}.tmp_{os.getpid()}_{time.time_ns()}"
    
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, cache_file)
        print(f"[CACHE SAVED] Dados salvos atomicamente em '{cache_file}'.", file=sys.stderr, flush=True)
    except Exception as e:
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception:
                pass
        print(f"[CACHE ERROR] Falha ao salvar cache '{chave_identificadora}': {str(e)}", file=sys.stderr, flush=True)
        return {"status": "erro", "mensagem": f"Falha ao persistir cache: {str(e)}"}
        
    return gerar_resposta_enriquecida_cache(clean_id, dados)
