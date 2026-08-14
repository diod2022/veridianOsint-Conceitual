"""
Testes automatizados para a consolidação de Dossiê Canônico
"""
import pytest
from src.providers.dossie_builder import (
    Dossie,
    ScoreConfianca,
    normalizar_unitfour_cpf,
    normalizar_bigdata_cpf,
    consolidar_cpf,
    dossie_para_markdown,
    construir_timeline_cnpj
)

def test_score_confianca():
    score = ScoreConfianca(base=50)
    score.adicionar_fonte("unitfour")
    score.adicionar_fonte("bigdatacorp")
    assert score.score == 100
    assert score.classificacao == "ALTA"
    assert score.corroborado is True

def test_dossie_deduplicacao_e_corroboracao():
    d = Dossie(cpf="12345678901")
    d.adicionar_telefone("11988887777", fonte="unitfour", dados_extras={"tipo": "celular"})
    d.adicionar_telefone("11988887777", fonte="bigdatacorp", dados_extras={"operadora": "VIVO"})
    
    assert len(d.telefones) == 1
    t = d.telefones[0]
    assert t["corroborado"] is True
    assert len(t["fontes"]) == 2
    assert "unitfour" in t["fontes"]
    assert "bigdatacorp" in t["fontes"]
    assert t["score_confianca"] >= 75

def test_timeline_cnpj():
    payload_mock = {
        "Result": [{
            "BasicData": {"OfficialName": "EMPRESA TESTE LTDA"},
            "CompanyEvolution": [
                {"Event": "Aumento de Capital", "Date": "2022-01-10", "Details": "Capital R$ 500.000"}
            ],
            "HistoryBasicData": [
                {"FieldName": "Situação", "OldValue": "NULA", "NewValue": "ATIVA", "ChangeDate": "2020-05-01"}
            ]
        }]
    }
    timeline = construir_timeline_cnpj(payload_mock)
    assert len(timeline) == 2
    assert timeline[0]["data"] <= timeline[1]["data"]
