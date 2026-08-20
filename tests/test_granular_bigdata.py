import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.app import mcp, custom_list_tools
from src.providers import bigdatacorp
from src.core.cache import obter_caminho_cache_seguro
from src.tools.cadastrais_tools import (
    bigdata_cpf_dados_basicos,
    bigdata_cpf_telefones,
    bigdata_cpf_emails,
    bigdata_cpf_enderecos,
    bigdata_cpf_processos,
    bigdata_cpf_empresas_e_socios,
    bigdata_cpf_parentes_e_relacionados,
    bigdata_cnpj_dados_basicos,
    bigdata_cnpj_telefones,
    bigdata_cnpj_emails,
    bigdata_cnpj_enderecos,
    bigdata_cnpj_quadro_societario,
    bigdata_cnpj_processos,
    bigdata_cnpj_evolucao_historica
)
from src.core.auth import obter_nome_whitelabel

def test_granular_whitelabel_names():
    """Valida se todas as ferramentas granulares são corretamente mascaradas com o prefixo veridian_."""
    assert obter_nome_whitelabel("bigdata_cpf_dados_basicos") == "veridian_cpf_dados_basicos"
    assert obter_nome_whitelabel("bigdata_cpf_telefones") == "veridian_cpf_telefones"
    assert obter_nome_whitelabel("bigdata_cpf_emails") == "veridian_cpf_emails"
    assert obter_nome_whitelabel("bigdata_cpf_enderecos") == "veridian_cpf_enderecos"
    assert obter_nome_whitelabel("bigdata_cpf_processos") == "veridian_cpf_processos"
    assert obter_nome_whitelabel("bigdata_cpf_empresas_e_socios") == "veridian_cpf_empresas_e_socios"
    assert obter_nome_whitelabel("bigdata_cpf_parentes_e_relacionados") == "veridian_cpf_parentes_e_relacionados"
    assert obter_nome_whitelabel("bigdata_cpf_historico_cadastral") == "veridian_cpf_historico_cadastral"
    assert obter_nome_whitelabel("bigdata_cpf_dados_profissionais") == "veridian_cpf_dados_profissionais"
    assert obter_nome_whitelabel("bigdata_cpf_dados_politicos") == "veridian_cpf_dados_politicos"
    assert obter_nome_whitelabel("bigdata_cpf_beneficios_sociais") == "veridian_cpf_beneficios_sociais"
    assert obter_nome_whitelabel("bigdata_cpf_presenca_online") == "veridian_cpf_presenca_online"

    assert obter_nome_whitelabel("bigdata_cnpj_dados_basicos") == "veridian_cnpj_dados_basicos"
    assert obter_nome_whitelabel("bigdata_cnpj_telefones") == "veridian_cnpj_telefones"
    assert obter_nome_whitelabel("bigdata_cnpj_emails") == "veridian_cnpj_emails"
    assert obter_nome_whitelabel("bigdata_cnpj_enderecos") == "veridian_cnpj_enderecos"
    assert obter_nome_whitelabel("bigdata_cnpj_quadro_societario") == "veridian_cnpj_quadro_societario"
    assert obter_nome_whitelabel("bigdata_cnpj_processos") == "veridian_cnpj_processos"
    assert obter_nome_whitelabel("bigdata_cnpj_evolucao_historica") == "veridian_cnpj_evolucao_historica"

@pytest.mark.asyncio
async def test_granular_cpf_execution_with_mock():
    """Valida se a ferramenta granular bigdata_cpf_telefones retorna apenas a fatia de telefones."""
    p = obter_caminho_cache_seguro("bigdata_23302234805")
    if p and os.path.exists(p):
        try: os.remove(p)
        except Exception: pass

    mock_api_resp = {
        "Status": {"Code": 0, "Message": "OK"},
        "Result": [
            {
                "BasicData": {"Name": "Investigado Teste", "TaxIdNumber": "23302234805"},
                "ExtendedPhones": [
                    {"Number": "67999887766", "Type": "Mobile", "Carrier": "Vivo"}
                ]
            }
        ]
    }
    
    with patch("src.providers.bigdatacorp.get_bigdata_token", return_value="fake_token"), \
         patch("src.providers.bigdatacorp.resilient_request") as mock_req:
        mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_api_resp)
        
        # Chama a ferramenta granular
        res = await bigdata_cpf_telefones("233.022.348-05")
        assert res.get("status") == "sucesso"
        assert res.get("dataset") == "bdcphones"
        assert len(res.get("bdcphones", [])) == 1
        assert res["bdcphones"][0]["Number"] == "67999887766"

    if p and os.path.exists(p):
        try: os.remove(p)
        except Exception: pass

@pytest.mark.asyncio
async def test_granular_tool_gating_disabled():
    """Valida se desativar uma consulta no config bloqueia sua execução."""
    mock_config = {
        "fontes_ativas": {"bigdata": True},
        "consultas_ativas": {
            "bigdata_cpf_processos": False
        }
    }
    with patch("src.core.auth.carregar_config_global", return_value=mock_config):
        res = await bigdata_cpf_processos("23302234805")
        assert ("error" in res) or (res.get("status") == "erro")
        msg = res.get("error") or res.get("mensagem") or ""
        assert "desativada" in msg.lower()

@pytest.mark.asyncio
async def test_custom_list_tools_filtering_granular():
    """Valida se ferramentas desativadas em consultas_ativas não são propagadas na lista do MCP."""
    mock_config = {
        "fontes_ativas": {
            "bigdata": True,
            "csint": False,
            "unitfour": True
        },
        "consultas_ativas": {
            "bigdata_cpf_dados_politicos": False,
            "veridian_cpf_beneficios_sociais": False
        }
    }
    with patch("src.app.carregar_config_global", return_value=mock_config):
        tools = await custom_list_tools()
        tool_names = [t.name for t in tools]
        
        # Ferramentas ativas devem aparecer
        assert "veridian_cpf_dados_basicos" in tool_names
        assert "veridian_cpf_telefones" in tool_names
        assert "veridian_cnpj_dados_basicos" in tool_names
        
        # Ferramentas desativadas pelo nome original ou whitelabel NÃO devem aparecer
        assert "veridian_cpf_dados_politicos" not in tool_names
        assert "bigdata_cpf_dados_politicos" not in tool_names
        assert "veridian_cpf_beneficios_sociais" not in tool_names
        assert "bigdata_cpf_beneficios_sociais" not in tool_names

@pytest.mark.asyncio
async def test_aggregated_consultar_cpf_filters_disabled_datasets():
    """Valida se consultar_cpf com múltiplos datasets filtra os datasets desativados antes da chamada."""
    p = obter_caminho_cache_seguro("bigdata_23302234805")
    if p and os.path.exists(p):
        try: os.remove(p)
        except Exception: pass

    mock_config = {
        "fontes_ativas": {"bigdata": True},
        "consultas_ativas": {
            "bigdata_cpf_processos": False,
            "bdcpolitics": False
        }
    }
    mock_api_resp = {
        "Status": {"Code": 0, "Message": "OK"},
        "Result": [
            {
                "BasicData": {"Name": "Investigado Teste", "TaxIdNumber": "23302234805"},
                "ExtendedPhones": [{"Number": "11999998888"}]
            }
        ]
    }
    
    with patch("src.core.auth.carregar_config_global", return_value=mock_config), \
         patch("src.providers.bigdatacorp.get_bigdata_token", return_value="fake_token"), \
         patch("src.providers.bigdatacorp.resilient_request") as mock_req:
        mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_api_resp)
        
        # Pede básico, telefones e processos (processos está desativado)
        res = await bigdatacorp.consultar_cpf("23302234805", datasets="bdcbasicdata,bdcphones,bdclawsuits")
        assert res.get("status") == "sucesso"
        
        # Confirma que a API foi chamada apenas com basic_data e phones_extended
        called_payload = mock_req.call_args.kwargs.get("json", {})
        called_datasets = called_payload.get("Datasets", "").split(",")
        assert "processes.limit(80)" not in called_datasets
        assert "basic_data" in called_datasets
        assert "phones_extended" in called_datasets

    if p and os.path.exists(p):
        try: os.remove(p)
        except Exception: pass
