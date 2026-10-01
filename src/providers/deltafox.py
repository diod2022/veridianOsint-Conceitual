import os
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import DELTAFOX_TOKEN, DELTAFOX_BASE_URL
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore
from src.core.security import normalizar_cpf, normalizar_cnpj, normalizar_placa, so_digitos

DELTAFOX_DEFAULT_URL = "https://api.deltaid.api.br"
TIMEOUT_DELTAFOX = 120.0

def _get_token() -> str:
    return os.environ.get("DELTAFOX_TOKEN", DELTAFOX_TOKEN).strip()

def _get_base_url() -> str:
    url = os.environ.get("DELTAFOX_BASE_URL", DELTAFOX_BASE_URL).strip()
    return url if url else DELTAFOX_DEFAULT_URL

def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Accept": "application/json"
    }

async def consultar_servicos_disponiveis() -> dict:
    """
    Lista todos os serviços veiculares e de condutores contratados e liberados para o token na DeltaFox.
    """
    token = _get_token()
    if not token:
        return {"error": "DELTAFOX_TOKEN não configurado no .env"}

    cache_key = "deltafox_servicos_disponiveis"
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    base_url = _get_base_url()
    async with get_semaphore("deltafox"):
        try:
            response = await resilient_request(
                "GET",
                f"{base_url}/api/servicos",
                headers=_get_headers(),
                timeout=TIMEOUT_DELTAFOX
            )
            if response.status_code == 200:
                data = response.json()
                return salvar_cache_universal(cache_key, data)
            elif response.status_code == 401:
                return {"error": "Token da DeltaFox inválido ou expirado."}
            else:
                return {
                    "error": f"Erro ao consultar serviços DeltaFox (HTTP {response.status_code}): {response.text}"
                }
        except Exception as e:
            return {"error": f"Falha de conexão com a DeltaFox: {str(e)}"}

async def _consultar_servico(servico: str, valor: str, cache_key: str) -> dict:
    """
    Função centralizada para chamada aos endpoints da DeltaFox com timeout estendido,
    controle de concorrência e tratamento específico de erros.
    """
    token = _get_token()
    if not token:
        return {"error": "DELTAFOX_TOKEN não configurado no .env"}

    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    base_url = _get_base_url()
    params = {
        "servico": servico,
        "valor": valor
    }

    async with get_semaphore("deltafox"):
        try:
            response = await resilient_request(
                "GET",
                f"{base_url}/api/consultar",
                headers=_get_headers(),
                params=params,
                timeout=TIMEOUT_DELTAFOX
            )

            if response.status_code == 200:
                data = response.json()
                return salvar_cache_universal(cache_key, data)

            elif response.status_code == 422:
                # 422: Consulta executada com sucesso, mas nenhum registro encontrado para a entrada
                try:
                    payload = response.json()
                except Exception:
                    payload = {
                        "sucesso": False,
                        "parcial": False,
                        "mensagens": ["Nenhum dado encontrado para a entrada informada."]
                    }
                return salvar_cache_universal(cache_key, payload)

            elif response.status_code == 400:
                try:
                    err_json = response.json()
                    msgs = err_json.get("mensagens", [err_json.get("erro", "Parâmetro inválido")])
                    return {"error": f"Parâmetro inválido: {'; '.join(msgs)}"}
                except Exception:
                    return {"error": f"Parâmetro inválido na consulta: {response.text}"}

            elif response.status_code == 401:
                return {"error": "Token de autenticação da DeltaFox inválido, inativo ou ausente."}

            elif response.status_code == 403:
                try:
                    err_json = response.json()
                    return {"error": f"Serviço não contratado ou não liberado: {err_json.get('erro', response.text)}"}
                except Exception:
                    return {"error": f"Acesso não autorizado na DeltaFox: {response.text}"}

            elif response.status_code == 429:
                return {"error": "Limite de consultas contratadas atingido. Aguarde alguns instantes e tente novamente."}

            elif response.status_code == 502:
                return {"error": "Serviço temporariamente indisponível nos órgãos de trânsito (HTTP 502). Tente novamente em instantes."}

            else:
                return {
                    "error": f"Erro na consulta DeltaFox (HTTP {response.status_code}): {response.text[:200]}"
                }

        except httpx.TimeoutException:
            return {"error": "Tempo limite esgotado (timeout de 120s) na consulta aos órgãos de trânsito."}
        except Exception as e:
            return {"error": f"Falha na comunicação com a DeltaFox: {str(e)}"}

async def consultar_renach_prontuario(cpf: Union[str, int]) -> dict:
    """
    Consulta o prontuário CNH / RENACH completo através do CPF.
    Retorna dados cadastrais da CNH (categoria, validade, 1ª habilitação, impedimentos, observações),
    filiação (mãe/pai), RG/órgão expedidor e endereço oficial cadastrado no Detran.
    """
    cpf_limpo = normalizar_cpf(cpf)
    if len(cpf_limpo) != 11:
        return {"error": f"CPF inválido: '{cpf}'. O CPF deve conter 11 dígitos numéricos."}

    cache_key = f"deltafox_renach_{cpf_limpo}"
    return await _consultar_servico("renach_prontuario", cpf_limpo, cache_key)

async def consultar_renajud_restricoes(placa: Union[str, int]) -> dict:
    """
    Consulta restrições judiciais ativas via RENAJUD associadas a um veículo pela Placa.
    Retorna Renavam, lista de processos de bloqueio/penhora judicial e restrições financeiras/administrativas.
    """
    placa_limpa = normalizar_placa(placa)
    if not placa_limpa:
        return {"error": "Placa não informada ou inválida."}

    cache_key = f"deltafox_renajud_{placa_limpa}"
    return await _consultar_servico("renajud_restricoes", placa_limpa, cache_key)

async def consultar_renavam_endereco(placa: Union[str, int]) -> dict:
    """
    Consulta endereço cadastrado do proprietário atual do veículo e dados do veículo pela Placa.
    Retorna nome completo do proprietário, endereço completo (logradouro, bairro, CEP, município/UF),
    chassi, marca/modelo, ano de fabricação e indicador de comunicação de venda ativa.
    """
    placa_limpa = normalizar_placa(placa)
    if not placa_limpa:
        return {"error": "Placa não informada ou inválida."}

    cache_key = f"deltafox_renavam_end_{placa_limpa}"
    return await _consultar_servico("renavam_endereco_proprietario", placa_limpa, cache_key)

async def consultar_renavam_frota(documento: Union[str, int]) -> dict:
    """
    Localiza a frota de veículos registrados em nome de uma Pessoa Física (CPF) ou Jurídica (CNPJ).
    Retorna o total de veículos e a lista detalhada de automóveis/motocicletas/caminhões vinculados.
    """
    digitos = so_digitos(documento)
    if len(digitos) == 11:
        doc_limpo = normalizar_cpf(digitos)
    elif len(digitos) == 14:
        doc_limpo = normalizar_cnpj(digitos)
    else:
        return {"error": f"Documento inválido: '{documento}'. Informe um CPF (11 dígitos) ou CNPJ (14 dígitos)."}

    cache_key = f"deltafox_renavam_frota_{doc_limpo}"
    return await _consultar_servico("renavam_frota", doc_limpo, cache_key)

async def consultar_renavam_historico_crv(placa: Union[str, int]) -> dict:
    """
    Consulta o histórico de emissões e transferências de CRV (Certificado de Registro de Veículo) pela Placa.
    Retorna histórico com quantidade de registros e movimentações de propriedade.
    """
    placa_limpa = normalizar_placa(placa)
    if not placa_limpa:
        return {"error": "Placa não informada ou inválida."}

    cache_key = f"deltafox_renavam_crv_{placa_limpa}"
    return await _consultar_servico("renavam_historico_crv", placa_limpa, cache_key)
