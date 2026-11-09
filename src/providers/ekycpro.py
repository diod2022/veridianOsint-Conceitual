import os
import re
import json
import time
import asyncio
import httpx
from typing import Union, Optional, Dict, Any, List, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

import src.core.config as config_mod
import src.core.cache as cache_mod
from src.core.http_client import http_client, get_semaphore

EKYCPRO_DEFAULT_URL = "https://api.ekycpro.com"
TIMEOUT_EKYCPRO = 20.0
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

PADRAO_COMBO_TELEFONE = "ws,ws_avatar,ws_business,instagram,facebook,telegram,threads,twitter,viber"
PADRAO_COMBO_EMAIL = "instagram_email,facebook_email,twitter_email,twitter_profile,email_avatar"

# Catálogo completo de serviços suportados pela API
CATALOGO_SERVICOS: Dict[str, Dict[str, str]] = {
    # Serviços por telefone
    "ws": {
        "plataforma": "WhatsApp",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no WhatsApp por telefone."
    },
    "ws_avatar": {
        "plataforma": "WhatsApp (Foto de Perfil)",
        "tipo": "phone",
        "descricao_servico": "Detecção de foto de perfil pública e URL da imagem no WhatsApp."
    },
    "ws_avatar_profile": {
        "plataforma": "WhatsApp (Atributos de Perfil)",
        "tipo": "phone",
        "descricao_servico": "Detecção de foto de perfil e atributos visuais no WhatsApp."
    },
    "ws_business": {
        "plataforma": "WhatsApp Business",
        "tipo": "phone",
        "descricao_servico": "Verificação se o número opera como conta comercial no WhatsApp Business."
    },
    "telegram": {
        "plataforma": "Telegram",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada e indicador de banimento no Telegram."
    },
    "facebook": {
        "plataforma": "Facebook",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone no Facebook."
    },
    "instagram": {
        "plataforma": "Instagram",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone no Instagram."
    },
    "threads": {
        "plataforma": "Threads",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone no Threads."
    },
    "twitter": {
        "plataforma": "Twitter / X",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone no Twitter / X."
    },
    "apple": {
        "plataforma": "Apple ID",
        "tipo": "phone",
        "descricao_servico": "Verificação de Apple ID vinculado ao número de telefone."
    },
    "viber": {
        "plataforma": "Viber",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no Viber."
    },
    "zalo": {
        "plataforma": "Zalo",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no Zalo."
    },
    "vk": {
        "plataforma": "VK (VKontakte)",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no VK."
    },
    "shopee": {
        "plataforma": "Shopee",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone na Shopee."
    },
    "carrier": {
        "plataforma": "Operadora Telefônica",
        "tipo": "phone",
        "descricao_servico": "Consulta de operadora, tipo de linha e localização por plano de numeração."
    },
    "amazon": {
        "plataforma": "Amazon",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta vinculada ao telefone na Amazon."
    },
    "microsoft": {
        "plataforma": "Microsoft",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta Microsoft vinculada ao telefone."
    },
    "band": {
        "plataforma": "Band",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no Band."
    },
    "goto": {
        "plataforma": "GoTo",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no GoTo."
    },
    "indiatimes": {
        "plataforma": "Indiatimes",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no Indiatimes."
    },
    "hh": {
        "plataforma": "HeadHunter",
        "tipo": "phone",
        "descricao_servico": "Verificação de conta registrada no HeadHunter."
    },
    # Serviços por e-mail
    "facebook_email": {
        "plataforma": "Facebook",
        "tipo": "email",
        "descricao_servico": "Verificação de conta vinculada ao endereço de e-mail no Facebook."
    },
    "instagram_email": {
        "plataforma": "Instagram",
        "tipo": "email",
        "descricao_servico": "Verificação de conta vinculada ao endereço de e-mail no Instagram."
    },
    "apple_email": {
        "plataforma": "Apple ID",
        "tipo": "email",
        "descricao_servico": "Verificação de Apple ID vinculado ao endereço de e-mail."
    },
    "amazon_email": {
        "plataforma": "Amazon",
        "tipo": "email",
        "descricao_servico": "Verificação de conta vinculada ao endereço de e-mail na Amazon."
    },
    "spotify_email": {
        "plataforma": "Spotify",
        "tipo": "email",
        "descricao_servico": "Verificação de conta vinculada ao endereço de e-mail no Spotify."
    },
    "email_check": {
        "plataforma": "Verificação de E-mail",
        "tipo": "email",
        "descricao_servico": "Verificação de registro de caixa postal ou perfil público por domínio de e-mail."
    },
    "email_avatar": {
        "plataforma": "Avatar de E-mail",
        "tipo": "email",
        "descricao_servico": "Verificação de foto de perfil pública associada ao endereço de e-mail."
    },
    "linkedin": {
        "plataforma": "LinkedIn",
        "tipo": "email",
        "descricao_servico": "Verificação de registro associado ao e-mail no LinkedIn."
    },
    "linkedin_profile": {
        "plataforma": "LinkedIn (Perfil)",
        "tipo": "email",
        "descricao_servico": "Consulta de dados de perfil do LinkedIn associados ao e-mail."
    },
    "twitter_email": {
        "plataforma": "Twitter / X",
        "tipo": "email",
        "descricao_servico": "Verificação de conta vinculada ao endereço de e-mail no Twitter / X."
    },
    "twitter_profile": {
        "plataforma": "Twitter / X (Perfil)",
        "tipo": "email",
        "descricao_servico": "Busca de nome e URL de perfil do Twitter / X associados ao endereço de e-mail."
    },
    # Serviços compatíveis com telefone ou e-mail
    "netflix": {
        "plataforma": "Netflix",
        "tipo": "both",
        "descricao_servico": "Verificação de conta vinculada na Netflix."
    },
}

ALIASES_TELEFONE: Dict[str, str] = {
    "whatsapp": "ws",
    "x": "twitter",
}

ALIASES_EMAIL: Dict[str, str] = {
    "whatsapp": "ws",
    "instagram": "instagram_email",
    "facebook": "facebook_email",
    "twitter": "twitter_email",
    "x": "twitter_email",
}

CAMPOS_OCULTOS_FORNECEDOR = {
    "cost",
    "cost_usd",
    "billed",
    "id",
    "transactionId",
    "transaction_id",
    "total_cost",
    "total_cost_usd",
    "billed_count",
    "pricingStrategy",
    "pricing_strategy",
}

OBSERVACAO_PADRAO = (
    "Os status 'sem_registro' e 'indeterminado' (incluindo 'indeterminado_timeout') "
    "indicam ausência de retorno em base consultada ou falha temporária de verificação e "
    "não provam ausência de conta ativa na plataforma."
)

_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _get_api_key() -> str:
    return os.environ.get("EKYCPRO_API_KEY", getattr(config_mod, "EKYCPRO_API_KEY", "")).strip()


def _get_base_url() -> str:
    url = os.environ.get("EKYCPRO_BASE_URL", getattr(config_mod, "EKYCPRO_BASE_URL", "")).strip()
    return (url if url else EKYCPRO_DEFAULT_URL).rstrip("/")


def _get_combo_telefone_padrao() -> List[str]:
    raw = os.environ.get(
        "EKYCPRO_COMBO_TELEFONE",
        getattr(config_mod, "EKYCPRO_COMBO_TELEFONE", PADRAO_COMBO_TELEFONE),
    )
    if not raw or not raw.strip():
        raw = PADRAO_COMBO_TELEFONE
    return [s.strip().lower() for s in raw.split(",") if s.strip()]


def _get_combo_email_padrao() -> List[str]:
    raw = os.environ.get(
        "EKYCPRO_COMBO_EMAIL",
        getattr(config_mod, "EKYCPRO_COMBO_EMAIL", PADRAO_COMBO_EMAIL),
    )
    if not raw or not raw.strip():
        raw = PADRAO_COMBO_EMAIL
    return [s.strip().lower() for s in raw.split(",") if s.strip()]


def _get_headers() -> Dict[str, str]:
    return {
        "X-API-Key": _get_api_key(),
        "Content-Type": "application/json",
    }


def normalizar_telefone_e164(telefone: Union[str, int]) -> str:
    """
    Normaliza um número de telefone para o padrão internacional E.164 (+DDI...).
    - Remove máscara, espaços e pontuação.
    - Remove zero inicial de longa distância nacional (ex.: 011999998888 -> 11999998888).
    - Números sem '+' ou '00' com 10 ou 11 dígitos são tratados como brasileiros (+55).
    - Converte prefixo internacional '00' para '+'.
    - Rejeita entradas com menos de 8 ou mais de 15 dígitos finais.
    """
    if telefone is None:
        raise ValueError("Telefone não informado.")

    raw = str(telefone).strip()
    if not raw:
        raise ValueError("Telefone não informado.")

    tem_mais = raw.startswith("+")
    digitos = re.sub(r"\D", "", raw)

    if not digitos:
        raise ValueError(f"Telefone inválido: '{telefone}'. Nenhum dígito numérico encontrado.")

    if not tem_mais and digitos.startswith("00"):
        digitos = digitos[2:]
        tem_prefixo_internacional = True
    else:
        tem_prefixo_internacional = tem_mais

    if not tem_prefixo_internacional:
        # Remove zero inicial de longa distância (ex.: 011999998888 ou 01133334444)
        if digitos.startswith("0") and len(digitos) in (11, 12):
            digitos = digitos[1:]
        # Número nacional brasileiro (DDD + 8 ou 9 dígitos)
        if len(digitos) in (10, 11):
            digitos = "55" + digitos
    else:
        # Caso +55011999998888
        if digitos.startswith("550") and len(digitos) in (13, 14):
            digitos = "55" + digitos[3:]

    if len(digitos) < 8 or len(digitos) > 15:
        raise ValueError(
            f"Telefone inválido: '{telefone}'. O número em formato E.164 deve conter entre 8 e 15 dígitos."
        )

    return f"+{digitos}"


def normalizar_email_ekyc(email: str) -> str:
    """Normaliza endereço de e-mail em minúsculas, sem espaços, e valida formato com regex simples."""
    if email is None:
        raise ValueError("E-mail não informado.")
    limpo = str(email).strip().lower()
    if not limpo or " " in limpo or not _EMAIL_REGEX.match(limpo):
        raise ValueError(f"Endereço de e-mail inválido: '{email}'.")
    return limpo


def _servico_compativel(servico: str, tipo_entrada: str) -> bool:
    info = CATALOGO_SERVICOS.get(servico)
    if not info:
        return False
    tipo_servico = info.get("tipo", "")
    return tipo_servico == tipo_entrada or tipo_servico == "both"


def resolver_servicos(
    servicos: Optional[Union[List[str], str]],
    tipo_entrada: str,
) -> Tuple[List[str], List[str]]:
    """
    Resolve aliases e separa os códigos em (servicos_validos, servicos_ignorados)
    de acordo com o tipo de entrada ('phone' ou 'email').
    """
    if servicos is None:
        brutos = _get_combo_telefone_padrao() if tipo_entrada == "phone" else _get_combo_email_padrao()
    elif isinstance(servicos, str):
        brutos = [s.strip() for s in servicos.split(",") if s.strip()]
    elif isinstance(servicos, (list, tuple, set)):
        brutos = []
        for item in servicos:
            if isinstance(item, str):
                brutos.extend([s.strip() for s in item.split(",") if s.strip()])
    else:
        brutos = []

    mapa_aliases = ALIASES_TELEFONE if tipo_entrada == "phone" else ALIASES_EMAIL
    validos: List[str] = []
    ignorados: List[str] = []

    for item in brutos:
        codigo_original = item.strip().lower()
        if not codigo_original:
            continue
        codigo = mapa_aliases.get(codigo_original, codigo_original)
        if _servico_compativel(codigo, tipo_entrada):
            if codigo not in validos:
                validos.append(codigo)
        else:
            if codigo_original not in ignorados:
                ignorados.append(codigo_original)

    return validos, ignorados


def classificar_status_no(registered: Optional[bool], error: Optional[str] = None) -> str:
    """
    Converte o retorno bruto de um nó da API para o status padronizado Veridian:
    - registered: True -> 'cadastrado'
    - registered: False -> 'nao_cadastrado'
    - registered: None com error 'NOT_FOUND' -> 'sem_registro'
    - registered: None com error 'timeout' -> 'indeterminado_timeout'
    - error 'insufficient balance' -> 'nao_consultado_saldo'
    - qualquer outro -> 'indeterminado'
    """
    err_norm = (error or "").strip()
    err_lower = err_norm.lower()

    if err_lower in ("insufficient balance", "insufficient_balance"):
        return "nao_consultado_saldo"

    if registered is True:
        return "cadastrado"
    if registered is False:
        return "nao_cadastrado"

    if err_norm == "NOT_FOUND" or err_lower == "not_found":
        return "sem_registro"
    if err_lower == "timeout":
        return "indeterminado_timeout"

    return "indeterminado"


def _gerar_descricao_status(servico: str, status: str, node: Dict[str, Any]) -> str:
    plataforma = CATALOGO_SERVICOS.get(servico, {}).get("plataforma", servico)
    if status == "cadastrado":
        if servico in ("ws_avatar", "email_avatar"):
            if node.get("avatar") is True:
                return f"Foto de perfil pública localizada em {plataforma}."
            return f"Conta localizada em {plataforma}, porém sem foto de perfil pública."
        if servico == "ws_business":
            if node.get("business") is True:
                return "Conta registrada e identificada como WhatsApp Business."
            return "Conta registrada no WhatsApp, mas não configurada como Business."
        if servico == "telegram" and node.get("banned") is True:
            return "Conta localizada no Telegram, porém sinalizada como banida."
        return f"Conta ou vínculo ativo identificado em {plataforma}."

    if status == "nao_cadastrado":
        if servico == "telegram":
            if node.get("banned") is True:
                return "Número banido no Telegram."
            return "Conta não encontrada no Telegram (pode não estar cadastrada ou estar banida)."
        if servico == "email_avatar":
            return "Nenhuma foto de perfil pública encontrada para o e-mail (não comprova inexistência da caixa postal)."
        return f"Nenhuma conta vinculada ao identificador em {plataforma}."

    if status == "sem_registro":
        return (
            f"Sem registro localizado para {plataforma} nas bases consultadas "
            "(não comprova ausência de conta ativa)."
        )

    if status == "indeterminado_timeout":
        return f"Tempo limite excedido ao verificar {plataforma}; resultado indeterminado."

    if status == "nao_consultado_saldo":
        return f"Verificação de {plataforma} não realizada por limite operacional no provedor."

    return f"Não foi possível determinar o vínculo em {plataforma} no momento."


def normalizar_no_servico(servico: str, node: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Formata o resultado de uma plataforma no padrão white-label exigido,
    renomeando campos conhecidos e removendo custos, IDs e metadados do fornecedor.
    """
    node_dict = node if isinstance(node, dict) else {}
    registered_raw = node_dict.get("registered")
    registered: Optional[bool] = registered_raw if isinstance(registered_raw, bool) else None
    error_raw = node_dict.get("error")

    status = classificar_status_no(registered, error_raw)
    info_cat = CATALOGO_SERVICOS.get(servico, {})
    plataforma = info_cat.get("plataforma", servico)
    descricao = _gerar_descricao_status(servico, status, node_dict)

    item: Dict[str, Any] = {
        "servico": servico,
        "plataforma": plataforma,
        "status": status,
        "cadastrado": registered,
        "descricao": descricao,
    }

    if "avatar" in node_dict or servico in ("ws_avatar", "email_avatar"):
        if "avatar" in node_dict:
            item["possui_foto_perfil"] = (
                bool(node_dict["avatar"]) if node_dict["avatar"] is not None else None
            )
        if "avatar_url" in node_dict:
            item["foto_perfil_url"] = node_dict.get("avatar_url") or ""

    if "business" in node_dict or servico == "ws_business":
        if "business" in node_dict:
            item["conta_business"] = (
                bool(node_dict["business"]) if node_dict["business"] is not None else None
            )

    chaves_ja_tratadas = (
        CAMPOS_OCULTOS_FORNECEDOR
        | {"registered", "error", "identifier", "service_type", "avatar", "avatar_url", "business"}
    )

    dados_extras: Dict[str, Any] = {}
    for k, v in node_dict.items():
        if k not in chaves_ja_tratadas:
            dados_extras[k] = v

    # Garante presença dos campos documentados em serviços específicos
    if servico == "twitter_profile" and status == "cadastrado":
        dados_extras.setdefault("name", node_dict.get("name", ""))
        dados_extras.setdefault("url", node_dict.get("url", ""))
    elif servico == "telegram" and "banned" in node_dict:
        dados_extras["banned"] = node_dict.get("banned")

    item["dados"] = dados_extras
    return item


def montar_resumo(plataformas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Gera o bloco de resumo com listas de plataformas agrupadas por status."""
    por_status: Dict[str, List[str]] = {
        "cadastrado": [],
        "nao_cadastrado": [],
        "sem_registro": [],
        "indeterminado_timeout": [],
        "nao_consultado_saldo": [],
        "indeterminado": [],
    }
    plataformas_cadastradas: List[str] = []

    for p in plataformas:
        st = p.get("status", "indeterminado")
        srv = p.get("servico", "")
        nome_plat = p.get("plataforma", srv)
        if st in por_status:
            por_status[st].append(srv)
        else:
            por_status["indeterminado"].append(srv)
        if st == "cadastrado":
            plataformas_cadastradas.append(nome_plat)

    return {
        "total_verificados": len(plataformas),
        "total_cadastrados": len(por_status["cadastrado"]),
        "plataformas_cadastradas": plataformas_cadastradas,
        "cadastrado": por_status["cadastrado"],
        "nao_cadastrado": por_status["nao_cadastrado"],
        "sem_registro": por_status["sem_registro"],
        "indeterminado_timeout": por_status["indeterminado_timeout"],
        "nao_consultado_saldo": por_status["nao_consultado_saldo"],
        "indeterminado": por_status["indeterminado"],
        "observacao": OBSERVACAO_PADRAO,
    }


def _resultado_cacheavel(plataformas: List[Dict[str, Any]]) -> bool:
    """
    Não grava em cache resultados com algum status indeterminado ou sem saldo.
    """
    if not plataformas:
        return False
    status_bloqueados = {"indeterminado", "indeterminado_timeout", "nao_consultado_saldo"}
    for p in plataformas:
        if p.get("status") in status_bloqueados:
            return False
    return True


def _gerar_chave_cache(identificador: str, servicos: List[str]) -> str:
    id_slug = re.sub(r"[^a-zA-Z0-9]", "_", identificador.lstrip("+").lower()).strip("_")
    servicos_ord = "_".join(sorted(set(servicos)))
    return f"presenca_{id_slug}_{servicos_ord}"


def _obter_caminho_arquivo_cache(cache_key: str) -> str:
    cache_dir = getattr(cache_mod, "CACHE_DIR", None) or getattr(config_mod, "CACHE_DIR")
    os.makedirs(cache_dir, exist_ok=True)
    clean_key = re.sub(r"[^a-zA-Z0-9_\-]", "_", cache_key)
    return os.path.join(cache_dir, f"{clean_key}.json")


def _ler_cache_presenca(cache_key: str) -> Optional[Dict[str, Any]]:
    caminho = _obter_caminho_arquivo_cache(cache_key)
    if not os.path.exists(caminho):
        return None
    try:
        mtime = os.path.getmtime(caminho)
        if (time.time() - mtime) > CACHE_TTL_SECONDS:
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if not isinstance(dados, dict):
            return None
        copia = dict(dados)
        copia["em_cache"] = True
        copia["cache_id"] = cache_key
        return copia
    except Exception:
        return None


def _salvar_cache_presenca(cache_key: str, dados: Dict[str, Any]) -> None:
    caminho = _obter_caminho_arquivo_cache(cache_key)
    tmp_path = f"{caminho}.tmp_{os.getpid()}_{time.time_ns()}"
    try:
        payload = dict(dados)
        payload["cache_id"] = cache_key
        payload["em_cache"] = False
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, caminho)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _eh_erro_conexao(exc: BaseException) -> bool:
    """Retenta apenas em falha de conexão (nunca em ReadTimeout)."""
    return isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout))


@retry(
    retry=retry_if_exception(_eh_erro_conexao),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    reraise=True,
)
async def _http_request_com_retry_conexao(method: str, url: str, **kwargs) -> httpx.Response:
    return await http_client.request(method, url, **kwargs)


async def _requisitar_api(
    method: str,
    path: str,
    json_body: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    url = f"{_get_base_url()}{path}"
    kwargs: Dict[str, Any] = {
        "headers": _get_headers(),
        "timeout": TIMEOUT_EKYCPRO,
    }
    if json_body is not None:
        kwargs["json"] = json_body

    async with get_semaphore("ekycpro"):
        return await _http_request_com_retry_conexao(method, url, **kwargs)


def _formatar_erro_http(response: httpx.Response) -> Dict[str, Any]:
    code = response.status_code
    if code == 400:
        return {
            "error": "Parâmetros inválidos: identificador malformado ou serviço incompatível com o tipo de consulta.",
            "http_status": 400,
        }
    if code == 401:
        return {
            "error": "Chave de autenticação inválida ou não autorizada para o serviço de presença digital.",
            "http_status": 401,
        }
    if code == 402:
        return {
            "error": "Saldo insuficiente no provedor para processar a verificação solicitada.",
            "http_status": 402,
        }
    if code == 429:
        return {
            "error": "Limite de requisições simultâneas atingido. Aguarde alguns instantes e tente novamente.",
            "http_status": 429,
        }
    return {
        "error": f"Erro ao consultar serviço de presença digital (HTTP {code}).",
        "http_status": code,
    }


async def _consultar_avulso_bruto(identificador: str, servico: str) -> Dict[str, Any]:
    """
    Executa POST /v1/check para um único serviço e retorna o dicionário de nó bruto
    (mesclando error de topo se houver).
    """
    try:
        resp = await _requisitar_api(
            "POST",
            "/v1/check",
            json_body={"service_type": servico, "identifier": identificador},
        )
        if resp.status_code != 200:
            err_info = _formatar_erro_http(resp)
            err_info["_http_error"] = True
            return err_info

        payload = resp.json() if resp.content else {}
        data_node = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        node = dict(data_node)
        if "error" not in node and payload.get("error"):
            node["error"] = payload.get("error")
        if "registered" not in node:
            node["registered"] = None
        return node
    except httpx.ReadTimeout:
        return {"registered": None, "error": "timeout"}
    except httpx.TimeoutException:
        return {"registered": None, "error": "timeout"}
    except Exception as e:
        return {"registered": None, "error": f"connection_error: {str(e)}"}


async def _executar_lote(
    endpoint: str,
    identificador: str,
    tipo_identificador: str,
    servicos_validos: List[str],
    servicos_ignorados: List[str],
) -> Dict[str, Any]:
    token = _get_api_key()
    if not token:
        return {"error": "EKYCPRO_API_KEY não configurada no .env"}

    cache_key = _gerar_chave_cache(identificador, servicos_validos)
    em_cache = _ler_cache_presenca(cache_key)
    if em_cache is not None:
        if servicos_ignorados:
            em_cache["servicos_ignorados"] = servicos_ignorados
        return em_cache

    results_map: Dict[str, Dict[str, Any]] = {}

    try:
        resp = await _requisitar_api(
            "POST",
            endpoint,
            json_body={"identifier": identificador, "service_types": servicos_validos},
        )

        # Ponto em aberto da seção 9: fallback se twitter_profile no lote de e-mail retornar 400
        if (
            resp.status_code == 400
            and endpoint == "/v1/check/combo/email"
            and "twitter_profile" in servicos_validos
            and len(servicos_validos) > 1
        ):
            restantes = [s for s in servicos_validos if s != "twitter_profile"]
            resp_lote, no_twitter = await asyncio.gather(
                _requisitar_api(
                    "POST",
                    endpoint,
                    json_body={"identifier": identificador, "service_types": restantes},
                ),
                _consultar_avulso_bruto(identificador, "twitter_profile"),
            )
            if resp_lote.status_code != 200:
                return _formatar_erro_http(resp_lote)
            body_lote = resp_lote.json() if resp_lote.content else {}
            results_map = dict((body_lote.get("data") or {}).get("results") or {})
            if not no_twitter.get("_http_error"):
                results_map["twitter_profile"] = no_twitter
            else:
                results_map["twitter_profile"] = {"registered": None, "error": "unable to verify identifier"}
        else:
            if resp.status_code != 200:
                return _formatar_erro_http(resp)
            body = resp.json() if resp.content else {}
            results_map = dict((body.get("data") or {}).get("results") or {})

    except httpx.TimeoutException:
        return {
            "error": "Tempo limite esgotado ao consultar verificação em lote.",
            "http_status": 504,
        }
    except Exception as e:
        return {"error": f"Falha de comunicação na verificação de presença digital: {str(e)}"}

    # Reconsulta uma vez, em paralelo, cada serviço que voltou timeout no lote via /v1/check
    servicos_timeout = [
        srv
        for srv in servicos_validos
        if isinstance(results_map.get(srv), dict)
        and str(results_map[srv].get("error") or "").strip().lower() == "timeout"
    ]

    if servicos_timeout:
        reconsultas = await asyncio.gather(
            *[_consultar_avulso_bruto(identificador, srv) for srv in servicos_timeout]
        )
        for srv, novo_no in zip(servicos_timeout, reconsultas):
            if isinstance(novo_no, dict) and not novo_no.get("_http_error"):
                results_map[srv] = novo_no

    plataformas_lista: List[Dict[str, Any]] = []
    resultados_por_servico: Dict[str, Dict[str, Any]] = {}

    for srv in servicos_validos:
        no_bruto = results_map.get(srv)
        item_norm = normalizar_no_servico(srv, no_bruto)
        plataformas_lista.append(item_norm)
        resultados_por_servico[srv] = item_norm

    resumo = montar_resumo(plataformas_lista)

    saida: Dict[str, Any] = {
        "identificador": identificador,
        "tipo_identificador": tipo_identificador,
        "servicos_consultados": servicos_validos,
        "servicos_ignorados": servicos_ignorados,
        "plataformas": plataformas_lista,
        "resultados": resultados_por_servico,
        "resumo": resumo,
        "observacao": OBSERVACAO_PADRAO,
        "em_cache": False,
    }

    if _resultado_cacheavel(plataformas_lista):
        saida["cache_id"] = cache_key
        _salvar_cache_presenca(cache_key, saida)

    return saida


async def verificar_telefone(
    telefone: Union[str, int],
    servicos: Optional[Union[List[str], str]] = None,
) -> Dict[str, Any]:
    """
    Verifica em lote a presença digital de um telefone (E.164) em redes sociais e mensageiros.
    """
    try:
        tel_e164 = normalizar_telefone_e164(telefone)
    except ValueError as e:
        return {"error": str(e)}

    validos, ignorados = resolver_servicos(servicos, "phone")
    if not validos:
        return {
            "error": "Nenhum serviço válido ou compatível com telefone foi informado.",
            "servicos_ignorados": ignorados,
        }

    return await _executar_lote(
        endpoint="/v1/check/combo/phone",
        identificador=tel_e164,
        tipo_identificador="telefone",
        servicos_validos=validos,
        servicos_ignorados=ignorados,
    )


async def verificar_email(
    email: str,
    servicos: Optional[Union[List[str], str]] = None,
) -> Dict[str, Any]:
    """
    Verifica em lote a presença digital de um endereço de e-mail em redes sociais e plataformas.
    """
    try:
        email_norm = normalizar_email_ekyc(email)
    except ValueError as e:
        return {"error": str(e)}

    validos, ignorados = resolver_servicos(servicos, "email")
    if not validos:
        return {
            "error": "Nenhum serviço válido ou compatível com e-mail foi informado.",
            "servicos_ignorados": ignorados,
        }

    return await _executar_lote(
        endpoint="/v1/check/combo/email",
        identificador=email_norm,
        tipo_identificador="email",
        servicos_validos=validos,
        servicos_ignorados=ignorados,
    )


async def verificar_servico(identificador: str, servico: str) -> Dict[str, Any]:
    """
    Realiza consulta avulsa de um único serviço/plataforma para um telefone ou e-mail.
    """
    if not identificador or not str(identificador).strip():
        return {"error": "Identificador (telefone ou e-mail) não informado."}
    if not servico or not str(servico).strip():
        return {"error": "Código do serviço/plataforma não informado."}

    id_raw = str(identificador).strip()
    eh_email = "@" in id_raw

    try:
        if eh_email:
            id_norm = normalizar_email_ekyc(id_raw)
            tipo_entrada = "email"
            tipo_label = "email"
        else:
            id_norm = normalizar_telefone_e164(id_raw)
            tipo_entrada = "phone"
            tipo_label = "telefone"
    except ValueError as e:
        return {"error": str(e)}

    validos, ignorados = resolver_servicos([servico], tipo_entrada)
    if not validos:
        return {
            "error": (
                f"Serviço '{servico}' inválido ou incompatível com identificador do tipo {tipo_label}."
            ),
            "servicos_ignorados": ignorados,
        }

    srv_codigo = validos[0]

    token = _get_api_key()
    if not token:
        return {"error": "EKYCPRO_API_KEY não configurada no .env"}

    cache_key = _gerar_chave_cache(id_norm, [srv_codigo])
    em_cache = _ler_cache_presenca(cache_key)
    if em_cache is not None:
        return em_cache

    try:
        resp = await _requisitar_api(
            "POST",
            "/v1/check",
            json_body={"service_type": srv_codigo, "identifier": id_norm},
        )
        if resp.status_code != 200:
            return _formatar_erro_http(resp)

        payload = resp.json() if resp.content else {}
        data_node = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        node = dict(data_node)
        if "error" not in node and payload.get("error"):
            node["error"] = payload.get("error")
        if "registered" not in node:
            node["registered"] = None
    except httpx.TimeoutException:
        return {
            "error": "Tempo limite esgotado ao consultar a plataforma solicitada.",
            "http_status": 504,
        }
    except Exception as e:
        return {"error": f"Falha de comunicação ao consultar plataforma: {str(e)}"}

    item_norm = normalizar_no_servico(srv_codigo, node)
    resumo = montar_resumo([item_norm])

    saida: Dict[str, Any] = {
        "identificador": id_norm,
        "tipo_identificador": tipo_label,
        **item_norm,
        "plataformas": [item_norm],
        "resultados": {srv_codigo: item_norm},
        "resumo": resumo,
        "observacao": OBSERVACAO_PADRAO,
        "em_cache": False,
    }

    if _resultado_cacheavel([item_norm]):
        saida["cache_id"] = cache_key
        _salvar_cache_presenca(cache_key, saida)

    return saida


async def perfil_twitter_por_email(email: str) -> Dict[str, Any]:
    """
    Consulta nome e URL de perfil do Twitter / X associados a um endereço de e-mail.
    """
    try:
        email_norm = normalizar_email_ekyc(email)
    except ValueError as e:
        return {"error": str(e)}

    return await verificar_servico(email_norm, "twitter_profile")


async def listar_servicos() -> Dict[str, Any]:
    """
    Lista as plataformas de presença digital verificáveis por telefone e e-mail.
    """
    token = _get_api_key()
    if not token:
        return {"error": "EKYCPRO_API_KEY não configurada no .env"}

    try:
        resp = await _requisitar_api("GET", "/v1/services")
        if resp.status_code != 200:
            return _formatar_erro_http(resp)

        payload = resp.json() if resp.content else {}
        servicos_api = payload.get("services") if isinstance(payload.get("services"), list) else []
    except httpx.TimeoutException:
        return {
            "error": "Tempo limite esgotado ao listar plataformas verificáveis.",
            "http_status": 504,
        }
    except Exception as e:
        return {"error": f"Falha de comunicação ao listar plataformas: {str(e)}"}

    combo_tel = _get_combo_telefone_padrao()
    combo_email = _get_combo_email_padrao()

    plataformas_formatadas: List[Dict[str, Any]] = []
    vistos = set()

    for s in servicos_api:
        if not isinstance(s, dict):
            continue
        codigo = str(s.get("type") or "").strip().lower()
        if not codigo:
            continue
        vistos.add(codigo)
        cat = CATALOGO_SERVICOS.get(codigo, {})
        data_type = str(s.get("data_type") or cat.get("tipo") or "").lower()
        plataformas_formatadas.append({
            "servico": codigo,
            "plataforma": cat.get("plataforma", codigo),
            "tipo_identificador": "telefone" if data_type == "phone" else ("email" if data_type == "email" else data_type),
            "disponivel": bool(s.get("enabled", True)),
            "descricao": cat.get("descricao_servico", ""),
        })

    for codigo, cat in CATALOGO_SERVICOS.items():
        if codigo not in vistos:
            dt = cat.get("tipo", "")
            plataformas_formatadas.append({
                "servico": codigo,
                "plataforma": cat.get("plataforma", codigo),
                "tipo_identificador": "telefone" if dt == "phone" else ("email" if dt == "email" else "ambos"),
                "disponivel": True,
                "descricao": cat.get("descricao_servico", ""),
            })

    return {
        "total_plataformas": len(plataformas_formatadas),
        "pacote_padrao_telefone": combo_tel,
        "pacote_padrao_email": combo_email,
        "aliases_aceitos": {
            "telefone": ALIASES_TELEFONE,
            "email": ALIASES_EMAIL,
        },
        "plataformas": plataformas_formatadas,
    }


async def consultar_saldo() -> Dict[str, Any]:
    """
    Consulta o saldo operacional interno no provedor (uso exclusivamente interno, sem tool MCP).
    """
    token = _get_api_key()
    if not token:
        return {"error": "EKYCPRO_API_KEY não configurada no .env"}

    try:
        resp = await _requisitar_api("GET", "/v1/balance")
        if resp.status_code != 200:
            return _formatar_erro_http(resp)
        return resp.json() if resp.content else {}
    except httpx.TimeoutException:
        return {"error": "Tempo limite esgotado ao consultar saldo.", "http_status": 504}
    except Exception as e:
        return {"error": f"Falha de comunicação ao consultar saldo: {str(e)}"}

