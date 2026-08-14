"""
Testes automatizados de registro e integridade do servidor FastMCP
"""
import pytest
from src.app import mcp
import src.tools
import src.resources
import src.prompts

@pytest.mark.asyncio
async def test_mcp_registration():
    tools = await mcp.list_tools()
    resources = await mcp.list_resources()
    prompts = await mcp.list_prompts()
    
    assert len(tools) > 30, f"Esperava mais de 30 ferramentas registradas, encontrou {len(tools)}"
    assert len(resources) >= 1, f"Esperava pelo menos 1 recurso nativo, encontrou {len(resources)}"
    assert len(prompts) >= 4, f"Esperava pelo menos 4 prompts nativos, encontrou {len(prompts)}"
    
    tool_names = [t.name for t in tools]
    assert "veridian_consultar_cadastro_cpf" in tool_names
    assert "veridian_buscar_processos_oab" in tool_names
    assert "veridian_mandados_prisao" in tool_names
    
    # Valida que as ferramentas de dossiê foram removidas conforme solicitado
    assert "veridian_gerar_dossie" not in tool_names
    assert "veridian_enriquecer_dossie" not in tool_names

@pytest.mark.asyncio
async def test_resource_status_execution():
    from src.resources.osint_resources import obter_status_servidor
    status_json = await obter_status_servidor()
    assert "veridianOsint-Conceitual" in status_json
    assert "FastMCP" in status_json
