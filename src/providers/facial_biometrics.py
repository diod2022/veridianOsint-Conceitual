import os
import io
import re
import sys
import base64
import hashlib
import asyncio
import numpy as np
from typing import Union, Optional, Dict, Any, List, Tuple
from PIL import Image

import cv2
from src.core.config import CACHE_DIR, BASE_DIR
from src.core.http_client import http_client, resilient_request, get_semaphore
from src.core.security import validar_url_segura_ssrf
from src.core.cache import obter_caminho_cache_seguro, salvar_cache_universal

MODELS_DIR = os.path.join(BASE_DIR, "models")
YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

_detector_instance = None
_recognizer_instance = None
_model_lock = asyncio.Lock()

async def _garantir_modelos_baixados() -> bool:
    """Verifica se os arquivos ONNX existem localmente e os baixa caso necessário."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    arquivos_para_baixar = []
    if not os.path.exists(YUNET_PATH) or os.path.getsize(YUNET_PATH) < 100000:
        arquivos_para_baixar.append((YUNET_URL, YUNET_PATH))
    if not os.path.exists(SFACE_PATH) or os.path.getsize(SFACE_PATH) < 10000000:
        arquivos_para_baixar.append((SFACE_URL, SFACE_PATH))

    if not arquivos_para_baixar:
        return True

    for url, destino in arquivos_para_baixar:
        try:
            async with http_client.stream("GET", url, follow_redirects=True, timeout=60.0) as resp:
                if resp.status_code != 200:
                    return False
                with open(destino, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
        except Exception as e:
            print(f"[BIOMETRICS ERROR] Falha ao baixar modelo {url}: {e}", file=sys.stderr, flush=True)
            return False
            
    return True

async def obter_modelos():
    """Retorna os singletons de detector (YuNet) e reconhecedor (SFace)."""
    global _detector_instance, _recognizer_instance
    if _detector_instance is not None and _recognizer_instance is not None:
        return _detector_instance, _recognizer_instance

    async with _model_lock:
        if _detector_instance is not None and _recognizer_instance is not None:
            return _detector_instance, _recognizer_instance
            
        ok = await _garantir_modelos_baixados()
        if not ok or not os.path.exists(YUNET_PATH) or not os.path.exists(SFACE_PATH):
            raise RuntimeError("Não foi possível carregar os modelos ONNX de biometria facial.")

        # Cria detector YuNet com dimensões padrão de entrada (320x320)
        _detector_instance = cv2.FaceDetectorYN.create(
            YUNET_PATH,
            "",
            (320, 320),
            0.6,    # score threshold
            0.3,    # nms threshold
            5000    # top k
        )
        
        # Cria reconhecedor SFace
        _recognizer_instance = cv2.FaceRecognizerSF.create(
            SFACE_PATH,
            ""
        )
        
        return _detector_instance, _recognizer_instance

async def carregar_imagem(entrada: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Carrega e decodifica uma imagem a partir de:
    - URL Web (HTTP/HTTPS com proteção SSRF e streaming limitado)
    - Base64 (Data URI ou raw string)
    - Caminho de arquivo local ou cache_id
    Retorna (matriz_bgr, mensagem_erro).
    """
    if not entrada or not isinstance(entrada, str):
        return None, "Entrada de imagem vazia ou em formato inválido."
        
    entrada_limpa = entrada.strip()
    
    # 1. Caso Base64
    if entrada_limpa.startswith("data:image/") or ";base64," in entrada_limpa or len(entrada_limpa) > 500 and not entrada_limpa.startswith("http"):
        try:
            b64_str = entrada_limpa
            if ";base64," in b64_str:
                b64_str = b64_str.split(";base64,")[1]
            img_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is not None:
                return img_bgr, None
        except Exception as e:
            return None, f"Falha ao decodificar imagem Base64: {e}"

    # 2. Caso Arquivo Local ou Cache ID
    caminho_local = obter_caminho_cache_seguro(entrada_limpa) or entrada_limpa
    if os.path.exists(caminho_local) and os.path.isfile(caminho_local):
        try:
            img_bgr = cv2.imread(caminho_local, cv2.IMREAD_COLOR)
            if img_bgr is not None:
                return img_bgr, None
        except Exception as e:
            return None, f"Falha ao ler arquivo de imagem local '{caminho_local}': {e}"

    # 3. Caso URL Web
    if entrada_limpa.startswith("http://") or entrada_limpa.startswith("https://"):
        url_valida, motivo = validar_url_segura_ssrf(entrada_limpa)
        if not url_valida:
            return None, f"URL bloqueada por segurança (SSRF): {motivo}"
            
        try:
            max_bytes = 10 * 1024 * 1024  # 10 MB
            conteudo_bytes = bytearray()
            
            async with http_client.stream("GET", entrada_limpa, follow_redirects=True, timeout=20.0) as resp:
                if resp.status_code != 200:
                    return None, f"Falha ao baixar imagem (HTTP {resp.status_code}): {resp.reason_phrase}"
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    conteudo_bytes.extend(chunk)
                    if len(conteudo_bytes) > max_bytes:
                        return None, "A imagem excede o limite máximo permitido de 10 MB."
                        
            nparr = np.frombuffer(conteudo_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is not None:
                return img_bgr, None
            return None, "O arquivo baixado não pôde ser decodificado como uma imagem válida."
        except Exception as e:
            return None, f"Erro ao baixar imagem da URL: {e}"

    return None, f"Formato de imagem não reconhecido para o valor fornecido: {entrada_limpa[:50]}..."

def _detectar_faces_em_matriz(detector, img_bgr: np.ndarray) -> List[np.ndarray]:
    """Detecta faces na imagem ajustando dinamicamente a resolução de entrada do detector."""
    h, w, _ = img_bgr.shape
    detector.setInputSize((w, h))
    _, faces = detector.detect(img_bgr)
    if faces is None or len(faces) == 0:
        return []
    return list(faces)

async def comparar_faces(foto_1: str, foto_2: str, limiar_confianca: float = 0.80) -> dict:
    """
    Compara duas fotos (Face Match 1:1) e calcula a similaridade biométrica usando YuNet e SFace.
    """
    try:
        detector, recognizer = await obter_modelos()
    except Exception as e:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_INICIALIZACAO_MODELO",
            "etapa": "inicializacao_biometria",
            "fornecedor": "Veridian",
            "mensagem": f"Falha ao inicializar modelos biométricos: {e}"
        }

    # Carrega as duas imagens
    img1, err1 = await carregar_imagem(foto_1)
    if err1 or img1 is None:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_CARREGAMENTO_FOTO1",
            "etapa": "processamento_imagem",
            "fornecedor": "Veridian",
            "mensagem": f"Foto 1 inválida: {err1}"
        }

    img2, err2 = await carregar_imagem(foto_2)
    if err2 or img2 is None:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_CARREGAMENTO_FOTO2",
            "etapa": "processamento_imagem",
            "fornecedor": "Veridian",
            "mensagem": f"Foto 2 inválida: {err2}"
        }

    # Detecta faces
    faces1 = _detectar_faces_em_matriz(detector, img1)
    if not faces1:
        return {
            "status": "erro",
            "codigo_erro": "SEM_ROSTO_FOTO1",
            "etapa": "deteccao_facial",
            "fornecedor": "Veridian",
            "mensagem": "Nenhum rosto humano foi detectado com clareza na Foto 1."
        }

    faces2 = _detectar_faces_em_matriz(detector, img2)
    if not faces2:
        return {
            "status": "erro",
            "codigo_erro": "SEM_ROSTO_FOTO2",
            "etapa": "deteccao_facial",
            "fornecedor": "Veridian",
            "mensagem": "Nenhum rosto humano foi detectado com clareza na Foto 2."
        }

    # Seleciona a face com maior confiança/área em cada foto
    face1 = max(faces1, key=lambda f: f[2] * f[3])  # maior w*h
    face2 = max(faces2, key=lambda f: f[2] * f[3])

    # Alinha e recorta as faces
    aligned_1 = recognizer.alignCrop(img1, face1)
    aligned_2 = recognizer.alignCrop(img2, face2)

    # Extrai vetores de características (embeddings)
    feat1 = recognizer.feature(aligned_1)
    feat2 = recognizer.feature(aligned_2)

    # Calcula distâncias
    # SFace: Cosine Similarity standard threshold = 0.363, L2 Distance threshold = 1.128
    score_cosine = float(recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_COSINE))
    score_l2 = float(recognizer.match(feat1, feat2, cv2.FaceRecognizerSF_FR_NORM_L2))

    # Converte para similaridade percentual calibrada (0% a 100%)
    # Para Cosine: -1.0 a 1.0 (onde >0.363 é match positivo e >0.60 é match quase certo)
    if score_cosine <= 0:
        similaridade_perc = max(0.0, round((score_cosine + 1.0) * 30.0, 2))
    elif score_cosine < 0.363:
        similaridade_perc = round(30.0 + (score_cosine / 0.363) * 35.0, 2)
    else:
        similaridade_perc = min(99.9, round(65.0 + ((score_cosine - 0.363) / (1.0 - 0.363)) * 34.9, 2))

    limiar = limiar_confianca * 100.0
    is_match = similaridade_perc >= limiar or (score_cosine >= 0.363 and similaridade_perc >= 65.0)

    if similaridade_perc >= 85.0:
        nivel_confianca = "ALTA"
        veredito = "Alta probabilidade de ser a mesma pessoa"
    elif similaridade_perc >= 65.0:
        nivel_confianca = "MODERADA"
        veredito = "Similaridade moderada / Compatível (sugere-se checagem adicional)"
    else:
        nivel_confianca = "BAIXA"
        veredito = "Pessoas distintas (incompatibilidade biométrica facial)"

    return {
        "status": "sucesso",
        "match": is_match,
        "similaridade_percentual": similaridade_perc,
        "nivel_confianca": nivel_confianca,
        "veredito": veredito,
        "metricas": {
            "distancia_cosseno": round(score_cosine, 4),
            "distancia_l2": round(score_l2, 4),
            "limiar_utilizado": f"{limiar:.1f}%"
        },
        "detalhes": {
            "faces_detectadas_foto_1": len(faces1),
            "faces_detectadas_foto_2": len(faces2),
            "qualidade_deteccao_foto_1": f"{float(face1[-1]):.2f}",
            "qualidade_deteccao_foto_2": f"{float(face2[-1]):.2f}"
        }
    }

async def detectar_faces(foto: str, salvar_recortes: bool = True) -> dict:
    """
    Detecta todos os rostos em uma foto, gera bounding boxes e opcionalmente salva recortes no cache.
    """
    try:
        detector, recognizer = await obter_modelos()
    except Exception as e:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_INICIALIZACAO_MODELO",
            "etapa": "inicializacao_biometria",
            "fornecedor": "Veridian",
            "mensagem": f"Falha ao inicializar modelos biométricos: {e}"
        }

    img, err = await carregar_imagem(foto)
    if err or img is None:
        return {
            "status": "erro",
            "codigo_erro": "FALHA_CARREGAMENTO_FOTO",
            "etapa": "processamento_imagem",
            "fornecedor": "Veridian",
            "mensagem": f"Imagem inválida: {err}"
        }

    h, w, _ = img.shape
    faces = _detectar_faces_em_matriz(detector, img)
    
    resultado_faces = []
    hash_foto = hashlib.md5(img.tobytes()[:10000]).hexdigest()[:8]

    for idx, f in enumerate(faces):
        x, y, fw, fh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
        conf = float(f[-1])
        
        face_info = {
            "indice": idx + 1,
            "confianca_deteccao": round(conf, 3),
            "posicao": {
                "x": max(0, x),
                "y": max(0, y),
                "largura": fw,
                "altura": fh
            }
        }
        
        if salvar_recortes:
            # Alinha e recorta a face perfeitamente para identificação futura
            try:
                aligned = recognizer.alignCrop(img, f)
                crop_filename = f"face_crop_{hash_foto}_{idx+1}.jpg"
                crop_path = os.path.join(CACHE_DIR, crop_filename)
                cv2.imwrite(crop_path, aligned)
                face_info["cache_id_recorte"] = crop_filename
            except Exception as e:
                face_info["erro_recorte"] = str(e)

        resultado_faces.append(face_info)

    return {
        "status": "sucesso",
        "total_faces_detectadas": len(faces),
        "dimensoes_imagem": f"{w}x{h}",
        "faces": resultado_faces
    }
