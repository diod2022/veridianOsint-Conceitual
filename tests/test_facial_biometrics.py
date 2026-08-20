import pytest
import os
import io
import base64
import numpy as np
from PIL import Image, ImageDraw
from unittest.mock import patch, MagicMock

import cv2
from src.app import mcp, custom_list_tools
from src.core.auth import obter_nome_whitelabel
from src.providers import facial_biometrics
from src.tools.biometria_tools import (
    biometria_comparar_faces,
    biometria_detectar_faces
)

def _criar_imagem_com_rosto_sintetico(cor_fundo=(240, 240, 240), deslocamento_olho=0) -> str:
    """Cria uma imagem sintética com estrutura facial legível e retorna como Data URI Base64."""
    img = Image.new("RGB", (300, 300), color=cor_fundo)
    draw = ImageDraw.Draw(img)
    
    # Contorno da cabeça
    draw.ellipse([60, 40, 240, 260], fill=(235, 200, 175), outline=(180, 140, 110), width=2)
    # Olho esquerdo
    draw.ellipse([100, 105, 130 + deslocamento_olho, 130], fill=(40, 40, 40))
    # Olho direito
    draw.ellipse([170, 105, 200, 130], fill=(40, 40, 40))
    # Nariz
    draw.polygon([(150, 135), (140, 175), (160, 175)], fill=(200, 150, 120))
    # Boca
    draw.arc([115, 180, 185, 220], start=0, end=180, fill=(160, 50, 50), width=4)
    
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def test_whitelabel_biometria_names():
    """Valida o mascaramento de nomes de biometria para a marca Veridian."""
    assert obter_nome_whitelabel("biometria_comparar_faces") == "veridian_comparar_faces"
    assert obter_nome_whitelabel("biometria_detectar_faces") == "veridian_detectar_faces"

@pytest.mark.asyncio
async def test_carregar_imagem_base64_e_arquivo():
    """Valida o carregamento seguro de imagens em formato Base64."""
    b64_uri = _criar_imagem_com_rosto_sintetico()
    matriz, erro = await facial_biometrics.carregar_imagem(b64_uri)
    
    assert erro is None
    assert matriz is not None
    assert isinstance(matriz, np.ndarray)
    assert matriz.shape == (300, 300, 3)

@pytest.mark.asyncio
async def test_comparar_faces_mesma_imagem():
    """Valida que comparar uma imagem consigo mesma resulta em Match Positivo com alta similaridade."""
    foto_b64 = _criar_imagem_com_rosto_sintetico()
    
    # Mock para teste unitário determinístico de inferência caso o rosto sintético não atinja o threshold do modelo pré-treinado
    mock_face = np.array([60, 40, 180, 220, 115, 117, 185, 117, 150, 155, 125, 200, 175, 200, 0.98])
    mock_feat = np.ones((1, 128), dtype=np.float32)
    
    with patch("src.providers.facial_biometrics._detectar_faces_em_matriz", return_value=[mock_face]), \
         patch("cv2.FaceRecognizerSF.alignCrop", return_value=np.zeros((112, 112, 3), dtype=np.uint8)), \
         patch("cv2.FaceRecognizerSF.feature", return_value=mock_feat), \
         patch("cv2.FaceRecognizerSF.match", return_value=1.0):
        
        res = await biometria_comparar_faces(foto_b64, foto_b64)
        assert res.get("status") == "sucesso"
        assert res.get("match") is True
        assert res.get("similaridade_percentual") > 90.0
        assert res.get("nivel_confianca") == "ALTA"
        assert "mesma pessoa" in res.get("veredito").lower()
        assert "metricas" in res
        assert "distancia_cosseno" in res["metricas"]

@pytest.mark.asyncio
async def test_comparar_faces_pessoas_distintas():
    """Valida que rostos distintos retornam Match Falso e nível de confiança baixo."""
    foto_1 = _criar_imagem_com_rosto_sintetico()
    foto_2 = _criar_imagem_com_rosto_sintetico(cor_fundo=(50, 50, 50))
    
    mock_face = np.array([60, 40, 180, 220, 115, 117, 185, 117, 150, 155, 125, 200, 175, 200, 0.95])
    mock_feat1 = np.ones((1, 128), dtype=np.float32)
    mock_feat2 = np.zeros((1, 128), dtype=np.float32)
    
    with patch("src.providers.facial_biometrics._detectar_faces_em_matriz", return_value=[mock_face]), \
         patch("cv2.FaceRecognizerSF.alignCrop", return_value=np.zeros((112, 112, 3), dtype=np.uint8)), \
         patch("cv2.FaceRecognizerSF.feature", side_effect=[mock_feat1, mock_feat2]), \
         patch("cv2.FaceRecognizerSF.match", return_value=-0.2):
        
        res = await biometria_comparar_faces(foto_1, foto_2)
        assert res.get("status") == "sucesso"
        assert res.get("match") is False
        assert res.get("nivel_confianca") == "BAIXA"
        assert "distintas" in res.get("veredito").lower()

@pytest.mark.asyncio
async def test_detectar_faces_sucesso():
    """Valida a detecção e mapeamento de faces em uma imagem."""
    foto_b64 = _criar_imagem_com_rosto_sintetico()
    
    mock_face1 = np.array([60, 40, 180, 220, 115, 117, 185, 117, 150, 155, 125, 200, 175, 200, 0.95])
    mock_face2 = np.array([20, 20, 80, 80, 40, 40, 70, 40, 55, 60, 45, 75, 65, 75, 0.88])
    
    with patch("src.providers.facial_biometrics._detectar_faces_em_matriz", return_value=[mock_face1, mock_face2]), \
         patch("cv2.FaceRecognizerSF.alignCrop", return_value=np.zeros((112, 112, 3), dtype=np.uint8)), \
         patch("cv2.imwrite", return_value=True):
        
        res = await biometria_detectar_faces(foto_b64, salvar_recortes=True)
        assert res.get("status") == "sucesso"
        assert res.get("total_faces_detectadas") == 2
        assert len(res.get("faces", [])) == 2
        assert res["faces"][0]["posicao"]["largura"] == 180
        assert "cache_id_recorte" in res["faces"][0]

@pytest.mark.asyncio
async def test_biometria_gating_disabled():
    """Valida que desativar biometria_comparar_faces bloqueia a execução no MCP."""
    mock_config = {
        "fontes_ativas": {"biometria": True},
        "consultas_ativas": {
            "biometria_comparar_faces": False
        }
    }
    with patch("src.core.auth.carregar_config_global", return_value=mock_config):
        res = await biometria_comparar_faces("invalido", "invalido")
        assert ("error" in res) or (res.get("status") == "erro")
        msg = res.get("error") or res.get("mensagem") or ""
        assert "desativada" in msg.lower()

@pytest.mark.asyncio
async def test_custom_list_tools_includes_biometria():
    """Valida que as ferramentas de biometria são propagadas via MCP com nomes whitelabel."""
    mock_config = {
        "fontes_ativas": {"biometria": True},
        "consultas_ativas": {
            "biometria_comparar_faces": True,
            "biometria_detectar_faces": True
        }
    }
    with patch("src.app.carregar_config_global", return_value=mock_config):
        tools = await custom_list_tools()
        tool_names = [t.name for t in tools]
        assert "veridian_comparar_faces" in tool_names
        assert "veridian_detectar_faces" in tool_names
