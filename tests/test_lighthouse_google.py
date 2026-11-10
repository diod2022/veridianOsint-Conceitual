import pytest
import respx
import httpx
from src.providers import lighthouse
from src.core import auth
from src.app import mcp
import src.tools.redes_sociais_tools  # noqa: F401


@pytest.fixture(autouse=True)
def isolar_ambiente(tmp_path, monkeypatch):
    cache_dir = str(tmp_path / "cache")
    monkeypatch.setattr("src.core.config.CACHE_DIR", cache_dir)
    monkeypatch.setattr("src.core.cache.CACHE_DIR", cache_dir)
    monkeypatch.setenv("LIGHTHOUSE_API_KEY", "lpr_test_key_123")
    monkeypatch.setattr("asyncio.sleep", lambda *_: _noop())


async def _noop():
    return None


@pytest.mark.asyncio
async def test_google_email_info_e_cache():
    with respx.mock(assert_all_called=True) as mock_http:
        post_route = mock_http.post("https://api.lighthouse.lampyre.io/api/1.0/tasks/email_google_v1").mock(
            return_value=httpx.Response(201, json={"task_id": "task-email-1", "job_name": "email_google_v1"})
        )
        get_route = mock_http.get(
            "https://api.lighthouse.lampyre.io/api/1.0/tasks/email_google_v1/task-email-1?token=lpr_test_key_123"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "task_status": 0,
                    "result": {
                        "result": [
                            {
                                "input": {"email": "alvo@gmail.com"},
                                "output": [
                                    {
                                        "google_profile_uid": "114547400629082890034",
                                        "fullname": "João Alvo",
                                        "avatar_url": "https://lh3.googleusercontent.com/a/avatar",
                                        "avatar_fileid": "file_abc",
                                        "updated": 1700000000,
                                        "url": "https://plus.google.com/114547400629082890034"
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        )

        res1 = await lighthouse.google_email_info("Alvo@Gmail.com ")
        assert res1["status"] == "sucesso"
        assert res1["encontrado"] is True
        assert res1["google_profile_uid"] == "114547400629082890034"
        assert res1["nome_completo"] == "João Alvo"
        assert res1["do_cache"] is False
        assert post_route.call_count == 1
        assert get_route.call_count == 1

        # Segunda chamada deve vir do cache sem nova requisição HTTP
        res2 = await lighthouse.google_email_info("alvo@gmail.com")
        assert res2["do_cache"] is True
        assert res2["google_profile_uid"] == "114547400629082890034"
        assert post_route.call_count == 1


@pytest.mark.asyncio
async def test_google_maps_por_email_fluxo_completo():
    with respx.mock(assert_all_called=True) as mock_http:
        mock_http.post("https://api.lighthouse.lampyre.io/api/1.0/tasks/email_google_v1").mock(
            return_value=httpx.Response(201, json={"task_id": "t-email", "job_name": "email_google_v1"})
        )
        mock_http.get(
            "https://api.lighthouse.lampyre.io/api/1.0/tasks/email_google_v1/t-email?token=lpr_test_key_123"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "task_status": 0,
                    "result": {
                        "result": [
                            {
                                "input": {"email": "viajante@gmail.com"},
                                "output": [
                                    {
                                        "google_profile_uid": "114547400629082890034",
                                        "fullname": "Maria Viajante",
                                        "avatar_url": "https://lh3.googleusercontent.com/a/maria"
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        )

        mock_http.post("https://api.lighthouse.lampyre.io/api/1.0/tasks/uid_google_maps_v1").mock(
            return_value=httpx.Response(201, json={"task_id": "t-maps", "job_name": "uid_google_maps_v1"})
        )
        mock_http.get(
            "https://api.lighthouse.lampyre.io/api/1.0/tasks/uid_google_maps_v1/t-maps?token=lpr_test_key_123"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "task_status": 0,
                    "result": {
                        "result": [
                            {
                                "input": {"google_profile_uid": "114547400629082890034"},
                                "output": [
                                    {
                                        "fullname": "Maria Viajante",
                                        "google_maps_profile_url": "https://www.google.com/maps/contrib/114547400629082890034",
                                        "counters_table": {"reviews": 1},
                                        "places": [
                                            {
                                                "place_id": "ChIJ_teste",
                                                "title": "Café Central",
                                                "address": "Av. Paulista, 1000 - São Paulo",
                                                "latitude": -23.564,
                                                "longitude": -46.652,
                                                "rating": "5",
                                                "feedback": "Excelente atendimento!",
                                                "string_date": "10/25"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        )

        res = await lighthouse.google_maps_por_email("viajante@gmail.com")
        assert res["status"] == "sucesso"
        assert res["encontrado"] is True
        assert res["google_profile_uid"] == "114547400629082890034"
        assert res["total_locais_avaliados"] == 1
        assert res["locais_avaliados"][0]["title"] == "Café Central"
        assert res["locais_avaliados"][0]["feedback"] == "Excelente atendimento!"


@pytest.mark.asyncio
async def test_whitelabel_google_lighthouse_tools():
    assert auth.obter_nome_whitelabel("lighthouse_google_email_info") == "veridian_google_conta_por_email"
    assert auth.obter_nome_whitelabel("lighthouse_google_maps_reviews") == "veridian_google_maps_reviews_por_id"
    assert auth.obter_nome_whitelabel("lighthouse_google_maps_photos") == "veridian_google_maps_fotos_por_id"
    assert auth.obter_nome_whitelabel("lighthouse_google_maps_por_email") == "veridian_google_maps_reviews_por_email"

    tools = await mcp.list_tools()
    nomes = {t.name for t in tools}
    assert "veridian_google_conta_por_email" in nomes
    assert "veridian_google_maps_reviews_por_id" in nomes
    assert "veridian_google_maps_fotos_por_id" in nomes
    assert "veridian_google_maps_reviews_por_email" in nomes
