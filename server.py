import os
import json
import httpx
import asyncio
import sys
import contextlib
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env baseado no diretório atual deste script
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# Shared HTTPX client com connection pooling persistente (melhor prática de performance)
http_client = httpx.AsyncClient(timeout=30.0)

@contextlib.asynccontextmanager
async def server_lifespan(server):
    # --- Startup ---
    print("[MCP] Servidor 'veridianOsint-Conceitual' iniciado com pool de conexões persistentes.", file=sys.stderr, flush=True)
    try:
        yield
    finally:
        # --- Shutdown ---
        print("[MCP] Fechando conexões do pool HTTP de forma limpa...", file=sys.stderr, flush=True)
        await http_client.aclose()

# Instância do servidor com lifespan registrado. Porta padrão definida como 8001 para não conflitar com o projeto Casas Bahia (porta 8000).
mcp = FastMCP("veridianOsint-Conceitual", lifespan=server_lifespan, port=int(os.environ.get("FASTMCP_PORT", 8001)))

# ==============================================================================
# SISTEMA DE WHITE-LABELING (MASCARAMENTO DE FORNECEDORES)
# ==============================================================================
def obter_nome_whitelabel(nome_funcao: str) -> str:
    # Remove prefixo do fornecedor e adiciona 'veridian_'
    for prefixo in ["whois_", "csint_", "bigdata_", "unitfour_", "instagram_", "tiktok_", "linkedin_", "lighthouse_", "escavador_", "investigador_"]:
        if nome_funcao.startswith(prefixo):
            sub_nome = nome_funcao[len(prefixo):]
            # Mapeamentos específicos para maior elegância e evitar duplicidades:
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
                sub_nome = sub_nome.replace("fb_uid_", "perfil_facebook_")
                sub_nome = sub_nome.replace("fb_", "facebook_")
            elif prefixo == "lighthouse_" and sub_nome == "image_facecheck":
                sub_nome = "reconhecimento_facial_amplo"
            elif prefixo == "lighthouse_" and sub_nome == "image_search4faces":
                sub_nome = "reconhecimento_facial_redes_sociais"
                
            return f"veridian_{sub_nome}"
            
    # Caso especial para Tavily, Firecrawl e Serper
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
        
        # Mapeamentos de nomes de funções antigas
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

def limpar_resultado_whitelabel(result):
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

# Interceptação dinâmica do decorador mcp.tool para injeção automática de RBAC (permissões de fontes de dados)
original_tool = mcp.tool

def custom_tool(*args, **kwargs):
    def decorator(func):
        nome_funcao = func.__name__
        nome_fonte = None
        if nome_funcao.startswith("whois_"):
            nome_fonte = "whois"
        elif nome_funcao.startswith("csint_"):
            nome_fonte = "csint"
        elif nome_funcao.startswith("bigdata_"):
            nome_fonte = "bigdata"
        elif nome_funcao.startswith("unitfour_"):
            nome_fonte = "unitfour"
        elif nome_funcao.startswith("instagram_") or nome_funcao.startswith("tiktok_"):
            nome_fonte = "instagram"
        elif nome_funcao.startswith("linkedin_"):
            nome_fonte = "linkedin"
        elif nome_funcao.startswith("lighthouse_"):
            nome_fonte = "lighthouse"
        elif nome_funcao.startswith("escavador_"):
            nome_fonte = "escavador"
        elif nome_funcao.startswith("tavily_"):
            nome_fonte = "tavily"
        elif nome_funcao.startswith("firecrawl_"):
            nome_fonte = "firecrawl"
        elif nome_funcao.startswith("serper_"):
            nome_fonte = "serper"
        elif nome_funcao.startswith("wayback_"):
            nome_fonte = "wayback"

        # Mascara o nome da ferramenta dinamicamente
        kwargs["name"] = obter_nome_whitelabel(nome_funcao)
        
        # Mascara a descrição da ferramenta dinamicamente se fornecida no decorator
        if "description" in kwargs:
            kwargs["description"] = limpar_descricao_whitelabel(kwargs["description"])

        import functools
        @functools.wraps(func)
        async def wrapper(*func_args, **func_kwargs):
            if nome_fonte:
                # Executa a checagem de permissão no backend passando a fonte e a consulta específica
                permissao = verificar_permissao_fonte(nome_fonte, nome_funcao)
                if permissao:
                    return permissao
            
            result = await func(*func_args, **func_kwargs)
            # Retorna o resultado mascarando qualquer marca/nome de fornecedores
            return limpar_resultado_whitelabel(result)

        # Garante que o docstring da função wrapper seja mascarado
        wrapper.__doc__ = limpar_descricao_whitelabel(func.__doc__)
        
        return original_tool(*args, **kwargs)(wrapper)
    return decorator

mcp.tool = custom_tool

# ==============================================================================
# CONFIGURAÇÕES GERAIS E DE CACHE
# ==============================================================================
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_consultas")
os.makedirs(CACHE_DIR, exist_ok=True)

def obter_caminho_cache_seguro(cache_id: str) -> str:
    """
    Sanitiza o cache_id e resolve o caminho absoluto, garantindo que o arquivo
    esteja estritamente dentro do diretório de cache (evita Path Traversal).
    Retorna None se o caminho for inválido ou tentar sair do CACHE_DIR.
    """
    if not cache_id:
        return None
        
    # Rejeita explicitamente se contiver subdiretórios ou tentativa de retroceder caminho
    if "/" in cache_id or "\\" in cache_id or ".." in cache_id:
        return None
        
    cache_id_seguro = os.path.basename(cache_id)
    # Se o ID resultante for vazio ou pontos, retorna None
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return None
        
    caminho_absoluto = os.path.abspath(os.path.join(CACHE_DIR, f"{cache_id_seguro}.json"))
    caminho_limite = os.path.abspath(CACHE_DIR)
    
    if caminho_absoluto.startswith(caminho_limite):
        return caminho_absoluto
    return None

def checar_cache_universal(chave_identificadora: str) -> dict:
    """Verifica se existe cache local e retorna o resumo imediatamente se existir (evita chamadas redundantes)."""
    cache_file = obter_caminho_cache_seguro(chave_identificadora)
    if not cache_file or not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        if isinstance(dados, dict):
            resumo = {"tipo": "objeto", "chaves_disponiveis": list(dados.keys())}
        elif isinstance(dados, list):
            resumo = {"tipo": "lista", "tamanho_total": len(dados), "amostra_primeiros_3": dados[:3]}
        else:
            resumo = str(dados)[:500]

        print(f"[CACHE HIT] '{chave_identificadora}' recuperado do cache local.", file=sys.stderr, flush=True)
        return {
            "status": "sucesso",
            "cache_id": chave_identificadora,
            "mensagem": "Dados recuperados do cache local (crédito e tempo poupados!).",
            "resumo_dos_dados": resumo,
            "instrucao": f"Use a ferramenta 'investigador_ler_cache' com o cache_id '{chave_identificadora}' para explorar os dados."
        }
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao ler cache '{chave_identificadora}': {str(e)}", file=sys.stderr, flush=True)
    return None

def salvar_cache_universal(chave_identificadora: str, dados) -> dict:
    """Helper que salva dados grandes localmente e retorna apenas um sumário pro LLM."""
    cache_file = obter_caminho_cache_seguro(chave_identificadora)
    if not cache_file:
        print(f"[CACHE ERROR] Chave de cache inválida ou insegura para salvar: {chave_identificadora}", file=sys.stderr, flush=True)
        return {"status": "erro", "mensagem": "Nome de cache inválido."}
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    if isinstance(dados, dict):
        resumo = {"tipo": "objeto", "chaves_disponiveis": list(dados.keys())}
    elif isinstance(dados, list):
        resumo = {"tipo": "lista", "tamanho_total": len(dados), "amostra_primeiros_3": dados[:3]}
    else:
        resumo = str(dados)[:500]

    print(f"[CACHE SAVE] '{chave_identificadora}' gravado no cache local.", file=sys.stderr, flush=True)
    return {
        "status": "sucesso",
        "cache_id": chave_identificadora,
        "mensagem": "Dados gigantes salvos no cache. NUNCA REPITA A MESMA BUSCA.",
        "resumo_dos_dados": resumo,
        "instrucao": f"Use a ferramenta 'investigador_ler_cache' com o cache_id '{chave_identificadora}' para explorar os dados."
    }

@mcp.tool()
async def investigador_ler_cache(cache_id: str, chave: str = None, slice_start: int = 0, slice_end: int = 20) -> dict:
    """
    Lê os dados brutos de um cache salvo por outras ferramentas (Instagram, LinkedIn, BigData, etc).
    Use esta ferramenta para fatiar e navegar em dados grandes sem exceder o limite de tokens do Claude.
    
    Args:
        cache_id: O ID do cache retornado pela ferramenta original.
        chave: (Opcional) Se o dado principal for um objeto/dicionário, informe a chave exata para ler apenas ela.
        slice_start: (Opcional) Índice inicial para paginar listas (padrão 0).
        slice_end: (Opcional) Índice final para paginar listas (padrão 20).
    """
    cache_file = obter_caminho_cache_seguro(cache_id)
    if not cache_file or not os.path.exists(cache_file):
        return {"error": f"Cache '{cache_id}' não encontrado ou caminho inválido."}
    
    with open(cache_file, "r", encoding="utf-8") as f:
        dados = json.load(f)
        
    alvo = dados
    if chave:
        if isinstance(dados, dict):
            # Lida com o formato padrão do BigDataCorp (Result[0])
            if "Result" in dados and isinstance(dados["Result"], list) and len(dados["Result"]) > 0 and chave in dados["Result"][0]:
                alvo = dados["Result"][0][chave]
            elif chave in dados:
                alvo = dados[chave]
            else:
                return {"error": f"Chave '{chave}' não encontrada. Verifique as chaves disponíveis no cache."}
        else:
            return {"error": "O cache raiz é uma lista, não um dicionário. Não use o parâmetro 'chave'."}
            
    if isinstance(alvo, list):
        total = len(alvo)
        fatia = alvo[slice_start:slice_end]
        return {
            "paginacao": f"Mostrando itens {slice_start} a {min(slice_end, total)} de {total}",
            "dados": fatia
        }
        
    return alvo

# ==============================================================================
# 00. INTEGRAÇÃO ESCAVADOR API v2
# ==============================================================================
ESCAVADOR_API_TOKEN = os.getenv("ESCAVADOR_API_TOKEN")

# Semáforo para controlar concorrência (limite de 3 chamadas simultâneas)
escavador_semaphore = asyncio.Semaphore(3)

@mcp.tool()
async def escavador_buscar_processos_oab(
    oab_numero: str, 
    oab_estado: str, 
    oab_tipo: str = "ADVOGADO"
) -> dict:
    """
    Busca processos de um advogado a partir da OAB usando a API v2 do Escavador.
    
    Args:
        oab_numero: Número da OAB (ex: '12345' ou '123456').
        oab_estado: Sigla do Estado da OAB (ex: 'SP', 'RJ').
        oab_tipo: Tipo de inscrição OAB (opcional, padrão 'ADVOGADO').
    """
    if not ESCAVADOR_API_TOKEN:
        return {"error": "ESCAVADOR_API_TOKEN não configurada no .env"}
        
    oab_num_clean = oab_numero.strip()
    oab_est_clean = oab_estado.strip().upper()
    oab_tipo_clean = oab_tipo.strip().upper()
    
    if not oab_num_clean or not oab_est_clean:
        return {"error": "Número da OAB e Estado são obrigatórios."}
        
    # Cria chave de cache segura
    cache_id = f"oab_{oab_est_clean.lower()}_{oab_num_clean.lower()}"
    chave_cache = f"escavador_{cache_id}"
    
    # Interceptação de cache local
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit
        
    print(f"[ESCAVADOR] Consultando processos por OAB: {oab_num_clean}/{oab_est_clean}...", file=sys.stderr, flush=True)
    
    headers = {
        "Authorization": f"Bearer {ESCAVADOR_API_TOKEN}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }
    
    params = {
        "oab_numero": oab_num_clean,
        "oab_estado": oab_est_clean,
        "oab_tipo": oab_tipo_clean
    }
    
    async with escavador_semaphore:
        try:
            response = await http_client.get(
                "https://api.escavador.com/api/v2/advogado/processos",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            dados = response.json()
            
            return salvar_cache_universal(chave_cache, dados)
            
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[ESCAVADOR ERROR] Erro HTTP {e.response.status_code} para OAB {oab_num_clean}/{oab_est_clean}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API do Escavador", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[ESCAVADOR ERROR] Erro de rede para OAB {oab_num_clean}/{oab_est_clean}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro de rede ao consultar Escavador: {str(e)}"}


# ==============================================================================
# 0. INTEGRAÇÃO WHOISXML API
# ==============================================================================
WHOISXML_API_KEY = os.getenv("WHOISXML_API_KEY")

# Semáforo para controlar concorrência (limite de 5 chamadas simultâneas)
whois_semaphore = asyncio.Semaphore(5)

@mcp.tool()
async def whois_consultar(target: str, ignore_raw_text: bool = True, hard_refresh: bool = False) -> dict:
    """
    Realiza uma consulta WHOIS para obter informações de propriedade e registro de um domínio, IP ou e-mail.
    Se receber um e-mail completo, extrai o domínio associado e realiza a pesquisa.
    
    Args:
        target: Domínio (ex: google.com), IP (ex: 8.8.8.8) ou e-mail do qual deseja obter dados.
        ignore_raw_text: Se True (recomendado), stripa o texto bruto da resposta para evitar Context Bloat.
        hard_refresh: Se True, força a consulta em tempo real na API WhoisXML (consome 5 créditos).
    """
    if not WHOISXML_API_KEY:
        return {"error": "WHOISXML_API_KEY não configurada no .env"}
        
    target_clean = target.strip()
    if "@" in target_clean:
        parts = target_clean.split("@")
        if len(parts) > 1:
            target_clean = parts[-1].strip()
            
    # Cria chave de cache segura
    cache_id = target_clean.lower().replace(".", "_").replace("-", "_").replace(":", "_").replace(" ", "_")
    chave_cache = f"whois_{cache_id}"
    
    # Interceptação de cache local
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit
        
    print(f"[WHOISXML] Consultando alvo: {target_clean}...", file=sys.stderr, flush=True)
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "domainName": target_clean,
        "apiKey": WHOISXML_API_KEY,
        "outputFormat": "JSON",
        "ignoreRawTexts": 1 if ignore_raw_text else 0,
        "_hardRefresh": 1 if hard_refresh else 0
    }
    
    async with whois_semaphore:
        try:
            response = await http_client.post(
                "https://www.whoisxmlapi.com/whoisserver/WhoisService",
                headers=headers,
                json=payload,
                timeout=25.0
            )
            response.raise_for_status()
            dados = response.json()
            
            # Se a resposta indicar erro da API
            if isinstance(dados, dict) and "ErrorMessage" in dados:
                msg = dados["ErrorMessage"].get("msg", "Erro retornado pela API WhoisXML")
                print(f"[WHOISXML ERROR] API retornou erro: {msg}", file=sys.stderr, flush=True)
                return {"error": f"Erro retornado pela API WhoisXML: {msg}"}
                
            return salvar_cache_universal(chave_cache, dados)
            
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[WHOISXML ERROR] Erro HTTP {e.response.status_code} para {target_clean}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API WhoisXML", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[WHOISXML ERROR] Erro de rede para {target_clean}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro de rede ao consultar WhoisXML: {str(e)}"}

# ==============================================================================
# 1. INTEGRAÇÃO CSINT.PRO
# ==============================================================================
CSINT_BASE_URL = "https://csint.pro/api"
CSINT_API_KEY = os.getenv("CSINT_API_KEY")

# Semáforo para controlar concorrência (limite de 5 chamadas simultâneas, abaixo do limite de 10 da API)
csint_semaphore = asyncio.Semaphore(5)

@mcp.tool()
async def csint_consultar_ip(ip: str) -> dict:
    """
    Busca informações avançadas sobre um endereço IP (Geolocalização, ISP, Risco, Detecção de VPN/TOR/Proxy) 
    utilizando a inteligência da plataforma CSINT.pro.
    
    Args:
        ip: Endereço IP (ex: 8.8.8.8)
    """
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    print(f"[CSINT] Consultando IP {ip}...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with csint_semaphore:
        try:
            response = await http_client.post(
                f"{CSINT_BASE_URL}/iplookup",
                headers=headers,
                json={"ip": ip},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[CSINT ERROR] Erro HTTP {e.response.status_code} para IP {ip}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[CSINT ERROR] Erro de rede para IP {ip}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro ao consultar IP no CSINT: {str(e)}"}

@mcp.tool()
async def csint_busca_universal(query: str | int, tipo: str = "auto") -> dict:
    """
    Realiza uma busca universal em múltiplos bancos de dados de vazamentos (LeakCheck, Snusbase, HackCheck, Breach.vip)
    em paralelo utilizando a API do CSINT.pro.
    
    Args:
        query: O dado a ser buscado (ex: email, telefone, username ou ip).
        tipo: O tipo de dado. Pode ser 'email', 'phone', 'username', 'ip' ou 'auto'.
    """
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    query_str = str(query)
    cache_id = query_str.replace('@', '').replace('.', '').replace('+', '').replace('-', '').replace(' ', '')
    chave_cache = f"csint_busca_{cache_id}"
    
    # Interceptação Ativa de Cache (Evita cobrança de API e retorna em <1ms!)
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[CSINT] Executando busca universal para '{query_str}' (Tipo: {tipo})...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with csint_semaphore:
        try:
            response = await http_client.post(
                f"{CSINT_BASE_URL}/search",
                headers=headers,
                json={"query": query_str, "type": tipo},
                timeout=35.0 # Busca universal pode demorar mais
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[CSINT ERROR] Erro HTTP {e.response.status_code} na busca universal: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[CSINT ERROR] Erro de rede na busca universal: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro na busca universal CSINT: {str(e)}"}

@mcp.tool()
async def csint_consultar_telefone(telefone: str | int) -> dict:
    """
    Realiza busca avançada de inteligência e reputação sobre um número de telefone utilizando a SEON API da CSINT.pro.
    Retorna a operadora, país, validade do número e contas vinculadas (WhatsApp, Telegram, redes sociais, etc).
    
    Args:
        telefone: O número de telefone completo com o código do país (ex: '+5511988887777').
    """
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    tel_str = str(telefone)
    cache_id = tel_str.replace('+', '').replace('-', '').replace(' ', '')
    chave_cache = f"csint_seon_phone_{cache_id}"
    
    # Interceptação Ativa de Cache
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[CSINT] Consultando telefone {tel_str} (SEON)...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with csint_semaphore:
        try:
            response = await http_client.post(
                f"{CSINT_BASE_URL}/seon/phone",
                headers=headers,
                json={"phone": tel_str},
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[CSINT ERROR] Erro HTTP {e.response.status_code} para telefone {tel_str}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[CSINT ERROR] Erro de rede para telefone {tel_str}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro ao consultar telefone no CSINT: {str(e)}"}

@mcp.tool()
async def csint_consultar_email(email: str | int) -> dict:
    """
    Realiza busca avançada de inteligência e reputação sobre um endereço de e-mail utilizando a SEON API da CSINT.pro.
    Verifica a existência do e-mail e mapeia contas e perfis registrados em mais de 20 plataformas 
    e redes sociais simultâneas (ex: LinkedIn, Twitter, Instagram, Netflix, Spotify, etc.).
    
    Args:
        email: O endereço de e-mail completo pesquisado.
    """
    if not CSINT_API_KEY:
        return {"error": "CSINT_API_KEY não configurada no .env"}
        
    email_str = str(email)
    cache_id = email_str.replace("@", "_at_").replace(".", "_").replace("+", "").replace("-", "")
    chave_cache = f"csint_seon_email_{cache_id}"
    
    # Interceptação Ativa de Cache
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[CSINT] Consultando e-mail {email_str} (SEON)...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": CSINT_API_KEY,
        "Content-Type": "application/json"
    }
    
    async with csint_semaphore:
        try:
            response = await http_client.post(
                f"{CSINT_BASE_URL}/seon/email",
                headers=headers,
                json={"email": email_str},
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[CSINT ERROR] Erro HTTP {e.response.status_code} para e-mail {email_str}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API CSINT", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[CSINT ERROR] Erro de rede para e-mail {email_str}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro ao consultar e-mail no CSINT: {str(e)}"}

# ==============================================================================
# 2. INTEGRAÇÃO BIGDATACORP (DRILL-DOWN)
# ==============================================================================
import re

BIGDATA_BASE_URL = "https://plataforma.bigdatacorp.com.br"
BIGDATA_TOKEN = os.getenv("BIGDATA_ACCESS_TOKEN")
BIGDATA_TOKEN_ID = os.getenv("BIGDATA_TOKEN_ID")

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

def get_nested_case_insensitive(data: dict, path: str) -> any:
    """
    Navega por um dicionário usando um caminho separado por ponto (ex: 'Contacts.Phones')
    de forma case-insensitive, tolerando variações de chaves.
    """
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

def filtrar_dados_pf(dados_completos: dict, dataset_code: str) -> dict:
    """Filtra o JSON bruto retornado pela API para retornar apenas a fatia correspondente ao código solicitado."""
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

def filtrar_dados_pj(dados_completos: dict, dataset_code: str) -> dict:
    """Filtra o JSON bruto de empresa correspondente ao código solicitado."""
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

@mcp.tool()
async def bigdata_consultar_cpf(cpf: str | int, datasets: str = "bdcbasicdata") -> dict:
    """
    Realiza consulta de Pessoa Física (CPF) na BigDataCorp, buscando um ou mais datasets.
    O CPF pode ser enviado com qualquer tipo de máscara (pontos, traços, etc) e com/sem zeros à esquerda.
    Salva os dados massivos no cache local e retorna as chaves disponíveis.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
        datasets: Lista de datasets separados por vírgula (ex: 'bdcbasicdata,bdcphones').
    """
    if not BIGDATA_TOKEN or BIGDATA_TOKEN == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    # Higienização de máscaras e preenchimento de zeros (zfill)
    cpf_limpo = re.sub(r"\D", "", str(cpf))
    if 9 <= len(cpf_limpo) <= 11:
        cpf_limpo = cpf_limpo.zfill(11)
        
    if len(cpf_limpo) != 11:
        return {"error": f"CPF inválido após higienização: '{cpf_limpo}' (deve ter 11 dígitos)"}
        
    chave_cache = f"bigdata_{cpf_limpo}"
    cache_file = os.path.join(CACHE_DIR, f"{chave_cache}.json")
    
    # Interceptação de cache local
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
            
    # Resolve os códigos informados para os datasets oficiais da API
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
            # Caso envie o nome técnico diretamente
            lista_datasets_api.append(cod)
            
    datasets_string = ",".join(list(set(lista_datasets_api)))
    print(f"[BDC] Consultando CPF {cpf_limpo} (Datasets API: {datasets_string})...", file=sys.stderr, flush=True)
    
    headers = {
        "AccessToken": BIGDATA_TOKEN,
        "Content-Type": "application/json"
    }
    if BIGDATA_TOKEN_ID:
        headers["TokenId"] = BIGDATA_TOKEN_ID

    payload = {
        "q": f"doc{{'{cpf_limpo}'}}",
        "Datasets": datasets_string
    }
    
    try:
        response = await http_client.post(
            f"{BIGDATA_BASE_URL}/pessoas",
            headers=headers,
            json=payload,
            timeout=25.0
        )
        response.raise_for_status()
        dados_completos = response.json()
        
        # Paginação de processos se necessário (limite de 1000)
        if contem_processes and "Result" in dados_completos and len(dados_completos["Result"]) > 0:
            alvo = dados_completos["Result"][0]
            if "Processes" in alvo:
                processes_data = alvo["Processes"]
                if processes_data and isinstance(processes_data, dict):
                    total_lawsuits = processes_data.get("TotalLawsuits", 0)
                    lawsuits_list = processes_data.get("Lawsuits", [])
                    max_lawsuits = min(total_lawsuits, 1000)
                    
                    if total_lawsuits > len(lawsuits_list) and len(lawsuits_list) < max_lawsuits:
                        print(f"[BDC PAGINATION] Buscando mais páginas para CPF {cpf_limpo}...", file=sys.stderr, flush=True)
                        next_page_id = processes_data.get("NextPageId")
                        page = 1
                        while next_page_id and len(lawsuits_list) < max_lawsuits:
                            payload_next = {
                                "q": f"doc{{'{cpf_limpo}'}}",
                                "Datasets": f"processes.next({next_page_id})"
                            }
                            try:
                                response_next = await http_client.post(
                                    f"{BIGDATA_BASE_URL}/pessoas",
                                    headers=headers,
                                    json=payload_next,
                                    timeout=25.0
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
                        
        # Salva em cache local
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

@mcp.tool()
async def bigdata_ver_categoria(cpf: str | int, dataset_code: str) -> dict:
    """
    Retorna apenas a fatia de dados correspondente a um código específico do cache do CPF.
    O CPF pode ser enviado com qualquer tipo de máscara (pontos, traços, etc) e com/sem zeros à esquerda.
    
    Args:
        cpf: O CPF do investigado (com ou sem máscara).
        dataset_code: O código do dataset desejado (ex: 'bdcphones', 'bdcbasicdata', 'bdclawsuits').
    """
    cpf_limpo = re.sub(r"\D", "", str(cpf))
    if 9 <= len(cpf_limpo) <= 11:
        cpf_limpo = cpf_limpo.zfill(11)
        
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

@mcp.tool()
async def bigdata_consultar_cnpj(cnpj: str | int, datasets: str = "bdccompanybasicdata") -> dict:
    """
    Realiza consulta de Pessoa Jurídica (CNPJ) na BigDataCorp, buscando um ou mais datasets.
    O CNPJ pode ser enviado com qualquer tipo de máscara (pontos, barras, traços, etc) e com/sem zeros à esquerda.
    Salva os dados massivos no cache local e retorna as chaves disponíveis.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
        datasets: Lista de datasets separados por vírgula (ex: 'bdccompanybasicdata,bdccompanyphones').
    """
    if not BIGDATA_TOKEN or BIGDATA_TOKEN == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    # Higienização de máscaras e preenchimento de zeros (zfill)
    cnpj_limpo = re.sub(r"\D", "", str(cnpj))
    if 11 <= len(cnpj_limpo) <= 14:
        cnpj_limpo = cnpj_limpo.zfill(14)
        
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
                "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados.",
                "categorias_disponiveis": chaves_disponiveis
            }
        except Exception as e:
            print(f"[CACHE ERROR] Falha ao carregar cache do CNPJ {cnpj_limpo}: {str(e)}", file=sys.stderr, flush=True)
            
    lista_codigos = [c.strip().lower() for c in datasets.split(",")]
    lista_datasets_api = []
    contem_processes = False
    
    for cod in lista_codigos:
        if cod in MAPA_DATASETS_PJ:
            api_dataset = MAPA_DATASETS_PJ[cod]
            if api_dataset == "processes":
                contem_processes = True
                lista_datasets_api.append("processes.limit(80)")
            else:
                lista_datasets_api.append(api_dataset)
        else:
            lista_datasets_api.append(cod)
            
    datasets_string = ",".join(list(set(lista_datasets_api)))
    print(f"[BDC] Consultando CNPJ {cnpj_limpo} (Datasets API: {datasets_string})...", file=sys.stderr, flush=True)
    
    headers = {
        "AccessToken": BIGDATA_TOKEN,
        "Content-Type": "application/json"
    }
    if BIGDATA_TOKEN_ID:
        headers["TokenId"] = BIGDATA_TOKEN_ID

    payload = {
        "q": f"doc{{'{cnpj_limpo}'}}",
        "Datasets": datasets_string
    }
    
    try:
        response = await http_client.post(
            f"{BIGDATA_BASE_URL}/empresas",
            headers=headers,
            json=payload,
            timeout=25.0
        )
        response.raise_for_status()
        dados_completos = response.json()
        
        # Paginação de processos para empresas (até 1000)
        if contem_processes and "Result" in dados_completos and len(dados_completos["Result"]) > 0:
            alvo = dados_completos["Result"][0]
            lawsuits_data = alvo.get("Lawsuits") or alvo.get("Processes")
            if lawsuits_data and isinstance(lawsuits_data, dict):
                total_lawsuits = lawsuits_data.get("TotalLawsuits", 0)
                lawsuits_list = lawsuits_data.get("Lawsuits", [])
                max_lawsuits = min(total_lawsuits, 1000)
                
                if total_lawsuits > len(lawsuits_list) and len(lawsuits_list) < max_lawsuits:
                    print(f"[BDC PAGINATION] Buscando mais páginas para CNPJ {cnpj_limpo}...", file=sys.stderr, flush=True)
                    next_page_id = lawsuits_data.get("NextPageId")
                    page = 1
                    while next_page_id and len(lawsuits_list) < max_lawsuits:
                        payload_next = {
                            "q": f"doc{{'{cnpj_limpo}'}}",
                            "Datasets": f"processes.next({next_page_id})"
                        }
                        try:
                            response_next = await http_client.post(
                                f"{BIGDATA_BASE_URL}/empresas",
                                headers=headers,
                                json=payload_next,
                                timeout=25.0
                            )
                            response_next.raise_for_status()
                            data_next = response_next.json()
                            
                            if "Result" in data_next and len(data_next["Result"]) > 0:
                                alvo_next = data_next["Result"][0]
                                lawsuits_data_next = alvo_next.get("Lawsuits") or alvo_next.get("Processes") or {}
                                next_list = lawsuits_data_next.get("Lawsuits", [])
                                if not next_list:
                                    break
                                lawsuits_list.extend(next_list)
                                next_page_id = lawsuits_data_next.get("NextPageId")
                            else:
                                break
                        except Exception as e:
                            print(f"[BDC PAGINATION ERROR] Falha na página {page} do CNPJ: {str(e)}", file=sys.stderr, flush=True)
                            break
                        page += 1
                    lawsuits_data["Lawsuits"] = lawsuits_list[:max_lawsuits]
                    
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
            "proximo_passo": "Use a ferramenta 'bigdata_ver_categoria_cnpj' passando o CNPJ e um dos códigos desejados.",
            "categorias_disponiveis": chaves_disponiveis
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"Erro HTTP {e.response.status_code} no BigDataCorp", "detalhes": e.response.text}
    except Exception as e:
        return {"error": f"Erro ao consultar CNPJ no BigDataCorp: {str(e)}"}

@mcp.tool()
async def bigdata_ver_categoria_cnpj(cnpj: str | int, dataset_code: str) -> dict:
    """
    Retorna apenas a fatia de dados correspondente a um código específico do cache do CNPJ.
    O CNPJ pode ser enviado com qualquer tipo de máscara (pontos, barras, traços, etc) e com/sem zeros à esquerda.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
        dataset_code: O código do dataset desejado (ex: 'bdccompanyphones', 'bdccompanybasicdata').
    """
    cnpj_limpo = re.sub(r"\D", "", str(cnpj))
    if 11 <= len(cnpj_limpo) <= 14:
        cnpj_limpo = cnpj_limpo.zfill(14)
        
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

@mcp.tool()
async def bigdata_consultar_processo(numero_processo: str | int, dataset_code: str = "bdclawsuitbasicdata") -> dict:
    """
    Busca os dados básicos de um Processo Judicial específico na BigDataCorp.
    
    Args:
        numero_processo: O número do processo (preferencialmente no formato CNJ xxxxxxx-xx.xxxx.x.xx.xxxx).
        dataset_code: O código do dataset (padrão é 'bdclawsuitbasicdata' que mapeia para 'basic_data').
    """
    if not BIGDATA_TOKEN:
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}
        
    processo_str = str(numero_processo).strip()
    headers = {
        "AccessToken": BIGDATA_TOKEN,
        "TokenId": BIGDATA_TOKEN_ID or "",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Resolve o código
    api_dataset = "basic_data"
    if dataset_code.strip().lower() != "bdclawsuitbasicdata":
        api_dataset = dataset_code.strip()
        
    payload = {
        "Datasets": api_dataset,
        "q": f"processnumber{{{processo_str}}}",
        "Limit": 1
    }
    
    try:
        response = await http_client.post(
            f"{BIGDATA_BASE_URL}/processos",
            headers=headers,
            json=payload,
            timeout=25.0
        )
        response.raise_for_status()
        cache_id = f"processo_{processo_str.replace('.', '').replace('-', '').replace('/', '')}"
        return salvar_cache_universal(cache_id, response.json())
    except Exception as e:
        return {"error": f"Erro ao consultar processo no BigDataCorp: {str(e)}"}


# ==============================================================================
# 3. INTEGRAÇÃO HIKERAPI (INSTAGRAM OSINT)
# ==============================================================================
HIKER_BASE_URL = "https://api.hikerapi.com"
HIKER_TOKEN = os.getenv("HIKER_API_TOKEN")

@mcp.tool()
async def instagram_buscar_usuario(username: str) -> dict:
    """
    Busca os dados de um perfil do Instagram usando o @username (sem o @).
    Esta é a PRIMEIRA ferramenta que deve ser usada, pois ela retorna o 'user_id' (pk) 
    necessário para as outras consultas (seguidores, posts, etc).
    
    Args:
        username: O nome de usuário do Instagram (ex: 'neymarjr').
    """
    if not HIKER_TOKEN:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    headers = {
        "x-access-key": HIKER_TOKEN,
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{HIKER_BASE_URL}/v2/user/by/username",
                headers=headers,
                params={"username": username},
                timeout=20.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"ig_user_{username}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na HikerAPI (buscar usuário): {str(e)}"}

@mcp.tool()
async def instagram_ver_seguidores(user_id: str | int) -> dict:
    """
    Extrai a primeira página de seguidores (e quem o alvo segue) usando o user_id.
    
    Args:
        user_id: O ID interno do usuário (obtido com instagram_buscar_usuario).
    """
    user_id = str(user_id)
    if not HIKER_TOKEN:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    headers = {"x-access-key": HIKER_TOKEN, "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Fazemos a busca de seguidores
            resp_followers = await client.get(
                f"{HIKER_BASE_URL}/v2/user/followers",
                headers=headers,
                params={"user_id": user_id},
                timeout=30.0
            )
            
            # Fazemos a busca de quem o usuário segue
            resp_following = await client.get(
                f"{HIKER_BASE_URL}/v2/user/following",
                headers=headers,
                params={"user_id": user_id},
                timeout=30.0
            )
            
            resultado = {}
            if resp_followers.status_code == 200:
                resultado["followers"] = resp_followers.json()
            if resp_following.status_code == 200:
                resultado["following"] = resp_following.json()
                
            if not resultado:
                return {"error": "Falha ao obter seguidores e seguindo"}
            return salvar_cache_universal(f"ig_followers_{user_id}", resultado)
        except httpx.HTTPError as e:
            return {"error": f"Erro na HikerAPI (seguidores): {str(e)}"}

@mcp.tool()
async def instagram_ver_posts(user_id: str | int) -> dict:
    """
    Puxa os posts recentes do feed do usuário. Útil para análise de fotos, legendas e locais.
    
    Args:
        user_id: O ID interno do usuário.
    """
    user_id = str(user_id)
    if not HIKER_TOKEN:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    headers = {"x-access-key": HIKER_TOKEN, "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{HIKER_BASE_URL}/v1/user/medias/chunk",
                headers=headers,
                params={"user_id": user_id},
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"ig_posts_{user_id}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na HikerAPI (ver posts): {str(e)}"}

@mcp.tool()
async def instagram_ver_stories(user_id: str | int) -> dict:
    """
    Puxa os stories que estão ativos/online neste exato momento para o usuário.
    
    Args:
        user_id: O ID interno do usuário.
    """
    user_id = str(user_id)
    if not HIKER_TOKEN:
        return {"error": "HIKER_API_TOKEN não configurado no .env"}
        
    headers = {"x-access-key": HIKER_TOKEN, "Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{HIKER_BASE_URL}/v2/user/stories",
                headers=headers,
                params={"user_id": user_id},
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"ig_stories_{user_id}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na HikerAPI (ver stories): {str(e)}"}

# ==============================================================================
# 4. INTEGRAÇÃO HARVEST API (LINKEDIN OSINT)
# ==============================================================================
HARVEST_BASE_URL = "https://api.hikerapi.com" # Algumas rotas mapeiam para hikerapi/harvest
HARVEST_TOKEN = os.getenv("HARVEST_API_TOKEN")

@mcp.tool()
async def linkedin_buscar_perfil(linkedin_url: str) -> dict:
    """
    Extrai o perfil completo de um usuário no LinkedIn usando a URL.
    
    Args:
        linkedin_url: A URL completa do perfil (ex: 'https://www.linkedin.com/in/williamhgates').
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    # Harvest API endpoint padrão para perfis
    endpoint = "https://api.harvest-api.com/linkedin/profile"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                endpoint,
                headers=headers,
                params={"url": linkedin_url},
                timeout=30.0
            )
            response.raise_for_status()
            import urllib.parse
            parsed_url = urllib.parse.urlparse(linkedin_url)
            perfil_id = parsed_url.path.strip("/").split("/")[-1] if "/" in parsed_url.path else "alvo"
            return salvar_cache_universal(f"li_perfil_{perfil_id}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na Harvest API (buscar perfil do LinkedIn): {str(e)}"}

@mcp.tool()
async def linkedin_consultar_endpoint(endpoint_name: str, target_url: str) -> dict:
    """
    Consulta endpoints avançados do LinkedIn na Harvest API (Posts, Comentários, Reações, etc).
    
    Args:
        endpoint_name: O nome final do endpoint. Opções válidas: 
                       'profile/posts', 'profile-comments', 'profile-reactions',
                       'post-comments', 'post-reactions', 'profile-search', 'company-search'.
        target_url: A URL alvo do LinkedIn (perfil, post ou empresa, dependendo do endpoint).
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    # Monta a URL baseado na rota oficial
    endpoint = f"https://api.harvest-api.com/linkedin/{endpoint_name}"
    
    # O Harvest costuma aceitar a url alvo via query params
    # Ex: /linkedin/profile/posts?url=...
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                endpoint,
                headers=headers,
                params={"url": target_url},
                timeout=40.0
            )
            response.raise_for_status()
            cache_id = f"li_endpoint_{endpoint_name.replace('/', '_')}"
            return salvar_cache_universal(cache_id, response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na Harvest API ({endpoint_name}): {str(e)}"}

@mcp.tool()
async def linkedin_buscar_pessoas_por_nome(nome_completo: str, nome: str = None, sobrenome: str = None) -> dict:
    """
    Busca perfis de pessoas no LinkedIn pelo nome ou palavras-chave.
    
    Args:
        nome_completo: O nome completo da pessoa ou termo de busca geral (ex: 'Mark Peterson').
        nome: Opcional. Apenas o primeiro nome (ex: 'Mark').
        sobrenome: Opcional. Apenas o sobrenome (ex: 'Peterson').
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    endpoint = "https://api.harvest-api.com/linkedin/profile-search"
    
    params = {"search": nome_completo}
    if nome:
        params["firstName"] = nome
    if sobrenome:
        params["lastName"] = sobrenome
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=40.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"li_search_{nome_completo.replace(' ', '_')}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro na Harvest API (buscar pessoas por nome): {str(e)}"}

@mcp.tool()
async def linkedin_ver_comentarios_post(post_url: str, sort_by: str = "relevance", page: int = 1) -> dict:
    """
    Recupera os comentários de uma publicação do LinkedIn a partir de sua URL.
    
    Args:
        post_url: A URL completa da publicação no LinkedIn.
        sort_by: Opcional. Ordenação dos comentários ('relevance' ou 'date'). Padrão é 'relevance'.
        page: Opcional. Número da página para paginação. Padrão é 1.
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    params = {
        "post": post_url,
        "sortBy": sort_by,
        "page": page
    }
    
    endpoint = "https://api.harvest-api.com/linkedin/post-comments"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            import urllib.parse
            parsed = urllib.parse.urlparse(post_url)
            post_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "post"
            return salvar_cache_universal(f"li_post_comments_{post_id}_p{page}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar comentários do post na Harvest API: {str(e)}"}

@mcp.tool()
async def linkedin_ver_reacoes_post(post_url: str, page: int = 1) -> dict:
    """
    Recupera as reações (curtidas, apoios, etc.) de uma publicação do LinkedIn a partir de sua URL.
    
    Args:
        post_url: A URL completa da publicação no LinkedIn.
        page: Opcional. Número da página para paginação. Padrão é 1.
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    params = {
        "post": post_url,
        "page": page
    }
    
    endpoint = "https://api.harvest-api.com/linkedin/post-reactions"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            import urllib.parse
            parsed = urllib.parse.urlparse(post_url)
            post_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "post"
            return salvar_cache_universal(f"li_post_reactions_{post_id}_p{page}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar reações do post na Harvest API: {str(e)}"}

@mcp.tool()
async def linkedin_buscar_posts(termo_busca: str, profile_url: str = None, company_url: str = None, posted_limit: str = None, page: int = 1) -> dict:
    """
    Busca publicações no LinkedIn com base em palavras-chave e filtros adicionais de autor ou data.
    
    Args:
        termo_busca: Palavras-chave ou tags pesquisadas nos posts.
        profile_url: Opcional. URL do perfil do autor para filtrar os resultados.
        company_url: Opcional. URL da empresa do autor para filtrar os resultados.
        posted_limit: Opcional. Limite de tempo do post no LinkedIn ('24h', 'week', 'month').
        page: Opcional. Número da página para paginação. Padrão é 1.
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    params = {
        "search": termo_busca,
        "page": page
    }
    if profile_url:
        params["profile"] = profile_url
    if company_url:
        params["company"] = company_url
    if posted_limit:
        params["postedLimit"] = posted_limit
        
    endpoint = "https://api.harvest-api.com/linkedin/post-search"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=40.0)
            response.raise_for_status()
            termo_limpo = termo_busca.replace(" ", "_").replace("\"", "")
            return salvar_cache_universal(f"li_post_search_{termo_limpo}_p{page}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar posts na Harvest API: {str(e)}"}

@mcp.tool()
async def linkedin_ver_posts_usuario(profile_url: str, posted_limit: str = None, page: int = 1) -> dict:
    """
    Recupera todas as publicações publicadas por um usuário específico no LinkedIn a partir da URL do seu perfil.
    
    Args:
        profile_url: A URL completa do perfil do LinkedIn.
        posted_limit: Opcional. Limite de tempo ('24h', 'week', 'month').
        page: Opcional. Número da página para paginação. Padrão é 1.
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    params = {
        "profile": profile_url,
        "page": page
    }
    if posted_limit:
        params["postedLimit"] = posted_limit
        
    endpoint = "https://api.harvest-api.com/linkedin/profile-posts"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=40.0)
            response.raise_for_status()
            import urllib.parse
            parsed = urllib.parse.urlparse(profile_url)
            perfil_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "alvo"
            return salvar_cache_universal(f"li_user_posts_{perfil_id}_p{page}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar posts do perfil na Harvest API: {str(e)}"}

@mcp.tool()
async def linkedin_buscar_email_perfil(profile_url: str, skip_smtp: bool = False) -> dict:
    """
    Tenta localizar e validar os endereços de e-mail atrelados a um perfil do LinkedIn
    usando geração e validação de e-mails em tempo real da Harvest API.
    
    Args:
        profile_url: A URL completa do perfil do LinkedIn.
        skip_smtp: Opcional. Se True, pula a validação SMTP ativa (busca mais rápida, porém menos precisa). Padrão é False.
    """
    if not HARVEST_TOKEN:
        return {"error": "HARVEST_API_TOKEN não configurado no .env"}
        
    headers = {
        "X-API-Key": HARVEST_TOKEN,
        "Accept": "application/json"
    }
    
    params = {
        "url": profile_url,
        "findEmail": "true"
    }
    if skip_smtp:
        params["skipSmtp"] = "true"
        
    endpoint = "https://api.harvest-api.com/linkedin/profile"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(endpoint, headers=headers, params=params, timeout=40.0)
            response.raise_for_status()
            import urllib.parse
            parsed = urllib.parse.urlparse(profile_url)
            perfil_id = parsed.path.strip("/").split("/")[-1] if "/" in parsed.path else "alvo"
            return salvar_cache_universal(f"li_email_{perfil_id}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar e-mail do perfil no LinkedIn: {str(e)}"}

# ==============================================================================
# 5. INTEGRAÇÃO UNITFOUR (LOCALIZAÇÃO E CADASTROS)
# ==============================================================================
UNITFOUR_BASE_URL = "https://webapi.unitfour.com.br"
UNITFOUR_TOKEN = os.getenv("UNITFOUR_TOKEN")

@mcp.tool()
async def unitfour_consultar_cpf(cpf: str | int) -> dict:
    """
    Busca os dados cadastrais completos de uma Pessoa Física (CPF) utilizando a Unitfour.
    Retorna dados cadastrais principais, endereços, telefones e e-mails estruturados.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cpf_str = str(cpf)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisica/{cpf_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_cpf_{cpf_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar CPF na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_pessoas_ligadas(cpf: str | int) -> dict:
    """
    Localiza parentes, possíveis pessoas ligadas e grau de parentesco a partir de um CPF.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cpf_str = str(cpf)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaPessoasLigadas/{cpf_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_ligados_{cpf_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar pessoas ligadas na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_mandados_prisao(cpf: str | int) -> dict:
    """
    Consulta mandados de prisão vigentes ("Aguardando Cumprimento") no Banco Nacional 
    de Mandados de Prisão (CNJ) a partir do CPF informado.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cpf_str = str(cpf)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Compliance/v1/MandadosPrisao/{cpf_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_mandados_{cpf_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar mandados de prisão na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_antecedentes_criminais(cpf: str | int, nome: str = None) -> dict:
    """
    Consulta a existência de registros criminais e emite a Certidão de Antecedentes Criminais 
    da Polícia Federal a partir do CPF (e opcionalmente do nome).
    
    Args:
        cpf: O CPF da pessoa (apenas números).
        nome: Opcional. O nome completo para refinar a busca na Polícia Federal.
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cpf_str = str(cpf)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    params = {}
    if nome:
        params["nome"] = nome
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Compliance/v1/AntecedentesCriminais/{cpf_str}",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_antecedentes_{cpf_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar antecedentes criminais na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_consulta_pep(cpf: str | int) -> dict:
    """
    Busca informações referentes a PEP (Pessoa Exposta Politicamente) Coaf a partir de um CPF.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cpf_str = str(cpf)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pep/v1/ConsultaPEPCoaf/{cpf_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_pep_{cpf_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar PEP na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_consultar_cnpj(cnpj: str | int) -> dict:
    """
    Busca os dados cadastrais completos de uma Empresa (CNPJ) utilizando a Unitfour.
    Retorna dados cadastrais de registro, endereço, contatos, atividades econômicas, etc.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cnpj_str = str(cnpj)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaJuridica/{cnpj_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_cnpj_{cnpj_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar CNPJ na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_tomadores_decisao(cnpj: str | int) -> dict:
    """
    Localiza sócios, diretores e tomadores de decisão (QSA) associados a um CNPJ.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cnpj_str = str(cnpj)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaTomadoresDecisao/{cnpj_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_tomadores_{cnpj_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar tomadores de decisão na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_empresas_ligadas(cnpj: str | int) -> dict:
    """
    Localiza empresas ligadas (participações societárias ou relações comerciais) a um determinado CNPJ.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cnpj_str = str(cnpj)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v1/LocalizaEmpresasLigadas/{cnpj_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_empresas_ligadas_{cnpj_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao buscar empresas ligadas na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_proprietario_veiculo_placa(placa: str) -> dict:
    """
    Busca dados detalhados do veículo (Renavam, chassi, modelo) e dados de identificação 
    do proprietário atual a partir da placa do veículo.
    
    Args:
        placa: A placa do veículo (sem hífen, ex: ABC1D23 ou ABC1234).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    placa_str = str(placa).upper().strip()
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Veiculo/v1/ProprietarioVeiculo/Placa/{placa_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_veiculo_{placa_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao consultar placa na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_busca_avancada_nome(nome: str, bairro: str = None, cidade: str = None, uf: str = None) -> dict:
    """
    Localiza CPFs e pessoas físicas a partir do nome (busca reversa).
    O caractere '*' pode ser usado para realizar correspondências parciais.
    
    Args:
        nome: O nome completo ou parcial pesquisado (ex: 'João da Silva' ou 'João*').
        bairro: Opcional. Bairro para filtrar a busca.
        cidade: Opcional. Cidade para filtrar a busca.
        uf: Opcional. Estado (UF) com duas letras para filtrar a busca.
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    nome_str = str(nome)
    import urllib.parse
    nome_quoted = urllib.parse.quote(nome_str)
    
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    params = {}
    if bairro:
        params["bairro"] = bairro
    if cidade:
        params["cidade"] = cidade
    if uf:
        params["uf"] = uf
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaNome/{nome_quoted}",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            # Salva no cache com nome amigável
            nome_limpo = "".join(c for c in nome_str if c.isalnum() or c == " ").strip().replace(" ", "_")
            return salvar_cache_universal(f"unitfour_busca_nome_{nome_limpo}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao realizar busca avançada por nome na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_busca_avancada_telefone(ddd: str | int, telefone: str | int) -> dict:
    """
    Localiza pessoas físicas associadas a um número de telefone específico (busca reversa por telefone).
    
    Args:
        ddd: O DDD do telefone (apenas 2 dígitos, ex: '11').
        telefone: O número do telefone (apenas números, ex: '988887777').
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    ddd_str = str(ddd)
    tel_str = str(telefone)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaTelefone/{ddd_str}/{tel_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_busca_tel_{ddd_str}{tel_str}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao realizar busca avançada por telefone na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_busca_avancada_email(email: str | int) -> dict:
    """
    Localiza pessoas físicas associadas a um endereço de e-mail (busca reversa por e-mail).
    
    Args:
        email: O endereço de e-mail completo pesquisado.
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    email_str = str(email)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    params = {"email": email_str}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaEmail",
                headers=headers,
                params=params,
                timeout=25.0
            )
            response.raise_for_status()
            email_limpo = email_str.replace("@", "_at_").replace(".", "_")
            return salvar_cache_universal(f"unitfour_busca_email_{email_limpo}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao realizar busca avançada por e-mail na Unitfour: {str(e)}"}

@mcp.tool()
async def unitfour_busca_avancada_cep(cep: str | int) -> dict:
    """
    Localiza pessoas físicas registradas em um determinado CEP (busca reversa por CEP).
    
    Args:
        cep: O CEP desejado (apenas números).
    """
    if not UNITFOUR_TOKEN:
        return {"error": "UNITFOUR_TOKEN não configurado no .env"}
        
    cep_str = str(cep)
    headers = {
        "Authorization": f"Token {UNITFOUR_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNITFOUR_BASE_URL}/api/Pessoa/v2/LocalizaPessoaFisicaAvancadaCep/{cep_str}",
                headers=headers,
                timeout=25.0
            )
            response.raise_for_status()
            return salvar_cache_universal(f"unitfour_busca_cep_{cep}", response.json())
        except httpx.HTTPError as e:
            return {"error": f"Erro ao realizar busca avançada por CEP na Unitfour: {str(e)}"}
# ==============================================================================
# 5. INTEGRAÇÃO LIGHTHOUSE (LAMPYRE) - FACEBOOK OSINT
# ==============================================================================
LIGHTHOUSE_BASE_URL = "https://api.lighthouse.lampyre.io/api/1.0"
LIGHTHOUSE_API_TOKEN = os.getenv("LIGHTHOUSE_API_TOKEN")

# Semáforo para controlar concorrência (limite de 3 chamadas simultâneas à API Lighthouse)
lighthouse_semaphore = asyncio.Semaphore(3)

async def async_executar_tarefa_lighthouse(job_name: str, task_info: dict, chave_cache: str) -> dict:
    """
    Executa de forma robusta e assíncrona uma tarefa na API Lighthouse.
    
    1. Verifica cache universal.
    2. Cria a tarefa via POST.
    3. Monitora/polla o status até a finalização (status 0 = sucesso, 1 = erro).
    4. Salva o resultado no cache universal local.
    """
    if not LIGHTHOUSE_API_TOKEN:
        return {"error": "LIGHTHOUSE_API_TOKEN não configurada no .env"}

    # Interceptação de cache
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    # Coerção ativa de inteiros para strings nos inputs do dicionário para evitar erros da API
    task_info_limpo = {}
    for k, v in task_info.items():
        if isinstance(v, int):
            task_info_limpo[k] = str(v)
        elif isinstance(v, dict):
            task_info_limpo[k] = {sub_k: (str(sub_v) if isinstance(sub_v, int) else sub_v) for sub_k, sub_v in v.items()}
        else:
            task_info_limpo[k] = v

    print(f"[LIGHTHOUSE] Iniciando tarefa '{job_name}' com parâmetros: {task_info_limpo}", file=sys.stderr, flush=True)

    url_post = f"{LIGHTHOUSE_BASE_URL}/tasks/{job_name}"
    payload = {
        "token": LIGHTHOUSE_API_TOKEN,
        "task_info": task_info_limpo
    }

    async with lighthouse_semaphore:
        try:
            # 1. Criar a tarefa
            response = await http_client.post(url_post, json=payload, timeout=20.0)
            if response.status_code != 201:
                return {
                    "error": f"Falha ao criar tarefa no Lighthouse (Código HTTP {response.status_code})",
                    "detalhes": response.text
                }
            
            task_data = response.json()
            task_id = task_data.get("task_id")
            if not task_id:
                return {"error": "A API do Lighthouse não retornou um task_id válido.", "detalhes": task_data}

            print(f"[LIGHTHOUSE] Tarefa criada com sucesso. ID: {task_id}. Iniciando polling...", file=sys.stderr, flush=True)

            # 2. Polling assíncrono de status (máximo 40 tentativas, esperando 3s entre elas = total 120s)
            url_get = f"{LIGHTHOUSE_BASE_URL}/tasks/{job_name}/{task_id}?token={LIGHTHOUSE_API_TOKEN}"
            
            for tentativa in range(40):
                await asyncio.sleep(3.0)
                status_resp = await http_client.get(url_get, timeout=15.0)
                if status_resp.status_code != 200:
                    continue # Tolera pequenas oscilações de rede
                
                status_data = status_resp.json()
                status = status_data.get("task_status")
                
                # status == 0: Sucesso
                if status == 0:
                    print(f"[LIGHTHOUSE] Tarefa {task_id} concluída com sucesso na tentativa {tentativa + 1}.", file=sys.stderr, flush=True)
                    # Salva e retorna o resultado da busca
                    return salvar_cache_universal(chave_cache, status_data.get("result", {}))
                
                # status == 1: Erro
                elif status == 1:
                    print(f"[LIGHTHOUSE] Tarefa {task_id} falhou na plataforma Lighthouse.", file=sys.stderr, flush=True)
                    return {
                        "error": "A tarefa falhou na execução remota do Lighthouse.",
                        "detalhes": status_data
                    }
                
                # status == 2 ou 3: Processando/Pendente
                # Continua o loop de polling
 
            # Se sair do loop por timeout
            print(f"[LIGHTHOUSE] Timeout: Tarefa {task_id} demorou mais que 120 segundos para concluir.", file=sys.stderr, flush=True)
            return {
                "error": "A busca no Lighthouse excedeu o limite de tempo (120 segundos).",
                "task_id": task_id,
                "mensagem": "A tarefa pode ainda estar rodando no Lighthouse. Você pode tentar pesquisar novamente mais tarde para recuperar do cache se ela tiver terminado."
            }

        except httpx.HTTPError as e:
            print(f"[LIGHTHOUSE ERROR] Falha de comunicação de rede: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro de comunicação de rede com Lighthouse: {str(e)}"}
        except Exception as e:
            print(f"[LIGHTHOUSE ERROR] Erro inesperado: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro inesperado na execução: {str(e)}"}
 
 
@mcp.tool()
async def lighthouse_fb_uid_info(facebook_profile_uid: str | int) -> dict:
    """
    Busca informações detalhadas de perfil cadastral do Facebook a partir do UID do perfil.
    Retorna o nome, foto de perfil, links, gênero e outros detalhes públicos estruturados.
    
    Custo: 10.6 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4' para Mark Zuckerberg).
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_info_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_user_info_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_wall(facebook_profile_uid: str | int, options: dict = None) -> dict:
    """
    Recupera as postagens e publicações do mural (timeline) de um usuário do Facebook pelo UID.
    
    Custo: 16.0 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
        options: Dicionário opcional com configurações extras de busca.
    """
    if options is None:
        options = {}
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_wall_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_wall_get_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str, "options": options},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_reposts(facebook_profile_uid: str | int) -> dict:
    """
    Recupera os compartilhamentos (reposts) feitos a partir do mural (timeline) de um usuário do Facebook pelo UID.
    
    Custo: 10.6 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_reposts_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_reposts_from_user_wall_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_likes(facebook_profile_uid: str | int) -> dict:
    """
    Recupera as curtidas (likes) deixadas nas postagens do mural de um usuário do Facebook pelo UID.
    
    Custo: 10.6 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_likes_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_likes_from_user_wall_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_comments(facebook_profile_uid: str | int) -> dict:
    """
    Recupera os comentários deixados nas postagens do mural de um usuário do Facebook pelo UID.
    
    Custo: 10.6 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_comments_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_comments_from_user_wall_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_friends(facebook_profile_uid: str | int) -> dict:
    """
    Recupera a lista clássica de amizades de um usuário do Facebook a partir de seu UID.
    
    Custo: 15.9 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_friends_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_friends_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_full_friends(facebook_profile_uid: str | int) -> dict:
    """
    Recupera a lista de amigos com detalhes cadastrais enriquecidos e completos a partir do UID do Facebook.
    
    Custo: 15.9 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_full_friends_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_full_friends_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_phone_restore(phone: str | int) -> dict:
    """
    Realiza busca reversa (account mapping) para identificar perfis e contas do Facebook vinculados a um telefone.
    Retorna o nome, UID, partes de e-mail e outras confirmações vinculadas.
    
    Custo: 3.0 Photons.
    
    Args:
        phone: O número de telefone móvel no formato internacional E.164 (ex: '+5511988887777').
    """
    phone_str = str(phone)
    phone_limpo = phone_str.replace("+", "").replace("-", "").replace(" ", "")
    chave_cache = f"lighthouse_fb_phone_restore_{phone_limpo}"
    return await async_executar_tarefa_lighthouse(
        job_name="phone_fb_restore_v1",
        task_info={"phone": phone_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_email_restore(email: str | int) -> dict:
    """
    Realiza busca reversa (account mapping) para identificar perfis e contas do Facebook vinculados a um e-mail.
    Retorna o nome, UID, partes de telefone e outras confirmações vinculadas.
    
    Custo: 0.48 Photons.
    
    Args:
        email: O endereço de e-mail pesquisado (ex: 'alice@gmail.com').
    """
    email_str = str(email)
    email_limpo = email_str.replace("@", "_at_").replace(".", "_").replace("+", "")
    chave_cache = f"lighthouse_fb_email_restore_{email_limpo}"
    return await async_executar_tarefa_lighthouse(
        job_name="email_fb_restore_v1",
        task_info={"email": email_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_username_restore(username: str | int) -> dict:
    """
    Busca e resolve uma conta do Facebook pelo seu nome de usuário (username / nickname / login handle).
    Útil para correlacionar IDs a partir de apelidos em outras redes sociais.
    
    Custo: 1.5 Photons.
    
    Args:
        username: O nome de usuário do Facebook (ex: 'zuck').
    """
    username_str = str(username)
    username_limpo = username_str.lower().strip()
    chave_cache = f"lighthouse_fb_username_restore_{username_limpo}"
    return await async_executar_tarefa_lighthouse(
        job_name="username_fb_restore_v1",
        task_info={"username": username_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_phone_darknet(phone: str | int) -> dict:
    """
    Realiza consulta avançada em bases vazadas da Darknet por número de telefone.
    Retorna credenciais vazadas, logins e informações expostas correlacionadas com contas Facebook.
    
    Custo: 3.0 Photons.
    
    Args:
        phone: O número de telefone móvel no formato internacional E.164 (ex: '+5511988887777').
    """
    phone_str = str(phone)
    phone_limpo = phone_str.replace("+", "").replace("-", "").replace(" ", "")
    chave_cache = f"lighthouse_fb_phone_darknet_{phone_limpo}"
    return await async_executar_tarefa_lighthouse(
        job_name="phone_fb_darknet_v1",
        task_info={"phone": phone_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_email_darknet(email: str | int) -> dict:
    """
    Realiza consulta avançada em bases vazadas da Darknet por endereço de e-mail.
    Retorna credenciais vazadas, senhas/hashes e informações correlacionadas expostas do Facebook.
    
    Custo: 3.0 Photons.
    
    Args:
        email: O endereço de e-mail pesquisado.
    """
    email_str = str(email)
    email_limpo = email_str.replace("@", "_at_").replace(".", "_").replace("+", "")
    chave_cache = f"lighthouse_fb_email_darknet_{email_limpo}"
    return await async_executar_tarefa_lighthouse(
        job_name="email_fb_darknet_v1",
        task_info={"email": email_str},
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_fb_uid_darknet(facebook_profile_uid: str | int) -> dict:
    """
    Realiza consulta avançada em bases vazadas da Darknet a partir de um UID de perfil do Facebook.
    Retorna vazamentos específicos associados à conta identificada.
    
    Custo: 3.0 Photons.
    
    Args:
        facebook_profile_uid: O UID do perfil do Facebook (ex: '4').
    """
    facebook_profile_uid_str = str(facebook_profile_uid)
    chave_cache = f"lighthouse_fb_uid_darknet_{facebook_profile_uid_str}"
    return await async_executar_tarefa_lighthouse(
        job_name="uid_fb_darknet_v1",
        task_info={"facebook_profile_uid": facebook_profile_uid_str},
        chave_cache=chave_cache
    )

@mcp.tool()
async def lighthouse_image_facecheck(photo_url: str = None, photo_b64: str = None, photo_fileid: str = None) -> dict:
    """
    Realiza busca e reconhecimento facial em bases OSINT através da plataforma FaceCheck.ID.
    Você deve fornecer pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'.
    
    Custo: 3.55 Photons.
    
    Args:
        photo_url: Opcional. A URL pública direta da imagem a ser pesquisada.
        photo_b64: Opcional. A imagem codificada em base64 (sem metadados data:image/...).
        photo_fileid: Opcional. O fileId de uma imagem carregada previamente no Lighthouse.
    """
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
        
    task_info = {}
    if photo_url:
        task_info["photo_url"] = photo_url
    if photo_b64:
        task_info["photo_b64"] = photo_b64
    if photo_fileid:
        task_info["photo_fileid"] = photo_fileid
        
    import hashlib
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    chave_cache = f"lighthouse_image_facecheck_{hash_id}"
    
    return await async_executar_tarefa_lighthouse(
        job_name="image_facecheck_v1",
        task_info=task_info,
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_image_geolocation(photo_url: str = None, photo_b64: str = None, photo_fileid: str = None) -> dict:
    """
    Realiza geolocalização OSINT baseada em imagens para tentar deduzir onde uma foto foi tirada 
    através de análise visual e metadados.
    Você deve fornecer pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'.
    
    Custo: 3.55 Photons.
    
    Args:
        photo_url: Opcional. A URL pública direta da imagem a ser pesquisada.
        photo_b64: Opcional. A imagem codificada em base64 (sem metadados data:image/...).
        photo_fileid: Opcional. O fileId de uma imagem carregada previamente no Lighthouse.
    """
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
        
    task_info = {}
    if photo_url:
        task_info["photo_url"] = photo_url
    if photo_b64:
        task_info["photo_b64"] = photo_b64
    if photo_fileid:
        task_info["photo_fileid"] = photo_fileid
        
    import hashlib
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    chave_cache = f"lighthouse_image_geolocation_{hash_id}"
    
    return await async_executar_tarefa_lighthouse(
        job_name="image_geolocation_v1",
        task_info=task_info,
        chave_cache=chave_cache
    )


@mcp.tool()
async def lighthouse_image_search4faces(photo_url: str = None, photo_b64: str = None, photo_fileid: str = None) -> dict:
    """
    Realiza reconhecimento facial e busca reversa em perfis de redes sociais (como VKontakte, Odnoklassniki e outras)
    utilizando a inteligência da plataforma Search4Faces.
    Você deve fornecer pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'.
    
    Custo: 3.55 Photons.
    
    Args:
        photo_url: Opcional. A URL pública direta da imagem a ser pesquisada.
        photo_b64: Opcional. A imagem codificada em base64 (sem metadados data:image/...).
        photo_fileid: Opcional. O fileId de uma imagem carregada previamente no Lighthouse.
    """
    if not photo_url and not photo_b64 and not photo_fileid:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'photo_url', 'photo_b64' ou 'photo_fileid'."}
        
    task_info = {}
    if photo_url:
        task_info["photo_url"] = photo_url
    if photo_b64:
        task_info["photo_b64"] = photo_b64
    if photo_fileid:
        task_info["photo_fileid"] = photo_fileid
        
    import hashlib
    param_str = photo_url or photo_b64 or photo_fileid
    hash_id = hashlib.md5(param_str.encode("utf-8")).hexdigest()
    chave_cache = f"lighthouse_image_search4faces_{hash_id}"
    
    return await async_executar_tarefa_lighthouse(
        job_name="image_search4faces_v1",
        task_info=task_info,
        chave_cache=chave_cache
    )


# ==============================================================================
# 6. INTEGRAÇÃO SOCIAVAULT (TIKTOK OSINT)
# ==============================================================================
SOCIAVAULT_BASE_URL = "https://api.sociavault.com"
SOCIAVAULT_API_KEY = os.getenv("SOCIAVAULT_API_KEY")

sociavault_semaphore = asyncio.Semaphore(5)

@mcp.tool()
async def tiktok_buscar_perfil(handle: str) -> dict:
    """
    Busca informações detalhadas de um perfil público do TikTok pelo handle (username, ex: 'stoolpresidente').
    Consome 1 crédito da API SociaVault.
    
    Args:
        handle: O nome de usuário do TikTok (sem o caractere '@').
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    chave_cache = f"tiktok_profile_{handle_limpo}"
    
    # Interceptação de cache local
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Buscando perfil do TikTok para '{handle_limpo}'...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/profile",
                headers=headers,
                params={"handle": handle_limpo},
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            print(f"[SOCIAVAULT ERROR] Erro HTTP {e.response.status_code} para perfil {handle_limpo}: {detalhes}", file=sys.stderr, flush=True)
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            print(f"[SOCIAVAULT ERROR] Erro de rede para perfil {handle_limpo}: {str(e)}", file=sys.stderr, flush=True)
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_listar_videos(handle: str, user_id: str | int = None, sort_by: str = "latest", max_cursor: str = None, trim: bool = False) -> dict:
    """
    Recupera a lista de vídeos postados por um perfil do TikTok.
    Consome 1 crédito da API SociaVault por requisição de página.
    
    Args:
        handle: O nome de usuário do TikTok (sem o caractere '@').
        user_id: Opcional. ID numérico do usuário do TikTok. Passar o user_id acelera o tempo de resposta da API.
        sort_by: Opcional. Ordenação dos vídeos. Valores possíveis: 'latest' (mais recentes) ou 'popular' (mais curtidos). Padrão é 'latest'.
        max_cursor: Opcional. Cursor para obter a próxima página de vídeos (obtido do campo 'max_cursor' do retorno anterior).
        trim: Opcional. Se 'True', retorna uma versão resumida/limpa dos dados do vídeo. Padrão é 'False'.
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    cursor_str = max_cursor or "initial"
    trim_str = "trimmed" if trim else "full"
    chave_cache = f"tiktok_videos_{handle_limpo}_{sort_by}_{cursor_str}_{trim_str}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Listando vídeos do TikTok para '{handle_limpo}'...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "handle": handle_limpo,
        "sort_by": sort_by,
        "trim": str(trim).lower()
    }
    if user_id:
        params["user_id"] = str(user_id)
    if max_cursor:
        params["max_cursor"] = str(max_cursor)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/videos",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_listar_comentarios(url: str, cursor: int = None, trim: bool = False) -> dict:
    """
    Recupera a lista de comentários de um vídeo do TikTok.
    Consome 1 crédito da API SociaVault por requisição de página.
    
    Args:
        url: A URL completa do vídeo do TikTok (ex: 'https://www.tiktok.com/@stoolpresidente/video/7604286086189288718').
        cursor: Opcional. Cursor numérico para paginação (ex: 20) obtido no retorno da consulta anterior.
        trim: Opcional. Se 'True', retorna uma versão reduzida dos dados do comentário. Padrão é 'False'.
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    import hashlib
    url_limpa = url.split("?")[0].strip()
    url_hash = hashlib.md5(url_limpa.encode("utf-8")).hexdigest()
    trim_str = "trimmed" if trim else "full"
    chave_cache = f"tiktok_comments_{url_hash}_{cursor or 0}_{trim_str}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Buscando comentários para o vídeo TikTok...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "url": url_limpa,
        "trim": str(trim).lower()
    }
    if cursor is not None:
        params["cursor"] = str(cursor)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/comments",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_listar_respostas_comentario(comment_id: str, url: str, cursor: int = None) -> dict:
    """
    Recupera as respostas de um comentário específico em um vídeo do TikTok.
    Consome 1 crédito da API SociaVault por requisição de página.
    
    Args:
        comment_id: O ID exclusivo do comentário (campo 'cid' retornado na consulta de comentários).
        url: A URL completa do vídeo do TikTok associado a esse comentário.
        cursor: Opcional. Cursor numérico para paginação (obtido da resposta anterior).
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    comment_id_str = str(comment_id).strip()
    chave_cache = f"tiktok_comment_replies_{comment_id_str}_{cursor or 0}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Buscando respostas para o comentário '{comment_id_str}'...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "comment_id": comment_id_str,
        "url": url.split("?")[0].strip()
    }
    if cursor is not None:
        params["cursor"] = str(cursor)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/comment-replies",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_listar_seguindo(handle: str, min_time: int = None, trim: bool = False) -> dict:
    """
    Lista as contas que um perfil do TikTok segue.
    Consome 1 crédito da API SociaVault por requisição de página.
    
    Args:
        handle: O nome de usuário do TikTok (sem o caractere '@').
        min_time: Opcional. Unix timestamp usado para paginação (obtido de 'min_time' no retorno anterior).
        trim: Opcional. Se 'True', retorna dados resumidos de cada conta. Padrão é 'False'.
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    handle_limpo = handle.strip().replace("@", "")
    chave_cache = f"tiktok_following_{handle_limpo}_{min_time or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Buscando lista de quem '{handle_limpo}' segue...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "handle": handle_limpo,
        "trim": str(trim).lower()
    }
    if min_time is not None:
        params["min_time"] = str(min_time)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/following",
                headers=headers,
                params=params,
                timeout=35.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_listar_seguidores(handle: str = None, user_id: str | int = None, min_time: int = None, trim: bool = False) -> dict:
    """
    Lista os seguidores de um perfil do TikTok.
    Consome 1 crédito da API SociaVault por requisição de página.
    Recomenda-se fornecer handle OU user_id (user_id acelera o tempo de resposta).
    
    Args:
        handle: Opcional. O nome de usuário do TikTok (sem o caractere '@').
        user_id: Opcional. O ID numérico do usuário do TikTok.
        min_time: Opcional. Unix timestamp usado para paginação (obtido de 'min_time' no retorno anterior).
        trim: Opcional. Se 'True', retorna dados resumidos. Padrão é 'False'.
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    if not handle and not user_id:
        return {"error": "Você deve informar pelo menos um dos parâmetros: 'handle' ou 'user_id'."}
        
    identificador = (handle.strip().replace("@", "")) if handle else str(user_id)
    chave_cache = f"tiktok_followers_{identificador}_{min_time or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Buscando lista de seguidores para '{identificador}'...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "trim": str(trim).lower()
    }
    if handle:
        params["handle"] = handle.strip().replace("@", "")
    if user_id:
        params["user_id"] = str(user_id)
    if min_time is not None:
        params["min_time"] = str(min_time)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/followers",
                headers=headers,
                params=params,
                timeout=35.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


@mcp.tool()
async def tiktok_buscar_usuarios(query: str, cursor: int = None, trim: bool = False) -> dict:
    """
    Pesquisa e lista usuários do TikTok que correspondam a uma consulta de pesquisa (termo de busca).
    Consome 1 crédito da API SociaVault por requisição de página.
    
    Args:
        query: O termo ou nome que deseja pesquisar (ex: 'taylorswift').
        cursor: Opcional. Cursor numérico para paginação (obtido de 'cursor' no retorno anterior).
        trim: Opcional. Se 'True', retorna dados resumidos. Padrão é 'False'.
    """
    if not SOCIAVAULT_API_KEY:
        return {"error": "SOCIAVAULT_API_KEY não configurada no .env"}
        
    query_limpa = query.strip()
    query_cache = query_limpa.replace(" ", "_")
    chave_cache = f"tiktok_search_{query_cache}_{cursor or 0}_{'trimmed' if trim else 'full'}"
    
    cache_hit = checar_cache_universal(chave_cache)
    if cache_hit:
        return cache_hit

    print(f"[SOCIAVAULT] Pesquisando usuários no TikTok para '{query_limpa}'...", file=sys.stderr, flush=True)
    
    headers = {
        "X-API-Key": SOCIAVAULT_API_KEY,
        "Accept": "application/json"
    }
    
    params = {
        "query": query_limpa,
        "trim": str(trim).lower()
    }
    if cursor is not None:
        params["cursor"] = str(cursor)
        
    async with sociavault_semaphore:
        try:
            response = await http_client.get(
                f"{SOCIAVAULT_BASE_URL}/v1/scrape/tiktok/search/users",
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return salvar_cache_universal(chave_cache, response.json())
        except httpx.HTTPStatusError as e:
            try:
                detalhes = e.response.json()
            except Exception:
                detalhes = e.response.text
            return {"error": f"Erro HTTP {e.response.status_code} na API SociaVault", "detalhes": detalhes}
        except httpx.HTTPError as e:
            return {"error": f"Erro de rede na API SociaVault: {str(e)}"}


# ==============================================================================
# CONSOLIDAÇÃO DE DOSSIÊ (produtização) — camada aditiva sobre o cache
# ==============================================================================
@mcp.tool()
async def investigador_gerar_dossie(cpf: str | int, salvar_laudo: bool = True) -> dict:
    """
    Consolida TODAS as consultas já feitas sobre um CPF (presentes no cache local)
    em um DOSSIÊ ÚNICO e estruturado: identificação, telefones/e-mails deduplicados
    e CORROBORADOS entre fontes, endereços, vínculos, participações empresariais e
    sinais de risco (PEP, mandado de prisão, antecedentes). Não gasta créditos de API
    — apenas cruza o que já foi coletado.

    Fluxo recomendado: rode primeiro as consultas de coleta (bigdata_consultar_cpf,
    unitfour_consultar_cpf, unitfour_pessoas_ligadas, unitfour_consulta_pep, etc.) e
    depois chame esta ferramenta para gerar o laudo consolidado.

    Args:
        cpf: O CPF do alvo (com ou sem máscara).
        salvar_laudo: Se True (padrão), grava o dossiê em JSON e um laudo em Markdown no cache.
    """
    try:
        import importlib
        import dossie as _dossie
        importlib.reload(_dossie)  # garante versão mais recente em dev
    except Exception as e:
        return {"error": f"Módulo 'dossie' indisponível: {str(e)}"}

    d_obj = _dossie.consolidar_cpf(cpf, cache_dir=CACHE_DIR)
    d = d_obj.to_dict()

    if not d["fontes_consultadas"]:
        return {
            "status": "vazio",
            "cpf": d["cpf"],
            "mensagem": ("Nenhuma consulta encontrada no cache para este CPF. "
                         "Rode primeiro bigdata_consultar_cpf e/ou unitfour_consultar_cpf."),
        }

    laudo_md = _dossie.dossie_para_markdown(d)

    if salvar_laudo:
        try:
            base = os.path.join(CACHE_DIR, f"dossie_{d['cpf']}")
            with open(f"{base}.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            with open(f"{base}.md", "w", encoding="utf-8") as f:
                f.write(laudo_md)
        except Exception as e:
            print(f"[DOSSIE] Falha ao salvar laudo: {e}", file=sys.stderr, flush=True)

    # Retorno enxuto para o LLM: sumário + laudo (compacto), sem despejar detalhes brutos.
    return {
        "status": "sucesso",
        "cpf": d["cpf"],
        "confianca_geral": d["confianca_geral"],
        "fontes_consultadas": d["fontes_consultadas"],
        "identificacao": d["identificacao"],
        "contagens": {
            "telefones": len(d["telefones"]),
            "emails": len(d["emails"]),
            "enderecos": len(d["enderecos"]),
            "vinculos": len(d["vinculos"]),
            "empresas": len(d["empresas"]),
            "riscos": len(d["riscos"]),
        },
        "riscos": d["riscos"],
        "laudo_markdown": laudo_md,
        "cache_id": f"dossie_{d['cpf']}",
        "instrucao": ("Dossiê consolidado. Use 'investigador_ler_cache' com o cache_id "
                      f"'dossie_{d['cpf']}' para explorar telefones/e-mails/vínculos completos."),
    }


# ==============================================================================
# ENRIQUECIMENTO AUTOMÁTICO DO DOSSIÊ (CSINT por contato + timeline de CNPJ)
# ==============================================================================
import inspect as _inspect


async def _invocar_tool(tool_obj, **kwargs):
    """Chama uma tool independentemente de estar embrulhada pelo FastMCP."""
    fn = getattr(tool_obj, "fn", None) or getattr(tool_obj, "func", None) or tool_obj
    res = fn(**kwargs)
    if _inspect.isawaitable(res):
        res = await res
    return res


def _ler_cache_raw(chave: str):
    """Lê o JSON bruto de um arquivo de cache (para folding). Retorna None se ausente."""
    caminho = obter_caminho_cache_seguro(chave)
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


async def _bigdata_cnpj_evolucao(cnpj_limpo: str) -> dict:
    """
    Busca os datasets de EVOLUÇÃO e HISTÓRICO de um CNPJ na BigDataCorp, com cache
    dedicado (chave própria, sem colidir com a consulta básica). Retorna o payload bruto.
    """
    if not BIGDATA_TOKEN or BIGDATA_TOKEN == "seu_token_jwt_aqui":
        return {"error": "BIGDATA_ACCESS_TOKEN não configurado no .env"}

    chave_cache = f"bigdata_cnpj_evolucao_{cnpj_limpo}"
    cache = _ler_cache_raw(chave_cache)
    if cache is not None:
        print(f"[CACHE HIT] Evolução CNPJ {cnpj_limpo} recuperada do cache.", file=sys.stderr, flush=True)
        return cache

    headers = {"AccessToken": BIGDATA_TOKEN, "Content-Type": "application/json"}
    if BIGDATA_TOKEN_ID:
        headers["TokenId"] = BIGDATA_TOKEN_ID
    payload = {"q": f"doc{{'{cnpj_limpo}'}}", "Datasets": "company_evolution,history_basic_data"}

    try:
        response = await http_client.post(f"{BIGDATA_BASE_URL}/empresas", headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        dados = response.json()
        with open(os.path.join(CACHE_DIR, f"{chave_cache}.json"), "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return dados
    except httpx.HTTPStatusError as e:
        return {"error": f"Erro HTTP {e.response.status_code} no BigDataCorp (evolução)", "detalhes": e.response.text}
    except Exception as e:
        return {"error": f"Erro ao consultar evolução do CNPJ: {str(e)}"}


@mcp.tool()
async def bigdata_cnpj_alteracoes(cnpj: str | int) -> dict:
    """
    Consulta as ALTERAÇÕES HISTÓRICAS de um CNPJ na BigDataCorp (datasets de evolução e
    histórico cadastral) e retorna uma TIMELINE cronológica das mudanças: razão social,
    situação cadastral, capital social, natureza jurídica, endereço, nº de funcionários, etc.

    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    import importlib
    import dossie as _dossie
    importlib.reload(_dossie)

    cnpj_limpo = re.sub(r"\D", "", str(cnpj)).zfill(14)[-14:]
    dados = await _bigdata_cnpj_evolucao(cnpj_limpo)
    if isinstance(dados, dict) and dados.get("error"):
        return dados

    nome = ""
    try:
        r0 = (dados.get("Result") or [{}])[0]
        nome = (r0.get("BasicData") or {}).get("OfficialName") or ""
    except Exception:
        pass

    timeline = _dossie.construir_timeline_cnpj(dados)
    md = _dossie.timeline_para_markdown(cnpj_limpo, nome, timeline)

    try:
        with open(os.path.join(CACHE_DIR, f"timeline_cnpj_{cnpj_limpo}.md"), "w", encoding="utf-8") as f:
            f.write(md)
    except Exception:
        pass

    return {
        "status": "sucesso",
        "cnpj": cnpj_limpo,
        "nome": nome,
        "total_alteracoes": len(timeline),
        "timeline": timeline,
        "timeline_markdown": md,
    }


@mcp.tool()
async def investigador_enriquecer_dossie(
    cpf: str | int,
    max_emails: int = 10,
    max_telefones: int = 10,
    max_cnpjs: int = 10,
    apenas_corroborados: bool = False,
    incluir_vazamentos: bool = True,
) -> dict:
    """
    Enriquece o dossiê de um CPF executando automaticamente:
      • Para CADA e-mail: reputação SEON (csint_consultar_email) + busca de vazamentos (opcional).
      • Para CADA telefone: reputação SEON (csint_consultar_telefone), convertendo para E.164.
      • Para CADA CNPJ ligado: alterações históricas + TIMELINE de mudanças (BigDataCorp).
    Todas as chamadas são cache-first (re-execuções não gastam créditos). Consolida os
    achados de volta no dossiê e gera um laudo enriquecido.

    ATENÇÃO: a primeira execução consome créditos de API (1 por contato/CNPJ novo). Use os
    parâmetros max_* e apenas_corroborados para controlar custo.

    Args:
        cpf: CPF do alvo (com ou sem máscara).
        max_emails/max_telefones/max_cnpjs: tetos de itens a enriquecer (controle de custo).
        apenas_corroborados: se True, só enriquece contatos confirmados por 2+ fontes.
        incluir_vazamentos: se True, roda também a busca universal de vazamentos por e-mail.
    """
    import importlib
    import dossie as _dossie
    importlib.reload(_dossie)

    d_obj = _dossie.consolidar_cpf(cpf, cache_dir=CACHE_DIR)
    d = d_obj.to_dict()
    if not d["fontes_consultadas"]:
        return {"status": "vazio", "cpf": d["cpf"],
                "mensagem": "Nenhuma consulta base no cache. Rode bigdata_consultar_cpf/unitfour_consultar_cpf antes."}

    alvos = _dossie.alvos_para_enriquecer(
        d, apenas_corroborados=apenas_corroborados,
        max_emails=max_emails, max_telefones=max_telefones, max_cnpjs=max_cnpjs,
    )
    relatorio = {"emails": [], "telefones": [], "cnpjs": []}

    # ---- E-MAILS (SEON + vazamentos) ----
    for email in alvos["emails"]:
        try:
            await _invocar_tool(csint_consultar_email, email=email)
            leak = None
            if incluir_vazamentos:
                await _invocar_tool(csint_busca_universal, query=email, tipo="email")
                cid = "csint_busca_" + email.replace('@', '').replace('.', '').replace('+', '').replace('-', '').replace(' ', '')
                leak = _ler_cache_raw(cid)
            seon_cid = "csint_seon_email_" + email.replace("@", "_at_").replace(".", "_").replace("+", "").replace("-", "")
            seon = _ler_cache_raw(seon_cid)
            _dossie.fold_csint_no_dossie(d_obj, "email", email, seon_data=seon, leak_data=leak)
            relatorio["emails"].append({"email": email, "status": "ok"})
        except Exception as e:
            relatorio["emails"].append({"email": email, "status": "erro", "detalhe": str(e)})

    # ---- TELEFONES (SEON) ----
    for tel in alvos["telefones"]:
        try:
            await _invocar_tool(csint_consultar_telefone, telefone=tel)
            seon_cid = "csint_seon_phone_" + tel.replace('+', '').replace('-', '').replace(' ', '')
            seon = _ler_cache_raw(seon_cid)
            _dossie.fold_csint_no_dossie(d_obj, "telefone", tel, seon_data=seon)
            relatorio["telefones"].append({"telefone": tel, "status": "ok"})
        except Exception as e:
            relatorio["telefones"].append({"telefone": tel, "status": "erro", "detalhe": str(e)})

    # ---- CNPJs (timeline de alterações) ----
    timelines_md = []
    for cnpj in alvos["cnpjs"]:
        try:
            dados_ev = await _bigdata_cnpj_evolucao(cnpj)
            nome = ""
            try:
                r0 = (dados_ev.get("Result") or [{}])[0]
                nome = (r0.get("BasicData") or {}).get("OfficialName") or ""
            except Exception:
                pass
            tl = _dossie.construir_timeline_cnpj(dados_ev)
            md = _dossie.timeline_para_markdown(cnpj, nome, tl)
            timelines_md.append(md)
            relatorio["cnpjs"].append({"cnpj": cnpj, "nome": nome, "alteracoes": len(tl),
                                       "status": "ok" if not (isinstance(dados_ev, dict) and dados_ev.get("error")) else "erro"})
        except Exception as e:
            relatorio["cnpjs"].append({"cnpj": cnpj, "status": "erro", "detalhe": str(e)})

    # ---- Consolida laudo enriquecido ----
    d_final = d_obj.to_dict()
    laudo = _dossie.dossie_para_markdown(d_final)
    if timelines_md:
        laudo += "\n\n## 8. Alterações Históricas de Empresas Ligadas\n\n" + "\n\n".join(timelines_md)

    try:
        base = os.path.join(CACHE_DIR, f"dossie_{d_final['cpf']}_enriquecido")
        with open(f"{base}.json", "w", encoding="utf-8") as f:
            json.dump(d_final, f, ensure_ascii=False, indent=2)
        with open(f"{base}.md", "w", encoding="utf-8") as f:
            f.write(laudo)
    except Exception as e:
        print(f"[ENRIQUECER] Falha ao salvar laudo: {e}", file=sys.stderr, flush=True)

    return {
        "status": "sucesso",
        "cpf": d_final["cpf"],
        "confianca_geral": d_final["confianca_geral"],
        "enriquecimento": {
            "emails_processados": len(relatorio["emails"]),
            "telefones_processados": len(relatorio["telefones"]),
            "cnpjs_processados": len(relatorio["cnpjs"]),
        },
        "relatorio": relatorio,
        "riscos": d_final["riscos"],
        "laudo_markdown": laudo,
        "cache_id": f"dossie_{d_final['cpf']}_enriquecido",
    }


# ==============================================================================
# ==============================================================================
# FERRAMENTAS DE BUSCA E RASPAGEM (TAVILY E FIRECRAWL)
# ==============================================================================

@mcp.tool()
async def tavily_buscar_web(query: str, search_depth: str = "basic") -> str:
    """
    Realiza uma busca otimizada na internet usando a API do Tavily.
    Útil para coletar notícias, artigos e referências recentes sobre alvos de investigação.
    
    :param query: Termo ou pergunta a ser pesquisada.
    :param search_depth: Profundidade da busca: 'basic' (rápida) ou 'advanced' (detalhada).
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Erro: Chave TAVILY_API_KEY não configurada no .env"
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_answer": True,
        "max_results": 5
    }
    
    try:
        response = await http_client.post(url, json=payload, timeout=15.0)
        if response.status_code != 200:
            return f"Erro na busca Tavily (HTTP {response.status_code}): {response.text}"
            
        data = response.json()
        
        output = []
        if data.get("answer"):
            output.append(f"### Resposta Direta:\n{data['answer']}\n")
            
        output.append("### Fontes Encontradas:")
        for result in data.get("results", []):
            output.append(f"- **[{result['title']}]({result['url']})**")
            output.append(f"  *Score de Relevância: {result.get('score', 0)}*")
            output.append(f"  {result['content']}\n")
            
        return "\n".join(output)
    except Exception as e:
        return f"Falha na consulta ao Tavily: {e}"


@mcp.tool()
async def firecrawl_raspar_pagina(url_alvo: str) -> str:
    """
    Raspa uma página web completa e a converte em Markdown estruturado.
    Excelente para extrair o texto limpo de portais de notícias, blogs ou fóruns sem tags HTML/propaganda.
    """
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return "Erro: Chave FIRECRAWL_API_KEY não configurada no .env"
        
    url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url_alvo,
        "formats": ["markdown"]
    }
    
    try:
        response = await http_client.post(url, json=payload, headers=headers, timeout=30.0)
        if response.status_code != 200:
            return f"Erro ao raspar com Firecrawl (HTTP {response.status_code}): {response.text}"
            
        data = response.json()
        if not data.get("success"):
            return f"Falha na raspagem: {data.get('error', 'Erro desconhecido')}"
            
        markdown_content = data.get("data", {}).get("markdown", "")
        
        limite_caracteres = 40000
        if len(markdown_content) > limite_caracteres:
            return markdown_content[:limite_caracteres] + "\n\n...[Conteúdo truncado para evitar estouro de contexto]..."
            
        return markdown_content
    except Exception as e:
        return f"Falha na consulta ao Firecrawl: {e}"


@mcp.tool()
async def serper_buscar_web_dorks(alvo: str, categoria: str = "arquivos_expostos") -> dict:
    """
    Realiza pesquisas avançadas utilizando Google Dorks automatizados (via Serper.dev) 
    para descobrir vazamentos de dados, subdomínios, portais expostos ou documentos confidenciais do alvo.
    
    :param alvo: O domínio alvo (ex: 'empresa.com.br') ou nome corporativo.
    :param categoria: Categoria de busca: 'arquivos_expostos', 'credenciais_e_backups', 'infraestrutura_e_login' ou 'subdominios'.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}

    dork_templates = {
        "arquivos_expostos": [
            'site:{alvo} filetype:pdf OR filetype:xlsx OR filetype:csv',
            'site:{alvo} filetype:docx OR filetype:doc OR filetype:rtf OR filetype:txt'
        ],
        "credenciais_e_backups": [
            'site:{alvo} filetype:sql OR filetype:env OR filetype:conf',
            'site:{alvo} filetype:bkp OR filetype:bak OR filetype:zip OR filetype:tar.gz',
            'site:{alvo} inurl:wp-config.php OR inurl:settings.py OR inurl:db_connect'
        ],
        "infraestrutura_e_login": [
            'site:{alvo} inurl:login OR inurl:admin OR inurl:portal OR inurl:signin',
            'site:{alvo} "Index of /" OR "Index of /backup" OR "Index of /uploads"'
        ],
        "subdominios": [
            'site:*.{alvo} -site:www.{alvo}'
        ]
    }

    templates = dork_templates.get(categoria)
    if not templates:
        return {"error": f"Categoria '{categoria}' inválida. Escolha entre: {list(dork_templates.keys())}"}

    queries = [tpl.format(alvo=alvo) for tpl in templates]
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    async def fazer_busca(query):
        try:
            payload = {"q": query}
            response = await http_client.post(url, json=payload, headers=headers, timeout=15.0)
            if response.status_code != 200:
                return {"query": query, "status": "error", "message": f"HTTP {response.status_code}"}
            
            data = response.json()
            achados = []
            for item in data.get("organic", []):
                achados.append({
                    "titulo": item.get("title"),
                    "url": item.get("link"),
                    "resumo": item.get("snippet")
                })
            return {
                "query": query,
                "status": "success",
                "total_encontrado": len(achados),
                "resultados": achados
            }
        except Exception as e:
            return {"query": query, "status": "error", "message": str(e)}

    # Executa as buscas em paralelo
    import asyncio
    tarefas = [fazer_busca(q) for q in queries]
    resultados = await asyncio.gather(*tarefas)

    return {
        "alvo": alvo,
        "categoria": categoria,
        "varredura": resultados
    }


@mcp.tool()
async def serper_buscar_google(query: str) -> dict:
    """
    Realiza uma pesquisa direta no Google utilizando a API do Serper.dev.
    Suporta operadores de busca avançados (Dorks) tais como site:, filetype:, intitle:, inurl:, etc.
    
    :param query: Termo de busca ou expressão Google Dork completa.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}
        
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    
    try:
        response = await http_client.post(url, json=payload, headers=headers, timeout=15.0)
        if response.status_code != 200:
            return {"error": f"Erro na busca Google (HTTP {response.status_code}): {response.text}"}
            
        data = response.json()
        achados = []
        for item in data.get("organic", []):
            achados.append({
                "titulo": item.get("title"),
                "url": item.get("link"),
                "resumo": item.get("snippet")
            })
            
        return {
            "query": query,
            "total_encontrado": len(achados),
            "resultados": achados
        }
    except Exception as e:
        return {"error": f"Falha na consulta ao Google: {str(e)}"}


@mcp.tool()
async def wayback_consultar_disponibilidade(url_alvo: str, timestamp: str = None) -> dict:
    """
    Verifica se uma URL possui capturas salvas no histórico do Wayback Machine (Internet Archive).
    Retorna o link para a captura mais próxima do momento atual ou de um timestamp específico.
    
    :param url_alvo: A URL a ser consultada (ex: 'http://example.com').
    :param timestamp: Opcional. Data/hora no formato AAAAMMDDhhmmss (ex: '20060101') para buscar capturas próximas àquela data.
    """
    url = "https://archive.org/wayback/available"
    params = {"url": url_alvo}
    if timestamp:
        params["timestamp"] = timestamp
        
    try:
        response = await http_client.get(url, params=params, timeout=10.0)
        if response.status_code != 200:
            return {"error": f"Erro na API do Wayback (HTTP {response.status_code}): {response.text}"}
        return response.json()
    except Exception as e:
        return {"error": f"Falha ao consultar o Wayback Machine: {str(e)}"}


@mcp.tool()
async def wayback_listar_imagens(url_alvo: str, limite: int = 50) -> dict:
    """
    Lista as imagens arquivadas no histórico do Wayback Machine para um domínio ou URL específica.
    Útil para descobrir mídias, logotipos ou imagens deletadas do alvo.
    
    :param url_alvo: O domínio ou URL do site (ex: 'uol.com.br' ou 'uol.com.br/noticias').
    :param limite: Opcional. Número máximo de resultados a retornar (padrão 50, máximo 500).
    """
    url_consulta = url_alvo.strip()
    if not url_consulta.endswith("*") and not url_consulta.endswith("/") and "." in url_consulta:
        if "/" not in url_consulta or url_consulta.count("/") == 1:
            url_consulta = f"{url_consulta}/*"
        else:
            url_consulta = f"{url_consulta}*"

    url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url_consulta,
        "output": "json",
        "filter": "mimetype:image/.*",
        "limit": min(limite, 500),
        "fl": "original,timestamp,mimetype,statuscode"
    }
    
    try:
        response = await http_client.get(url, params=params, timeout=20.0)
        if response.status_code != 200:
            return {"error": f"Erro na API CDX do Wayback (HTTP {response.status_code}): {response.text}"}
            
        data = response.json()
        if not data or len(data) <= 1:
            return {"url_alvo": url_alvo, "total_encontrado": 0, "imagens": []}
            
        headers = data[0]
        rows = data[1:]
        
        imagens = []
        for row in rows:
            if len(row) < 4:
                continue
            original, timestamp, mimetype, statuscode = row[0], row[1], row[2], row[3]
            link_captura = f"http://web.archive.org/web/{timestamp}/{original}"
            imagens.append({
                "url_original": original,
                "timestamp": timestamp,
                "tipo_mimetype": mimetype,
                "status_http": statuscode,
                "link_visualizacao": link_captura
            })
            
        return {
            "url_alvo": url_alvo,
            "total_encontrado": len(imagens),
            "imagens": imagens
        }
    except Exception as e:
        return {"error": f"Falha ao listar imagens no Wayback: {str(e)}"}


@mcp.tool()
async def wayback_listar_snapshots(url_alvo: str, limite: int = 100, apenas_mudancas: bool = True) -> dict:
    """
    Lista todos os snapshots arquivados no Wayback Machine para uma URL específica desde a primeira captura.
    Permite obter o histórico cronológico completo de capturas de uma página.
    
    :param url_alvo: A URL específica da página (ex: 'example.com' ou 'http://example.com/noticia.html').
    :param limite: Opcional. Número máximo de registros (padrão 100, máximo 1000).
    :param apenas_mudancas: Opcional. Se 'True' (padrão), remove duplicidades consecutivas onde o conteúdo não sofreu alteração (usando collapse=digest).
    """
    url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url_alvo.strip(),
        "output": "json",
        "fl": "timestamp,original,statuscode,digest",
        "limit": min(limite, 1000)
    }
    if apenas_mudancas:
        params["collapse"] = "digest"
        
    try:
        response = await http_client.get(url, params=params, timeout=20.0)
        if response.status_code != 200:
            return {"error": f"Erro na API CDX do Wayback (HTTP {response.status_code}): {response.text}"}
            
        data = response.json()
        if not data or len(data) <= 1:
            return {"url_alvo": url_alvo, "total_encontrado": 0, "snapshots": []}
            
        headers = data[0]
        rows = data[1:]
        
        snapshots = []
        for row in rows:
            if len(row) < 4:
                continue
            timestamp, original, statuscode, digest = row[0], row[1], row[2], row[3]
            link_captura = f"http://web.archive.org/web/{timestamp}/{original}"
            snapshots.append({
                "timestamp": timestamp,
                "url_original": original,
                "status_http": statuscode,
                "checksum_digest": digest,
                "link_visualizacao": link_captura
            })
            
        return {
            "url_alvo": url_alvo,
            "apenas_mudancas": apenas_mudancas,
            "total_encontrado": len(snapshots),
            "snapshots": snapshots
        }
    except Exception as e:
        return {"error": f"Falha ao listar snapshots no Wayback: {str(e)}"}


# ==============================================================================
# SEGURANÇA E AUTENTICAÇÃO VIA CHAVE DE API (TRANSPORTE SSE)
# ==============================================================================
import secrets
import time
import sqlite3
from uuid import UUID
from contextvars import ContextVar
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
import uvicorn
import anyio
import mcp.server.sse as mcp_sse

# Monkeypatch quote no mcp.server.sse para não corromper URLs absolutas
_orig_quote = mcp_sse.quote
def _custom_quote(string, safe='/', encoding=None, errors=None):
    if string.startswith("http://") or string.startswith("https://"):
        parts = string.split("://", 1)
        return parts[0] + "://" + _orig_quote(parts[1], safe=safe, encoding=encoding, errors=errors)
    return _orig_quote(string, safe=safe, encoding=encoding, errors=errors)
mcp_sse.quote = _custom_quote

class ForceHTTPSMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            host = headers.get(b"host", b"").decode("utf-8")
            if "localhost" not in host and "127.0.0.1" not in host and "0.0.0.0" not in host:
                scope["scheme"] = "https"
        await self.app(scope, receive, send)

sessao_corrente: ContextVar[UUID] = ContextVar("sessao_corrente")
sessoes_autorizadas = set()
sessoes_ativas = {} # session_id -> {"usuario": "...", "permissoes": [...], "token": "..."}

DB_LOGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_logs.db")

def inicializar_db_logs():
    try:
        conn = sqlite3.connect(DB_LOGS_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_id TEXT,
                usuario TEXT,
                token_prefix TEXT,
                method TEXT,
                tool_name TEXT,
                arguments TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Falha ao inicializar banco de logs: {e}", file=sys.stderr, flush=True)

def registrar_log_busca(session_id, token: str, method: str, params: dict):
    usuario = "desconhecido"
    if session_id:
        try:
            sid = UUID(hex=session_id) if isinstance(session_id, str) else session_id
            sess_info = sessoes_ativas.get(sid)
            if sess_info:
                usuario = sess_info.get("usuario", "desconhecido")
        except Exception:
            pass
            
    if usuario == "desconhecido" and token:
        try:
            chaves = carregar_chaves_autorizadas()
            if token in chaves:
                usuario = chaves[token].get("usuario", "desconhecido")
        except Exception:
            pass

    args_str = json.dumps(params.get("arguments", {}), ensure_ascii=False)
    
    try:
        conn = sqlite3.connect(DB_LOGS_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mcp_logs (timestamp, session_id, usuario, token_prefix, method, tool_name, arguments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(session_id.hex) if session_id and hasattr(session_id, "hex") else (str(session_id) if session_id else None),
            usuario,
            token[:10] if token else None,
            method,
            params.get("name") if method == "tools/call" else None,
            args_str
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOG ERROR] Falha ao registrar log no SQLite: {e}", file=sys.stderr, flush=True)

class LoggingReceiveStream:
    def __init__(self, original_stream, session_id, token):
        self.original_stream = original_stream
        self.session_id = session_id
        self.token = token

    async def receive(self):
        message = await self.original_stream.receive()
        try:
            if hasattr(message, "method") and message.method == "tools/call":
                tool_name = getattr(message.params, "name", None)
                arguments = getattr(message.params, "arguments", {})
                registrar_log_busca(
                    self.session_id, 
                    self.token, 
                    message.method, 
                    {"name": tool_name, "arguments": arguments}
                )
        except Exception as e:
            print(f"[LOG ERROR] Falha ao interceptar mensagem na stream: {e}", file=sys.stderr, flush=True)
        return message

    async def aclose(self):
        await self.original_stream.aclose()

KEYS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_keys.json")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_config.json")
_cached_keys = {}
_cached_keys_mtime = 0

def carregar_config_global() -> dict:
    default_config = {
        "fontes_ativas": {
            "bigdata": True,
            "csint": True,
            "unitfour": True,
            "instagram": True,
            "linkedin": True,
            "lighthouse": True,
            "whois": True,
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

def verificar_permissao_fonte(nome_fonte: str, nome_consulta: str = None) -> dict | None:
    # 1. Verifica ativação global da fonte
    config = carregar_config_global()
    fontes_ativas = config.get("fontes_ativas", {})
    if fontes_ativas.get(nome_fonte) is False:
        return {"error": f"Fonte '{nome_fonte}' desativada globalmente pelo administrador."}

    # 2. Verifica ativação global da consulta individual
    if nome_consulta:
        consultas_ativas = config.get("consultas_ativas", {})
        if consultas_ativas.get(nome_consulta) is False:
            return {"error": f"Consulta '{nome_consulta}' desativada globalmente pelo administrador."}

    # 3. Verifica permissão individual do usuário
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
    if "*" not in permissoes and nome_fonte not in permissoes:
        if nome_consulta and nome_consulta in permissoes:
            pass
        else:
            return {"error": f"Acesso não autorizado. Chave de API sem permissão para '{nome_fonte}' ou '{nome_consulta}'."}

    return None

def carregar_chaves_autorizadas() -> dict:
    global _cached_keys, _cached_keys_mtime
    
    chaves_env = os.environ.get("MCP_API_KEYS", "").strip()
    
    # 1. Se mcp_keys.json não existir e também não houver chaves no .env, gera uma chave admin padrão
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
            print(f"\n=======================================================================", file=sys.stderr)
            print(f"[AUTH] ARQUIVO mcp_keys.json NÃO ENCONTRADO E MCP_API_KEYS AUSENTE NO .env", file=sys.stderr)
            print(f"[AUTH] UMA NOVA CHAVE DE API FOI GERADA COM SUCESSO:", file=sys.stderr)
            print(f"[AUTH] Usuário: admin", file=sys.stderr)
            print(f"[AUTH] Chave: {chave_inicial}", file=sys.stderr)
            print(f"[AUTH] Guarde esta chave! Ela foi salva em: {KEYS_FILE}", file=sys.stderr)
            print(f"=======================================================================\n", file=sys.stderr)
        except Exception as e:
            print(f"[AUTH ERROR] Falha ao criar {KEYS_FILE}: {e}", file=sys.stderr)
            
    # 2. Carrega as chaves do arquivo mcp_keys.json
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
                print(f"[AUTH] Chaves de API do arquivo {KEYS_FILE} carregadas/atualizadas. Total: {len(_cached_keys)}", file=sys.stderr)
        except Exception as e:
            print(f"[AUTH ERROR] Falha ao ler/recarregar {KEYS_FILE}: {e}", file=sys.stderr)
            
    # 3. Incorpora chaves do .env
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

def extrair_token(request) -> str:
    # Prints de depuração temporários
    print(f"[AUTH DEBUG] headers={dict(request.headers)}", file=sys.stderr, flush=True)
    try:
        print(f"[AUTH DEBUG] query_params={dict(request.query_params)}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[AUTH DEBUG] falha ao ler query_params: {e}", file=sys.stderr, flush=True)
        
    # 1. Tenta no Header Authorization (Bearer <token>)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        print(f"[AUTH DEBUG] extraído Bearer token: {token}", file=sys.stderr, flush=True)
        return token
        
    # 2. Tenta no Header X-API-Key
    x_api_key = request.headers.get("x-api-key")
    if x_api_key:
        token = x_api_key.strip()
        print(f"[AUTH DEBUG] extraído X-API-Key token: {token}", file=sys.stderr, flush=True)
        return token
        
    # 3. Tenta nos parâmetros da URL (Query String)
    query_token = request.query_params.get("api_key") or request.query_params.get("token")
    if query_token:
        token = query_token.strip()
        print(f"[AUTH DEBUG] extraído query token: {token}", file=sys.stderr, flush=True)
        return token
        
    print("[AUTH DEBUG] nenhum token encontrado", file=sys.stderr, flush=True)
    return None

def obter_chave_admin() -> str | None:
    # 1. Tenta do .env
    env_admin = os.environ.get("ADMIN_API_KEY", "").strip()
    if env_admin:
        return env_admin
    # 2. Tenta do mcp_keys.json (procurando o usuário "admin")
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict) and "admin" in dados:
                info = dados["admin"]
                if isinstance(info, dict):
                    return info.get("key")
                elif isinstance(info, str):
                    return info
    except Exception:
        pass
    # 3. Fallback: procura nos cached_keys alguma chave pertencente ao admin
    chaves = carregar_chaves_autorizadas()
    for token, info in chaves.items():
        if info.get("usuario") == "admin":
            return token
    return None

async def run_sse_with_auth(self_mcp) -> None:
    """Roda o FastMCP usando SSE com interceptação de autenticação nas conexões."""
    inicializar_db_logs()
    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        from starlette.requests import Request
        request = Request(scope, receive)
        
        if request.method == "POST":
            req_id = None
            try:
                body = await request.body()
                json_data = json.loads(body)
                method = json_data.get("method")
                req_id = json_data.get("id")
                params = json_data.get("params", {})
                
                # Check Auth first (same token validation!)
                token = extrair_token(request)
                if not verificar_token(token):
                    response = JSONResponse({"error": "Unauthorized. Invalid or missing API key."}, status_code=401)
                    await response(scope, receive, send)
                    return
                
                response_data = None
                
                if method == "initialize":
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "experimental": {},
                                "prompts": {"listChanged": False},
                                "resources": {"subscribe": False, "listChanged": False},
                                "tools": {"listChanged": False}
                            },
                            "serverInfo": {
                                "name": "veridianOsint-Conceitual",
                                "version": "1.2.0"
                            }
                        }
                    }
                elif method == "notifications/initialized":
                    response = Response("", status_code=204)
                    await response(scope, receive, send)
                    return
                elif method == "ping":
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {}
                    }
                elif method == "tools/list":
                    tools = await self_mcp.list_tools()
                    tools_json = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": tools_json
                        }
                    }
                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})
                    registrar_log_busca(None, token, method, params)
                    result = await self_mcp.call_tool(tool_name, tool_args)
                    result_json = [r.model_dump(mode="json", by_alias=True, exclude_none=True) for r in result]
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": result_json
                        }
                    }
                elif method == "resources/list":
                    resources = await self_mcp.list_resources()
                    resources_json = [r.model_dump(mode="json", by_alias=True, exclude_none=True) for r in resources]
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "resources": resources_json
                        }
                    }
                elif method == "prompts/list":
                    prompts = await self_mcp.list_prompts()
                    prompts_json = [p.model_dump(mode="json", by_alias=True, exclude_none=True) for p in prompts]
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "prompts": prompts_json
                        }
                    }
                else:
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                print(f"[AUTH DEBUG] POST /sse (método: {method}) -> Respondendo com JSON-RPC", file=sys.stderr, flush=True)
                response = JSONResponse(response_data, status_code=200)
                await response(scope, receive, send)
                return
                
            except Exception as e:
                print(f"[AUTH DEBUG] POST /sse falha ao processar: {e}", file=sys.stderr, flush=True)
                response_data = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                response = JSONResponse(response_data, status_code=500)
                await response(scope, receive, send)
                return
        
        # Constrói a URL absoluta para o endpoint de POST /messages/
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
        
        # Força https se for um domínio público para evitar bloqueio de Mixed Content no navegador
        if "localhost" not in host and "127.0.0.1" not in host and "0.0.0.0" not in host:
            proto = "https"
            
        base_url = f"{proto}://{host}"
        sse._endpoint = f"{base_url}/messages/"
        
        token = extrair_token(request)
        if not verificar_token(token):
            print(f"[AUTH DENIED] Conexão SSE recusada por token ausente ou inválido.", file=sys.stderr)
            response = JSONResponse({"error": "Unauthorized. Invalid or missing API key."}, status_code=401)
            await response(scope, receive, send)
            return
        
        sessoes_antes = set(sse._read_stream_writers.keys())
        
        async with sse.connect_sse(scope, receive, send) as streams:
            sessoes_depois = set(sse._read_stream_writers.keys())
            novas_sessoes = sessoes_depois - sessoes_antes
            
            novo_session_id = None
            if novas_sessoes:
                novo_session_id = list(novas_sessoes)[0]
                sessoes_autorizadas.add(novo_session_id)
                
                chaves = carregar_chaves_autorizadas()
                usr_info = chaves.get(token, {"usuario": "desconhecido", "permissoes": ["*"]})
                
                sessoes_ativas[novo_session_id] = {
                    "usuario": usr_info["usuario"],
                    "permissoes": usr_info.get("permissoes", ["*"]),
                    "token": token
                }
                print(f"[AUTH] Conexão SSE iniciada. Sessão: {novo_session_id.hex} | Usuário: {usr_info['usuario']}", file=sys.stderr, flush=True)
            
            try:
                logging_stream = LoggingReceiveStream(streams[0], novo_session_id, token)
                await self_mcp._mcp_server.run(
                    logging_stream,
                    streams[1],
                    self_mcp._mcp_server.create_initialization_options(),
                )
            finally:
                if novo_session_id:
                    sessoes_autorizadas.discard(novo_session_id)
                    sessoes_ativas.pop(novo_session_id, None)
                    print(f"[AUTH] Conexão SSE encerrada. Sessão: {novo_session_id.hex}", file=sys.stderr, flush=True)

    async def handle_messages(scope, receive, send):
        from starlette.requests import Request
        request = Request(scope, receive)
        session_id_param = request.query_params.get("session_id")
        if not session_id_param:
            response = Response("session_id is required", status_code=400)
            await response(scope, receive, send)
            return
        
        try:
            session_id = UUID(hex=session_id_param)
        except ValueError:
            response = Response("Invalid session ID", status_code=400)
            await response(scope, receive, send)
            return
            
        # Validação de segurança: a sessão precisa constar em sessoes_ativas
        if session_id not in sessoes_ativas:
            print(f"[AUTH DENIED] Tentativa de POST em /messages para sessão não autorizada/inexistente: {session_id_param}", file=sys.stderr, flush=True)
            response = Response("Unauthorized session", status_code=401)
            await response(scope, receive, send)
            return
            
        token_ctx = sessao_corrente.set(session_id)
        try:
            await sse.handle_post_message(scope, receive, send)
        finally:
            sessao_corrente.reset(token_ctx)

    async def serve_admin_page(scope, receive, send):
        caminho_admin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin.html")
        if not os.path.exists(caminho_admin):
            response = Response("admin.html não encontrado no servidor", status_code=404)
            await response(scope, receive, send)
            return
        
        try:
            with open(caminho_admin, "r", encoding="utf-8") as f:
                html_content = f.read()
            from starlette.responses import HTMLResponse
            response = HTMLResponse(html_content)
            await response(scope, receive, send)
        except Exception as e:
            response = Response(f"Erro ao ler página admin: {str(e)}", status_code=500)
            await response(scope, receive, send)

    async def admin_api_auth(request) -> bool:
        chave_admin = obter_chave_admin()
        if not chave_admin:
            return False
        auth_header = request.headers.get("authorization")
        token = None
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        if not token:
            token = request.headers.get("x-admin-key")
        if not token:
            token = request.query_params.get("admin_key")
        return token == chave_admin

    async def admin_api_status(request):
        if not await admin_api_auth(request):
            return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        config = carregar_config_global()
        chaves_brutas = {}
        try:
            if os.path.exists(KEYS_FILE):
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if isinstance(dados, dict):
                    for usr, info in dados.items():
                        if isinstance(info, dict) and "key" in info:
                            chaves_brutas[info["key"]] = {
                                "usuario": usr,
                                "description": info.get("description", ""),
                                "permissoes": info.get("permissoes", ["*"])
                            }
                        elif isinstance(info, str):
                            chaves_brutas[info] = {"usuario": usr, "description": "", "permissoes": ["*"]}
        except Exception:
            pass
        for token, info in _cached_keys.items():
            if token not in chaves_brutas:
                chaves_brutas[token] = {
                    "usuario": info.get("usuario"),
                    "description": info.get("description", ""),
                    "permissoes": info.get("permissoes", ["*"])
                }
        return JSONResponse({
            "fontes_ativas": config.get("fontes_ativas", {}),
            "consultas_ativas": config.get("consultas_ativas", {}),
            "chaves": chaves_brutas
        })

    async def admin_api_config(request):
        if not await admin_api_auth(request):
            return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
        config_type = body.get("type", "source")
        name = body.get("name") or body.get("source")
        active = body.get("active")
        
        if not name or active is None:
            return JSONResponse({"error": "name/source and active are required"}, status_code=400)
            
        config = carregar_config_global()
        if config_type == "query":
            if "consultas_ativas" not in config:
                config["consultas_ativas"] = {}
            config["consultas_ativas"][name] = bool(active)
        else:
            if "fontes_ativas" not in config:
                config["fontes_ativas"] = {}
            config["fontes_ativas"][name] = bool(active)
            
        if salvar_config_global(config):
            return JSONResponse({"status": "success", "config": config})
        else:
            return JSONResponse({"error": "Failed to save configuration"}, status_code=500)

    async def admin_api_keys_add(request):
        if not await admin_api_auth(request):
            return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        usuario = body.get("usuario")
        token = body.get("token")
        permissoes = body.get("permissoes", ["*"])
        if not usuario:
            return JSONResponse({"error": "usuario is required"}, status_code=400)
        if not token:
            token = "mcp_key_" + secrets.token_hex(20)
        dados = {}
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if not isinstance(dados, dict):
                    dados = {}
            except Exception:
                dados = {}
        dados[usuario] = {
            "key": token,
            "description": f"Chave criada via Painel Administrativo",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "permissoes": permissoes
        }
        try:
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            carregar_chaves_autorizadas()
            return JSONResponse({"status": "success", "token": token, "usuario": usuario})
        except Exception as e:
            return JSONResponse({"error": f"Failed to write keys file: {str(e)}"}, status_code=500)

    async def admin_api_keys_delete(request):
        if not await admin_api_auth(request):
            return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        token = body.get("token")
        if not token:
            return JSONResponse({"error": "token is required"}, status_code=400)
        dados = {}
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if not isinstance(dados, dict):
                    dados = {}
            except Exception:
                dados = {}
        usuario_removido = None
        for usr, info in list(dados.items()):
            if isinstance(info, dict) and info.get("key") == token:
                usuario_removido = usr
                del dados[usr]
                break
            elif isinstance(info, str) and info == token:
                usuario_removido = usr
                del dados[usr]
                break
        if not usuario_removido:
            return JSONResponse({"error": "Token not found in keys file"}, status_code=404)
        try:
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            carregar_chaves_autorizadas()
            return JSONResponse({"status": "success", "usuario": usuario_removido})
        except Exception as e:
            return JSONResponse({"error": f"Failed to write keys file: {str(e)}"}, status_code=500)

    async def admin_api_logs(request):
        if not await admin_api_auth(request):
            return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
            
        usuario_filter = request.query_params.get("usuario")
        tool_filter = request.query_params.get("tool_name")
        limit_val = request.query_params.get("limit", "50")
        offset_val = request.query_params.get("offset", "0")
        
        try:
            limit = int(limit_val)
            offset = int(offset_val)
        except ValueError:
            limit = 50
            offset = 0
            
        try:
            conn = sqlite3.connect(DB_LOGS_FILE)
            cursor = conn.cursor()
            
            query = "SELECT id, timestamp, session_id, usuario, token_prefix, method, tool_name, arguments FROM mcp_logs"
            params = []
            where_clauses = []
            
            if usuario_filter:
                where_clauses.append("usuario = ?")
                params.append(usuario_filter)
                
            if tool_filter:
                where_clauses.append("tool_name = ?")
                params.append(tool_filter)
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            count_query = "SELECT COUNT(*) FROM mcp_logs"
            if where_clauses:
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(count_query, params[:-2])
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            logs_list = []
            for row in rows:
                logs_list.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "session_id": row[2],
                    "usuario": row[3],
                    "token_prefix": row[4],
                    "method": row[5],
                    "tool_name": row[6],
                    "arguments": row[7]
                })
                
            return JSONResponse({
                "logs": logs_list,
                "total": total_count,
                "limit": limit,
                "offset": offset
            })
            
        except Exception as e:
            return JSONResponse({"error": f"Failed to retrieve logs: {str(e)}"}, status_code=500)

    admin_port_env = os.environ.get("ADMIN_PORT")
    admin_port = None
    if admin_port_env:
        try:
            admin_port = int(admin_port_env)
        except ValueError:
            print(f"[AUTH ERROR] Valor de ADMIN_PORT inválido: {admin_port_env}. Usando mesma porta.", file=sys.stderr)
            admin_port = None

    if admin_port:
        mcp_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )
        
        admin_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Route("/admin/api/status", endpoint=admin_api_status, methods=["GET"]),
                Route("/admin/api/config", endpoint=admin_api_config, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_add, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_delete, methods=["DELETE"]),
                Route("/admin/api/logs", endpoint=admin_api_logs, methods=["GET"]),
                Mount("/admin", app=serve_admin_page),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )

        mcp_config = uvicorn.Config(
            mcp_app,
            host=self_mcp.settings.host,
            port=self_mcp.settings.port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        
        admin_config = uvicorn.Config(
            admin_app,
            host=self_mcp.settings.host,
            port=admin_port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )

        mcp_server = uvicorn.Server(mcp_config)
        admin_server = uvicorn.Server(admin_config)

        print(f"[MCP] Servidor MCP rodando na porta: {self_mcp.settings.port}", file=sys.stderr, flush=True)
        print(f"[ADMIN] Painel Administrativo rodando na porta: {admin_port}", file=sys.stderr, flush=True)

        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp_server.serve)
            tg.start_soon(admin_server.serve)
    else:
        starlette_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
                Route("/admin/api/status", endpoint=admin_api_status, methods=["GET"]),
                Route("/admin/api/config", endpoint=admin_api_config, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_add, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_delete, methods=["DELETE"]),
                Route("/admin/api/logs", endpoint=admin_api_logs, methods=["GET"]),
                Mount("/admin", app=serve_admin_page),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )

        config = uvicorn.Config(
            starlette_app,
            host=self_mcp.settings.host,
            port=self_mcp.settings.port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        server = uvicorn.Server(config)
        await server.serve()


# Ponto de entrada
if __name__ == "__main__":
    import sys
    import os
    
    # Determina o modo de transporte (stdio por padrão, ou sse se configurado/passado argumento)
    transport_mode = os.environ.get("FASTMCP_TRANSPORT", "stdio")
    if "--sse" in sys.argv:
        transport_mode = "sse"
        
    print("Iniciando servidor MCP 'veridianOsint-Conceitual' com CSINT, BigDataCorp, HikerAPI, Harvest API (LinkedIn), Unitfour, Lighthouse (Facebook e Imagens OSINT) e SociaVault (TikTok OSINT)...", file=sys.stderr, flush=True)
    
    if transport_mode == "sse":
        print(f"[MCP] Rodando em modo SSE (Web) protegido por Chave de API na porta: {mcp.settings.port}", file=sys.stderr, flush=True)
        # Inicializa o pool de chaves antes de rodar
        carregar_chaves_autorizadas()
        anyio.run(run_sse_with_auth, mcp)
    else:
        print("[MCP] Rodando em modo STDIO.", file=sys.stderr, flush=True)
        mcp.run(transport="stdio")

