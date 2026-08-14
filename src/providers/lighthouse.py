import os
import sys
import asyncio
import hashlib
import httpx
from typing import Union, Optional, Dict, Any
from src.core.config import LIGHTHOUSE_API_KEY
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.http_client import resilient_request, get_semaphore

LIGHTHOUSE_BASE_URL = "https://lh.lampyre.io/api/v1"

def _get_token() -> str:
    return os.environ.get("LIGHTHOUSE_API_KEY") or os.environ.get("LIGHTHOUSE_API_TOKEN", "")

async def async_executar_tarefa_lighthouse(job_name: str, task_info: dict, chave_cache: str) -> dict:
    token = _get_token()
    if not token:
        return {"error": "LIGHTHOUSE_API_KEY não configurada no .env"}

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
            response = await resilient_request("POST", url_post, json=payload)
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
                status_resp = await resilient_request("GET", url_get)
                if status_resp.status_code != 200:
                    continue
                
                status_data = status_resp.json()
                status = status_data.get("task_status")
                
                if status == 0:
                    return salvar_cache_universal(chave_cache, status_data.get("result", {}))
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

# Facebook endpoints
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
        job_name="uid_fb_user_wall_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_uid_wall_{uid_str}"
    )

async def fb_uid_reposts(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_reposts_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_reposts_{uid_str}"
    )

async def fb_uid_likes(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_likes_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_likes_{uid_str}"
    )

async def fb_uid_comments(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_comments_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_comments_{uid_str}"
    )

async def fb_uid_friends(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_friends_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_friends_{uid_str}"
    )

async def fb_uid_photos(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_photos_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_photos_{uid_str}"
    )

async def fb_uid_albums(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_albums_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_albums_{uid_str}"
    )

async def fb_uid_live_streams(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_live_streams_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_live_streams_{uid_str}"
    )

async def fb_uid_games(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_games_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_games_{uid_str}"
    )

async def fb_uid_groups(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_groups_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_groups_{uid_str}"
    )

async def fb_search_posts(query: str, options: Optional[dict] = None) -> dict:
    q = query.strip()
    task_info = {"query": q}
    if options: task_info["options"] = options
    hash_id = hashlib.md5(q.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="search_fb_posts_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_search_posts_{hash_id}"
    )

async def fb_search_comments(query: str, options: Optional[dict] = None) -> dict:
    q = query.strip()
    task_info = {"query": q}
    if options: task_info["options"] = options
    hash_id = hashlib.md5(q.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="search_fb_comments_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_search_comments_{hash_id}"
    )

async def fb_search_places(query: str, options: Optional[dict] = None) -> dict:
    q = query.strip()
    task_info = {"query": q}
    if options: task_info["options"] = options
    hash_id = hashlib.md5(q.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="search_fb_places_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_search_places_{hash_id}"
    )

async def fb_search_events(query: str, options: Optional[dict] = None) -> dict:
    q = query.strip()
    task_info = {"query": q}
    if options: task_info["options"] = options
    hash_id = hashlib.md5(q.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="search_fb_events_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_fb_search_events_{hash_id}"
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

async def fb_uid_darknet(facebook_profile_uid: Union[str, int]) -> dict:
    uid_str = str(facebook_profile_uid).strip()
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_darknet_v1",
        task_info={"facebook_profile_uid": uid_str},
        chave_cache=f"lighthouse_fb_uid_darknet_{uid_str}"
    )

async def fb_phone_to_name(phone: Union[str, int]) -> dict:
    ph = str(phone).strip().replace("+", "").replace("-", "").replace(" ", "")
    return await async_executar_tarefa_lighthouse(
        job_name="phone_fb_to_name_v1",
        task_info={"phone": ph},
        chave_cache=f"lighthouse_fb_phone_to_name_{ph}"
    )

# Images / Facecheck / Geolocation
async def image_facecheck(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
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

async def image_search4faces(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
    task_info = {}
    if photo_url: task_info["photo_url"] = photo_url
    if photo_b64: task_info["photo_b64"] = photo_b64
    if photo_fileid: task_info["photo_fileid"] = photo_fileid
    
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    return await async_executar_tarefa_lighthouse(
        job_name="image_search4faces_v1",
        task_info=task_info,
        chave_cache=f"lighthouse_image_search4faces_{hash_id}"
    )

async def image_geolocation(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
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
