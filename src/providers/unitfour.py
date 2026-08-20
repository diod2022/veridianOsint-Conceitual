import os
import urllib.parse
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import UNITFOUR_TOKEN
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore
from src.core.security import normalizar_cpf, normalizar_cnpj

UNITFOUR_BASE_URL = "https://webapi.unitfour.com.br"

def _get_headers() -> dict:
    token = os.environ.get("UNITFOUR_TOKEN", "")
    return {
        "Authorization": f"Token {token}",
        "Accept": "application/json"
    }

async def consultar_cpf(cpf: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cpf_str = normalizar_cpf(cpf)
    
    cache_hit = checar_cache_universal(f"unitfour_cpf_{cpf_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisica/{cpf_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_cpf_{cpf_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar CPF na Unitfour: {str(e)}"}

async def pessoas_ligadas(cpf: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cpf_str = normalizar_cpf(cpf)
    
    cache_hit = checar_cache_universal(f"unitfour_ligados_{cpf_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaPessoasLigadas/{cpf_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_ligados_{cpf_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar pessoas ligadas na Unitfour: {str(e)}"}

async def mandados_prisao(cpf: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cpf_str = normalizar_cpf(cpf)
    
    cache_hit = checar_cache_universal(f"unitfour_mandados_{cpf_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Compliance/v1/MandadosPrisao/{cpf_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_mandados_{cpf_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar mandados de prisão na Unitfour: {str(e)}"}

async def antecedentes_criminais(cpf: Union[str, int], nome: Optional[str] = None) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cpf_str = normalizar_cpf(cpf)
    
    cache_hit = checar_cache_universal(f"unitfour_antecedentes_{cpf_str}")
    if cache_hit:
        return cache_hit

    params = {"nome": nome} if nome else {}
    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Compliance/v1/AntecedentesCriminais/{cpf_str}",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_antecedentes_{cpf_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar antecedentes criminais na Unitfour: {str(e)}"}

async def consulta_pep(cpf: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cpf_str = normalizar_cpf(cpf)
    
    cache_hit = checar_cache_universal(f"unitfour_pep_{cpf_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pep/v1/ConsultaPEPCoaf/{cpf_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_pep_{cpf_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar PEP na Unitfour: {str(e)}"}

async def consultar_cnpj(cnpj: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cnpj_str = normalizar_cnpj(cnpj)
    
    cache_hit = checar_cache_universal(f"unitfour_cnpj_{cnpj_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaJuridica/{cnpj_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_cnpj_{cnpj_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar CNPJ na Unitfour: {str(e)}"}

async def tomadores_decisao(cnpj: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cnpj_str = normalizar_cnpj(cnpj)
    
    cache_hit = checar_cache_universal(f"unitfour_tomadores_{cnpj_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaTomadoresDecisao/{cnpj_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_tomadores_{cnpj_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar tomadores de decisão na Unitfour: {str(e)}"}

async def empresas_ligadas(cnpj: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cnpj_str = normalizar_cnpj(cnpj)
    
    cache_hit = checar_cache_universal(f"unitfour_empresas_ligadas_{cnpj_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaEmpresasLigadas/{cnpj_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_empresas_ligadas_{cnpj_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao buscar empresas ligadas na Unitfour: {str(e)}"}

async def proprietario_veiculo_placa(placa: str) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    placa_str = str(placa).upper().strip().replace("-", "")
    
    cache_hit = checar_cache_universal(f"unitfour_veiculo_{placa_str}")
    if cache_hit:
        return cache_hit

    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Veiculo/v1/ProprietarioVeiculo/Placa/{placa_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_veiculo_{placa_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao consultar placa na Unitfour: {str(e)}"}

async def busca_avancada_nome(nome: str, bairro: str = None, cidade: str = None, uf: str = None) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    nome_str = str(nome).strip()
    nome_quoted = urllib.parse.quote(nome_str)
    
    params = {}
    if bairro: params["bairro"] = bairro
    if cidade: params["cidade"] = cidade
    if uf: params["uf"] = uf
    
    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaNome/{nome_quoted}",
                headers=_get_headers(),
                params=params
            )
            response.raise_for_status()
            nome_limpo = "".join(c for c in nome_str if c.isalnum() or c == " ").strip().lower().replace(" ", "_")
            return salvar_cache_universal(f"unitfour_busca_nome_{nome_limpo}", response.json())
        except Exception as e:
            return {"error": f"Erro ao realizar busca avançada por nome na Unitfour: {str(e)}"}

async def busca_avancada_telefone(ddd: Union[str, int], telefone: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    ddd_str = str(ddd).strip()
    tel_str = str(telefone).strip()
    
    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaTelefone/{ddd_str}/{tel_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_busca_tel_{ddd_str}{tel_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao realizar busca avançada por telefone na Unitfour: {str(e)}"}

async def busca_avancada_email(email: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    email_str = str(email).strip().lower()
    
    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaEmail",
                headers=_get_headers(),
                params={"email": email_str}
            )
            response.raise_for_status()
            email_limpo = email_str.replace("@", "_at_").replace(".", "_")
            return salvar_cache_universal(f"unitfour_busca_email_{email_limpo}", response.json())
        except Exception as e:
            return {"error": f"Erro ao realizar busca avançada por e-mail na Unitfour: {str(e)}"}

async def busca_avancada_cep(cep: Union[str, int]) -> dict:
    if not os.environ.get("UNITFOUR_TOKEN"):
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
    cep_str = str(cep).strip().replace("-", "")
    
    async with get_semaphore("unitfour"):
        try:
            response = await resilient_request(
                "GET",
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaCep/{cep_str}",
                headers=_get_headers()
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_busca_cep_{cep_str}", response.json())
        except Exception as e:
            return {"error": f"Erro ao realizar busca avançada por CEP na Unitfour: {str(e)}"}
