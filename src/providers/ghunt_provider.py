import os
import sys
import json
import base64
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.security import normalizar_email

VENV_GHUNT_BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".venv", "bin", "ghunt")

def _obter_caminho_ghunt() -> str:
    if os.path.isfile(VENV_GHUNT_BIN) and os.access(VENV_GHUNT_BIN, os.X_OK):
        return VENV_GHUNT_BIN
    return "ghunt"

def verificar_status_autenticacao() -> dict:
    """
    Verifica se existe uma sessão válida salva do Google OSINT (GHunt).
    """
    from ghunt.objects.base import GHuntCreds
    try:
        creds = GHuntCreds()
        creds.load_creds(silent=True)
        return {
            "autenticado": True,
            "caminho_credenciais": creds.creds_path,
            "mensagem": "Sessão do Google OSINT ativa e pronta para consultas de perfis e Google Maps."
        }
    except Exception as e:
        return {
            "autenticado": False,
            "mensagem": "Nenhuma sessão ativa do Google OSINT configurada.",
            "instrucoes": (
                "Para ativar as consultas de reviews e GAIA ID:\n"
                "1. Abra seu navegador em uma conta Google (recomenda-se conta secundária/sock puppet).\n"
                "2. Utilize a extensão oficial 'GHunt Companion' (disponível para Chrome, Edge e Firefox: https://github.com/mxrch/ghunt_companion).\n"
                "3. Clique na extensão, copie o código Base64 gerado e utilize a ferramenta 'veridian_autenticar_google_osint' com o código.\n"
                "Ou execute './.venv/bin/ghunt login' no terminal da máquina."
            ),
            "detalhes": str(e)
        }

async def autenticar_google(codigo_base64_ou_token: str) -> dict:
    """
    Configura e valida a sessão do Google OSINT utilizando o token base64
    do GHunt Companion ou tokens OAuth2/Master Token do Google.
    """
    from ghunt.objects.base import GHuntCreds
    from ghunt.helpers import auth
    from ghunt.helpers.utils import get_httpx_client

    texto = codigo_base64_ou_token.strip().strip('"').strip("'")
    if not texto:
        return {"error": "Código de autenticação vazio."}

    oauth_token = ""
    master_token = ""

    if texto.startswith("oauth2_4/"):
        oauth_token = texto
    elif texto.startswith("aas_et/"):
        master_token = texto
    else:
        try:
            # Tenta decodificar o base64 do GHunt Companion
            decoded_bytes = base64.b64decode(texto)
            decoded_json = json.loads(decoded_bytes.decode("utf-8"))
            oauth_token = decoded_json.get("oauth_token", "")
            master_token = decoded_json.get("master_token", "")
        except Exception:
            oauth_token = texto

    as_client = get_httpx_client()
    try:
        ghunt_creds = GHuntCreds()
        owner_email = None
        owner_name = None

        if oauth_token:
            master_token, services, owner_email, owner_name = await auth.android_master_auth(as_client, oauth_token)
        elif not master_token:
            return {
                "error": "Não foi possível extrair um token válido. Cole o código Base64 da extensão GHunt Companion ou o token oauth2_4/ / aas_et/."
            }

        ghunt_creds.android.master_token = master_token
        ghunt_creds.cookies = {"a": "a"}
        ghunt_creds.osids = {"a": "a"}

        await auth.gen_cookies_and_osids(as_client, ghunt_creds)
        ghunt_creds.save_creds(silent=True)

        return {
            "status": "sucesso",
            "mensagem": "Autenticação do Google OSINT realizada e salva com sucesso!",
            "conta_conectada": owner_email or "Autenticado via Master Token",
            "nome_conectado": owner_name
        }
    except Exception as e:
        return {"error": f"Falha ao validar credenciais do Google: {str(e)}"}
    finally:
        await as_client.aclose()

async def investigar_email_google(email: str) -> dict:
    """
    Investiga um e-mail no ecossistema Google via GHunt.
    Extrai: Nome, Gaia ID, Foto de perfil, Avaliações e Fotos do Google Maps (reviews),
    Calendário público e serviços Google ativos.
    """
    email_limpo = normalizar_email(email)
    if not email_limpo or "@" not in email_limpo:
        return {"error": f"E-mail inválido para investigação Google: '{email}'."}

    cache_id = email_limpo.replace("@", "_at_").replace(".", "_")
    cache_key = f"ghunt_email_{cache_id}"

    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    # Verifica se há credenciais salvas antes de disparar o processo
    status_auth = verificar_status_autenticacao()
    if not status_auth.get("autenticado"):
        return {
            "status": "autenticacao_necessaria",
            "mensagem": status_auth.get("mensagem"),
            "instrucoes": status_auth.get("instrucoes")
        }

    ghunt_bin = _obter_caminho_ghunt()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        tmp_json_path = tmp_file.name

    try:
        cmd = [ghunt_bin, "email", "--json", tmp_json_path, email_limpo]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        # Verifica se o arquivo JSON foi gerado com sucesso
        if os.path.exists(tmp_json_path) and os.path.getsize(tmp_json_path) > 0:
            with open(tmp_json_path, "r", encoding="utf-8") as f:
                dados_brutos = json.load(f)

            # Processa e normaliza o retorno do GHunt para formato amigável
            container_profile = dados_brutos.get("PROFILE_CONTAINER", {})
            profile_data = container_profile.get("profile", {})
            maps_data = container_profile.get("maps", {})
            calendar_data = container_profile.get("calendar", {})

            # Avaliações do Google Maps
            reviews_maps = maps_data.get("reviews", []) if maps_data else []
            reviews_processados = []
            for r in reviews_maps:
                loc = r.get("location", {})
                reviews_processados.append({
                    "local": loc.get("name"),
                    "endereco": loc.get("address"),
                    "local_id": loc.get("id"),
                    "estrelas": r.get("rating"),
                    "data": r.get("date"),
                    "comentario": r.get("comment")
                })

            resultado = {
                "email": email_limpo,
                "encontrado": True,
                "gaia_id": getattr(profile_data, "personId", None) or profile_data.get("personId"),
                "nome": profile_data.get("names", {}).get("PROFILE", {}).get("fullname") if isinstance(profile_data.get("names"), dict) else None,
                "foto_perfil": profile_data.get("profilePhotos", {}).get("PROFILE", {}).get("url") if isinstance(profile_data.get("profilePhotos"), dict) else None,
                "ultima_edicao_perfil": profile_data.get("sourceIds", {}).get("PROFILE", {}).get("lastUpdated") if isinstance(profile_data.get("sourceIds"), dict) else None,
                "estatisticas_maps": maps_data.get("stats") if maps_data else {},
                "total_reviews_maps": len(reviews_processados),
                "reviews_google_maps": reviews_processados,
                "calendario_publico": calendar_data.get("details") if calendar_data else None,
                "dados_completos_brutos": dados_brutos
            }

            return salvar_cache_universal(cache_key, resultado)

        # Se falhou e não gerou JSON
        if "Please generate a new session" in stdout_str or "Please generate a new session" in stderr_str:
            return {
                "status": "sessao_expirada",
                "mensagem": "A sessão do Google OSINT expirou ou é inválida.",
                "instrucoes": status_auth.get("instrucoes")
            }

        if "The target wasn't found" in stdout_str or "The target wasn't found" in stderr_str:
            resultado_vazio = {
                "email": email_limpo,
                "encontrado": False,
                "mensagem": "Nenhuma conta Google pública foi localizada para este endereço de e-mail."
            }
            return salvar_cache_universal(cache_key, resultado_vazio)

        return {
            "error": "Falha na execução do GHunt.",
            "stdout": stdout_str[:300],
            "stderr": stderr_str[:300]
        }

    except Exception as e:
        return {"error": f"Erro interno ao executar investigação do e-mail: {str(e)}"}
    finally:
        if os.path.exists(tmp_json_path):
            try:
                os.remove(tmp_json_path)
            except Exception:
                pass

async def investigar_gaia_id(gaia_id: str) -> dict:
    """
    Investiga diretamente um Gaia ID do Google (identificador numérico de 21 dígitos).
    Extrai o histórico de avaliações, fotos e perfil público do Google Maps associado.
    """
    gaia_limpo = str(gaia_id).strip()
    if not gaia_limpo.isdigit():
        return {"error": f"Gaia ID inválido: '{gaia_id}'. Deve conter apenas dígitos numéricos."}

    cache_key = f"ghunt_gaia_{gaia_limpo}"
    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    status_auth = verificar_status_autenticacao()
    if not status_auth.get("autenticado"):
        return {
            "status": "autenticacao_necessaria",
            "mensagem": status_auth.get("mensagem"),
            "instrucoes": status_auth.get("instrucoes")
        }

    ghunt_bin = _obter_caminho_ghunt()

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        tmp_json_path = tmp_file.name

    try:
        cmd = [ghunt_bin, "gaia", "--json", tmp_json_path, gaia_limpo]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if os.path.exists(tmp_json_path) and os.path.getsize(tmp_json_path) > 0:
            with open(tmp_json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return salvar_cache_universal(cache_key, dados)

        return {
            "error": "Falha ao consultar Gaia ID.",
            "detalhes": stdout.decode("utf-8", errors="replace")[:300]
        }
    except Exception as e:
        return {"error": f"Erro interno ao consultar Gaia ID: {str(e)}"}
    finally:
        if os.path.exists(tmp_json_path):
            try:
                os.remove(tmp_json_path)
            except Exception:
                pass
