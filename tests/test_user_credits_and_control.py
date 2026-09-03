import pytest
import asyncio
import time
from src.core.db import (
    salvar_usuario_db,
    obter_usuario_db,
    deletar_usuario_db,
    adicionar_creditos_atomico,
    debitar_credito_atomico,
    alternar_status_consultas,
    alternar_perfil_usuario,
    obter_extrato_usuario
)
from src.core.auth import (
    detectar_tipo_e_custo_operacao,
    validar_e_debitar_execucao,
    usuario_corrente,
    token_corrente,
    carregar_chaves_autorizadas
)

@pytest.fixture(autouse=True)
def setup_auth():
    carregar_chaves_autorizadas()

def test_detectar_tipo_e_custo_operacao():
    """Testa a diferenciação determinística entre consulta inicial e paginação."""
    # Consulta inicial simples
    tipo, custo, _ = detectar_tipo_e_custo_operacao("veridian_consultar_cpf", {"cpf": "12345678900"})
    assert tipo == "consumo_consulta"
    assert custo == 1

    # Consulta com page=1 ainda é inicial
    tipo, custo, _ = detectar_tipo_e_custo_operacao("veridian_buscar_posts", {"search": "alvo", "page": 1})
    assert tipo == "consumo_consulta"
    assert custo == 1

    # Consulta com page=2 é paginação
    tipo, custo, detalhe = detectar_tipo_e_custo_operacao("veridian_buscar_posts", {"search": "alvo", "page": 2})
    assert tipo == "consumo_paginacao"
    assert custo == 1
    assert "página 2" in detalhe

    # Consulta com cursor/end_cursor/page_id é paginação
    tipo, custo, _ = detectar_tipo_e_custo_operacao("veridian_ver_posts", {"user_id": "123", "page_id": "cursor_xyz"})
    assert tipo == "consumo_paginacao"
    assert custo == 1

    tipo, custo, _ = detectar_tipo_e_custo_operacao("veridian_ver_seguidores", {"user_id": "123", "end_cursor": "cursor_end"})
    assert tipo == "consumo_paginacao"
    assert custo == 1

def test_atomic_credits_and_insufficient_balance():
    """Testa criação de usuário, recarga, débitos até esgotamento e bloqueio por saldo insuficiente."""
    usr = "test_user_cred_flow"
    tok = "mcp_key_test_cred_flow_123"
    deletar_usuario_db(usr)

    salvo = salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 3,
        "consultas_habilitadas": True
    })
    assert salvo is True

    u = obter_usuario_db(usr)
    assert u["saldo_creditos"] == 3
    assert u["tipo_perfil"] == "creditos"
    assert u["consultas_habilitadas"] is True

    # Débito 1
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf", "Busca 1")
    assert ok is True
    assert saldo == 2

    # Débito 2 (Paginação)
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_paginacao", "tool_cpf", "Página 2")
    assert ok is True
    assert saldo == 1

    # Débito 3
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf", "Busca 3")
    assert ok is True
    assert saldo == 0

    # Débito 4 (Deve falhar: saldo insuficiente)
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf", "Busca 4")
    assert ok is False
    assert "Saldo insuficiente" in msg
    assert saldo == 0

    # Recarga pelo admin
    rec_ok, rec_msg, novo_saldo = adicionar_creditos_atomico(usr, 50, "Recarga de teste", "admin")
    assert rec_ok is True
    assert novo_saldo == 50

    u_after = obter_usuario_db(usr)
    assert u_after["saldo_creditos"] == 50
    assert u_after["total_consultas"] == 2
    assert u_after["total_paginacoes"] == 1

    deletar_usuario_db(usr)

@pytest.mark.asyncio
async def test_concurrency_anti_double_spending():
    """
    STRESS TEST: Simula 20 requisições simultâneas assíncronas com saldo de apenas 3 créditos.
    Garante que exatamente 3 operações passem e 17 sejam rejeitadas, com saldo final exatamente 0.
    """
    usr = "test_user_concurrency"
    tok = "mcp_key_test_concurrency_999"
    deletar_usuario_db(usr)

    salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 3,
        "consultas_habilitadas": True
    })

    async def tentar_debito(idx):
        # Pequeno delay concorrente para acentuar a disputa
        await asyncio.sleep(0.005)
        return debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf", f"Chamada concorrente #{idx}")

    tasks = [tentar_debito(i) for i in range(20)]
    resultados = await asyncio.gather(*tasks)

    sucessos = [r for r in resultados if r[0] is True]
    falhas = [r for r in resultados if r[0] is False]

    assert len(sucessos) == 3, f"Esperado exatamente 3 sucessos, obteve {len(sucessos)}"
    assert len(falhas) == 17, f"Esperado 17 falhas, obteve {len(falhas)}"

    u_final = obter_usuario_db(usr)
    assert u_final["saldo_creditos"] == 0, f"Saldo deveria ser 0, mas foi {u_final['saldo_creditos']}"
    assert u_final["total_consultas"] == 3

    deletar_usuario_db(usr)

def test_toggle_queries_enabled():
    """Testa a suspensão e reativação de consultas para um usuário."""
    usr = "test_user_toggle"
    tok = "mcp_key_test_toggle_777"
    deletar_usuario_db(usr)

    salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 100,
        "consultas_habilitadas": True
    })

    # Desabilita consultas
    ok = alternar_status_consultas(usr, False)
    assert ok is True
    u = obter_usuario_db(usr)
    assert u["consultas_habilitadas"] is False

    # Tentativa de debitar/consultar deve ser barrada imediatamente
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf")
    assert ok is False
    assert "Consultas desabilitadas" in msg
    assert saldo == 100  # Saldo não foi tocado

    # Reabilita consultas
    ok = alternar_status_consultas(usr, True)
    assert ok is True
    ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_cpf")
    assert ok is True
    assert saldo == 99

    deletar_usuario_db(usr)

def test_unlimited_profile():
    """Testa o perfil ilimitado (sem limite de créditos)."""
    usr = "test_user_unlimited"
    tok = "mcp_key_test_unlimited_555"
    deletar_usuario_db(usr)

    salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "ilimitado",
        "saldo_creditos": 0,
        "consultas_habilitadas": True
    })

    # Executa 5 consultas
    for i in range(5):
        ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_social", f"Consulta {i}")
        assert ok is True
        assert saldo == 0

    # Executa 3 paginações
    for i in range(3):
        ok, msg, saldo = debitar_credito_atomico(usr, 1, "consumo_paginacao", "tool_social", f"Página {i}")
        assert ok is True
        assert saldo == 0

    u = obter_usuario_db(usr)
    assert u["saldo_creditos"] == 0
    assert u["total_consultas"] == 5
    assert u["total_paginacoes"] == 3

    # Alterna para perfil de créditos
    alternar_perfil_usuario(usr, "creditos")
    u_switch = obter_usuario_db(usr)
    assert u_switch["tipo_perfil"] == "creditos"

    # Agora com perfil de créditos e saldo 0, deve falhar
    ok, msg, _ = debitar_credito_atomico(usr, 1, "consumo_consulta", "tool_social")
    assert ok is False
    assert "Saldo insuficiente" in msg

    deletar_usuario_db(usr)

def test_admin_protection():
    """Garante que o usuário admin permaneça sempre ilimitado, habilitado e imune a exclusão."""
    u_admin = obter_usuario_db("admin")
    assert u_admin is not None
    assert u_admin["tipo_perfil"] == "ilimitado"
    assert u_admin["consultas_habilitadas"] is True

    # Tentativa de desabilitar admin deve ser ignorada
    alternar_status_consultas("admin", False)
    u_admin_after = obter_usuario_db("admin")
    assert u_admin_after["consultas_habilitadas"] is True

    # Tentativa de mudar perfil do admin deve ser ignorada
    alternar_perfil_usuario("admin", "creditos")
    u_admin_after2 = obter_usuario_db("admin")
    assert u_admin_after2["tipo_perfil"] == "ilimitado"

    # Tentativa de deletar admin deve ser recusada
    removido = deletar_usuario_db("admin")
    assert removido is None
    assert obter_usuario_db("admin") is not None

def test_ledger_audit_trail():
    """Testa a integridade da trilha de auditoria (Ledger de Créditos)."""
    usr = "test_user_ledger"
    tok = "mcp_key_test_ledger_333"
    deletar_usuario_db(usr)

    salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 0,
        "consultas_habilitadas": True
    })

    # Recarga
    adicionar_creditos_atomico(usr, 20, "Compra Pacote Básico", "admin")
    # Consulta
    debitar_credito_atomico(usr, 1, "consumo_consulta", "veridian_consultar_cadastro_cpf", "Busca inicial de CPF")
    # Paginação
    debitar_credito_atomico(usr, 1, "consumo_paginacao", "veridian_ver_posts_instagram", "Página 2 de posts")

    extrato = obter_extrato_usuario(usr, limit=10)
    assert len(extrato) >= 3

    # As transações vêm em ordem decrescente (mais recente primeiro)
    tx_pag = extrato[0]
    assert tx_pag["tipo"] == "consumo_paginacao"
    assert tx_pag["quantidade"] == -1
    assert tx_pag["saldo_anterior"] == 19
    assert tx_pag["saldo_posterior"] == 18

    tx_cons = extrato[1]
    assert tx_cons["tipo"] == "consumo_consulta"
    assert tx_cons["quantidade"] == -1
    assert tx_cons["saldo_anterior"] == 20
    assert tx_cons["saldo_posterior"] == 19

    tx_rec = extrato[2]
    assert tx_rec["tipo"] == "recarga_admin"
    assert tx_rec["quantidade"] == 20
    assert tx_rec["saldo_anterior"] == 0
    assert tx_rec["saldo_posterior"] == 20

    deletar_usuario_db(usr)

def test_validar_e_debitar_execucao_com_contextvar():
    """Testa a integração de alto nível do contextvar com validar_e_debitar_execucao."""
    usr = "test_user_ctx"
    tok = "mcp_key_test_ctx_111"
    deletar_usuario_db(usr)

    salvar_usuario_db({
        "usuario": usr,
        "token": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 2,
        "consultas_habilitadas": True
    })

    usr_info = {
        "usuario": usr,
        "token": tok,
        "key": tok,
        "tipo_perfil": "creditos",
        "saldo_creditos": 2,
        "consultas_habilitadas": True,
        "permissoes": ["*"]
    }
    usuario_corrente.set(usr_info)
    token_corrente.set(tok)

    # 1. Primeira consulta (deve passar)
    bloqueio, tx = validar_e_debitar_execucao("veridian_consultar_cadastro_cpf", {"cpf": "11122233344"})
    assert bloqueio is None
    assert tx["saldo_posterior"] == 1

    # 2. Paginação (deve passar)
    bloqueio, tx = validar_e_debitar_execucao("veridian_buscar_posts_linkedin", {"search": "teste", "page": 2})
    assert bloqueio is None
    assert tx["saldo_posterior"] == 0

    # 3. Próxima consulta (deve ser bloqueada)
    bloqueio, tx = validar_e_debitar_execucao("veridian_consultar_cadastro_cpf", {"cpf": "11122233344"})
    assert bloqueio is not None
    assert bloqueio["code"] == "INSUFFICIENT_CREDITS"
    assert tx is None

    deletar_usuario_db(usr)
