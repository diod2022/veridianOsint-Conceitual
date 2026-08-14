"""
Testes automatizados para White-labeling e RBAC
"""
import pytest
from src.core.auth import (
    obter_nome_whitelabel,
    limpar_descricao_whitelabel,
    limpar_resultado_whitelabel,
    verificar_permissao_fonte,
    carregar_config_global,
    salvar_config_global
)

def test_mapeamento_nomes_whitelabel():
    assert obter_nome_whitelabel("bigdata_consultar_cpf") == "veridian_consultar_cadastro_cpf"
    assert obter_nome_whitelabel("unitfour_mandados_prisao") == "veridian_mandados_prisao"
    assert obter_nome_whitelabel("escavador_buscar_processos_oab") == "veridian_buscar_processos_oab"
    assert obter_nome_whitelabel("csint_busca_universal") == "veridian_busca_vazamentos"
    assert obter_nome_whitelabel("instagram_buscar_usuario") == "veridian_buscar_perfil_instagram"
    assert obter_nome_whitelabel("tavily_buscar_web") == "veridian_buscar_web"

def test_sanitizacao_descricao_e_resultados():
    desc = "Consulta CPF na BigDataCorp e dados na Unitfour e CSINT.pro."
    limpa = limpar_descricao_whitelabel(desc)
    assert "BigDataCorp" not in limpa
    assert "Unitfour" not in limpa
    assert "CSINT.pro" not in limpa
    assert "Veridian" in limpa

    res = {
        "fornecedor": "BigDataCorp",
        "api": "https://api.csint.pro/v1",
        "mensagem": "Sucesso retornado pela API Escavador",
        "nested": [
            {"fonte": "UnitFour"}
        ]
    }
    res_limpo = limpar_resultado_whitelabel(res)
    assert "BigDataCorp" not in str(res_limpo)
    assert "csint.pro" not in str(res_limpo)
    assert "Escavador" not in str(res_limpo)
    assert "UnitFour" not in str(res_limpo)
