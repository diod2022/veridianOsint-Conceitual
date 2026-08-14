"""
Testes automatizados para o sistema de cache e segurança
"""
import pytest
import os
import json
from src.core.security import normalizar_cpf, normalizar_cnpj, normalizar_telefone, normalizar_email, normalizar_oab, eh_caminho_seguro
from src.core.cache import obter_caminho_cache_seguro, obter_caminho_cache_seguro_ext, salvar_cache_universal, checar_cache_universal

def test_normalizacoes():
    assert normalizar_cpf("123.456.789-00") == "12345678900"
    assert normalizar_cpf(12345678900) == "12345678900"
    assert normalizar_cnpj("12.345.678/0001-90") == "12345678000190"
    assert normalizar_telefone(completo="+55 11 98888-7777") == "11988887777"
    assert normalizar_email("  User.Test+tag@Domain.COM  ") == "user.test+tag@domain.com"
    
    # OAB normalization
    num, uf = normalizar_oab("7008/MS")
    assert num == "7008" and uf == "MS"
    num, uf = normalizar_oab("OAB/SP 123456")
    assert num == "123456" and uf == "SP"

def test_seguranca_path_traversal():
    assert eh_caminho_seguro("valid_cache_id") is True
    assert eh_caminho_seguro("../secret_file") is False
    assert eh_caminho_seguro("..\\secret_file") is False
    assert eh_caminho_seguro("/etc/passwd") is False
    assert eh_caminho_seguro("folder/file") is False

def test_cache_universal(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.config.CACHE_DIR", str(tmp_path))
    monkeypatch.setattr("src.core.cache.CACHE_DIR", str(tmp_path))
    
    dados = {"teste": "ok", "valor": 123}
    salvo = salvar_cache_universal("unit_test_key", dados)
    assert salvo["status"] == "sucesso"
    assert salvo["cache_id"] == "unit_test_key"
    
    recuperado = checar_cache_universal("unit_test_key")
    assert recuperado["status"] == "sucesso"
    assert checar_cache_universal("chave_inexistente") is None
