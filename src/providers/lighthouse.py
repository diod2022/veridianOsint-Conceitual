import os
import sys
import json
import asyncio
import hashlib
import httpx
from typing import Union, Optional, Dict, Any, List
from src.core.config import LIGHTHOUSE_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal, obter_caminho_cache_seguro
from src.core.http_client import resilient_request, get_semaphore
from src.core.security import normalizar_email

# URL oficial da API Lampyre / Lighthouse 1.0
LIGHTHOUSE_BASE_URL = "https://api.lighthouse.lampyre.io/api/1.0"

def _get_token() -> str:
    return os.environ.get("LIGHTHOUSE_API_KEY") or os.environ.get("LIGHTHOUSE_API_TOKEN", "")

async def _lighthouse_request(method: str, url: str, **kwargs) -> httpx.Response:
    """
    Executa requisição via resilient_request e faz fallback sem verificação estrita
    de cadeia SSL apenas quando o certificado intermediário da Lampyre falha no OpenSSL 3.
    """
    try:
        return await resilient_request(method, url, **kwargs)
    except httpx.ConnectError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(30.0, connect=10.0)) as fallback_client:
                return await fallback_client.request(method, url, **kwargs)
        raise

def _ler_cache_bruto_lighthouse(chave_cache: str) -> Optional[Any]:
    """Lê o arquivo JSON bruto salvo no cache local, se existir."""
    caminho = obter_caminho_cache_seguro(chave_cache)
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _extrair_outputs_lighthouse(raw_result: Any) -> List[Dict[str, Any]]:
    """
    Extrai a lista de objetos de `output` retornados por uma tarefa Lighthouse
    (`result.result[].output[]`).
    """
    outputs: List[Dict[str, Any]] = []
    if not isinstance(raw_result, dict):
        return outputs
    blocos = raw_result.get("result")
    if isinstance(blocos, list):
        for bloco in blocos:
            if isinstance(bloco, dict):
                out_list = bloco.get("output")
                if isinstance(out_list, list):
                    for item in out_list:
                        if isinstance(item, dict):
                            outputs.append(item)
                elif isinstance(out_list, dict):
                    outputs.append(out_list)
    elif isinstance(raw_result.get("output"), list):
        for item in raw_result["output"]:
            if isinstance(item, dict):
                outputs.append(item)
    return outputs

async def async_executar_tarefa_lighthouse(
    job_name: str,
    task_info: dict,
    chave_cache: str,
    retornar_bruto: bool = False
) -> dict:
    token = _get_token()
    if not token:
        return {"error": "LIGHTHOUSE_API_KEY não configurada no .env"}

    if retornar_bruto:
        dados_cache = _ler_cache_bruto_lighthouse(chave_cache)
        if dados_cache is not None:
            return {"_do_cache": True, "cache_id": chave_cache, "result": dados_cache}
    else:
        cache_hit = checar_cache_universal(chave_cache)
        if cache_hit:
            return cache_hit

    task_info_limpo = {}
    for k, v in task_info.items():
        if isinstance(v, int):
            task_info_limpo[k] = str(v)
        elif isinstance(v, dict):
            task_info_limpo[k] = {sub_k: (str(sub_v) if isinstance(sub_v, int) else sub_v) for sub_k, sub_v in v.items()}
        else:
            task_info_limpo[k] = v

    url_post = f"{LIGHTHOUSE_BASE_URL}/tasks/{job_name}"
    payload = {
        "token": token,
        "task_info": task_info_limpo
    }

    async with get_semaphore("lighthouse"):
        try:
            response = await _lighthouse_request("POST", url_post, json=payload)
            if response.status_code != 201:
                return {
                    "error": f"Falha ao criar tarefa no Lighthouse (Código HTTP {response.status_code})",
                    "detalhes": response.text
                }
            
            task_data = response.json()
            task_id = task_data.get("task_id")
            if not task_id:
                return {"error": "A API do Lighthouse não retornou um task_id válido.", "detalhes": task_data}

            url_get = f"{LIGHTHOUSE_BASE_URL}/tasks/{job_name}/{task_id}?token={token}"
            
            for tentativa in range(40):
                await asyncio.sleep(3.0)
                status_resp = await _lighthouse_request("GET", url_get)
                if status_resp.status_code != 200:
                    continue
                
                status_data = status_resp.json()
                status = status_data.get("task_status")
                
                if status == 0:
                    result_obj = status_data.get("result", {})
                    resumo_cache = salvar_cache_universal(chave_cache, result_obj)
                    if retornar_bruto:
                        return {"_do_cache": False, "cache_id": chave_cache, "result": result_obj}
                    return resumo_cache
                elif status == 1:
                    return {
                        "error": "A tarefa falhou na execução remota do Lighthouse.",
                        "detalhes": status_data
                    }

            return {
                "error": "A busca no Lighthouse excedeu o limite de tempo (120 segundos).",
                "task_id": task_id,
                "mensagem": "A tarefa pode ainda estar rodando no Lighthouse. Tente novamente mais tarde para puxar do cache."
            }

        except Exception as e:
            return {"error": f"Erro na execução da tarefa Lighthouse ({job_name}): {str(e)}"}

# ==============================================================================
# FACEBOOK ENDPOINTS (LAMPYRE API 1.0)
# ==============================================================================

async def fb_uid_info(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_info_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_info_{uid_str}"
    )

async def fb_uid_wall(facebook_profile_uid: Union[str, int], options: Optional[dict] = None) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    task_info = {"facebook_profile_uid": uid_str}
    if options: task_info["options"] = options
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_wall_get_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_uid_wall_{uid_str}"
    )

async def fb_uid_reposts(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_reposts_from_user_wall_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_reposts_{uid_str}"
    )

async def fb_uid_likes(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_likes_from_user_wall_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_likes_{uid_str}"
    )

async def fb_uid_comments(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_comments_from_user_wall_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_comments_{uid_str}"
    )

async def fb_uid_friends(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_friends_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_friends_{uid_str}"
    )

async def fb_uid_full_friends(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_full_friends_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_full_friends_{uid_str}"
    )

async def fb_email_restore(email: str) -> dict:
    em = email.strip().lower()
    email_clean = em.replace("@", "_at_").replace(".", "_")
    return await async_executar_tarefa_lighthouse(
        job_name="email_fb_restore_v1",
        task_info={"email": em},
        chave_cache=f"lighthouse_fb_email_restore_{email_clean}"
    )

async def fb_phone_restore(phone: Union[str, int]) -> dict:
    ph = str(phone).strip().replace("+", "").replace("-", "").replace(" ", "")
    return await async_executar_tarefa_lighthouse(
        job_name="phone_fb_restore_v1",
        task_info={"phone": ph},
        chave_cache=f"lighthouse_fb_phone_restore_{ph}"
    )

async def fb_username_restore(username: str) -> dict:
    usr = username.strip().lstrip("@")
    return await async_executar_tarefa_lighthouse(
        job_name="username_fb_restore_v1",
        task_info={"username": usr},
        chave_cache=f"lighthouse_fb_username_restore_{usr}"
    )

async def fb_uid_darknet(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_darknet_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_darknet_{uid_str}"
    )

async def fb_email_darknet(email: str) -> dict:
    em = email.strip().lower()
    email_clean = em.replace("@", "_at_").replace(".", "_")
    return await async_executar_tarefa_lighthouse(
        job_name="email_fb_darknet_v1",
        task_info={"email": em},
        chave_cache=f"lighthouse_fb_email_darknet_{email_clean}"
    )

async def fb_phone_darknet(phone: Union[str, int]) -> dict:
    ph = str(phone).strip().replace("+", "").replace("-", "").replace(" ", "")
    return await async_executar_tarefa_lighthouse(
        job_name="phone_fb_darknet_v1",
        task_info={"phone": ph},
        chave_cache=f"lighthouse_fb_phone_darknet_{ph}"
    )

# ==============================================================================
# RECONHECIMENTO FACIAL E IMAGENS OSINT (LAMPYRE API 1.0)
# ==============================================================================

async def image_facecheck(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    """Busca reversa facial na web aberta com FaceCheck.ID via Lampyre."""
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
    task_info = {}
    if photo_url: task_info["photo_url"] = photo_url
    if photo_b64: task_info["photo_b64"] = photo_b64
    if photo_fileid: task_info["photo_fileid"] = photo_fileid
    
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="image_facecheck_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_image_facecheck_{hash_id}"
    )

async def image_geolocation(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    """Estimativa de geolocalização e marcos geográficos por IA a partir de imagem."""
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
    task_info = {}
    if photo_url: task_info["photo_url"] = photo_url
    if photo_b64: task_info["photo_b64"] = photo_b64
    if photo_fileid: task_info["photo_fileid"] = photo_fileid
    
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="image_geolocation_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_image_geolocation_{hash_id}"
    )

# ==============================================================================
# GOOGLE ACCOUNT & GOOGLE MAPS OSINT (LAMPYRE API 1.0)
# ==============================================================================

async def google_email_info(email: str) -> dict:
    """
    Descobre o ID da conta Google (google_profile_uid / GAIA ID), nome completo,
    foto de perfil e última atualização a partir de um endereço de e-mail (email_google_v1).
    """
    em = normalizar_email(email)
    if not em or "@" not in em:
        return {"error": f"E-mail inválido para consulta Google: '{email}'."}

    email_clean = em.replace("@", "_at_").replace(".", "_")
    chave_cache = f"lighthouse_google_email_{email_clean}"

    resp = await async_executar_tarefa_lighthouse(
        job_name="email_google_v1",
        task_info={"email": em},
        chave_cache=chave_cache,
        retornar_bruto=True
    )
    if "error" in resp:
        return resp

    outputs = _extrair_outputs_lighthouse(resp.get("result", {}))
    primeiro = outputs[0] if outputs else {}
    google_uid = primeiro.get("google_profile_uid")

    return {
        "status": "sucesso",
        "email": em,
        "encontrado": bool(google_uid or outputs),
        "google_profile_uid": str(google_uid) if google_uid else None,
        "nome_completo": primeiro.get("fullname") or None,
        "foto_perfil_url": primeiro.get("avatar_url") or None,
        "foto_perfil_fileid": primeiro.get("avatar_fileid") or None,
        "perfil_url": primeiro.get("url") or None,
        "ultima_atualizacao_unix": primeiro.get("updated"),
        "perfis_encontrados": outputs,
        "cache_id": resp.get("cache_id", chave_cache),
        "do_cache": bool(resp.get("_do_cache", False))
    }

async def google_maps_reviews(google_profile_uid: Union[str, int]) -> dict:
    """
    Extrai o histórico de locais avaliados (reviews, notas, comentários e coordenadas GPS)
    no Google Maps a partir do ID da conta Google (uid_google_maps_v1).
    """
    uid_str = str(google_profile_uid).strip()
    if not uid_str or not uid_str.isdigit():
        return {"error": f"ID da conta Google (google_profile_uid) inválido: '{google_profile_uid}'. Deve conter apenas dígitos."}

    chave_cache = f"lighthouse_google_maps_reviews_{uid_str}"
    resp = await async_executar_tarefa_lighthouse(
        job_name="uid_google_maps_v1",
        task_info={"google_profile_uid": uid_str},
        chave_cache=chave_cache,
        retornar_bruto=True
    )
    if "error" in resp:
        return resp

    outputs = _extrair_outputs_lighthouse(resp.get("result", {}))
    primeiro = outputs[0] if outputs else {}
    places: List[Dict[str, Any]] = []
    for item in outputs:
        item_places = item.get("places")
        if isinstance(item_places, list):
            places.extend(item_places)

    return {
        "status": "sucesso",
        "google_profile_uid": uid_str,
        "encontrado": bool(outputs),
        "nome_completo": primeiro.get("fullname") or None,
        "foto_perfil_url": primeiro.get("avatar_url") or None,
        "google_maps_profile_url": primeiro.get("google_maps_profile_url") or None,
        "estatisticas": primeiro.get("counters_table") or {},
        "total_locais_avaliados": len(places),
        "locais_avaliados": places,
        "cache_id": resp.get("cache_id", chave_cache),
        "do_cache": bool(resp.get("_do_cache", False))
    }

async def google_maps_photos(google_profile_uid: Union[str, int]) -> dict:
    """
    Extrai as fotos publicadas em estabelecimentos e locais do Google Maps
    a partir do ID da conta Google (uid_google_maps_photos_v1).
    """
    uid_str = str(google_profile_uid).strip()
    if not uid_str or not uid_str.isdigit():
        return {"error": f"ID da conta Google (google_profile_uid) inválido: '{google_profile_uid}'. Deve conter apenas dígitos."}

    chave_cache = f"lighthouse_google_maps_photos_{uid_str}"
    resp = await async_executar_tarefa_lighthouse(
        job_name="uid_google_maps_photos_v1",
        task_info={"google_profile_uid": uid_str},
        chave_cache=chave_cache,
        retornar_bruto=True
    )
    if "error" in resp:
        return resp

    outputs = _extrair_outputs_lighthouse(resp.get("result", {}))
    primeiro = outputs[0] if outputs else {}
    photos: List[Dict[str, Any]] = []
    for item in outputs:
        item_photos = item.get("photos")
        if isinstance(item_photos, list):
            photos.extend(item_photos)

    return {
        "status": "sucesso",
        "google_profile_uid": uid_str,
        "encontrado": bool(outputs),
        "nome_completo": primeiro.get("fullname") or None,
        "foto_perfil_url": primeiro.get("avatar_url") or None,
        "google_maps_profile_url": primeiro.get("google_maps_profile_url") or None,
        "estatisticas": primeiro.get("counters_table") or {},
        "total_fotos_locais": len(photos),
        "fotos_locais": photos,
        "cache_id": resp.get("cache_id", chave_cache),
        "do_cache": bool(resp.get("_do_cache", False))
    }

async def google_maps_por_email(email: str, incluir_fotos: bool = False) -> dict:
    """
    Fluxo completo em uma chamada:
    1) Resolve o e-mail para o ID da conta Google (google_profile_uid / GAIA ID);
    2) Consulta automaticamente as avaliações de locais no Google Maps (e fotos, se incluir_fotos=True).
    """
    conta = await google_email_info(email)
    if "error" in conta:
        return conta

    uid = conta.get("google_profile_uid")
    if not uid:
        return {
            "status": "sucesso",
            "email": conta.get("email"),
            "encontrado": False,
            "google_profile_uid": None,
            "mensagem": "Nenhuma conta Google pública ou ID (google_profile_uid) foi encontrado para este e-mail.",
            "conta_google": conta
        }

    if incluir_fotos:
        reviews_resp, photos_resp = await asyncio.gather(
            google_maps_reviews(uid),
            google_maps_photos(uid)
        )
    else:
        reviews_resp = await google_maps_reviews(uid)
        photos_resp = None

    resultado = {
        "status": "sucesso",
        "email": conta.get("email"),
        "encontrado": True,
        "google_profile_uid": uid,
        "nome_completo": conta.get("nome_completo") or (reviews_resp.get("nome_completo") if isinstance(reviews_resp, dict) else None),
        "foto_perfil_url": conta.get("foto_perfil_url") or (reviews_resp.get("foto_perfil_url") if isinstance(reviews_resp, dict) else None),
        "ultima_atualizacao_unix": conta.get("ultima_atualizacao_unix"),
        "google_maps_profile_url": reviews_resp.get("google_maps_profile_url") if isinstance(reviews_resp, dict) else None,
        "estatisticas_maps": reviews_resp.get("estatisticas") if isinstance(reviews_resp, dict) else {},
        "total_locais_avaliados": reviews_resp.get("total_locais_avaliados", 0) if isinstance(reviews_resp, dict) else 0,
        "locais_avaliados": reviews_resp.get("locais_avaliados", []) if isinstance(reviews_resp, dict) else [],
        "cache_ids": {
            "conta_google": conta.get("cache_id"),
            "maps_reviews": reviews_resp.get("cache_id") if isinstance(reviews_resp, dict) else None
        }
    }
    if isinstance(reviews_resp, dict) and "error" in reviews_resp:
        resultado["erro_maps_reviews"] = reviews_resp["error"]

    if incluir_fotos and isinstance(photos_resp, dict):
        resultado["total_fotos_locais"] = photos_resp.get("total_fotos_locais", 0)
        resultado["fotos_locais"] = photos_resp.get("fotos_locais", [])
        resultado["cache_ids"]["maps_photos"] = photos_resp.get("cache_id")
        if "error" in photos_resp:
            resultado["erro_maps_photos"] = photos_resp["error"]

    return resultado

# ==============================================================================
# DUOLINGO OSINT (LAMPYRE API 1.0)
# ==============================================================================

async def duolingo_email_info(email: str) -> dict:
    """
    Consulta um e-mail no Duolingo (email_duolingo_v1) para extrair existência de conta,
    ID do perfil (duolingo_profile_uid), nome completo, @username, foto de perfil,
    idioma estudado, data de criação e URL do perfil.
    """
    em = normalizar_email(email)
    if not em or "@" not in em:
        return {"error": f"E-mail inválido para consulta Duolingo: '{email}'."}

    email_clean = em.replace("@", "_at_").replace(".", "_")
    chave_cache = f"lighthouse_duolingo_email_{email_clean}"

    resp = await async_executar_tarefa_lighthouse(
        job_name="email_duolingo_v1",
        task_info={"email": em},
        chave_cache=chave_cache,
        retornar_bruto=True
    )
    if "error" in resp:
        return resp

    outputs = _extrair_outputs_lighthouse(resp.get("result", {}))
    primeiro = outputs[0] if outputs else {}
    duolingo_uid = primeiro.get("duolingo_profile_uid")
    existe = primeiro.get("exists")
    encontrado = bool(existe) if existe is not None else bool(duolingo_uid or primeiro.get("username"))

    return {
        "status": "sucesso",
        "email": em,
        "encontrado": encontrado,
        "duolingo_profile_uid": str(duolingo_uid) if duolingo_uid else None,
        "nome_completo": primeiro.get("fullname") or None,
        "username": primeiro.get("username") or None,
        "foto_perfil_url": primeiro.get("avatar_url") or None,
        "foto_perfil_fileid": primeiro.get("avatar_fileid") or None,
        "idioma_estudado": primeiro.get("learning_language") or None,
        "criado_em_unix": primeiro.get("created"),
        "perfil_url": primeiro.get("url") or None,
        "perfis_encontrados": outputs,
        "cache_id": resp.get("cache_id", chave_cache),
        "do_cache": bool(resp.get("_do_cache", False))
    }
