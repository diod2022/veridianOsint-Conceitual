import os
import functools
from mcp.server.fastmcp import FastMCP
from src.core.config import FASTMCP_PORT
from src.core.http_client import server_lifespan
from src.core.auth import (
    obter_nome_whitelabel,
    limpar_descricao_whitelabel,
    limpar_resultado_whitelabel,
    verificar_permissao_fonte
)

# Instância unificada do FastMCP
mcp = FastMCP(
    "veridianOsint-Conceitual",
    lifespan=server_lifespan,
    port=FASTMCP_PORT
)

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

        @functools.wraps(func)
        async def wrapper(*func_args, **func_kwargs):
            if nome_fonte:
                permissao = verificar_permissao_fonte(nome_fonte, nome_funcao)
                if permissao:
                    return permissao
            
            result = await func(*func_args, **func_kwargs)
            return limpar_resultado_whitelabel(result)

        wrapper.__doc__ = limpar_descricao_whitelabel(func.__doc__)
        return original_tool(*args, **kwargs)(wrapper)
    return decorator

mcp.tool = custom_tool
