import json
import pytest
import httpx
import respx

from src.app import mcp
import src.tools
from src.core.auth import (
    obter_nome_whitelabel,
    limpar_descricao_whitelabel,
    limpar_resultado_whitelabel,
)
from src.providers import ekycpro


@pytest.fixture(autouse=True)
def isolar_ambiente_e_cache(tmp_path, monkeypatch):
    """Isola CACHE_DIR e variáveis de ambiente da eKYC Pro em todos os testes."""
    cache_dir = str(tmp_path / "cache_ekyc")
    monkeypatch.setattr("src.core.cache.CACHE_DIR", cache_dir)
    monkeypatch.setattr("src.core.config.CACHE_DIR", cache_dir)
    monkeypatch.setenv("EKYCPRO_API_KEY", "test_ekyc_secret_key")
    monkeypatch.setenv("EKYCPRO_BASE_URL", "https://api.ekycpro.com")
    monkeypatch.setenv(
        "EKYCPRO_COMBO_TELEFONE",
        "ws,ws_avatar,ws_business,instagram,facebook,telegram,threads,twitter,viber",
    )
    monkeypatch.setenv(
        "EKYCPRO_COMBO_EMAIL",
        "instagram_email,facebook_email,twitter_email,twitter_profile,email_avatar",
    )


# ==============================================================================
# 1. NORMALIZAÇÃO DE TELEFONE E E-MAIL
# ==============================================================================

@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("11999998888", "+5511999998888"),
        ("(11) 99999-8888", "+5511999998888"),
        ("011999998888", "+5511999998888"),
        ("+55 11 99999-8888", "+5511999998888"),
        ("5511999998888", "+5511999998888"),
        ("+351912345678", "+351912345678"),
        ("00351912345678", "+351912345678"),
    ],
)
def test_normalizacao_telefone_valida(entrada, esperado):
    assert ekycpro.normalizar_telefone_e164(entrada) == esperado


@pytest.mark.parametrize("invalido", ["123", "", "abc", "+1234567", "12345678901234567"])
@pytest.mark.asyncio
async def test_normalizacao_telefone_invalida(invalido):
    with pytest.raises(ValueError):
        ekycpro.normalizar_telefone_e164(invalido)

    with respx.mock(assert_all_called=False) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check/combo/phone")
        res = await ekycpro.verificar_telefone(invalido)
        assert "error" in res
        assert not rota.called


def test_normalizacao_email():
    assert ekycpro.normalizar_email_ekyc("  Alvo.Teste@Exemplo.COM  ") == "alvo.teste@exemplo.com"
    with pytest.raises(ValueError):
        ekycpro.normalizar_email_ekyc("email_invalido_sem_arroba")
    with pytest.raises(ValueError):
        ekycpro.normalizar_email_ekyc("com espaco@exemplo.com")


# ==============================================================================
# 2. LOTE DE TELEFONE, HIGIENE DE SAÍDA E CACHE
# ==============================================================================

@pytest.mark.asyncio
async def test_lote_telefone_completo_e_cache():
    resposta_api = {
        "success": True,
        "transactionId": "cmb_secret_12345",
        "pricingStrategy": "PAY",
        "data": {
            "id": "cmb_secret_12345",
            "identifier": "+5511999998888",
            "results": {
                "ws": {"registered": True, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "ws_avatar": {
                    "registered": True,
                    "avatar": True,
                    "avatar_url": "https://cdn.exemplo.com/foto.jpg",
                    "billed": True,
                    "cost": 8000,
                    "cost_usd": 0.008,
                },
                "ws_business": {
                    "registered": True,
                    "business": False,
                    "billed": True,
                    "cost": 5000,
                    "cost_usd": 0.005,
                },
                "instagram": {"registered": True, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "facebook": {"registered": False, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "telegram": {
                    "registered": False,
                    "banned": True,
                    "billed": True,
                    "cost": 5000,
                    "cost_usd": 0.005,
                },
                "threads": {"registered": False, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "twitter": {"registered": False, "billed": True, "cost": 4000, "cost_usd": 0.004},
                "viber": {
                    "registered": None,
                    "error": "NOT_FOUND",
                    "billed": True,
                    "cost": 5000,
                    "cost_usd": 0.005,
                },
            },
            "billed_count": 9,
            "total_cost": 47000,
            "total_cost_usd": 0.047,
        },
    }

    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check/combo/phone").mock(
            return_value=httpx.Response(200, json=resposta_api)
        )

        # 1ª chamada: deve bater na API
        res1 = await ekycpro.verificar_telefone("(11) 99999-8888")
        assert rota.call_count == 1

        req = rota.calls[0].request
        assert req.headers.get("X-API-Key") == "test_ekyc_secret_key"
        corpo_enviado = json.loads(req.content.decode("utf-8"))
        assert corpo_enviado["identifier"] == "+5511999998888"
        assert corpo_enviado["service_types"] == [
            "ws",
            "ws_avatar",
            "ws_business",
            "instagram",
            "facebook",
            "telegram",
            "threads",
            "twitter",
            "viber",
        ]

        assert res1["identificador"] == "+5511999998888"
        assert res1["em_cache"] is False
        assert res1["cache_id"].startswith("presenca_")
        assert "ekyc" not in res1["cache_id"].lower()

        # Verifica extras renomeados e dados
        plat_map = {p["servico"]: p for p in res1["plataformas"]}
        assert plat_map["ws"]["status"] == "cadastrado"
        assert plat_map["ws_avatar"]["possui_foto_perfil"] is True
        assert plat_map["ws_avatar"]["foto_perfil_url"] == "https://cdn.exemplo.com/foto.jpg"
        assert plat_map["ws_business"]["conta_business"] is False
        assert plat_map["facebook"]["status"] == "nao_cadastrado"
        assert plat_map["viber"]["status"] == "sem_registro"
        assert plat_map["telegram"]["status"] == "nao_cadastrado"
        assert plat_map["telegram"]["dados"]["banned"] is True

        # Verifica resumo
        resumo = res1["resumo"]
        assert set(resumo["cadastrado"]) == {"ws", "ws_avatar", "ws_business", "instagram"}
        assert set(resumo["nao_cadastrado"]) == {"facebook", "telegram", "threads", "twitter"}
        assert resumo["sem_registro"] == ["viber"]
        assert "sem_registro" in resumo["observacao"]

        # Verifica ausência total de custos, IDs e nome do fornecedor
        texto_saida = json.dumps(res1)
        for proibido in ("cost", "cost_usd", "billed", "transactionId", "cmb_secret_12345", "ekyc"):
            assert proibido not in texto_saida.lower()

        # 2ª chamada: deve vir integralmente do cache sem nova requisição HTTP
        res2 = await ekycpro.verificar_telefone("11999998888")
        assert rota.call_count == 1
        assert res2["em_cache"] is True
        assert len(res2["plataformas"]) == 9


# ==============================================================================
# 3. TIMEOUT NO LOTE -> RECONSULTA EM /v1/check E NÃO CACHEIA INDETERMINADO
# ==============================================================================

@pytest.mark.asyncio
async def test_timeout_no_lote_reconsulta_e_nao_salva_cache_se_indeterminado():
    lote_payload = {
        "success": True,
        "data": {
            "id": "cmb_timeout_1",
            "identifier": "+5511999998888",
            "results": {
                "ws": {"registered": True, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "instagram": {"registered": None, "error": "timeout", "billed": False, "cost": 0, "cost_usd": 0},
                "telegram": {"registered": None, "error": "timeout", "billed": False, "cost": 0, "cost_usd": 0},
            },
        },
    }

    def check_side_effect(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        if body["service_type"] == "instagram":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "id": "chk_ig_1",
                        "identifier": "+5511999998888",
                        "registered": True,
                        "billed": True,
                        "cost": 5000,
                        "cost_usd": 0.005,
                    },
                },
            )
        # telegram continua com timeout na reconsulta
        return httpx.Response(
            200,
            json={
                "success": False,
                "error": "timeout",
                "pricingStrategy": "FREE",
                "data": {"registered": None, "billed": False, "cost": 0, "cost_usd": 0},
            },
        )

    with respx.mock(assert_all_called=True) as mock_http:
        rota_lote = mock_http.post("https://api.ekycpro.com/v1/check/combo/phone").mock(
            return_value=httpx.Response(200, json=lote_payload)
        )
        rota_check = mock_http.post("https://api.ekycpro.com/v1/check").mock(side_effect=check_side_effect)

        res = await ekycpro.verificar_telefone("11999998888", servicos=["whatsapp", "instagram", "telegram"])
        assert rota_lote.call_count == 1
        assert rota_check.call_count == 2

        plat_map = {p["servico"]: p for p in res["plataformas"]}
        assert plat_map["ws"]["status"] == "cadastrado"
        assert plat_map["instagram"]["status"] == "cadastrado"
        assert plat_map["telegram"]["status"] == "indeterminado_timeout"

        # Como telegram ficou indeterminado_timeout, o resultado NÃO pode ir para o cache
        assert "cache_id" not in res
        res_segunda = await ekycpro.verificar_telefone("11999998888", servicos=["ws", "instagram", "telegram"])
        assert rota_lote.call_count == 2
        assert res_segunda["em_cache"] is False


# ==============================================================================
# 4. ERROS HTTP 400, 401, 402 E AUSÊNCIA DE API KEY
# ==============================================================================

@pytest.mark.parametrize("status_code", [400, 401, 402])
@pytest.mark.asyncio
async def test_erros_http_400_401_402(status_code):
    with respx.mock(assert_all_called=True) as mock_http:
        mock_http.post("https://api.ekycpro.com/v1/check/combo/phone").mock(
            return_value=httpx.Response(status_code, json={"success": False, "error": "API error"})
        )
        res = await ekycpro.verificar_telefone("11999998888", servicos=["ws"])
        assert "error" in res
        assert res["http_status"] == status_code
        assert "ekyc" not in res["error"].lower()


@pytest.mark.asyncio
async def test_sem_api_key_nao_faz_chamada_http(monkeypatch):
    monkeypatch.setenv("EKYCPRO_API_KEY", "")
    monkeypatch.setattr("src.core.config.EKYCPRO_API_KEY", "")

    with respx.mock(assert_all_called=False) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check/combo/phone")
        res = await ekycpro.verificar_telefone("11999998888")
        assert "error" in res
        assert "EKYCPRO_API_KEY" in res["error"]
        assert not rota.called


# ==============================================================================
# 5. E-MAIL, PACOTE DO .ENV, NOT_FOUND -> SEM_REGISTRO, TWITTER_PROFILE E ALIASES
# ==============================================================================

@pytest.mark.asyncio
async def test_lote_email_padrao_env_not_found_e_twitter_profile(monkeypatch):
    monkeypatch.setenv("EKYCPRO_COMBO_EMAIL", "instagram_email,twitter_profile,email_avatar")

    resposta_email = {
        "success": True,
        "data": {
            "id": "cmb_email_1",
            "identifier": "alvo@exemplo.com",
            "results": {
                "instagram_email": {"registered": True, "billed": True, "cost": 5000, "cost_usd": 0.005},
                "twitter_profile": {
                    "registered": None,
                    "error": "NOT_FOUND",
                    "billed": True,
                    "cost": 5000,
                    "cost_usd": 0.005,
                },
                "email_avatar": {
                    "registered": False,
                    "avatar": False,
                    "avatar_url": "",
                    "billed": True,
                    "cost": 5000,
                    "cost_usd": 0.005,
                },
            },
        },
    }

    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check/combo/email").mock(
            return_value=httpx.Response(200, json=resposta_email)
        )
        res = await ekycpro.verificar_email("  ALVO@Exemplo.com ")
        assert rota.call_count == 1
        enviado = json.loads(rota.calls[0].request.content.decode("utf-8"))
        assert enviado["identifier"] == "alvo@exemplo.com"
        assert enviado["service_types"] == ["instagram_email", "twitter_profile", "email_avatar"]

        plat_map = {p["servico"]: p for p in res["plataformas"]}
        assert plat_map["instagram_email"]["status"] == "cadastrado"
        assert plat_map["twitter_profile"]["status"] == "sem_registro"
        assert plat_map["email_avatar"]["status"] == "nao_cadastrado"
        assert plat_map["email_avatar"]["possui_foto_perfil"] is False


@pytest.mark.asyncio
async def test_perfil_twitter_por_email_campos_name_e_url_em_dados():
    resposta_twitter = {
        "success": True,
        "transactionId": "chk_tw_99",
        "pricingStrategy": "PAY",
        "data": {
            "id": "chk_tw_99",
            "identifier": "alvo@exemplo.com",
            "registered": True,
            "name": "Alvo Investigado",
            "url": "https://x.com/alvoinvestigado",
            "billed": True,
            "cost": 5000,
            "cost_usd": 0.005,
        },
    }

    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check").mock(
            return_value=httpx.Response(200, json=resposta_twitter)
        )
        res = await ekycpro.perfil_twitter_por_email("Alvo@Exemplo.com")
        assert rota.call_count == 1
        assert res["status"] == "cadastrado"
        assert res["dados"]["name"] == "Alvo Investigado"
        assert res["dados"]["url"] == "https://x.com/alvoinvestigado"
        assert "cost" not in json.dumps(res)


@pytest.mark.asyncio
async def test_aliases_e_servicos_incompativeis_ignorados():
    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check/combo/email").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "results": {
                            "instagram_email": {"registered": True},
                            "facebook_email": {"registered": False},
                            "twitter_email": {"registered": True},
                        }
                    },
                },
            )
        )
        res = await ekycpro.verificar_email(
            "alvo@exemplo.com",
            servicos=["instagram", "facebook", "x", "telegram", "ws"],
        )
        enviado = json.loads(rota.calls[0].request.content.decode("utf-8"))
        assert enviado["service_types"] == ["instagram_email", "facebook_email", "twitter_email"]
        assert set(res["servicos_ignorados"]) == {"telegram", "ws"}


@pytest.mark.asyncio
async def test_nao_repete_post_em_read_timeout():
    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check").mock(
            side_effect=httpx.ReadTimeout("Read timeout")
        )
        res = await ekycpro.verificar_servico("+5511999998888", "ws")
        assert rota.call_count == 1
        assert "error" in res
        assert res["http_status"] == 504


@pytest.mark.asyncio
async def test_repete_em_connect_error():
    contador = 0

    def connect_then_ok(request: httpx.Request) -> httpx.Response:
        nonlocal contador
        contador += 1
        if contador < 3:
            raise httpx.ConnectError("Connection refused")
        return httpx.Response(
            200,
            json={"success": True, "data": {"registered": True, "billed": True, "cost": 5000}},
        )

    with respx.mock(assert_all_called=True) as mock_http:
        rota = mock_http.post("https://api.ekycpro.com/v1/check").mock(side_effect=connect_then_ok)
        res = await ekycpro.verificar_servico("+5511999998888", "ws")
        assert rota.call_count == 3
        assert res["status"] == "cadastrado"


@pytest.mark.asyncio
async def test_fallback_twitter_profile_400_no_lote_email():
    chamadas_lote = []

    def combo_email_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        chamadas_lote.append(body["service_types"])
        if "twitter_profile" in body["service_types"]:
            return httpx.Response(400, json={"success": False, "error": "unsupported service in combo"})
        return httpx.Response(
            200,
            json={
                "success": True,
                "data": {
                    "results": {
                        "instagram_email": {"registered": True},
                    }
                },
            },
        )

    with respx.mock(assert_all_called=True) as mock_http:
        mock_http.post("https://api.ekycpro.com/v1/check/combo/email").mock(side_effect=combo_email_handler)
        mock_http.post("https://api.ekycpro.com/v1/check").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": {
                        "registered": True,
                        "name": "Twitter User",
                        "url": "https://x.com/twitteruser",
                    },
                },
            )
        )
        res = await ekycpro.verificar_email("alvo@exemplo.com", servicos=["instagram_email", "twitter_profile"])
        assert len(chamadas_lote) == 2
        plat_map = {p["servico"]: p for p in res["plataformas"]}
        assert plat_map["instagram_email"]["status"] == "cadastrado"
        assert plat_map["twitter_profile"]["status"] == "cadastrado"
        assert plat_map["twitter_profile"]["dados"]["url"] == "https://x.com/twitteruser"


@pytest.mark.asyncio
async def test_listar_servicos_e_consultar_saldo():
    with respx.mock(assert_all_called=True) as mock_http:
        mock_http.get("https://api.ekycpro.com/v1/services").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "services": [
                        {"type": "ws", "data_type": "phone", "enabled": True},
                        {"type": "instagram_email", "data_type": "email", "enabled": True},
                    ],
                },
            )
        )
        mock_http.get("https://api.ekycpro.com/v1/balance").mock(
            return_value=httpx.Response(200, json={"success": True, "balance_usd": 19.5})
        )

        lista = await ekycpro.listar_servicos()
        assert lista["total_plataformas"] >= 20
        assert "ws" in lista["pacote_padrao_telefone"]
        assert "instagram_email" in lista["pacote_padrao_email"]
        assert "ekyc" not in json.dumps(lista).lower()

        saldo = await ekycpro.consultar_saldo()
        assert saldo["balance_usd"] == 19.5


# ==============================================================================
# 6. WHITE-LABEL E REGISTRO DAS 5 TOOLS NO MCP
# ==============================================================================

def test_whitelabel_nomes_e_sanitizacao_ekycpro():
    assert obter_nome_whitelabel("ekycpro_verificar_telefone_plataformas") == "veridian_verificar_presenca_telefone"
    assert obter_nome_whitelabel("ekycpro_verificar_email_plataformas") == "veridian_verificar_presenca_email"
    assert obter_nome_whitelabel("ekycpro_perfil_twitter_por_email") == "veridian_perfil_twitter_por_email"
    assert obter_nome_whitelabel("ekycpro_verificar_servico") == "veridian_verificar_plataforma"
    assert obter_nome_whitelabel("ekycpro_listar_servicos") == "veridian_listar_plataformas_verificaveis"

    desc = "Integração com eKYC Pro, eKYCPro e EkycPro."
    desc_limpa = limpar_descricao_whitelabel(desc)
    assert "ekyc" not in desc_limpa.lower()
    assert "Veridian" in desc_limpa

    resultado_sujo = {"fornecedor": "eKYC Pro", "detalhe": "Retorno de EkycPro / eKYCPro"}
    resultado_limpo = limpar_resultado_whitelabel(resultado_sujo)
    assert "ekyc" not in json.dumps(resultado_limpo).lower()


@pytest.mark.asyncio
async def test_registro_5_tools_publicas_mcp():
    tools = await mcp.list_tools()
    nomes_tools = {t.name: t for t in tools}

    esperadas = [
        "veridian_verificar_presenca_telefone",
        "veridian_verificar_presenca_email",
        "veridian_perfil_twitter_por_email",
        "veridian_verificar_plataforma",
        "veridian_listar_plataformas_verificaveis",
    ]
    for nome in esperadas:
        assert nome in nomes_tools, f"Tool '{nome}' não encontrada entre as tools registradas"
        descricao = nomes_tools[nome].description or ""
        assert "ekyc" not in descricao.lower()
