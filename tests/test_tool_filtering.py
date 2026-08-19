"""
Testes automatizados para validação de desativação e propagação de consultas no MCP.
"""
import pytest
from unittest.mock import patch
from src.app import mcp
import src.tools

@pytest.mark.asyncio
async def test_tool_filtered_when_query_disabled():
    """Valida que quando uma consulta específica está desativada, ela não é propagada no list_tools."""
    mock_config = {
        "fontes_ativas": {
            "bigdata": True,
            "escavador": True
        },
        "consultas_ativas": {
            "bigdata_consultar_cpf": False
        }
    }
    
    with patch("src.app.carregar_config_global", return_value=mock_config):
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        
        # bigdata_consultar_cpf -> veridian_consultar_cadastro_cpf deve estar AUSENTE
        assert "veridian_consultar_cadastro_cpf" not in tool_names
        # Outras consultas de bigdata devem continuar PRESENTES
        assert "veridian_ver_categoria" in tool_names
        assert "veridian_consultar_cadastro_cnpj" in tool_names

@pytest.mark.asyncio
async def test_tool_filtered_when_source_disabled():
    """Valida que quando uma fonte inteira está desativada, todas as suas consultas são excluídas do list_tools."""
    mock_config = {
        "fontes_ativas": {
            "escavador": False,
            "bigdata": True
        },
        "consultas_ativas": {}
    }
    
    with patch("src.app.carregar_config_global", return_value=mock_config):
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        
        # escavador_buscar_processos_oab -> veridian_buscar_processos_oab
        assert "veridian_buscar_processos_oab" not in tool_names
        # Consultas de bigdata devem estar presentes
        assert "veridian_consultar_cadastro_cpf" in tool_names

@pytest.mark.asyncio
async def test_tool_filtered_by_whitelabel_name():
    """Valida desativação usando o nome whitelabel da ferramenta."""
    mock_config = {
        "fontes_ativas": {
            "bigdata": True
        },
        "consultas_ativas": {
            "veridian_consultar_cadastro_cpf": False
        }
    }
    
    with patch("src.app.carregar_config_global", return_value=mock_config):
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        
        assert "veridian_consultar_cadastro_cpf" not in tool_names

@pytest.mark.asyncio
async def test_tool_execution_blocked_when_disabled():
    """Valida que chamar uma ferramenta desativada retorna erro de permissão."""
    mock_config = {
        "fontes_ativas": {
            "bigdata": True
        },
        "consultas_ativas": {
            "bigdata_consultar_cpf": False
        }
    }
    
    with patch("src.core.auth.carregar_config_global", return_value=mock_config):
        result = await mcp.call_tool("veridian_consultar_cadastro_cpf", {"cpf": "12345678900"})
        assert len(result) >= 1
        # Verifica se o erro foi retornado no texto
        content_text = result[0].text
        assert "desativada globalmente" in content_text.lower()
