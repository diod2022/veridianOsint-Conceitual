import pytest
import os
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from src.core.config import ADMIN_HTML_PATH
from src.admin.routes import (
    admin_api_status,
    admin_api_keys_add,
    admin_api_keys_delete,
    admin_api_users_credits,
    admin_api_users_toggle_query,
    admin_api_users_profile,
    admin_api_users_statement,
    serve_admin_page
)
from src.core.auth import carregar_chaves_autorizadas

ADMIN_KEY = "mcp_admin_key_teste_secreto_9999"

@pytest.fixture(scope="module")
def client():
    carregar_chaves_autorizadas()
    app = Starlette(
        routes=[
            Route("/admin/api/status", endpoint=admin_api_status, methods=["GET"]),
            Route("/admin/api/keys", endpoint=admin_api_keys_add, methods=["POST"]),
            Route("/admin/api/keys", endpoint=admin_api_keys_delete, methods=["DELETE"]),
            Route("/admin/api/users/credits", endpoint=admin_api_users_credits, methods=["POST"]),
            Route("/admin/api/users/toggle_query", endpoint=admin_api_users_toggle_query, methods=["POST"]),
            Route("/admin/api/users/profile", endpoint=admin_api_users_profile, methods=["POST"]),
            Route("/admin/api/users/statement", endpoint=admin_api_users_statement, methods=["GET"]),
            Mount("/admin", app=serve_admin_page),
        ]
    )
    return TestClient(app)

def test_admin_html_ui_components(client):
    """Valida se o HTML servido contém todos os recursos visuais de interface (UI) exigidos."""
    resp = client.get("/admin/")
    assert resp.status_code == 200
    html = resp.text

    # 1. Validação dos cabeçalhos da Tabela de Usuários
    assert "<th>Usuário</th>" in html
    assert "<th>Chave de Acesso</th>" in html
    assert "<th>Perfil</th>" in html
    assert "<th>Saldo</th>" in html
    assert "<th>Consultas</th>" in html
    assert "<th>Atividade</th>" in html
    assert "<th>Permissões</th>" in html
    assert "Ações</th>" in html
    assert 'id="userTableBody"' in html

    # 2. Validação do Modal de Novo Usuário com novos controles
    assert 'id="addModal"' in html
    assert 'id="newUserProfile"' in html
    assert 'value="creditos"' in html
    assert 'value="ilimitado"' in html
    assert 'id="newUserCredits"' in html
    assert 'id="newUserEnabled"' in html

    # 3. Validação do Modal de Recarga de Créditos
    assert 'id="creditsModal"' in html
    assert 'id="creditsTargetUser"' in html
    assert 'id="creditsCurrentBalance"' in html
    assert 'id="creditsAmount"' in html
    assert 'id="creditsReason"' in html
    assert 'id="saveCreditsBtn"' in html

    # 4. Validação do Modal de Extrato e Auditoria (Ledger)
    assert 'id="statementModal"' in html
    assert 'id="statementTargetUser"' in html
    assert 'id="statementTableBody"' in html
    assert "Saldo Resultante" in html
    assert "Descrição / Justificativa" in html

    # 5. Validação das funções de interação no JavaScript da UI
    assert "function renderizarTabelaUsuarios(" in html
    assert "function abrirModalCreditos(" in html
    assert "function abrirModalExtrato(" in html
    assert "function alternarStatusConsulta(" in html
    assert "function alternarPerfil(" in html
    assert "btn-toggle-query" in html
    assert "btn-action-credits" in html
    assert "btn-action-statement" in html

def test_admin_ui_api_flow(client):
    """Valida o fluxo interativo completo consumido pela interface administrativa."""
    headers = {"X-Admin-Key": ADMIN_KEY}

    # 1. Carregamento do Painel (Status)
    status_res = client.get("/admin/api/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "chaves" in status_data
    assert "admin" in [u["usuario"] for u in status_data["chaves"].values()]

    # 2. Criação de Usuário com perfil de créditos e consultas habilitadas
    novo_usr = "agente_ui_test"
    create_res = client.post(
        "/admin/api/keys",
        headers=headers,
        json={
            "usuario": novo_usr,
            "tipo_perfil": "creditos",
            "saldo_creditos": 120,
            "consultas_habilitadas": True,
            "permissoes": ["*"]
        }
    )
    assert create_res.status_code == 200
    user_created = create_res.json()
    assert user_created["usuario"] == novo_usr
    assert user_created["tipo_perfil"] == "creditos"
    assert user_created["saldo_creditos"] == 120
    token_usr = user_created["token"]

    # 3. Recarga de Créditos (Modal de Recarga da UI)
    recarga_res = client.post(
        "/admin/api/users/credits",
        headers=headers,
        json={
            "usuario": novo_usr,
            "quantidade": 80,
            "motivo": "Recarga de teste UI"
        }
    )
    assert recarga_res.status_code == 200
    recarga_data = recarga_res.json()
    assert recarga_data["saldo_atual"] == 200  # 120 + 80 = 200

    # 4. Alternância de Status de Consultas (Toggle da UI: Ativo -> Suspenso)
    toggle_res = client.post(
        "/admin/api/users/toggle_query",
        headers=headers,
        json={"usuario": novo_usr, "habilitado": False}
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["consultas_habilitadas"] is False

    # Reabilita consultas
    toggle_res2 = client.post(
        "/admin/api/users/toggle_query",
        headers=headers,
        json={"usuario": novo_usr, "habilitado": True}
    )
    assert toggle_res2.status_code == 200
    assert toggle_res2.json()["consultas_habilitadas"] is True

    # 5. Alternância de Perfil (Botão Perfil da UI: Créditos -> Ilimitado)
    profile_res = client.post(
        "/admin/api/users/profile",
        headers=headers,
        json={"usuario": novo_usr, "tipo_perfil": "ilimitado"}
    )
    assert profile_res.status_code == 200
    assert profile_res.json()["tipo_perfil"] == "ilimitado"

    # 6. Consulta do Extrato (Modal de Extrato da UI)
    statement_res = client.get(
        f"/admin/api/users/statement?usuario={novo_usr}",
        headers=headers
    )
    assert statement_res.status_code == 200
    extrato_data = statement_res.json()
    assert "extrato" in extrato_data
    assert len(extrato_data["extrato"]) >= 2  # Criação inicial + recarga de 80

    # 7. Remoção do Usuário
    delete_res = client.request(
        "DELETE",
        "/admin/api/keys",
        headers=headers,
        json={"token": token_usr}
    )
    assert delete_res.status_code == 200
