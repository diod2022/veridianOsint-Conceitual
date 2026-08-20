import os
import functools
from mcp.server.fastmcp import FastMCP
from src.core.config import FASTMCP_PORT
from src.core.http_client import server_lifespan
from src.core.auth import (
    obter_nome_whitelabel,
    limpar_descricao_whitelabel,
    limpar_resultado_whitelabel,
    verificar_permissao_fonte,
    carregar_config_global
)
from mcp.types import Tool as MCPTool

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
        whitelabel_name = obter_nome_whitelabel(nome_funcao)
        kwargs["name"] = whitelabel_name
        
        # Mascara a descrição da ferramenta dinamicamente se fornecida no decorator
        if "description" in kwargs:
            kwargs["description"] = limpar_descricao_whitelabel(kwargs["description"])

        @functools.wraps(func)
        async def wrapper(*func_args, **func_kwargs):
            if nome_fonte or nome_funcao:
                permissao = verificar_permissao_fonte(nome_fonte, nome_funcao)
                if permissao:
                    return permissao
            
            result = await func(*func_args, **func_kwargs)
            return limpar_resultado_whitelabel(result)

        wrapper.__doc__ = limpar_descricao_whitelabel(func.__doc__)
        wrapper._orig_func_name = nome_funcao
        wrapper._source_name = nome_fonte
        wrapper._whitelabel_name = whitelabel_name

        res = original_tool(*args, **kwargs)(wrapper)

        registered_tool = mcp._tool_manager.get_tool(whitelabel_name)
        if registered_tool:
            registered_tool._orig_func_name = nome_funcao
            registered_tool._source_name = nome_fonte
            registered_tool._whitelabel_name = whitelabel_name

        return res
    return decorator

mcp.tool = custom_tool

async def custom_list_tools() -> list[MCPTool]:
    """Lista ferramentas disponíveis no MCP filtrando consultas e fontes desativadas."""
    config = carregar_config_global()
    fontes_ativas = config.get("fontes_ativas", {})
    consultas_ativas = config.get("consultas_ativas", {})

    tools = mcp._tool_manager.list_tools()
    active_tools = []

    for info in tools:
        orig_name = (
            getattr(info, "_orig_func_name", None)
            or getattr(getattr(info, "fn", None), "_orig_func_name", None)
            or getattr(getattr(info, "fn", None), "__name__", None)
        )
        source_name = (
            getattr(info, "_source_name", None)
            or getattr(getattr(info, "fn", None), "_source_name", None)
        )
        tool_name = info.name

        if not source_name and orig_name:
            for prefix, fonte in [
                ("whois_", "whois"),
                ("csint_", "csint"),
                ("bigdata_", "bigdata"),
                ("unitfour_", "unitfour"),
                ("instagram_", "instagram"),
                ("tiktok_", "instagram"),
                ("linkedin_", "linkedin"),
                ("lighthouse_", "lighthouse"),
                ("escavador_", "escavador"),
                ("tavily_", "tavily"),
                ("firecrawl_", "firecrawl"),
                ("serper_", "serper"),
                ("wayback_", "wayback"),
                ("biometria_", "biometria"),
            ]:
                if orig_name.startswith(prefix):
                    source_name = fonte
                    break

        # Se a fonte inteira estiver desativada, não propaga
        if source_name and fontes_ativas.get(source_name) is False:
            continue

        # Se a consulta específica estiver desativada pelo nome original ou whitelabel, não propaga
        if orig_name and consultas_ativas.get(orig_name) is False:
            continue
        if tool_name and consultas_ativas.get(tool_name) is False:
            continue

        active_tools.append(
            MCPTool(
                name=info.name,
                description=info.description,
                inputSchema=info.parameters,
            )
        )

    return active_tools

# Sobrescreve list_tools no FastMCP e registra no servidor MCP interno
mcp.list_tools = custom_list_tools
mcp._mcp_server.list_tools()(custom_list_tools)

