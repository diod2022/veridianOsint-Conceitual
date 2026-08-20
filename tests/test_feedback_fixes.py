"""
Testes automatizados cobrindo as correções do feedback do Emil:
1. Resolução e atomicidade do cache.
2. Validação e normalização de CPF, CNPJ e CNJ (Módulo 97-10).
3. Proteção SSRF em URLs.
4. Merge incremental de datasets no BigDataCorp.
5. Consulta de processos por CNJ no Escavador.
6. Extração resiliente de PDF.
"""
import io
import os
import json
import pytest
import pypdf
from unittest.mock import patch, MagicMock
import httpx

from src.core.security import (
    validar_cpf,
    validar_cnpj,
    validar_cnj,
    normalizar_cnj,
    validar_url_segura_ssrf
)
from src.core.cache import (
    obter_caminho_cache_seguro,
    obter_caminho_cache_seguro_ext,
    salvar_cache_universal,
    checar_cache_universal
)
from src.tools.cache_tools import investigador_ler_cache
from src.providers import bigdatacorp, escavador, web_osint

def test_validacao_identificadores():
    """Valida funções matemáticas de CPF, CNPJ e CNJ."""
    # CPF
    assert validar_cpf("52998224725") is True
    assert validar_cpf("529.982.247-25") is True
    assert validar_cpf("11111111111") is False
    assert validar_cpf("123456") is False

    # CNPJ
    assert validar_cnpj("00000000000191") is True
    assert validar_cnpj("00.000.000/0001-91") is True
    assert validar_cnpj("11111111111111") is False

    # CNJ (Módulo 97-10)
    assert validar_cnj("1415618-82.2026.8.12.0000") is True
    assert validar_cnj("14156188220268120000") is True
    assert validar_cnj("1415618-83.2026.8.12.0000") is False

    cnj_fmt, cnj_raw = normalizar_cnj("14156188220268120000")
    assert cnj_fmt == "1415618-82.2026.8.12.0000"
    assert cnj_raw == "14156188220268120000"

def test_validacao_ssrf():
    """Valida bloqueio de SSRF para URLs locais, privadas e de metadados cloud."""
    assert validar_url_segura_ssrf("http://localhost:8000")[0] is False
    assert validar_url_segura_ssrf("http://127.0.0.1:8080/secret")[0] is False
    assert validar_url_segura_ssrf("http://169.254.169.254/latest/meta-data/")[0] is False
    assert validar_url_segura_ssrf("http://10.0.0.1/admin")[0] is False
    assert validar_url_segura_ssrf("http://192.168.1.1/config")[0] is False
    assert validar_url_segura_ssrf("ftp://example.com/file")[0] is False
    assert validar_url_segura_ssrf("https://www.google.com")[0] is True
    assert validar_url_segura_ssrf("https://tribunal.jus.br/documento.pdf")[0] is True

def test_resolucao_cache():
    """Valida que obter_caminho_cache_seguro resolve com e sem extensão .json."""
    caminho1 = obter_caminho_cache_seguro("teste_unitario_cache")
    caminho2 = obter_caminho_cache_seguro("teste_unitario_cache.json")
    
    assert caminho1 is not None
    assert caminho2 is not None
    assert caminho1 == caminho2
    assert caminho1.endswith("teste_unitario_cache.json")
    assert not caminho1.endswith(".json.json")

    # Salva e testa atomicidade
    dados_teste = {"status": "ok", "valor": 42}
    res_salvar = salvar_cache_universal("teste_unitario_cache", dados_teste)
    assert res_salvar["status"] == "sucesso"
    assert res_salvar["cache_id"] == "teste_unitario_cache"
    assert os.path.exists(caminho1)

@pytest.mark.asyncio
async def test_investigador_ler_cache_estruturado():
    """Valida que ler cache inexistente retorna erro estruturado em vez de texto bruto."""
    res = await investigador_ler_cache(cache_id="id_que_certamente_nao_existe_999")
    assert res.get("status") == "erro"
    assert res.get("codigo_erro") == "CACHE_NAO_ENCONTRADO"
    assert res.get("fornecedor") == "Veridian"

@pytest.mark.asyncio
async def test_bigdata_merge_incremental_datasets():
    """Valida que consultas subsequentes com novos datasets mesclam dados sem sobrescrever."""
    cpf_teste = "52998224725"
    cache_path = obter_caminho_cache_seguro(f"bigdata_{cpf_teste}")
    if cache_path and os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except Exception:
            pass
    
    # Mock da resposta de BasicData
    mock_resp_basic = {
        "Status": {"Code": 0, "Message": "OK"},
        "Result": [{"BasicData": {"Name": "Miguel Dau Teste", "TaxIdNumber": cpf_teste}}]
    }
    
    # Mock da resposta de ExtendedPhones
    mock_resp_phones = {
        "Status": {"Code": 0, "Message": "OK"},
        "Result": [{"ExtendedPhones": [{"AreaCode": "11", "Number": "988887777"}]}]
    }

    try:
        with patch("src.providers.bigdatacorp.get_bigdata_token", return_value="fake_token"), \
             patch("src.providers.bigdatacorp.get_bigdata_token_id", return_value="fake_id"):
            
            # 1. Primeira consulta (apenas basic_data)
            with patch("src.providers.bigdatacorp.resilient_request") as mock_req:
                mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_resp_basic)
                
                res1 = await bigdatacorp.consultar_cpf(cpf_teste, datasets="bdcbasicdata")
                assert res1.get("status") == "sucesso"
                assert res1.get("cache_id") == f"bigdata_{cpf_teste}"
                
            # 2. Segunda consulta (pedindo basic_data de novo -> CACHE HIT, zero requisições à API)
            with patch("src.providers.bigdatacorp.resilient_request") as mock_req:
                res2 = await bigdatacorp.consultar_cpf(cpf_teste, datasets="bdcbasicdata")
                assert res2.get("status") == "sucesso"
                mock_req.assert_not_called()

            # 3. Terceira consulta (pedindo bdcphones -> deve buscar APENAS bdcphones e mesclar)
            with patch("src.providers.bigdatacorp.resilient_request") as mock_req:
                mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_resp_phones)
                
                res3 = await bigdatacorp.consultar_cpf(cpf_teste, datasets="bdcbasicdata,bdcphones")
                assert res3.get("status") == "sucesso"
                assert mock_req.call_count == 1
                # Valida que na chamada para a API foi pedido apenas bdcphones (phones_extended)
                call_kwargs = mock_req.call_args.kwargs
                assert call_kwargs["json"]["Datasets"] == "phones_extended"

            # 4. Lê categoria bdcphones e basic_data do mesmo cache
            cat_basic = await bigdatacorp.ver_categoria_cpf(cpf_teste, "bdcbasicdata")
            assert cat_basic["bdcbasicdata"]["Name"] == "Miguel Dau Teste"
            
            cat_phones = await bigdatacorp.ver_categoria_cpf(cpf_teste, "bdcphones")
            assert len(cat_phones["bdcphones"]) == 1
            assert cat_phones["bdcphones"][0]["Number"] == "988887777"
    finally:
        if cache_path and os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception:
                pass

@pytest.mark.asyncio
async def test_escavador_consulta_processo_cnj():
    """Valida consulta de processo CNJ com validação de formato e retorno de polos/advogados."""
    cnj_valido = "1415618-82.2026.8.12.0000"
    cnj_invalido = "1415618-83.2026.8.12.0000"
    cache_path = obter_caminho_cache_seguro("processo_cnj_14156188220268120000")
    if cache_path and os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except Exception:
            pass

    try:
        # CNJ inválido é rejeitado localmente sem chamar a API
        res_inv = await escavador.consultar_processo_cnj(cnj_invalido)
        assert res_inv.get("status") == "erro"
        assert res_inv.get("codigo_erro") == "CNJ_INVALIDO"

        # Mock de resposta do Escavador para CNJ válido
        mock_escavador_resp = {
            "numero_cnj": cnj_valido,
            "titulo_polo_ativo": "Empresa Alfa S.A.",
            "titulo_polo_passivo": "Empresa Beta Ltda",
            "data_inicio": "2026-01-15",
            "unidade_origem": {"tribunal_sigla": "TJMS"},
            "partes": [
                {
                    "nome": "Empresa Alfa S.A.",
                    "tipo_polo": "ATIVO",
                    "advogados": [{"nome": "Dr. Carlos Advogado", "oab": "7008/MS"}]
                }
            ],
            "movimentacoes": [
                {"data": "2026-02-01", "conteudo": "Juntada de petição de contestação"}
            ]
        }

        with patch("src.providers.escavador._get_token", return_value="fake_token"), \
             patch("src.providers.escavador.resilient_request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_escavador_resp)
            
            res_val = await escavador.consultar_processo_cnj(cnj_valido)
            assert res_val.get("status") == "sucesso"
            assert res_val.get("polo_ativo") == "Empresa Alfa S.A."
            assert res_val.get("polo_passivo") == "Empresa Beta Ltda"
            assert len(res_val.get("advogados", [])) == 1
            assert res_val["advogados"][0]["oab"] == "7008/MS"
    finally:
        if cache_path and os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception:
                pass

@pytest.mark.asyncio
async def test_pdf_extraction_fallback():
    """Valida a extração de texto de PDF diretamente via pypdf."""
    # Cria um PDF válido em memória contendo texto
    pdf_writer = pypdf.PdfWriter()
    page = pdf_writer.add_blank_page(width=300, height=300)
    pdf_buf = io.BytesIO()
    pdf_writer.write(pdf_buf)
    pdf_bytes = pdf_buf.getvalue()

    # Mock do stream HTTP retornando o PDF
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.reason_phrase = "OK"
    
    async def aiter_bytes(chunk_size=65536):
        yield pdf_bytes
        
    mock_resp.aiter_bytes = aiter_bytes
    
    class AsyncContextManager:
        async def __aenter__(self):
            return mock_resp
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("src.providers.web_osint.http_client.stream", return_value=AsyncContextManager()):
        texto = await web_osint._extrair_texto_pdf_direto("https://example.com/documento.pdf")
        # Como o PDF criado não tem texto, deve detectar como rasterizado sem OCR
        assert "PDF" in texto
        assert "sem camada de texto OCR" in texto

def test_filtrar_dados_pf_aliases():
    """Valida que aliases de datasets (Processes, ExtendedPhones, Companies, etc) retornam suas categorias corretas e nunca BasicData indevido."""
    dados_mock = {
        "Result": [
            {
                "BasicData": {"Name": "Miguel Dau", "TaxIdNumber": "96765585834"},
                "ExtendedPhones": [{"Number": "988887777"}],
                "Processes": {"TotalLawsuits": 2, "Lawsuits": [{"Number": "123"}]},
                "Relationships": {"Companies": [{"Name": "Empresa X", "CNPJ": "11111111000100"}]}
            }
        ]
    }

    # 1. Busca por alias exato ou variação de maiúsculas/minúsculas
    res_phones = bigdatacorp.filtrar_dados_pf(dados_mock, "ExtendedPhones")
    assert len(res_phones) == 1
    assert res_phones[0]["Number"] == "988887777"

    res_proc = bigdatacorp.filtrar_dados_pf(dados_mock, "Processes")
    assert res_proc.get("TotalLawsuits") == 2

    res_comp = bigdatacorp.filtrar_dados_pf(dados_mock, "Companies")
    assert len(res_comp) == 1
    assert res_comp[0]["Name"] == "Empresa X"

    res_rel_comp = bigdatacorp.filtrar_dados_pf(dados_mock, "bdcrelatedcompanies")
    assert len(res_rel_comp) == 1

    # 2. Categoria inexistente retorna {} e NUNCA o alvo completo com BasicData
    res_inexistente = bigdatacorp.filtrar_dados_pf(dados_mock, "CategoriaInexistente")
    assert res_inexistente == {}

def test_resilient_cache_lookups():
    """Valida resolução resiliente para caminhos com barra, CPFs formatados e buscas nominais."""
    cpf_teste = "23302234805"
    p1 = obter_caminho_cache_seguro(f"bigdata_{cpf_teste}")
    p2 = obter_caminho_cache_seguro(f"unitfour_ligados_{cpf_teste}")
    p3 = obter_caminho_cache_seguro("unitfour_busca_nome_miguel_dau")
    for p in (p1, p2, p3):
        if p and os.path.exists(p):
            try: os.remove(p)
            except Exception: pass

    try:
        dados = {"status": "sucesso", "teste": "ok"}
        salvar_cache_universal(f"bigdata_{cpf_teste}", dados)
        salvar_cache_universal(f"unitfour_ligados_{cpf_teste}", {"ligados": []})
        salvar_cache_universal("unitfour_busca_nome_miguel_dau", {"pessoas": ["Miguel Dau"]})

        # Resolução por CPF com máscara
        path_cpf_mascara = obter_caminho_cache_seguro("233.022.348-05")
        assert path_cpf_mascara is not None
        assert path_cpf_mascara.endswith(f"bigdata_{cpf_teste}.json")

        # Resolução por caminho relativo com barra
        path_relativo = obter_caminho_cache_seguro(f"cache_consultas/bigdata_{cpf_teste}.json")
        assert path_relativo is not None
        assert path_relativo.endswith(f"bigdata_{cpf_teste}.json")

        # Resolução por busca nominal
        path_nome = obter_caminho_cache_seguro("Miguel Dau")
        assert path_nome is not None
        assert path_nome.endswith("unitfour_busca_nome_miguel_dau.json")

        # Resolução para pessoas ligadas com prefixo explícito
        path_ligados = obter_caminho_cache_seguro(f"unitfour_ligados_233.022.348-05")
        assert path_ligados is not None
        assert path_ligados.endswith(f"unitfour_ligados_{cpf_teste}.json")
    finally:
        for p in (p1, p2, p3):
            if p and os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

@pytest.mark.asyncio
async def test_judiciais_cross_cache_resolution():
    """Valida que processo judicial presente no cache de CPF é extraído e retornado sem precisar de nova requisição externa."""
    from src.tools.judiciais_tools import bigdata_consultar_processo
    cnj_teste = "1415618-82.2026.8.12.0000"
    p_proc = obter_caminho_cache_seguro("processo_cnj_14156188220268120000")
    p_cpf = obter_caminho_cache_seguro("bigdata_23302234805")
    for p in (p_proc, p_cpf):
        if p and os.path.exists(p):
            try: os.remove(p)
            except Exception: pass
    
    dados_cpf_com_processos = {
        "Result": [
            {
                "BasicData": {"Name": "Investigado Teste"},
                "Processes": {
                    "TotalLawsuits": 1,
                    "Lawsuits": [
                        {
                            "Number": cnj_teste,
                            "Court": "TJMS",
                            "Parties": [
                                {"Name": "Empresa Autora", "Role": "POLO ATIVO", "Lawyers": [{"Name": "Advogado Autor", "OAB": "1234/MS"}]},
                                {"Name": "Investigado Teste", "Role": "POLO PASSIVO"}
                            ],
                            "Updates": [{"Date": "2026-02-10", "Description": "Decisão liminar concedida"}]
                        }
                    ]
                }
            }
        ]
    }
    
    try:
        salvar_cache_universal("bigdata_23302234805", dados_cpf_com_processos)

        # Consulta de processo deve encontrar no cache cruzado do CPF
        res_proc = await bigdata_consultar_processo(cnj_teste)
        assert res_proc.get("status") == "sucesso"
        assert res_proc.get("polo_ativo") == "Empresa Autora"
        assert res_proc.get("polo_passivo") == "Investigado Teste"
        assert res_proc.get("tribunal") == "TJMS"
        assert len(res_proc.get("advogados", [])) == 1
        assert res_proc["advogados"][0]["oab"] == "1234/MS"
    finally:
        for p in (p_proc, p_cpf):
            if p and os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

@pytest.mark.asyncio
async def test_bigdata_processo_status_negativo():
    """Valida que retorno com Status.Code negativo da BigDataCorp resulta em erro estruturado, nunca em status sucesso."""
    mock_resp_erro = {
        "Status": {"Code": -148, "Message": "INVALID LAWSUITS PARAMETER"},
        "Result": []
    }
    with patch("src.providers.bigdatacorp.get_bigdata_token", return_value="fake_token"), \
         patch("src.providers.bigdatacorp.resilient_request") as mock_req:
        mock_req.return_value = MagicMock(status_code=200, json=lambda: mock_resp_erro)

        res = await bigdatacorp.consultar_processo("1415618-82.2026.8.12.0000")
        assert res.get("status") == "erro"
        assert res.get("codigo_erro") == "BIGDATA_-148"
        assert "INVALID LAWSUITS PARAMETER" in res.get("mensagem")

