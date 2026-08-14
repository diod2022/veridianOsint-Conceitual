import os
import json
import re
import sys
import httpx
from typing import Optional, Union, Dict, Any, List
from src.core.config import CACHE_DIR, get_bigdata_token, get_bigdata_token_id
from src.core.http_client import resilient_request, get_semaphore
from src.core.security import normalizar_cpf, normalizar_cnpj

BIGDATA_BASE_URL = "https://plataforma.bigdatacorp.com.br"

MAPA_DATASETS_PF = {
    "bdcbasicdata": "basic_data",
    "bdcphones": "phones_extended",
    "bdcemails": "emails_extended",
    "bdcaddresses": "addresses_extended",
    "bdclawsuits": "processes",
    "bdcrelatedpeople": "related_people",
    "bdcrelatedcompanies": "related_people",
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

    dataset_code = dataset_code.strip().lower()
    
    if dataset_code == "bdcbasicdata":
        return get_nested_case_insensitive(alvo, "BasicData") or {}
    elif dataset_code == "bdcphones":
        return get_nested_case_insensitive(alvo, "ExtendedPhones") or []
    elif dataset_code == "bdcemails":
        return get_nested_case_insensitive(alvo, "ExtendedEmails") or []
    elif dataset_code == "bdcaddresses":
        return get_nested_case_insensitive(alvo, "ExtendedAddresses") or []
    elif dataset_code == "bdclawsuits":
        return get_nested_case_insensitive(alvo, "Processes") or {}
    elif dataset_code == "bdcrelatedpeople":
        return get_nested_case_insensitive(alvo, "RelatedPeople") or []
    elif dataset_code == "bdcrelatedcompanies":
        return get_nested_case_insensitive(alvo, "RelatedPeople") or []
    elif dataset_code == "bdcdomains":
        return get_nested_case_insensitive(alvo, "Domains") or []
    elif dataset_code == "bdcpolitics":
        return get_nested_case_insensitive(alvo, "ElectoralData") or {}
    elif dataset_code == "bdchistorical":
        return get_nested_case_insensitive(alvo, "HistoricalBasicData") or {}
    elif dataset_code == "bdcfamilysocialbenefits":
        return get_nested_case_insensitive(alvo, "KycData") or {}
    elif dataset_code == "bdcprofessional":
        return get_nested_case_insensitive(alvo, "ProfessionData") or {}
    elif dataset_code == "bdcclass":
        return get_nested_case_insensitive(alvo, "Memberships") or []
    elif dataset_code == "bdclicenses":
        return get_nested_case_insensitive(alvo, "Memberships") or []
    elif dataset_code == "bdcindustrialproperty":
        return get_nested_case_insensitive(alvo, "IndustrialProperty") or {}
    elif dataset_code == "bdcpublicservant":
        return get_nested_case_insensitive(alvo, "ProfessionData") or {}
    elif dataset_code == "bdcturnover":
        return get_nested_case_insensitive(alvo, "FinantialData") or {}
    elif dataset_code == "bdcelectoralcandidate":
        return get_nested_case_insensitive(alvo, "ElectionCandidateData") or []
    elif dataset_code == "bdcelectoralproviders":
        return get_nested_case_insensitive(alvo, "ElectoralProviders") or []
    elif dataset_code == "bdconlineadvertisements":
        return get_nested_case_insensitive(alvo, "OnlineAds") or []
    elif dataset_code == "bdcgovernmentdebtors":
        return get_nested_case_insensitive(alvo, "GovernmentDebtors") or {}
    elif dataset_code == "bdcelectoraldonorspersonal":
        return get_nested_case_insensitive(alvo, "ElectoralDonors") or []
    elif dataset_code == "bdccollections":
        return get_nested_case_insensitive(alvo, "Collections") or []
    elif dataset_code == "bdcsocialassistance":
        return get_nested_case_insensitive(alvo, "KycData") or {}
    elif dataset_code == "bdcfamilypoliticalhistory":
        return get_nested_case_insensitive(alvo, "FamilyPoliticalHistory") or {}
    elif dataset_code == "bdconlinepresence":
        return get_nested_case_insensitive(alvo, "OnlinePresence") or {}
        
    return alvo

def filtrar_dados_pj(dados_completos: dict, dataset_code: str) -> Any:
    alvo = dados_completos
    if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
        alvo = dados_completos["Result"][0]
        
    if not isinstance(alvo, dict):
        return alvo

    dataset_code = dataset_code.strip().lower()
    
    if dataset_code == "bdccompanybasicdata":
        return get_nested_case_insensitive(alvo, "BasicData") or {}
    elif dataset_code == "bdccompanyphones":
        return get_nested_case_insensitive(alvo, "ExtendedPhones") or get_nested_case_insensitive(alvo, "Contacts.Phones") or []
    elif dataset_code == "bdccompanyemails":
        return get_nested_case_insensitive(alvo, "ExtendedEmails") or get_nested_case_insensitive(alvo, "Contacts.Emails") or []
    elif dataset_code == "bdccompanyaddresses":
        return get_nested_case_insensitive(alvo, "ExtendedAddresses") or get_nested_case_insensitive(alvo, "Contacts.Addresses") or []
    elif dataset_code == "bdccompanyevolution":
        return get_nested_case_insensitive(alvo, "CompanyEvolutionData") or get_nested_case_insensitive(alvo, "CompanyEvolution") or {}
    elif dataset_code == "bdcelectoraldonorscompany":
        return get_nested_case_insensitive(alvo, "ElectoralDonors") or []
    elif dataset_code == "bdclawsuits":
        return get_nested_case_insensitive(alvo, "Lawsuits") or get_nested_case_insensitive(alvo, "Processes") or {}
    elif dataset_code == "bdccompanyrelationships":
        return get_nested_case_insensitive(alvo, "Relationships") or {}
    elif dataset_code == "bdccompanyhistorical":
        return get_nested_case_insensitive(alvo, "HistoryBasicData") or {}

    return alvo

async def consultar_cpf(cpf: Union[str, int], datasets: str = "bdcbasicdata") -> dict:
    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    cpf_limpo = normalizar_cpf(cpf)
    if len(cpf_limpo) != 11:
        return {"error": f"CPF inválido após higienização: '{cpf_limpo}' (deve ter 11 dígitos)"}
        
    chave_cache = f"bigdata_{cpf_limpo}"
    cache_file = os.path.join(CACHE_DIR, f"{chave_cache}.json")
    
    if os.path.exists(cache_file):
        print(f"[CACHE HIT] CPF {cpf_limpo} recuperado do cache local.", file=sys.stderr, flush=True)
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_completos = json.load(f)
            chaves_disponiveis = []
            if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
                chaves_disponiveis = list(dados_completos["Result"][0].keys())
            else:
                chaves_disponiveis = list(dados_completos.keys())
            return {
                "status": "sucesso",
                "mensagem": f"Consulta do CPF {cpf_limpo} recuperada do CACHE LOCAL.",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria' passando o CPF e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": chaves_disponiveis
            }
        except Exception as e:
            print(f"[CACHE ERROR] Falha ao carregar cache do CPF {cpf_limpo}: {str(e)}", file=sys.stderr, flush=True)
            
    lista_codigos = [c.strip().lower() for c in datasets.split(",")]
    lista_datasets_api = []
    contem_processes = False
    
    for cod in lista_codigos:
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
            response.raise_for_status()
            dados_completos = response.json()
            
            if contem_processes and "Result" in dados_completos and len(dados_completos["Result"]) > 0:
                alvo = dados_completos["Result"][0]
                if "Processes" in alvo:
                    processes_data = alvo["Processes"]
                    if processes_data and isinstance(processes_data, dict):
                        total_lawsuits = processes_data.get("TotalLawsuits", 0)
                        lawsuits_list = processes_data.get("Lawsuits", [])
                        max_lawsuits = min(total_lawsuits, 1000)
                        
                        if total_lawsuits > len(lawsuits_list) and len(lawsuits_list) < max_lawsuits:
                            next_page_id = processes_data.get("NextPageId")
                            page = 1
                            while next_page_id and len(lawsuits_list) < max_lawsuits:
                                payload_next = {
                                    "q": f"doc{{'{cpf_limpo}'}}",
                                    "Datasets": f"processes.next({next_page_id})"
                                }
                                try:
                                    response_next = await resilient_request(
                                        "POST",
                                        f"{BIGDATA_BASE_URL}/pessoas",
                                        headers=headers,
                                        json=payload_next
                                    )
                                    response_next.raise_for_status()
                                    data_next = response_next.json()
                                    
                                    if "Result" in data_next and len(data_next["Result"]) > 0:
                                        alvo_next = data_next["Result"][0]
                                        lawsuits_data_next = alvo_next.get("Processes", {})
                                        next_list = lawsuits_data_next.get("Lawsuits", [])
                                        if not next_list:
                                            break
                                        lawsuits_list.extend(next_list)
                                        next_page_id = lawsuits_data_next.get("NextPageId")
                                    else:
                                        break
                                except Exception as e:
                                    print(f"[BDC PAGINATION ERROR] Falha na página {page}: {str(e)}", file=sys.stderr, flush=True)
                                    break
                                page += 1
                            processes_data["Lawsuits"] = lawsuits_list[:max_lawsuits]
                            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)
                
            chaves_disponiveis = []
            if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
                chaves_disponiveis = list(dados_completos["Result"][0].keys())
            else:
                chaves_disponiveis = list(dados_completos.keys())
                
            return {
                "status": "sucesso",
                "mensagem": f"Consulta do CPF {cpf_limpo} realizada e salva no cache local.",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria' passando o CPF e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": chaves_disponiveis
            }
    except httpx.HTTPStatusError as e:
        return {"error": f"Erro HTTP {e.response.status_code} no BigDataCorp", "detalhes": e.response.text}
    except Exception as e:
        return {"error": f"Erro ao consultar CPF no BigDataCorp: {str(e)}"}

async def ver_categoria_cpf(cpf: Union[str, int], dataset_code: str) -> dict:
    cpf_limpo = normalizar_cpf(cpf)
    cache_file = os.path.join(CACHE_DIR, f"bigdata_{cpf_limpo}.json")
    
    if not os.path.exists(cache_file):
        return {"error": f"Nenhum cache encontrado para o CPF {cpf_limpo}. Execute `bigdata_consultar_cpf` primeiro."}
        
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados_completos = json.load(f)
            
        codigo_limpo = dataset_code.strip().lower()
        resultado = filtrar_dados_pf(dados_completos, codigo_limpo)
        return {codigo_limpo: resultado}
    except Exception as e:
        return {"error": f"Erro ao ler o cache do CPF: {str(e)}"}

async def consultar_cnpj(cnpj: Union[str, int], datasets: str = "bdccompanybasicdata") -> dict:
    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    cnpj_limpo = normalizar_cnpj(cnpj)
    if len(cnpj_limpo) != 14:
        return {"error": f"CNPJ inválido após higienização: '{cnpj_limpo}' (deve ter 14 dígitos)"}
        
    chave_cache = f"bigdata_cnpj_{cnpj_limpo}"
    cache_file = os.path.join(CACHE_DIR, f"{chave_cache}.json")
    
    if os.path.exists(cache_file):
        print(f"[CACHE HIT] CNPJ {cnpj_limpo} recuperado do cache local.", file=sys.stderr, flush=True)
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_completos = json.load(f)
            chaves_disponiveis = []
            if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
                chaves_disponiveis = list(dados_completos["Result"][0].keys())
            else:
                chaves_disponiveis = list(dados_completos.keys())
            return {
                "status": "sucesso",
                "mensagem": f"Consulta do CNPJ {cnpj_limpo} recuperada do CACHE LOCAL.",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": chaves_disponiveis
            }
        except Exception as e:
            print(f"[CACHE ERROR] Falha ao carregar cache do CNPJ {cnpj_limpo}: {str(e)}", file=sys.stderr, flush=True)

    lista_codigos = [c.strip().lower() for c in datasets.split(",")]
    lista_datasets_api = []
    
    for cod in lista_codigos:
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
            response.raise_for_status()
            dados_completos = response.json()
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(dados_completos, f, ensure_ascii=False, indent=2)
                
            chaves_disponiveis = []
            if "Result" in dados_completos and len(dados_completos["Result"]) > 0:
                chaves_disponiveis = list(dados_completos["Result"][0].keys())
            else:
                chaves_disponiveis = list(dados_completos.keys())
                
            return {
                "status": "sucesso",
                "mensagem": f"Consulta do CNPJ {cnpj_limpo} realizada e salva no cache local.",
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados para ler os detalhes fatiados.",
                "categorias_disponiveis": chaves_disponiveis
            }
    except httpx.HTTPStatusError as e:
        return {"error": f"Erro HTTP {e.response.status_code} no BigDataCorp", "detalhes": e.response.text}
    except Exception as e:
        return {"error": f"Erro ao consultar CNPJ no BigDataCorp: {str(e)}"}

async def ver_categoria_cnpj(cnpj: Union[str, int], dataset_code: str) -> dict:
    cnpj_limpo = normalizar_cnpj(cnpj)
    cache_file = os.path.join(CACHE_DIR, f"bigdata_cnpj_{cnpj_limpo}.json")
    
    if not os.path.exists(cache_file):
        return {"error": f"Nenhum cache encontrado para o CNPJ {cnpj_limpo}. Execute `bigdata_consultar_cnpj` primeiro."}
        
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados_completos = json.load(f)
            
        codigo_limpo = dataset_code.strip().lower()
        resultado = filtrar_dados_pj(dados_completos, codigo_limpo)
        return {codigo_limpo: resultado}
    except Exception as e:
        return {"error": f"Erro ao ler o cache do CNPJ: {str(e)}"}

async def consultar_processo(numero_processo: Union[str, int], dataset_code: str = "bdclawsuitbasicdata") -> dict:
    bigdata_token = get_bigdata_token()
    bigdata_token_id = get_bigdata_token_id()
    if not bigdata_token or bigdata_token == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    proc_str = str(numero_processo).strip()
    proc_limpo = re.sub(r"[^\d\-.]", "", proc_str)
    
    headers = {
        "AccessToken": bigdata_token,
        "Content-Type": "application/json"
    }
    if bigdata_token_id:
        headers["TokenId"] = bigdata_token_id

    payload = {
        "q": f"lawsuit_cnj_number{{'{proc_limpo}'}}",
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
            response.raise_for_status()
            dados = response.json()
            return {"status": "sucesso", "resultado": dados}
    except Exception as e:
        return {"error": f"Erro ao consultar processo no BigDataCorp: {str(e)}"}
