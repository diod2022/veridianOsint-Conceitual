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
usuario_corrente: ContextVar[Optional[dict]] = ContextVar("usuario_corrente", default=None)
token_corrente: ContextVar[Optional[str]] = ContextVar("token_corrente", default=None)

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
            "wayback": True,
            "deltafox": True
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
    """
    Carrega chaves autorizadas integrando com SQLite (Single Source of Truth)
    e garantindo migração transparente e retrocompatibilidade com mcp_keys.json.
    """
    global _cached_keys, _cached_keys_mtime
    from src.core.db import listar_usuarios_db, salvar_usuario_db

    chaves_env = os.environ.get("MCP_API_KEYS", "").strip()
    
    # 1. Se não existir KEYS_FILE nem variáveis de ambiente, inicializa chave administrativa
    if not os.path.exists(KEYS_FILE) and not chaves_env:
        chave_inicial = "mcp_key_" + secrets.token_hex(24)
        dados_iniciais = {
            "admin": {
                "key": chave_inicial,
                "description": "Chave de acesso administrativo criada automaticamente no primeiro startup",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "tipo_perfil": "ilimitado",
                "saldo_creditos": 0,
                "consultas_habilitadas": True,
                "permissoes": ["*"]
            }
        }
        try:
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(dados_iniciais, f, ensure_ascii=False, indent=2)
            print(f"[AUTH] Nova chave administrativa criada em {KEYS_FILE}", file=sys.stderr)
        except Exception as e:
            print(f"[AUTH ERROR] Falha ao criar {KEYS_FILE}: {e}", file=sys.stderr)

    # 2. Migração transparente de KEYS_FILE para SQLite caso o banco esteja vazio
    usuarios_db = listar_usuarios_db()
    if not usuarios_db and os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                for usr, info in dados.items():
                    if isinstance(info, dict):
                        token = info.get("key") or info.get("token")
                        is_adm = (usr == "admin")
                        salvar_usuario_db({
                            "usuario": usr,
                            "token": token,
                            "description": info.get("description", ""),
                            "tipo_perfil": "ilimitado" if is_adm else info.get("tipo_perfil", "creditos"),
                            "saldo_creditos": 0 if is_adm else int(info.get("saldo_creditos", 100)),
                            "consultas_habilitadas": True if is_adm else bool(info.get("consultas_habilitadas", True)),
                            "total_consultas": int(info.get("total_consultas", 0)),
                            "total_paginacoes": int(info.get("total_paginacoes", 0)),
                            "permissoes": info.get("permissoes", ["*"]),
                            "created_at": info.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        })
            usuarios_db = listar_usuarios_db()
        except Exception as e:
            print(f"[AUTH ERROR] Falha na migração de {KEYS_FILE} para SQLite: {e}", file=sys.stderr)

    # 3. Reconstrói o mapa de chaves autorizadas em memória a partir do SQLite
    novas_chaves = {}
    for u in usuarios_db:
        tok = u.get("token")
        if tok:
            novas_chaves[tok] = {
                "usuario": u["usuario"],
                "token": tok,
                "key": tok,
                "description": u.get("description", ""),
                "tipo_perfil": u.get("tipo_perfil", "creditos"),
                "saldo_creditos": u.get("saldo_creditos", 0),
                "consultas_habilitadas": u.get("consultas_habilitadas", True),
                "total_consultas": u.get("total_consultas", 0),
                "total_paginacoes": u.get("total_paginacoes", 0),
                "permissoes": u.get("permissoes", ["*"])
            }

    # 4. Fallback de chaves em variáveis de ambiente
    if chaves_env:
        for k in chaves_env.split(","):
            token = k.strip()
            if token and token not in novas_chaves:
                novas_chaves[token] = {
                    "usuario": "env_fallback",
                    "token": token,
                    "key": token,
                    "description": "Carregado via .env",
                    "tipo_perfil": "ilimitado",
                    "saldo_creditos": 9999,
                    "consultas_habilitadas": True,
                    "total_consultas": 0,
                    "total_paginacoes": 0,
                    "permissoes": ["*"]
                }

    _cached_keys = novas_chaves
    if os.path.exists(KEYS_FILE):
        _cached_keys_mtime = os.path.getmtime(KEYS_FILE)

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

def obter_contexto_usuario_atual() -> Optional[dict]:
    """Recupera o usuário associado à execução atual a partir de ContextVar ou sessões."""
    usr = usuario_corrente.get()
    if usr:
        return usr
    tok = token_corrente.get()
    if tok:
        chaves = carregar_chaves_autorizadas()
        if tok in chaves:
            return chaves[tok]
    try:
        sid = sessao_corrente.get()
        if sid and sid in sessoes_ativas:
            return sessoes_ativas[sid]
    except LookupError:
        pass
    return None

def detectar_tipo_e_custo_operacao(tool_name: str, arguments: dict) -> tuple[str, int, str]:
    """
    Motor unificado de inspeção de parâmetros:
    Diferencia consultas iniciais de solicitações de paginação de forma determinística.
    Retorna (tipo_op, custo, detalhe).
    """
    if not isinstance(arguments, dict):
        return ("consumo_consulta", 1, "Consulta inicial padrão")

    page = arguments.get("page")
    if page is not None:
        try:
            if int(page) > 1:
                return ("consumo_paginacao", 1, f"Paginação: página {page}")
        except (ValueError, TypeError):
            pass

    # Parâmetros de cursor conhecidos em todas as ferramentas integradas
    cursor_params = [
        "cursor", "end_cursor", "page_id", "page_id_followers",
        "page_id_following", "max_id", "next_cursor", "offset"
    ]
    for cp in cursor_params:
        val = arguments.get(cp)
        if val is not None and str(val).strip() != "" and str(val) not in ("0", "1"):
            return ("consumo_paginacao", 1, f"Paginação via cursor: {cp}={str(val)[:20]}")

    return ("consumo_consulta", 1, "Consulta inicial")

def validar_e_debitar_execucao(tool_name: str, arguments: dict) -> tuple[Optional[dict], Optional[dict]]:
    """
    Valida se o usuário pode consultar e executa o débito atômico imediato (Pre-Charge).
    Retorna:
      - (None, tx_info) em caso de sucesso.
      - (dict_erro, None) em caso de bloqueio (consultas desabilitadas ou saldo insuficiente).
    """
    from src.core.db import obter_usuario_db, debitar_credito_atomico

    usr_ctx = obter_contexto_usuario_atual()
    
    # Se não houver contexto mas for teste local ou inicialização sem chave informada
    if not usr_ctx:
        # Fallback para admin caso não haja usuário especificado em testes unitários locais
        chaves = carregar_chaves_autorizadas()
        for tok, info in chaves.items():
            if info.get("usuario") == "admin":
                usr_ctx = info
                break

    if not usr_ctx:
        return {"error": "Acesso não autorizado. Chave de API não informada ou inválida."}, None

    usuario = usr_ctx.get("usuario", "desconhecido")
    tipo_op, custo, detalhe = detectar_tipo_e_custo_operacao(tool_name, arguments)

    # Proteção rigorosa do Admin
    if usuario == "admin":
        return None, {"usuario": "admin", "custo": 0, "tipo_op": tipo_op, "tool_name": tool_name}

    # Busca estado mais atualizado do banco de dados (Single Source of Truth)
    u_db = obter_usuario_db(usuario)
    if not u_db:
        return {"error": f"Usuário '{usuario}' não encontrado na base de dados."}, None

    if not u_db.get("consultas_habilitadas", True):
        return {
            "error": f"Consultas desabilitadas para o usuário '{usuario}' pelo administrador.",
            "code": "QUERIES_DISABLED"
        }, None

    tipo_perfil = u_db.get("tipo_perfil", "creditos")
    if tipo_perfil == "ilimitado":
        debitar_credito_atomico(usuario, 0, tipo_op, tool_name, detalhe)
        return None, {"usuario": usuario, "custo": 0, "tipo_op": tipo_op, "tool_name": tool_name}

    # Perfil baseado em créditos: realiza o débito atômico
    sucesso, msg, saldo_pos = debitar_credito_atomico(usuario, custo, tipo_op, tool_name, detalhe)
    if not sucesso:
        return {
            "error": msg,
            "code": "INSUFFICIENT_CREDITS" if "Saldo insuficiente" in msg else "OPERATION_DENIED",
            "saldo_atual": saldo_pos
        }, None

    return None, {
        "usuario": usuario,
        "custo": custo,
        "tipo_op": tipo_op,
        "tool_name": tool_name,
        "saldo_posterior": saldo_pos
    }

def estornar_se_aplicavel(tx_info: Optional[dict], motivo: str = ""):
    """Efetua o estorno do débito em caso de falha grave de rede."""
    if not tx_info:
        return
    custo = tx_info.get("custo", 0)
    usuario = tx_info.get("usuario")
    tool_name = tx_info.get("tool_name", "")
    if custo > 0 and usuario and usuario != "admin":
        from src.core.db import estornar_credito_atomico
        estornar_credito_atomico(usuario, custo, tool_name, motivo)

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

    session_info = obter_contexto_usuario_atual()
    if not session_info:
        return None

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
    for prefixo in ["whois_", "csint_", "bigdata_", "unitfour_", "instagram_", "tiktok_", "linkedin_", "lighthouse_", "escavador_", "investigador_", "biometria_", "deltafox_"]:
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
            elif prefixo == "lighthouse_" and sub_nome == "image_geolocation":
                sub_nome = "geolocalizacao_imagem"
            elif prefixo == "deltafox_" and sub_nome == "cnh_prontuario":
                sub_nome = "consultar_cnh_prontuario"
            elif prefixo == "deltafox_" and sub_nome == "veiculo_restricoes_renajud":
                sub_nome = "consultar_veiculo_renajud"
            elif prefixo == "deltafox_" and sub_nome == "veiculo_endereco_proprietario":
                sub_nome = "consultar_veiculo_proprietario"
            elif prefixo == "deltafox_" and sub_nome == "frota_veiculos":
                sub_nome = "consultar_frota_veiculos"
            elif prefixo == "deltafox_" and sub_nome == "veiculo_historico_crv":
                sub_nome = "consultar_veiculo_historico_crv"
            elif prefixo == "deltafox_" and sub_nome == "servicos_disponiveis":
                sub_nome = "servicos_veiculares_disponiveis"
                
            return f"veridian_{sub_nome}"
            
    if nome_funcao == "tavily_buscar_web":
        return "veridian_buscar_web"
    if nome_funcao == "firecrawl_raspar_pagina":
        return "veridian_extrair_texto_site"
    if nome_funcao == "serper_buscar_web_dorks":
        return "veridian_pesquisa_dorks"
    if nome_funcao == "serper_buscar_google":
        return "veridian_buscar_google"
    if nome_funcao == "serper_buscar_avaliacoes_empresa":
        return "veridian_buscar_avaliacoes_empresa"
    if nome_funcao == "serper_buscar_reviews_por_email":
        return "veridian_buscar_reviews_por_email"
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
        "DeltaFox": "Veridian",
        "deltafox": "veridian",
        "DeltaID": "Veridian",
        "deltaid": "veridian",
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
        "Internet Archive": "Veridian Histórico",
        "DeltaFox": "Veridian",
        "deltafox": "Veridian",
        "DeltaID": "Veridian",
        "deltaid": "Veridian"
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

