import os
import json
import time
import secrets
import sys
from contextvars import ContextVar
from typing import Optional, Any
from src.core.config import KEYS_FILE, BASE_DIR

CONFIG_FILE = os.path.join(BASE_DIR, "mcp_config.json")
sessao_corrente: ContextVar[Optional[str]] = ContextVar("sessao_corrente", default=None)
sessoes_ativas: dict[str, dict] = {}
sessoes_autorizadas: set = set()

_cached_keys = {}
_cached_keys_mtime = 0

def carregar_config_global() -> dict:
    default_config = {
        "fontes_ativas": {
            "bigdata": True,
            "csint": True,
            "unitfour": True,
            "instagram": True,
            "tiktok": True,
            "linkedin": True,
            "lighthouse": True,
            "whois": True,
            "escavador": True,
            "tavily": True,
            "firecrawl": True,
            "serper": True,
            "wayback": True
        },
        "consultas_ativas": {}
    }
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CONFIG ERROR] Falha ao criar {CONFIG_FILE}: {e}", file=sys.stderr)
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "fontes_ativas" not in config:
            config["fontes_ativas"] = {}
        for k, v in default_config["fontes_ativas"].items():
            if k not in config["fontes_ativas"]:
                config["fontes_ativas"][k] = v
        if "consultas_ativas" not in config:
            config["consultas_ativas"] = {}
        return config
    except Exception as e:
        print(f"[CONFIG ERROR] Falha ao ler {CONFIG_FILE}: {e}", file=sys.stderr)
        return default_config

def salvar_config_global(config: dict) -> bool:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[CONFIG ERROR] Falha ao salvar {CONFIG_FILE}: {e}", file=sys.stderr)
        return False

def carregar_chaves_autorizadas() -> dict:
    global _cached_keys, _cached_keys_mtime
    chaves_env = os.environ.get("MCP_API_KEYS", "").strip()
    
    if not os.path.exists(KEYS_FILE) and not chaves_env:
        chave_inicial = "mcp_key_" + secrets.token_hex(24)
        dados_iniciais = {
            "admin": {
                "key": chave_inicial,
                "description": "Chave de acesso administrativo criada automaticamente no primeiro startup",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        try:
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(dados_iniciais, f, ensure_ascii=False, indent=2)
            print(f"[AUTH] Nova chave administrativa criada em {KEYS_FILE}", file=sys.stderr)
        except Exception as e:
            print(f"[AUTH ERROR] Falha ao criar {KEYS_FILE}: {e}", file=sys.stderr)
            
    if os.path.exists(KEYS_FILE):
        try:
            mtime = os.path.getmtime(KEYS_FILE)
            if mtime != _cached_keys_mtime:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                novas_chaves = {}
                if isinstance(dados, dict):
                    for usr, info in dados.items():
                        if isinstance(info, dict) and "key" in info:
                            novas_chaves[info["key"]] = {
                                "usuario": usr, 
                                "description": info.get("description", ""),
                                "permissoes": info.get("permissoes", ["*"])
                            }
                        elif isinstance(info, str):
                            novas_chaves[info] = {"usuario": usr, "description": "", "permissoes": ["*"]}
                elif isinstance(dados, list):
                    for item in dados:
                        if isinstance(item, dict) and "key" in item:
                            novas_chaves[item["key"]] = {
                                "usuario": item.get("usuario", "desconhecido"), 
                                "description": item.get("description", ""),
                                "permissoes": item.get("permissoes", ["*"])
                            }
                        elif isinstance(item, str):
                            novas_chaves[item] = {"usuario": "desconhecido", "description": "", "permissoes": ["*"]}
                
                _cached_keys = novas_chaves
                _cached_keys_mtime = mtime
        except Exception as e:
            print(f"[AUTH ERROR] Falha ao ler/recarregar {KEYS_FILE}: {e}", file=sys.stderr)
            
    if chaves_env:
        for k in chaves_env.split(","):
            token = k.strip()
            if token and token not in _cached_keys:
                _cached_keys[token] = {"usuario": "env_fallback", "description": "Carregado via .env", "permissoes": ["*"]}
                
    return _cached_keys

def verificar_token(token_fornecido: str) -> bool:
    if not token_fornecido:
        return False
    chaves = carregar_chaves_autorizadas()
    return token_fornecido in chaves

def extrair_token(request) -> Optional[str]:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
        
    x_api_key = request.headers.get("x-api-key")
    if x_api_key:
        return x_api_key.strip()
        
    mcp_api_key = request.headers.get("mcp-api-key")
    if mcp_api_key:
        return mcp_api_key.strip()
        
    token_query = request.query_params.get("token") or request.query_params.get("api_key") or request.query_params.get("key")
    if token_query:
        return token_query.strip()
        
    return None

def verificar_permissao_fonte(nome_fonte: Optional[str] = None, nome_consulta: Optional[str] = None) -> Optional[dict]:
    config = carregar_config_global()
    if nome_fonte:
        fontes_ativas = config.get("fontes_ativas", {})
        if fontes_ativas.get(nome_fonte) is False:
            return {"error": f"Fonte '{nome_fonte}' desativada globalmente pelo administrador."}

    if nome_consulta:
        consultas_ativas = config.get("consultas_ativas", {})
        if consultas_ativas.get(nome_consulta) is False:
            return {"error": f"Consulta '{nome_consulta}' desativada globalmente pelo administrador."}
        whitelabel = obter_nome_whitelabel(nome_consulta)
        if whitelabel and consultas_ativas.get(whitelabel) is False:
            return {"error": f"Consulta '{nome_consulta}' desativada globalmente pelo administrador."}

    try:
        sid = sessao_corrente.get()
    except LookupError:
        return None

    if not sid:
        return None

    session_info = sessoes_ativas.get(sid)
    if not session_info:
        return {"error": "Sessão inválida ou expirada."}

    permissoes = session_info.get("permissoes", ["*"])
    if "*" not in permissoes and nome_fonte and nome_fonte not in permissoes:
        if nome_consulta and nome_consulta in permissoes:
            pass
        else:
            return {"error": f"Acesso não autorizado. Chave de API sem permissão para '{nome_fonte}' ou '{nome_consulta}'."}

    return None

# ==============================================================================
# SISTEMA DE WHITE-LABELING (MASCARAMENTO DE FORNECEDORES)
# ==============================================================================
def obter_nome_whitelabel(nome_funcao: str) -> str:
    for prefixo in ["whois_", "csint_", "bigdata_", "unitfour_", "instagram_", "tiktok_", "linkedin_", "lighthouse_", "escavador_", "investigador_", "biometria_"]:
        if nome_funcao.startswith(prefixo):
            sub_nome = nome_funcao[len(prefixo):]
            if prefixo == "csint_" and sub_nome == "busca_universal":
                sub_nome = "busca_vazamentos"
            elif prefixo == "csint_" and sub_nome == "consultar_telefone":
                sub_nome = "consultar_telefone_vazamento"
            elif prefixo == "csint_" and sub_nome == "consultar_email":
                sub_nome = "consultar_email_vazamento"
            elif prefixo == "bigdata_" and sub_nome == "consultar_cpf":
                sub_nome = "consultar_cadastro_cpf"
            elif prefixo == "bigdata_" and sub_nome == "consultar_cnpj":
                sub_nome = "consultar_cadastro_cnpj"
            elif prefixo == "bigdata_" and sub_nome == "consultar_processo":
                sub_nome = "consultar_processos_judiciais"
            elif prefixo == "unitfour_" and sub_nome == "consultar_cpf":
                sub_nome = "consultar_dados_cadastrais_cpf"
            elif prefixo == "unitfour_" and sub_nome == "consultar_cnpj":
                sub_nome = "consultar_dados_cadastrais_cnpj"
            elif prefixo == "unitfour_" and sub_nome == "pessoas_ligadas":
                sub_nome = "ver_parentes_e_socios_cpf"
            elif prefixo == "unitfour_" and sub_nome == "tomadores_decisao":
                sub_nome = "ver_tomadores_decisao_cnpj"
            elif prefixo == "unitfour_" and sub_nome == "empresas_ligadas":
                sub_nome = "ver_empresas_ligadas_cnpj"
            elif prefixo == "unitfour_" and sub_nome == "proprietario_veiculo_placa":
                sub_nome = "consultar_proprietario_placa"
            elif prefixo == "instagram_" and sub_nome == "buscar_usuario":
                sub_nome = "buscar_perfil_instagram"
            elif prefixo == "instagram_" and sub_nome == "pesquisar_perfis":
                sub_nome = "pesquisar_perfis_instagram"
            elif prefixo == "instagram_" and sub_nome == "ver_seguidores":
                sub_nome = "ver_seguidores_instagram"
            elif prefixo == "instagram_" and sub_nome == "ver_posts":
                sub_nome = "ver_posts_instagram"
            elif prefixo == "instagram_" and sub_nome == "ver_stories":
                sub_nome = "ver_stories_instagram"
            elif prefixo == "tiktok_" and sub_nome == "buscar_perfil":
                sub_nome = "buscar_perfil_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "listar_videos":
                sub_nome = "listar_videos_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "listar_comentarios":
                sub_nome = "listar_comentarios_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "listar_respostas_comentario":
                sub_nome = "listar_respostas_comentario_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "listar_seguindo":
                sub_nome = "listar_seguidos_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "listar_seguidores":
                sub_nome = "listar_seguidores_tiktok"
            elif prefixo == "tiktok_" and sub_nome == "buscar_usuarios":
                sub_nome = "buscar_usuarios_tiktok"
            elif prefixo == "linkedin_" and sub_nome == "buscar_perfil":
                sub_nome = "buscar_perfil_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "consultar_endpoint":
                sub_nome = "linkedin_consulta_direta"
            elif prefixo == "linkedin_" and sub_nome == "buscar_pessoas_por_nome":
                sub_nome = "buscar_pessoas_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "ver_comentarios_post":
                sub_nome = "ver_comentarios_post_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "ver_reacoes_post":
                sub_nome = "ver_reacoes_post_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "buscar_posts":
                sub_nome = "buscar_posts_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "ver_posts_usuario":
                sub_nome = "ver_posts_usuario_linkedin"
            elif prefixo == "linkedin_" and sub_nome == "buscar_email_perfil":
                sub_nome = "buscar_email_perfil_linkedin"
            elif prefixo == "lighthouse_" and sub_nome.startswith("fb_"):
                sub_nome = sub_nome.replace("fb_uid_", "perfil_facebook_").replace("fb_", "facebook_")
            elif prefixo == "lighthouse_" and sub_nome == "image_facecheck":
                sub_nome = "reconhecimento_facial_amplo"
            elif prefixo == "lighthouse_" and sub_nome == "image_search4faces":
                sub_nome = "reconhecimento_facial_redes_sociais"
                
            return f"veridian_{sub_nome}"
            
    if nome_funcao == "tavily_buscar_web":
        return "veridian_buscar_web"
    if nome_funcao == "firecrawl_raspar_pagina":
        return "veridian_extrair_texto_site"
    if nome_funcao == "serper_buscar_web_dorks":
        return "veridian_pesquisa_dorks"
    if nome_funcao == "serper_buscar_google":
        return "veridian_buscar_google"
    if nome_funcao == "wayback_consultar_disponibilidade":
        return "veridian_pesquisa_historica_web"
    if nome_funcao == "wayback_listar_imagens":
        return "veridian_listar_imagens_historicas"
    if nome_funcao == "wayback_listar_snapshots":
        return "veridian_listar_snapshots_historicos"
        
    if nome_funcao.startswith("veridian_"):
        return nome_funcao
        
    return f"veridian_{nome_funcao}"

def limpar_descricao_whitelabel(docstring: str) -> str:
    if not docstring:
        return ""
    substituicoes = {
        "BigDataCorp": "Veridian",
        "BigData": "Veridian",
        "CSINT.pro": "Veridian",
        "CSINT": "Veridian",
        "UnitFour": "Veridian",
        "Unitfour": "Veridian",
        "HikerAPI": "Veridian",
        "Hiker API": "Veridian",
        "Harvest API": "Veridian",
        "Harvest": "Veridian",
        "Lighthouse": "Veridian",
        "WhoisXML API": "Veridian",
        "WhoisXML": "Veridian",
        "Escavador": "Veridian",
        "Tavily": "Veridian",
        "Firecrawl": "Veridian",
        "Serper.dev": "Veridian",
        "Serper": "Veridian",
        "Wayback Machine": "Veridian Histórico",
        "Wayback": "Veridian Histórico",
        "Internet Archive": "Veridian Histórico",
        "bigdata_consultar_cpf": "veridian_consultar_cadastro_cpf",
        "unitfour_consultar_cpf": "veridian_consultar_dados_cadastrais_cpf",
        "unitfour_pessoas_ligadas": "veridian_ver_parentes_e_socios_cpf",
        "unitfour_consulta_pep": "veridian_verificar_pep_cpf",
        "csint_consultar_email": "veridian_consultar_email_vazamento",
        "csint_consultar_telefone": "veridian_consultar_telefone_vazamento"
    }
    texto = docstring
    for de, para in substituicoes.items():
        texto = texto.replace(de, para)
    return texto

def limpar_resultado_whitelabel(result: Any) -> Any:
    substituicoes = {
        "BigDataCorp": "Veridian",
        "BigData": "Veridian",
        "bigdatacorp": "Veridian",
        "CSINT.pro": "Veridian",
        "csint.pro": "Veridian",
        "CSINT": "Veridian",
        "csint": "Veridian",
        "UnitFour": "Veridian",
        "Unitfour": "Veridian",
        "unitfour": "Veridian",
        "Escavador": "Veridian",
        "escavador": "Veridian",
        "HikerAPI": "Veridian",
        "Hiker API": "Veridian",
        "Harvest API": "Veridian",
        "Harvest": "Veridian",
        "Lighthouse": "Veridian",
        "WhoisXML API": "Veridian",
        "WhoisXML": "Veridian",
        "whoisxml": "Veridian",
        "Tavily": "Veridian",
        "Firecrawl": "Veridian",
        "Serper.dev": "Veridian",
        "Serper": "Veridian",
        "Wayback Machine": "Veridian Histórico",
        "Wayback": "Veridian Histórico",
        "Internet Archive": "Veridian Histórico"
    }
    
    def processar(val):
        if isinstance(val, str):
            for de, para in substituicoes.items():
                val = val.replace(de, para)
            return val
        elif isinstance(val, dict):
            return {k: processar(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [processar(v) for v in val]
        return val

    return processar(result)

