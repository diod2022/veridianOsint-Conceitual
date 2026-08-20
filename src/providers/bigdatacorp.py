import os
import json
import re
import sys
import time
import asyncio
import httpx
from typing import Optional, Union, Dict, Any, List
from src.core.config import CACHE_DIR, get_bigdata_token, get_bigdata_token_id
from src.core.http_client import resilient_request, get_semaphore
from src.core.security import normalizar_cpf, normalizar_cnpj, validar_cpf, validar_cnpj, normalizar_cnj, validar_cnj
from src.core.cache import obter_caminho_cache_seguro, salvar_cache_universal

BIGDATA_BASE_URL = "https://plataforma.bigdatacorp.com.br"

_cpf_locks: Dict[str, asyncio.Lock] = {}
_cnpj_locks: Dict[str, asyncio.Lock] = {}

def _get_doc_lock(doc_key: str, lock_dict: Dict[str, asyncio.Lock]) -> asyncio.Lock:
    if doc_key not in lock_dict:
        lock_dict[doc_key] = asyncio.Lock()
    return lock_dict[doc_key]

MAPA_DATASETS_PF = {
    "bdcbasicdata": "basic_data",
    "bdcphones": "phones_extended",
    "bdcemails": "emails_extended",
    "bdcaddresses": "addresses_extended",
    "bdclawsuits": "processes",
    "bdcrelatedpeople": "related_people",
    "bdcrelatedcompanies": "relationships",
    "bdccompanies": "relationships",
    "bdcbusinessrelationships": "relationships",
    "bdcpartnerships": "relationships",
    "bdcdomains": "domains",
    "bdcpolitics": "electoral_data",
    "bdchistorical": "historical_basic_data",
    "bdcfamilysocialbenefits": "kyc",
    "bdcprofessional": "profession_data",
    "bdcclass": "class_organization",
    "bdclicenses": "class_organization",
    "bdcindustrialproperty": "industrial_property",
    "bdcpublicservant": "occupation_data",
    "bdcturnover": "financial_data",
    "bdcelectoralcandidate": "election_candidate_data",
    "bdcelectoralproviders": "electoral_providers",
    "bdconlineadvertisements": "online_ads",
    "bdcgovernmentdebtors": "government_debtors",
    "bdcelectoraldonorspersonal": "electoral_donors",
    "bdccollections": "collections",
    "bdcsocialassistance": "kyc",
    "bdcfamilypoliticalhistory": "family_political_history",
    "bdconlinepresence": "online_presence"
}

MAPA_DATASETS_PJ = {
    "bdccompanybasicdata": "basic_data",
    "bdccompanyphones": "phones_extended",
    "bdccompanyemails": "emails_extended",
    "bdccompanyaddresses": "addresses_extended",
    "bdccompanyevolution": "company_evolution",
    "bdcelectoraldonorscompany": "electoral_donors",
    "bdclawsuits": "processes",
    "bdccompanyrelationships": "relationships",
    "bdccompanyhistorical": "history_basic_data"
}

# Mapeamento reverso de chaves do Result[0] da BigDataCorp para códigos de dataset
MAPA_RESULT_KEYS_PF = {
    "basicdata": "bdcbasicdata",
    "extendedphones": "bdcphones",
    "phones": "bdcphones",
    "extendedemails": "bdcemails",
    "emails": "bdcemails",
    "extendedaddresses": "bdcaddresses",
    "addresses": "bdcaddresses",
    "processes": "bdclawsuits",
    "lawsuits": "bdclawsuits",
    "relatedpeople": "bdcrelatedpeople",
    "relationships": "bdcrelatedcompanies",
    "businessrelationships": "bdcrelatedcompanies",
    "companies": "bdcrelatedcompanies",
    "relatedcompanies": "bdcrelatedcompanies",
    "domains": "bdcdomains",
    "electoraldata": "bdcpolitics",
    "historicalbasicdata": "bdchistorical",
    "kycdata": "bdcfamilysocialbenefits",
    "professiondata": "bdcprofessional",
    "memberships": "bdcclass",
    "industrialproperty": "bdcindustrialproperty",
    "finantialdata": "bdcturnover",
    "electioncandidatedata": "bdcelectoralcandidate",
    "electoralproviders": "bdcelectoralproviders",
    "onlineads": "bdconlineadvertisements",
    "governmentdebtors": "bdcgovernmentdebtors",
    "electoraldonors": "bdcelectoraldonorspersonal",
    "collections": "bdccollections",
    "familypoliticalhistory": "bdcfamilypoliticalhistory",
    "onlinepresence": "bdconlinepresence"
}

MAPA_RESULT_KEYS_PJ = {
    "basicdata": "bdccompanybasicdata",
    "extendedphones": "bdccompanyphones",
    "phones": "bdccompanyphones",
    "extendedemails": "bdccompanyemails",
    "emails": "bdccompanyemails",
    "extendedaddresses": "bdccompanyaddresses",
    "addresses": "bdccompanyaddresses",
    "companyevolutiondata": "bdccompanyevolution",
    "companyevolution": "bdccompanyevolution",
    "electoraldonors": "bdcelectoraldonorscompany",
    "processes": "bdclawsuits",
    "lawsuits": "bdclawsuits",
    "relationships": "bdccompanyrelationships",
    "historybasicdata": "bdccompanyhistorical"
}

# Mapeamento de datasets para ferramentas granulares (para validação de consultas_ativas no mcp_config.json)
DATASET_TOOL_NAMES_PF = {
    "bdcbasicdata": ["bigdata_cpf_dados_basicos", "veridian_cpf_dados_basicos", "bigdata_consultar_cpf", "veridian_consultar_cadastro_cpf"],
    "bdcphones": ["bigdata_cpf_telefones", "veridian_cpf_telefones"],
    "bdcemails": ["bigdata_cpf_emails", "veridian_cpf_emails"],
    "bdcaddresses": ["bigdata_cpf_enderecos", "veridian_cpf_enderecos"],
    "bdclawsuits": ["bigdata_cpf_processos", "veridian_cpf_processos"],
    "bdcrelatedcompanies": ["bigdata_cpf_empresas_e_socios", "veridian_cpf_empresas_e_socios"],
    "bdccompanies": ["bigdata_cpf_empresas_e_socios", "veridian_cpf_empresas_e_socios"],
    "bdcbusinessrelationships": ["bigdata_cpf_empresas_e_socios", "veridian_cpf_empresas_e_socios"],
    "bdcpartnerships": ["bigdata_cpf_empresas_e_socios", "veridian_cpf_empresas_e_socios"],
    "bdcrelatedpeople": ["bigdata_cpf_parentes_e_relacionados", "veridian_cpf_parentes_e_relacionados"],
    "bdchistorical": ["bigdata_cpf_historico_cadastral", "veridian_cpf_historico_cadastral"],
    "bdcprofessional": ["bigdata_cpf_dados_profissionais", "veridian_cpf_dados_profissionais"],
    "bdcpolitics": ["bigdata_cpf_dados_politicos", "veridian_cpf_dados_politicos"],
    "bdcfamilysocialbenefits": ["bigdata_cpf_beneficios_sociais", "veridian_cpf_beneficios_sociais"],
    "bdconlinepresence": ["bigdata_cpf_presenca_online", "veridian_cpf_presenca_online"]
}

DATASET_TOOL_NAMES_PJ = {
    "bdccompanybasicdata": ["bigdata_cnpj_dados_basicos", "veridian_cnpj_dados_basicos", "bigdata_consultar_cnpj", "veridian_consultar_cadastro_cnpj"],
    "bdccompanyphones": ["bigdata_cnpj_telefones", "veridian_cnpj_telefones"],
    "bdccompanyemails": ["bigdata_cnpj_emails", "veridian_cnpj_emails"],
    "bdccompanyaddresses": ["bigdata_cnpj_enderecos", "veridian_cnpj_enderecos"],
    "bdccompanyrelationships": ["bigdata_cnpj_quadro_societario", "veridian_cnpj_quadro_societario"],
    "bdclawsuits": ["bigdata_cnpj_processos", "veridian_cnpj_processos"],
    "bdccompanyevolution": ["bigdata_cnpj_evolucao_historica", "veridian_cnpj_evolucao_historica"],
    "bdccompanyhistorical": ["bigdata_cnpj_historico", "veridian_cnpj_historico"]
}

def is_dataset_ativo(dataset_code: str, tipo: str = "pf") -> bool:
    """Verifica se o dataset está ativo nas configurações globais (consultas_ativas / fontes_ativas)."""
    try:
        from src.core.auth import carregar_config_global
        config = carregar_config_global()
    except Exception:
        return True
        
    fontes_ativas = config.get("fontes_ativas", {})
    if fontes_ativas.get("bigdata") is False:
        return False
        
    consultas_ativas = config.get("consultas_ativas", {})
    code_norm = dataset_code.strip().lower()
    
    # 1. Checa o código do dataset direto
    if consultas_ativas.get(code_norm) is False:
        return False
        
    # 2. Checa as ferramentas associadas
    mapping = DATASET_TOOL_NAMES_PF if tipo == "pf" else DATASET_TOOL_NAMES_PJ
    tool_names = mapping.get(code_norm, [])
    for t_name in tool_names:
        if consultas_ativas.get(t_name) is False:
            return False
            
    return True

def get_nested_case_insensitive(data: dict, path: str) -> Any:
    if not isinstance(data, dict):
        return None
    parts = path.split(".")
    curr = data
    for part in parts:
        part_lower = part.lower()
        found = False
        if not isinstance(curr, dict):
            return None
        for k, v in curr.items():
            if k.lower() == part_lower:
                curr = v
                found = True
                break
        if not found:
            return None
    return curr

def filtrar_dados_pf(dados_completos: dict, dataset_code: str) -> Any:
    alvo = dados_completos
    if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
        alvo = dados_completos["Result"][0]
        
    if not isinstance(alvo, dict):
        return alvo

    code_raw = dataset_code.strip().lower()
    code_norm = code_raw.replace("_", "").replace("-", "")
    
    # 1. Aliases diretos e canônicos
    if code_norm in ("bdcbasicdata", "basicdata"):
        return get_nested_case_insensitive(alvo, "BasicData") or {}
    elif code_norm in ("bdcphones", "phones", "extendedphones", "phonesextended"):
        return get_nested_case_insensitive(alvo, "ExtendedPhones") or get_nested_case_insensitive(alvo, "Contacts.Phones") or []
    elif code_norm in ("bdcemails", "emails", "extendedemails", "emailsextended"):
        return get_nested_case_insensitive(alvo, "ExtendedEmails") or get_nested_case_insensitive(alvo, "Contacts.Emails") or []
    elif code_norm in ("bdcaddresses", "addresses", "extendedaddresses", "addressesextended"):
        return get_nested_case_insensitive(alvo, "ExtendedAddresses") or get_nested_case_insensitive(alvo, "Contacts.Addresses") or []
    elif code_norm in ("bdclawsuits", "lawsuits", "processes", "processos"):
        return get_nested_case_insensitive(alvo, "Processes") or get_nested_case_insensitive(alvo, "Lawsuits") or {}
    elif code_norm in ("bdcrelatedpeople", "relatedpeople", "parentes", "pessoasrelacionadas"):
        return get_nested_case_insensitive(alvo, "RelatedPeople") or []
    elif code_norm in ("bdcrelatedcompanies", "relatedcompanies", "companies", "empresas", "relationships", "businessrelationships", "partnerships", "socios"):
        res_comp = (
            get_nested_case_insensitive(alvo, "Relationships.Companies") or
            get_nested_case_insensitive(alvo, "BusinessRelationships") or
            get_nested_case_insensitive(alvo, "Relationships") or
            get_nested_case_insensitive(alvo, "Companies") or
            get_nested_case_insensitive(alvo, "RelatedCompanies") or
            get_nested_case_insensitive(alvo, "RelatedEntities")
        )
        return res_comp if res_comp is not None else []
    elif code_norm in ("bdcdomains", "domains"):
        return get_nested_case_insensitive(alvo, "Domains") or []
    elif code_norm in ("bdcpolitics", "electoraldata", "politics"):
        return get_nested_case_insensitive(alvo, "ElectoralData") or {}
    elif code_norm in ("bdchistorical", "historicalbasicdata"):
        return get_nested_case_insensitive(alvo, "HistoricalBasicData") or {}
    elif code_norm in ("bdcfamilysocialbenefits", "kycdata", "socialbenefits"):
        return get_nested_case_insensitive(alvo, "KycData") or {}
    elif code_norm in ("bdcprofessional", "professiondata", "profession"):
        return get_nested_case_insensitive(alvo, "ProfessionData") or {}
    elif code_norm in ("bdcclass", "memberships", "classorganization"):
        return get_nested_case_insensitive(alvo, "Memberships") or []
    elif code_norm in ("bdclicenses", "licenses"):
        return get_nested_case_insensitive(alvo, "Memberships") or get_nested_case_insensitive(alvo, "Licenses") or []
    elif code_norm in ("bdcindustrialproperty", "industrialproperty"):
        return get_nested_case_insensitive(alvo, "IndustrialProperty") or {}
    elif code_norm in ("bdcpublicservant", "publicservant"):
        return get_nested_case_insensitive(alvo, "ProfessionData") or {}
    elif code_norm in ("bdcturnover", "finantialdata", "financialdata"):
        return get_nested_case_insensitive(alvo, "FinantialData") or get_nested_case_insensitive(alvo, "FinancialData") or {}
    elif code_norm in ("bdcelectoralcandidate", "electioncandidatedata"):
        return get_nested_case_insensitive(alvo, "ElectionCandidateData") or []
    elif code_norm in ("bdcelectoralproviders", "electoralproviders"):
        return get_nested_case_insensitive(alvo, "ElectoralProviders") or []
    elif code_norm in ("bdconlineadvertisements", "onlineads"):
        return get_nested_case_insensitive(alvo, "OnlineAds") or []
    elif code_norm in ("bdcgovernmentdebtors", "governmentdebtors"):
        return get_nested_case_insensitive(alvo, "GovernmentDebtors") or {}
    elif code_norm in ("bdcelectoraldonorspersonal", "electoraldonors"):
        return get_nested_case_insensitive(alvo, "ElectoralDonors") or []
    elif code_norm in ("bdccollections", "collections"):
        return get_nested_case_insensitive(alvo, "Collections") or []
    elif code_norm in ("bdcsocialassistance", "socialassistance"):
        return get_nested_case_insensitive(alvo, "KycData") or {}
    elif code_norm in ("bdcfamilypoliticalhistory", "familypoliticalhistory"):
        return get_nested_case_insensitive(alvo, "FamilyPoliticalHistory") or {}
    elif code_norm in ("bdconlinepresence", "onlinepresence"):
        return get_nested_case_insensitive(alvo, "OnlinePresence") or {}
        
    # 2. Busca dinâmica case-insensitive em alvo
    res_dinamico = get_nested_case_insensitive(alvo, dataset_code)
    if res_dinamico is not None:
        return res_dinamico

    for k, v in alvo.items():
        if k.lower().replace("_", "") == code_norm:
            return v

    # 3. Retorna vazio se a categoria solicitada não existir no alvo (nunca retorna alvo completo)
    return {}

def filtrar_dados_pj(dados_completos: dict, dataset_code: str) -> Any:
    alvo = dados_completos
    if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
        alvo = dados_completos["Result"][0]
        
    if not isinstance(alvo, dict):
        return alvo

    code_raw = dataset_code.strip().lower()
    code_norm = code_raw.replace("_", "").replace("-", "")
    
    if code_norm in ("bdccompanybasicdata", "basicdata"):
        return get_nested_case_insensitive(alvo, "BasicData") or {}
    elif code_norm in ("bdccompanyphones", "phones", "extendedphones", "phonesextended"):
        return get_nested_case_insensitive(alvo, "ExtendedPhones") or get_nested_case_insensitive(alvo, "Contacts.Phones") or []
    elif code_norm in ("bdccompanyemails", "emails", "extendedemails", "emailsextended"):
        return get_nested_case_insensitive(alvo, "ExtendedEmails") or get_nested_case_insensitive(alvo, "Contacts.Emails") or []
    elif code_norm in ("bdccompanyaddresses", "addresses", "extendedaddresses", "addressesextended"):
        return get_nested_case_insensitive(alvo, "ExtendedAddresses") or get_nested_case_insensitive(alvo, "Contacts.Addresses") or []
    elif code_norm in ("bdccompanyevolution", "companyevolution", "companyevolutiondata"):
        return get_nested_case_insensitive(alvo, "CompanyEvolutionData") or get_nested_case_insensitive(alvo, "CompanyEvolution") or {}
    elif code_norm in ("bdcelectoraldonorscompany", "electoraldonors"):
        return get_nested_case_insensitive(alvo, "ElectoralDonors") or []
    elif code_norm in ("bdclawsuits", "lawsuits", "processes", "processos"):
        return get_nested_case_insensitive(alvo, "Lawsuits") or get_nested_case_insensitive(alvo, "Processes") or {}
    elif code_norm in ("bdccompanyrelationships", "relationships", "socios", "qsa"):
        return get_nested_case_insensitive(alvo, "Relationships") or {}
    elif code_norm in ("bdccompanyhistorical", "historybasicdata", "historical"):
        return get_nested_case_insensitive(alvo, "HistoryBasicData") or {}

    res_dinamico = get_nested_case_insensitive(alvo, dataset_code)
    if res_dinamico is not None:
        return res_dinamico

    for k, v in alvo.items():
        if k.lower().replace("_", "") == code_norm:
            return v

    return {}

async def consultar_cpf(cpf: Union[str, int], datasets: str = "bdcbasicdata") -> dict:
    cpf_str = str(cpf).strip()
    cpf_limpo = normalizar_cpf(cpf)
    
    if len(cpf_limpo) != 11:
        return {
            "status": "erro",
            "codigo_erro": "CPF_TAMANHO_INVALIDO",
            "etapa": "validacao_local",
            "fornecedor": "Veridian",
            "mensagem": f"CPF '{cpf_str}' inválido após higienização: deve conter 11 dígitos.",
            "retentavel": False
        }

    if not validar_cpf(cpf_limpo):
        return {
            "status": "erro",
            "codigo_erro": "CPF_INVALIDO",
            "etapa": "validacao_local",
            "fornecedor": "Veridian",
            "mensagem": f"CPF '{cpf_str}' é matematicamente inválido (dígitos verificadores incorretos).",
            "retentavel": False
        }

    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {
            "status": "erro",
            "codigo_erro": "CREDENCIAIS_AUSENTES",
            "etapa": "autenticacao",
            "fornecedor": "BigDataCorp",
            "mensagem": "BIGDATA_ACCESS_TOKEN não configurado no .env",
            "retentavel": False
        }

    chave_cache = f"bigdata_{cpf_limpo}"
    lock = _get_doc_lock(cpf_limpo, _cpf_locks)

    async with lock:
        cache_file = obter_caminho_cache_seguro(chave_cache)
        dados_cache = None
        datasets_existentes = set()

        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    dados_cache = json.load(f)
                if isinstance(dados_cache, dict):
                    meta = dados_cache.get("_metadata") or {}
                    datasets_existentes = set(meta.get("datasets_consultados", []))
                    if not datasets_existentes and "Result" in dados_cache and len(dados_cache["Result"]) > 0:
                        # Mapeia chaves existentes em códigos de dataset
                        r0 = dados_cache["Result"][0]
                        for k in r0.keys():
                            if k.startswith("_"): continue
                            k_lower = k.lower()
                            if k_lower in MAPA_RESULT_KEYS_PF:
                                datasets_existentes.add(MAPA_RESULT_KEYS_PF[k_lower])
                            for code_k, api_val in MAPA_DATASETS_PF.items():
                                if api_val.lower().replace("_", "") in k_lower:
                                    datasets_existentes.add(code_k)
            except Exception as e:
                print(f"[CACHE ERROR] Falha ao inspecionar cache existente do CPF {cpf_limpo}: {e}", file=sys.stderr, flush=True)

        lista_codigos = [c.strip().lower() for c in datasets.split(",") if c.strip()]
        lista_codigos_ativos = [c for c in lista_codigos if is_dataset_ativo(c, "pf")]
        if not lista_codigos_ativos:
            return {
                "status": "erro",
                "codigo_erro": "CONSULTA_DESATIVADA",
                "etapa": "validacao_permissao",
                "fornecedor": "Veridian",
                "mensagem": "Todos os datasets solicitados estão desativados pelo administrador nas configurações do MCP.",
                "retentavel": False
            }
        lista_codigos = lista_codigos_ativos
        datasets_faltantes = [c for c in lista_codigos if c not in datasets_existentes]

        # Se todos os datasets pedidos já estão no cache, retorna cache hit imediatamente
        if dados_cache and not datasets_faltantes:
            chaves_disp = list(dados_cache.get("Result", [{}])[0].keys()) if ("Result" in dados_cache and len(dados_cache["Result"]) > 0) else list(dados_cache.keys())
            return {
                "status": "sucesso",
                "cache_id": chave_cache,
                "mensagem": f"Consulta do CPF {cpf_limpo} recuperada do CACHE LOCAL (todos os datasets solicitados já estavam presentes).",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria' passando o CPF e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": [k for k in chaves_disp if not k.startswith("_")]
            }

        # Busca na API apenas os datasets faltantes (ou todos se não houver cache)
        datasets_para_buscar = datasets_faltantes if datasets_faltantes else lista_codigos
        lista_datasets_api = []
        contem_processes = False

        for cod in datasets_para_buscar:
            if cod in MAPA_DATASETS_PF:
                api_dataset = MAPA_DATASETS_PF[cod]
                if api_dataset == "processes":
                    contem_processes = True
                    lista_datasets_api.append("processes.limit(80)")
                else:
                    lista_datasets_api.append(api_dataset)
            else:
                lista_datasets_api.append(cod)

        datasets_string = ",".join(list(set(lista_datasets_api)))
        headers = {
            "AccessToken": bigdata_token,
            "Content-Type": "application/json"
        }
        if bigdata_token_id:
            headers["TokenId"] = bigdata_token_id

        payload = {
            "q": f"doc{{'{cpf_limpo}'}}",
            "Datasets": datasets_string
        }

        try:
            async with get_semaphore("bigdata"):
                response = await resilient_request(
                    "POST",
                    f"{BIGDATA_BASE_URL}/pessoas",
                    headers=headers,
                    json=payload
                )
                if response.status_code != 200:
                    return {
                        "status": "erro",
                        "codigo_erro": f"BIGDATA_HTTP_{response.status_code}",
                        "etapa": "requisicao_api",
                        "fornecedor": "BigDataCorp",
                        "mensagem": f"Erro HTTP {response.status_code} retornado pelo BigDataCorp: {response.text}",
                        "retentavel": response.status_code in (429, 502, 503, 504)
                    }

                novos_dados = response.json()
                
                # Inspeciona Status retornado pelo BigDataCorp
                status_obj = novos_dados.get("Status") or {}
                status_code = status_obj.get("Code", 0)
                status_msg = status_obj.get("Message", "OK")
                
                if status_code != 0:
                    return {
                        "status": "erro",
                        "codigo_erro": f"BIGDATA_{status_code}",
                        "etapa": "requisicao_api",
                        "fornecedor": "BigDataCorp",
                        "mensagem": f"Erro na API BigDataCorp: {status_msg} (Código {status_code})",
                        "retentavel": False,
                        "detalhes": status_obj
                    }

                # Paginação automática de processos se solicitado
                if contem_processes and "Result" in novos_dados and len(novos_dados["Result"]) > 0:
                    alvo_p = novos_dados["Result"][0]
                    if "Processes" in alvo_p:
                        proc_p = alvo_p["Processes"]
                        if proc_p and isinstance(proc_p, dict):
                            total_lawsuits = proc_p.get("TotalLawsuits", 0)
                            lawsuits_list = proc_p.get("Lawsuits", [])
                            max_lawsuits = min(total_lawsuits, 1000)
                            next_page_id = proc_p.get("NextPageId")
                            page = 1
                            while next_page_id and len(lawsuits_list) < max_lawsuits:
                                payload_next = {
                                    "q": f"doc{{'{cpf_limpo}'}}",
                                    "Datasets": f"processes.next({next_page_id})"
                                }
                                try:
                                    resp_next = await resilient_request("POST", f"{BIGDATA_BASE_URL}/pessoas", headers=headers, json=payload_next)
                                    if resp_next.status_code == 200:
                                        d_next = resp_next.json()
                                        if "Result" in d_next and len(d_next["Result"]) > 0:
                                            next_list = (d_next["Result"][0].get("Processes") or {}).get("Lawsuits", [])
                                            if not next_list: break
                                            lawsuits_list.extend(next_list)
                                            next_page_id = (d_next["Result"][0].get("Processes") or {}).get("NextPageId")
                                        else: break
                                    else: break
                                except Exception:
                                    break
                                page += 1
                            proc_p["Lawsuits"] = lawsuits_list[:max_lawsuits]

                # Merge inteligente: atualiza ou cria o cache com os novos datasets
                datasets_atualizados = list(datasets_existentes.union(set(datasets_para_buscar)))
                
                if dados_cache and isinstance(dados_cache, dict) and "Result" in dados_cache and len(dados_cache["Result"]) > 0:
                    if "Result" in novos_dados and len(novos_dados["Result"]) > 0:
                        dados_cache["Result"][0].update(novos_dados["Result"][0])
                    dados_cache["_metadata"] = {
                        "cache_id": chave_cache,
                        "datasets_consultados": datasets_atualizados,
                        "atualizado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    dados_finais = dados_cache
                else:
                    novos_dados["_metadata"] = {
                        "cache_id": chave_cache,
                        "datasets_consultados": datasets_atualizados,
                        "criado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    dados_finais = novos_dados

                salvar_cache_universal(chave_cache, dados_finais)

                chaves_disp = list(dados_finais["Result"][0].keys()) if ("Result" in dados_finais and len(dados_finais["Result"]) > 0) else list(dados_finais.keys())
                return {
                    "status": "sucesso",
                    "cache_id": chave_cache,
                    "mensagem": f"Consulta do CPF {cpf_limpo} realizada e salva no cache local ({len(datasets_para_buscar)} novos datasets mesclados).",
                    "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria' passando o CPF e um dos códigos desejados para ler os detalhes fatiados.",
                    "categorias_disponiveis": [k for k in chaves_disp if not k.startswith("_")]
                }

        except Exception as e:
            return {
                "status": "erro",
                "codigo_erro": "EXCECAO_CONSULTA_CPF",
                "etapa": "requisicao_api",
                "fornecedor": "BigDataCorp",
                "mensagem": f"Falha ao consultar CPF no BigDataCorp: {str(e) or repr(e)}",
                "retentavel": False
            }

async def ver_categoria_cpf(cpf: Union[str, int], dataset_code: str) -> dict:
    cpf_limpo = normalizar_cpf(cpf)
    codigo_limpo = dataset_code.strip().lower()
    
    # Mapeia aliases flexíveis (ex: 'processes', 'extendedphones', 'companies') para o código de dataset canônico
    codigo_canonico = MAPA_RESULT_KEYS_PF.get(codigo_limpo, codigo_limpo)
    if codigo_canonico not in MAPA_DATASETS_PF:
        for k, v in MAPA_DATASETS_PF.items():
            if v == codigo_limpo or v.replace("_", "") == codigo_limpo.replace("_", ""):
                codigo_canonico = k
                break
                
    chave_cache = f"bigdata_{cpf_limpo}"
    cache_file = obter_caminho_cache_seguro(chave_cache)
    
    dados_completos = None
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_completos = json.load(f)
        except Exception:
            dados_completos = None

    # Se o cache não existe ou o dataset pedido não foi consultado ainda, busca sob demanda na API
    meta_datasets = set((dados_completos.get("_metadata") or {}).get("datasets_consultados", [])) if dados_completos else set()
    precisa_consultar = (
        not dados_completos or
        (codigo_canonico in MAPA_DATASETS_PF and codigo_canonico not in meta_datasets)
    )
    
    if precisa_consultar and codigo_canonico in MAPA_DATASETS_PF:
        res_busca = await consultar_cpf(cpf, datasets=codigo_canonico)
        if res_busca.get("status") == "erro":
            return res_busca
        cache_file = obter_caminho_cache_seguro(chave_cache)
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    dados_completos = json.load(f)
            except Exception:
                return {"status": "erro", "mensagem": "Falha ao ler cache após consulta automática."}

    if not dados_completos:
        return {"status": "erro", "mensagem": f"Nenhum dado localizado para o CPF {cpf_limpo}."}

    resultado = filtrar_dados_pf(dados_completos, codigo_limpo)
    return {
        "status": "sucesso",
        "cache_id": chave_cache,
        "dataset": codigo_canonico if codigo_canonico in MAPA_DATASETS_PF else codigo_limpo,
        codigo_limpo: resultado
    }

async def consultar_cnpj(cnpj: Union[str, int], datasets: str = "bdccompanybasicdata") -> dict:
    cnpj_str = str(cnpj).strip()
    cnpj_limpo = normalizar_cnpj(cnpj)
    
    if len(cnpj_limpo) != 14:
        return {
            "status": "erro",
            "codigo_erro": "CNPJ_TAMANHO_INVALIDO",
            "etapa": "validacao_local",
            "fornecedor": "Veridian",
            "mensagem": f"CNPJ '{cnpj_str}' inválido após higienização: deve conter 14 dígitos.",
            "retentavel": False
        }

    if not validar_cnpj(cnpj_limpo):
        return {
            "status": "erro",
            "codigo_erro": "CNPJ_INVALIDO",
            "etapa": "validacao_local",
            "fornecedor": "Veridian",
            "mensagem": f"CNPJ '{cnpj_str}' é matematicamente inválido (dígitos verificadores incorretos).",
            "retentavel": False
        }

    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {
            "status": "erro",
            "codigo_erro": "CREDENCIAIS_AUSENTES",
            "etapa": "autenticacao",
            "fornecedor": "BigDataCorp",
            "mensagem": "BIGDATA_ACCESS_TOKEN não configurado no .env",
            "retentavel": False
        }

    chave_cache = f"bigdata_cnpj_{cnpj_limpo}"
    lock = _get_doc_lock(cnpj_limpo, _cnpj_locks)

    async with lock:
        cache_file = obter_caminho_cache_seguro(chave_cache)
        dados_cache = None
        datasets_existentes = set()

        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    dados_cache = json.load(f)
                if isinstance(dados_cache, dict):
                    meta = dados_cache.get("_metadata") or {}
                    datasets_existentes = set(meta.get("datasets_consultados", []))
                    if not datasets_existentes and "Result" in dados_cache and len(dados_cache["Result"]) > 0:
                        r0 = dados_cache["Result"][0]
                        for k in r0.keys():
                            if k.startswith("_"): continue
                            k_lower = k.lower()
                            if k_lower in MAPA_RESULT_KEYS_PJ:
                                datasets_existentes.add(MAPA_RESULT_KEYS_PJ[k_lower])
                            for code_k, api_val in MAPA_DATASETS_PJ.items():
                                if api_val.lower().replace("_", "") in k_lower:
                                    datasets_existentes.add(code_k)
            except Exception as e:
                print(f"[CACHE ERROR] Falha ao inspecionar cache existente do CNPJ {cnpj_limpo}: {e}", file=sys.stderr, flush=True)

        lista_codigos = [c.strip().lower() for c in datasets.split(",") if c.strip()]
        lista_codigos_ativos = [c for c in lista_codigos if is_dataset_ativo(c, "pj")]
        if not lista_codigos_ativos:
            return {
                "status": "erro",
                "codigo_erro": "CONSULTA_DESATIVADA",
                "etapa": "validacao_permissao",
                "fornecedor": "Veridian",
                "mensagem": "Todos os datasets solicitados estão desativados pelo administrador nas configurações do MCP.",
                "retentavel": False
            }
        lista_codigos = lista_codigos_ativos
        datasets_faltantes = [c for c in lista_codigos if c not in datasets_existentes]

        if dados_cache and not datasets_faltantes:
            chaves_disp = list(dados_cache.get("Result", [{}])[0].keys()) if ("Result" in dados_cache and len(dados_cache["Result"]) > 0) else list(dados_cache.keys())
            return {
                "status": "sucesso",
                "cache_id": chave_cache,
                "mensagem": f"Consulta do CNPJ {cnpj_limpo} recuperada do CACHE LOCAL (todos os datasets solicitados já estavam presentes).",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": [k for k in chaves_disp if not k.startswith("_")]
            }

        datasets_para_buscar = datasets_faltantes if datasets_faltantes else lista_codigos
        lista_datasets_api = []
        
        for cod in datasets_para_buscar:
            if cod in MAPA_DATASETS_PJ:
                api_dataset = MAPA_DATASETS_PJ[cod]
                lista_datasets_api.append(api_dataset)
            else:
                lista_datasets_api.append(cod)

        datasets_string = ",".join(list(set(lista_datasets_api)))
        headers = {
            "AccessToken": bigdata_token,
            "Content-Type": "application/json"
        }
        if bigdata_token_id:
            headers["TokenId"] = bigdata_token_id

        payload = {
            "q": f"doc{{'{cnpj_limpo}'}}",
            "Datasets": datasets_string
        }

        try:
            async with get_semaphore("bigdata"):
                response = await resilient_request(
                    "POST",
                    f"{BIGDATA_BASE_URL}/empresas",
                    headers=headers,
                    json=payload
                )
                if response.status_code != 200:
                    return {
                        "status": "erro",
                        "codigo_erro": f"BIGDATA_HTTP_{response.status_code}",
                        "etapa": "requisicao_api",
                        "fornecedor": "BigDataCorp",
                        "mensagem": f"Erro HTTP {response.status_code} retornado pelo BigDataCorp: {response.text}",
                        "retentavel": response.status_code in (429, 502, 503, 504)
                    }

                novos_dados = response.json()
                status_obj = novos_dados.get("Status") or {}
                status_code = status_obj.get("Code", 0)
                status_msg = status_obj.get("Message", "OK")
                
                if status_code != 0:
                    return {
                        "status": "erro",
                        "codigo_erro": f"BIGDATA_{status_code}",
                        "etapa": "requisicao_api",
                        "fornecedor": "BigDataCorp",
                        "mensagem": f"Erro na API BigDataCorp: {status_msg} (Código {status_code})",
                        "retentavel": False,
                        "detalhes": status_obj
                    }

                datasets_atualizados = list(datasets_existentes.union(set(datasets_para_buscar)))
                
                if dados_cache and isinstance(dados_cache, dict) and "Result" in dados_cache and len(dados_cache["Result"]) > 0:
                    if "Result" in novos_dados and len(novos_dados["Result"]) > 0:
                        dados_cache["Result"][0].update(novos_dados["Result"][0])
                    dados_cache["_metadata"] = {
                        "cache_id": chave_cache,
                        "datasets_consultados": datasets_atualizados,
                        "atualizado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    dados_finais = dados_cache
                else:
                    novos_dados["_metadata"] = {
                        "cache_id": chave_cache,
                        "datasets_consultados": datasets_atualizados,
                        "criado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                    dados_finais = novos_dados

                salvar_cache_universal(chave_cache, dados_finais)

                chaves_disp = list(dados_finais["Result"][0].keys()) if ("Result" in dados_finais and len(dados_finais["Result"]) > 0) else list(dados_finais.keys())
                return {
                    "status": "sucesso",
                    "cache_id": chave_cache,
                    "mensagem": f"Consulta do CNPJ {cnpj_limpo} realizada e salva no cache local ({len(datasets_para_buscar)} novos datasets mesclados).",
                    "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados para ler os detalhes fatiados.",
                    "categorias_disponiveis": [k for k in chaves_disp if not k.startswith("_")]
                }

        except Exception as e:
            return {
                "status": "erro",
                "codigo_erro": "EXCECAO_CONSULTA_CNPJ",
                "etapa": "requisicao_api",
                "fornecedor": "BigDataCorp",
                "mensagem": f"Falha ao consultar CNPJ no BigDataCorp: {str(e) or repr(e)}",
                "retentavel": False
            }

async def ver_categoria_cnpj(cnpj: Union[str, int], dataset_code: str) -> dict:
    cnpj_limpo = normalizar_cnpj(cnpj)
    codigo_limpo = dataset_code.strip().lower()
    
    codigo_canonico = MAPA_RESULT_KEYS_PJ.get(codigo_limpo, codigo_limpo)
    if codigo_canonico not in MAPA_DATASETS_PJ:
        for k, v in MAPA_DATASETS_PJ.items():
            if v == codigo_limpo or v.replace("_", "") == codigo_limpo.replace("_", ""):
                codigo_canonico = k
                break
                
    chave_cache = f"bigdata_cnpj_{cnpj_limpo}"
    cache_file = obter_caminho_cache_seguro(chave_cache)
    
    dados_completos = None
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_completos = json.load(f)
        except Exception:
            dados_completos = None

    meta_datasets = set((dados_completos.get("_metadata") or {}).get("datasets_consultados", [])) if dados_completos else set()
    precisa_consultar = (
        not dados_completos or
        (codigo_canonico in MAPA_DATASETS_PJ and codigo_canonico not in meta_datasets)
    )
    
    if precisa_consultar and codigo_canonico in MAPA_DATASETS_PJ:
        res_busca = await consultar_cnpj(cnpj, datasets=codigo_canonico)
        if res_busca.get("status") == "erro":
            return res_busca
        cache_file = obter_caminho_cache_seguro(chave_cache)
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    dados_completos = json.load(f)
            except Exception:
                return {"status": "erro", "mensagem": "Falha ao ler cache após consulta automática."}

    if not dados_completos:
        return {"status": "erro", "mensagem": f"Nenhum dado localizado para o CNPJ {cnpj_limpo}."}

    resultado = filtrar_dados_pj(dados_completos, codigo_limpo)
    return {
        "status": "sucesso",
        "cache_id": chave_cache,
        "dataset": codigo_canonico if codigo_canonico in MAPA_DATASETS_PJ else codigo_limpo,
        codigo_limpo: resultado
    }

async def consultar_processo(numero_processo: Union[str, int], dataset_code: str = "bdclawsuitbasicdata") -> dict:
    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {
            "status": "erro",
            "codigo_erro": "CREDENCIAIS_AUSENTES",
            "etapa": "autenticacao",
            "fornecedor": "BigDataCorp",
            "mensagem": "BIGDATA_ACCESS_TOKEN não configurado no .env",
            "retentavel": False
        }
        
    cnj_formatado, proc_limpo = normalizar_cnj(numero_processo)
    
    headers = {
        "AccessToken": bigdata_token,
        "Content-Type": "application/json"
    }
    query_param = cnj_formatado if cnj_formatado else proc_limpo
    payload = {
        "q": f"lawsuit_cnj_number{{'{query_param}'}}",
        "Datasets": "processes"
    }
    
    try:
        async with get_semaphore("bigdata"):
            response = await resilient_request(
                "POST",
                f"{BIGDATA_BASE_URL}/processos",
                headers=headers,
                json=payload
            )
            if response.status_code != 200:
                return {
                    "status": "erro",
                    "codigo_erro": f"BIGDATA_HTTP_{response.status_code}",
                    "etapa": "requisicao_api",
                    "fornecedor": "BigDataCorp",
                    "mensagem": f"Erro na consulta de processo no BigDataCorp: HTTP {response.status_code}",
                    "detalhes": response.text
                }
            dados = response.json()
            status_obj = dados.get("Status") or {}
            status_code = status_obj.get("Code", 0)
            status_msg = status_obj.get("Message", "OK")
            
            if status_code != 0:
                return {
                    "status": "erro",
                    "codigo_erro": f"BIGDATA_{status_code}",
                    "etapa": "requisicao_api",
                    "fornecedor": "BigDataCorp",
                    "mensagem": f"Erro retornado pela API BigDataCorp: {status_msg} (Código {status_code})",
                    "retentavel": False,
                    "detalhes": status_obj
                }

            return {"status": "sucesso", "resultado": dados}
    except Exception as e:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_CONEXAO",
            "etapa": "requisicao_api",
            "fornecedor": "BigDataCorp",
            "mensagem": f"Erro ao consultar processo no BigDataCorp: {str(e)}",
            "retentavel": False
        }

async def consultar_categoria_cpf(cpf: Union[str, int], dataset_code: str) -> dict:
    """
    Executa a consulta de um dataset específico de PF na BigDataCorp e retorna a fatia correspondente.
    Verifica se a consulta está habilitada no MCP.
    """
    if not is_dataset_ativo(dataset_code, "pf"):
        return {
            "status": "erro",
            "codigo_erro": "CONSULTA_DESATIVADA",
            "etapa": "validacao_permissao",
            "fornecedor": "Veridian",
            "mensagem": f"A consulta do dataset '{dataset_code}' está desativada nas configurações do MCP.",
            "retentavel": False
        }
    res_consulta = await consultar_cpf(cpf, datasets=dataset_code)
    if res_consulta.get("status") == "erro":
        return res_consulta
    return await ver_categoria_cpf(cpf, dataset_code=dataset_code)

async def consultar_categoria_cnpj(cnpj: Union[str, int], dataset_code: str) -> dict:
    """
    Executa a consulta de um dataset específico de PJ na BigDataCorp e retorna a fatia correspondente.
    Verifica se a consulta está habilitada no MCP.
    """
    if not is_dataset_ativo(dataset_code, "pj"):
        return {
            "status": "erro",
            "codigo_erro": "CONSULTA_DESATIVADA",
            "etapa": "validacao_permissao",
            "fornecedor": "Veridian",
            "mensagem": f"A consulta do dataset '{dataset_code}' está desativada nas configurações do MCP.",
            "retentavel": False
        }
    res_consulta = await consultar_cnpj(cnpj, datasets=dataset_code)
    if res_consulta.get("status") == "erro":
        return res_consulta
    return await ver_categoria_cnpj(cnpj, dataset_code=dataset_code)

