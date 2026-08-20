from typing import Union, Optional
from src.app import mcp
from src.providers import facial_biometrics

@mcp.tool()
async def biometria_comparar_faces(foto_1: str, foto_2: str, limiar_confianca: float = 0.80) -> dict:
    """
    Compara biometricamente duas fotografias (Face Match 1:1) utilizando visão computacional e Deep Learning local (YuNet + SFace).
    Permite validar se duas imagens de perfil em diferentes redes sociais (Instagram, LinkedIn, TikTok, Facebook) pertencem à mesma pessoa.
    
    Args:
        foto_1: URL web direta (HTTP/HTTPS), string Base64 ou cache_id/caminho do arquivo local da primeira imagem.
        foto_2: URL web direta (HTTP/HTTPS), string Base64 ou cache_id/caminho do arquivo local da segunda imagem.
        limiar_confianca: (Opcional, padrão 0.80) Limiar percentual de confiança para veredito positivo (0.50 a 0.95).
        
    Retorna:
        - match: Verdadeiro se a similaridade superar o limiar estipulado.
        - similaridade_percentual: Índice de proximidade biométrica (0.0% a 100.0%).
        - nivel_confianca: 'ALTA', 'MODERADA' ou 'BAIXA'.
        - veredito: Diagnóstico analítico legível.
        - metricas: Distância cosseno e norma euclidiana L2.
    """
    return await facial_biometrics.comparar_faces(foto_1, foto_2, limiar_confianca)

@mcp.tool()
async def biometria_detectar_faces(foto: str, salvar_recortes: bool = True) -> dict:
    """
    Detecta e mapeia todos os rostos humanos presentes em uma imagem (fotos individuais ou em grupo).
    Extrai coordenadas dos rostos, pontuação de qualidade/confiança e opcionalmente salva recortes biométricos no cache local.
    
    Args:
        foto: URL web direta (HTTP/HTTPS), string Base64 ou cache_id/caminho do arquivo local da imagem.
        salvar_recortes: (Opcional, padrão True) Se True, salva os recortes faciais no cache local para uso posterior em comparações.
        
    Retorna:
        - total_faces_detectadas: Quantidade de pessoas/rostos localizados.
        - dimensoes_imagem: Resolução da imagem processada.
        - faces: Lista detalhada contendo coordenadas (x, y, largura, altura), confiança e cache_id do recorte facial.
    """
    return await facial_biometrics.detectar_faces(foto, salvar_recortes)
