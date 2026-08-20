import os
import json
import io
import zipfile
import base64
import sys
from typing import Optional
from src.app import mcp
from src.core.config import CACHE_DIR
from src.core.cache import obter_caminho_cache_seguro, obter_caminho_cache_seguro_ext

@mcp.tool()
async def investigador_ler_cache(cache_id: str, chave: Optional[str] = None, slice_start: int = 0, slice_end: int = 20) -> dict:
    """
    Lê os dados brutos de um cache salvo por outras ferramentas (Instagram, LinkedIn, BigData, etc).
    Use esta ferramenta para fatiar e navegar em dados grandes sem exceder o limite de tokens do Claude.
    
    Args:
        cache_id: O ID do cache retornado pela ferramenta original.
        chave: (Opcional) Se o dado principal for um objeto/dicionário, informe a chave exata para ler apenas ela.
        slice_start: (Opcional) Índice inicial para paginar listas (padrão 0).
        slice_end: (Opcional) Índice final para paginar listas (padrão 20).
    """
    cache_file = obter_caminho_cache_seguro(cache_id)
    if not cache_file or not os.path.exists(cache_file):
        return {
            "status": "erro",
            "codigo_erro": "CACHE_NAO_ENCONTRADO",
            "etapa": "leitura_cache",
            "fornecedor": "Veridian",
            "mensagem": f"Cache '{cache_id}' não encontrado ou caminho inválido.",
            "retentavel": False,
            "detalhes": {
                "cache_id_solicitado": cache_id,
                "sugestao": "Verifique se a ferramenta de busca (CPF, CNPJ, OAB, etc) foi executada com sucesso antes de requisitar a leitura do cache."
            }
        }
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except Exception as e:
        return {
            "status": "erro",
            "codigo_erro": "CORRUPCAO_CACHE",
            "etapa": "leitura_cache",
            "fornecedor": "Veridian",
            "mensagem": f"Falha ao desserializar JSON do cache '{cache_id}': {str(e)}",
            "retentavel": False
        }
        
    alvo = dados
    if chave:
        if isinstance(dados, dict):
            if "Result" in dados and isinstance(dados["Result"], list) and len(dados["Result"]) > 0 and chave in dados["Result"][0]:
                alvo = dados["Result"][0][chave]
            elif chave in dados:
                alvo = dados[chave]
            else:
                chaves_disp = list(dados["Result"][0].keys()) if ("Result" in dados and isinstance(dados["Result"], list) and len(dados["Result"]) > 0) else list(dados.keys())
                return {
                    "status": "erro",
                    "codigo_erro": "CHAVE_NAO_ENCONTRADA",
                    "etapa": "leitura_cache",
                    "fornecedor": "Veridian",
                    "mensagem": f"Chave '{chave}' não encontrada no cache '{cache_id}'.",
                    "chaves_disponiveis": [k for k in chaves_disp if not k.startswith("_")]
                }
        else:
            return {
                "status": "erro",
                "codigo_erro": "ESTRUTURA_INVALIDA",
                "etapa": "leitura_cache",
                "fornecedor": "Veridian",
                "mensagem": "O cache raiz é uma lista, não um dicionário. Não use o parâmetro 'chave'."
            }
            
    if isinstance(alvo, list):
        total = len(alvo)
        fatia = alvo[slice_start:slice_end]
        return {
            "status": "sucesso",
            "cache_id": cache_id,
            "paginacao": f"Mostrando itens {slice_start} a {min(slice_end, total)} de {total}",
            "dados": fatia
        }
        
    return alvo

@mcp.tool()
async def investigador_limpar_cache(cache_id: Optional[str] = None, limpar_tudo: bool = False) -> dict:
    """
    Remove arquivos de cache locais (consultas BigDataCorp, Instagram, LinkedIn, WHOIS, etc)
    para liberar espaço ou forçar a atualização de buscas antigas.
    
    Args:
        cache_id: (Opcional) O ID específico do cache a ser limpo (ex: 'bigdata_01660684625').
        limpar_tudo: (Opcional) Se True, limpa todo o diretório de cache (exceto pastas internas do sistema).
    """
    if not cache_id and not limpar_tudo:
        return {
            "status": "erro",
            "mensagem": "Informe um 'cache_id' específico ou defina 'limpar_tudo' como True."
        }
        
    deleted_count = 0
    freed_bytes = 0
    errors = []
    
    if cache_id:
        for ext in [".json", ".md"]:
            file_path = obter_caminho_cache_seguro_ext(cache_id, ext)
            if file_path and os.path.exists(file_path):
                try:
                    sz = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    freed_bytes += sz
                except Exception as e:
                    errors.append(f"Erro ao remover {os.path.basename(file_path)}: {str(e)}")
                    
        if deleted_count == 0:
            if errors:
                return {"status": "erro", "mensagem": f"Falha ao deletar arquivos: {', '.join(errors)}"}
            return {"status": "erro", "mensagem": f"Nenhum arquivo encontrado para o cache_id '{cache_id}'."}
            
        return {
            "status": "sucesso",
            "mensagem": f"Cache '{cache_id}' limpo com sucesso. {deleted_count} arquivo(s) removido(s) ({freed_bytes} bytes liberados)."
        }
        
    if limpar_tudo:
        if os.path.exists(CACHE_DIR):
            for item in os.listdir(CACHE_DIR):
                item_path = os.path.join(CACHE_DIR, item)
                if os.path.isfile(item_path):
                    if item.startswith('.'):
                        continue
                    try:
                        sz = os.path.getsize(item_path)
                        os.remove(item_path)
                        deleted_count += 1
                        freed_bytes += sz
                    except Exception as e:
                        errors.append(f"Erro ao remover {item}: {str(e)}")
                        
        return {
            "status": "sucesso",
            "mensagem": f"Todo o cache de consultas foi limpo. {deleted_count} arquivos removidos ({freed_bytes} bytes liberados).",
            "erros": errors if errors else None
        }

@mcp.tool()
async def investigador_obter_cache_compactado(cache_id: str) -> dict:
    """
    Compacta os arquivos de cache de consultas associados a um cache_id específico 
    em um único arquivo ZIP e retorna seu caminho local e conteúdo em Base64.
    
    Args:
        cache_id: O ID do cache a ser compactado (ex: 'bigdata_01660684625').
    """
    if not cache_id or "/" in cache_id or "\\" in cache_id or ".." in cache_id:
        return {"status": "erro", "mensagem": "Nome de cache inválido ou inseguro."}
        
    cache_id_seguro = os.path.basename(cache_id)
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return {"status": "erro", "mensagem": "Nome de cache inválido."}
        
    zip_buffer = io.BytesIO()
    arquivos_adicionados = 0
    tamanho_original = 0
    
    for ext in [".json", ".md"]:
        file_path = obter_caminho_cache_seguro_ext(cache_id_seguro, ext)
        if file_path and os.path.exists(file_path):
            try:
                sz = os.path.getsize(file_path)
                tamanho_original += sz
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(file_path, arcname=f"{cache_id_seguro}{ext}")
                arquivos_adicionados += 1
            except Exception as e:
                print(f"[COMPRESS ERROR] Erro ao adicionar {file_path} ao ZIP: {str(e)}", file=sys.stderr, flush=True)
                
    if arquivos_adicionados == 0:
        return {"status": "erro", "mensagem": f"Nenhum arquivo de cache encontrado para o cache_id '{cache_id}'."}
        
    zip_data = zip_buffer.getvalue()
    caminho_zip = os.path.abspath(os.path.join(CACHE_DIR, f"{cache_id_seguro}.zip"))
    try:
        with open(caminho_zip, "wb") as f:
            f.write(zip_data)
    except Exception as e:
        print(f"[COMPRESS ERROR] Erro ao gravar ZIP local em {caminho_zip}: {str(e)}", file=sys.stderr, flush=True)
        caminho_zip = "Erro ao gravar arquivo em disco"
        
    conteudo_b64 = base64.b64encode(zip_data).decode("utf-8")
    
    return {
        "status": "sucesso",
        "cache_id": cache_id_seguro,
        "arquivos_compactados": arquivos_adicionados,
        "tamanho_original_bytes": tamanho_original,
        "tamanho_zip_bytes": len(zip_data),
        "caminho_arquivo_zip": caminho_zip,
        "base64_zip": conteudo_b64
    }
