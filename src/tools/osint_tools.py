from typing import Union, Optional
from src.app import mcp
from src.providers import whois, csint, web_osint

@mcp.tool()
async def whois_consultar(target: str, ignore_raw_text: bool = True, hard_refresh: bool = False) -> dict:
    """
    Realiza uma consulta WHOIS para obter informações de propriedade e registro de um domínio, IP ou e-mail.
    
    Args:
        target: Domínio (ex: google.com), IP (ex: 8.8.8.8) ou e-mail do qual deseja obter dados.
        ignore_raw_text: Se True, omite o texto bruto desestruturado poupando tokens.
        hard_refresh: Se True, força a consulta em tempo real na API WhoisXML.
    """
    return await whois.whois_consultar(target, ignore_raw_text, hard_refresh)

@mcp.tool()
async def csint_consultar_ip(ip: str) -> dict:
    """
    Busca informações avançadas sobre um endereço IP (Geolocalização, ISP, Risco, Detecção de VPN/TOR/Proxy).
    
    Args:
        ip: Endereço IP (ex: 8.8.8.8)
    """
    return await csint.consultar_ip(ip)

@mcp.tool()
async def csint_busca_universal(query: Union[str, int], tipo: str = "auto") -> dict:
    """
    Realiza uma busca universal em múltiplos bancos de dados de vazamentos em paralelo utilizando o CSINT.pro.
    
    Args:
        query: O dado a ser buscado (ex: email, telefone, username ou ip).
        tipo: O tipo de dado. Pode ser 'email', 'phone', 'username', 'ip' ou 'auto'.
    """
    return await csint.busca_universal(query, tipo)

@mcp.tool()
async def csint_consultar_telefone(telefone: Union[str, int]) -> dict:
    """
    Realiza busca avançada de inteligência e reputação sobre um número de telefone utilizando a SEON API da CSINT.pro.
    
    Args:
        telefone: O número de telefone completo com o código do país (ex: '+5511988887777').
    """
    return await csint.consultar_telefone(telefone)

@mcp.tool()
async def csint_consultar_email(email: Union[str, int]) -> dict:
    """
    Realiza busca avançada de inteligência e reputação sobre um endereço de e-mail utilizando a SEON API da CSINT.pro.
    
    Args:
        email: O endereço de e-mail completo pesquisado.
    """
    return await csint.consultar_email(email)

@mcp.tool()
async def tavily_buscar_web(query: str, search_depth: str = "basic") -> str:
    """
    Realiza uma busca otimizada na internet usando a API do Tavily.
    
    Args:
        query: Termo ou pergunta a ser pesquisada.
        search_depth: 'basic' (rápida) ou 'advanced' (detalhada).
    """
    return await web_osint.tavily_buscar_web(query, search_depth)

@mcp.tool()
async def firecrawl_raspar_pagina(url_alvo: str) -> str:
    """
    Raspa uma página web completa e a converte em Markdown estruturado.
    
    Args:
        url_alvo: A URL completa da página a ser raspada.
    """
    return await web_osint.firecrawl_raspar_pagina(url_alvo)

@mcp.tool()
async def serper_buscar_web_dorks(alvo: str, categoria: str = "arquivos_expostos") -> dict:
    """
    Realiza pesquisas avançadas utilizando Google Dorks automatizados (via Serper.dev).
    
    Args:
        alvo: O domínio alvo (ex: 'empresa.com.br') ou nome corporativo.
        categoria: 'arquivos_expostos', 'credenciais_e_backups', 'infraestrutura_e_login' ou 'subdominios'.
    """
    return await web_osint.serper_buscar_web_dorks(alvo, categoria)

@mcp.tool()
async def serper_buscar_google(query: str) -> dict:
    """
    Realiza uma pesquisa direta no Google utilizando a API do Serper.dev.
    
    Args:
        query: Termo de busca ou expressão Google Dork completa.
    """
    return await web_osint.serper_buscar_google(query)

@mcp.tool()
async def serper_buscar_avaliacoes_empresa(
    empresa_ou_local: str,
    cid: Optional[str] = None,
    place_id: Optional[str] = None,
    fid: Optional[str] = None,
    sort_by: str = "newest",
    next_page_token: Optional[str] = None,
    termo_filtro: Optional[str] = None,
    gl: str = "br",
    hl: str = "pt-br"
) -> dict:
    """
    Busca avaliações (reviews) de estabelecimentos e empresas no Google Maps através do Serper.dev,
    seguindo rigorosamente a especificação do Serper Playground (https://serper.dev/playground).
    
    Args:
        empresa_ou_local: Nome da empresa/local para resolução automática no Maps ou identificador direto.
        cid: Opcional. Google Customer ID / CID numérico direto do local.
        place_id: Opcional. Google Place ID.
        fid: Opcional. Google Feature ID.
        sort_by: 'newest' (mais recentes), 'mostRelevant' (mais relevantes), 'highestRating' (melhores notas), 'lowestRating' (piores notas).
        next_page_token: Opcional. Token para recuperar a próxima página de avaliações.
        termo_filtro: Opcional. Palavra-chave para filtrar comentários específicos.
        gl: Código do país (padrão 'br').
        hl: Idioma das avaliações (padrão 'pt-br').
    """
    return await web_osint.serper_buscar_avaliacoes_empresa(
        empresa_ou_local=empresa_ou_local,
        cid=cid,
        place_id=place_id,
        fid=fid,
        sort_by=sort_by,
        next_page_token=next_page_token,
        termo_filtro=termo_filtro,
        gl=gl,
        hl=hl
    )

@mcp.tool()
async def serper_buscar_avaliacoes_produto(
    produto_ou_id: str,
    next_page_token: Optional[str] = None,
    gl: str = "br",
    hl: str = "pt-br"
) -> dict:
    """
    Busca avaliações de produtos (Product Reviews) via Serper.dev conforme especificado no Serper Playground.
    
    Args:
        produto_ou_id: ID do produto no Google Shopping ou nome/modelo do produto a pesquisar.
        next_page_token: Opcional. Token para a próxima página de avaliações.
        gl: País (padrão 'br').
        hl: Idioma (padrão 'pt-br').
    """
    return await web_osint.serper_buscar_avaliacoes_produto(
        produto_ou_id=produto_ou_id,
        next_page_token=next_page_token,
        gl=gl,
        hl=hl
    )

@mcp.tool()
async def serper_buscar_reviews_por_email(
    email: str,
    incluir_username: bool = True
) -> dict:
    """
    Realiza varredura investigativa multivetorial para localizar avaliações, reclamações e depoimentos
    associados a um endereço de e-mail (e seu username) em portais de consumo, Google Maps e web.
    
    Args:
        email: O endereço de e-mail do alvo a ser investigado.
        incluir_username: Se True, também pesquisa o identificador/usuário do e-mail em portais de reclamação.
    """
    return await web_osint.serper_buscar_reviews_por_email(email, incluir_username)

@mcp.tool()
async def wayback_consultar_disponibilidade(url_alvo: str, timestamp: Optional[str] = None) -> dict:
    """
    Verifica se uma URL possui capturas salvas no histórico do Wayback Machine (Internet Archive).
    
    Args:
        url_alvo: A URL a ser consultada.
        timestamp: Opcional. Data/hora no formato AAAAMMDDhhmmss (ex: '20060101').
    """
    return await web_osint.wayback_consultar_disponibilidade(url_alvo, timestamp)

@mcp.tool()
async def wayback_listar_imagens(url_alvo: str, limite: int = 50) -> dict:
    """
    Lista as imagens arquivadas no histórico do Wayback Machine para um domínio ou URL específica.
    
    Args:
        url_alvo: O domínio ou URL do site.
        limite: Opcional. Número máximo de resultados a retornar.
    """
    return await web_osint.wayback_listar_imagens(url_alvo, limite)

@mcp.tool()
async def wayback_listar_snapshots(url_alvo: str, limite: int = 100, apenas_mudancas: bool = True) -> dict:
    """
    Lista todos os snapshots arquivados no Wayback Machine para uma URL específica.
    
    Args:
        url_alvo: A URL específica da página.
        limite: Opcional. Número máximo de registros.
        apenas_mudancas: Se True, remove duplicidades onde o conteúdo não sofreu alteração.
    """
    return await web_osint.wayback_listar_snapshots(url_alvo, limite, apenas_mudancas)
