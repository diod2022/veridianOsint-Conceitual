import os
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from src.core.config import TAVILY_API_KEY, FIRECRAWL_API_KEY, SERPER_API_KEY
from src.core.http_client import resilient_request, get_semaphore

async def tavily_buscar_web(query: str, search_depth: str = "basic") -> str:
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "Erro: Chave TAVILY_API_KEY não configurada no .env"
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": search_depth,
        "include_answer": True,
        "max_results": 5
    }
    
    async with get_semaphore("web"):
        try:
            response = await resilient_request("POST", url, json=payload)
            if response.status_code != 200:
                return f"Erro na busca Tavily (HTTP {response.status_code}): {response.text}"
                
            data = response.json()
            output = []
            if data.get("answer"):
                output.append(f"### Resposta Direta:\n{data['answer']}\n")
                
            output.append("### Fontes Encontradas:")
            for result in data.get("results", []):
                output.append(f"- **[{result['title']}]({result['url']})**")
                output.append(f"  *Score de Relevância: {result.get('score', 0)}*")
                output.append(f"  {result['content']}\n")
                
            return "\n".join(output)
        except Exception as e:
            return f"Falha na consulta ao Tavily: {e}"

async def firecrawl_raspar_pagina(url_alvo: str) -> str:
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        return "Erro: Chave FIRECRAWL_API_KEY não configurada no .env"
        
    url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url_alvo,
        "formats": ["markdown"]
    }
    
    async with get_semaphore("web"):
        try:
            response = await resilient_request("POST", url, json=payload, headers=headers)
            if response.status_code != 200:
                return f"Erro ao raspar com Firecrawl (HTTP {response.status_code}): {response.text}"
                
            data = response.json()
            if not data.get("success"):
                return f"Falha na raspagem: {data.get('error', 'Erro desconhecido')}"
                
            markdown_content = data.get("data", {}).get("markdown", "")
            limite_caracteres = 40000
            if len(markdown_content) > limite_caracteres:
                return markdown_content[:limite_caracteres] + "\n\n...[Conteúdo truncado para evitar estouro de contexto]..."
                
            return markdown_content
        except Exception as e:
            return f"Falha na consulta ao Firecrawl: {e}"

async def serper_buscar_web_dorks(alvo: str, categoria: str = "arquivos_expostos") -> dict:
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}

    dork_templates = {
        "arquivos_expostos": [
            'site:{alvo} filetype:pdf OR filetype:xlsx OR filetype:csv',
            'site:{alvo} filetype:docx OR filetype:doc OR filetype:rtf OR filetype:txt'
        ],
        "credenciais_e_backups": [
            'site:{alvo} filetype:sql OR filetype:env OR filetype:conf',
            'site:{alvo} filetype:bkp OR filetype:bak OR filetype:zip OR filetype:tar.gz',
            'site:{alvo} inurl:wp-config.php OR inurl:settings.py OR inurl:db_connect'
        ],
        "infraestrutura_e_login": [
            'site:{alvo} inurl:login OR inurl:admin OR inurl:portal OR inurl:signin',
            'site:{alvo} "Index of /" OR "Index of /backup" OR "Index of /uploads"'
        ],
        "subdominios": [
            'site:*.{alvo} -site:www.{alvo}'
        ]
    }

    templates = dork_templates.get(categoria)
    if not templates:
        return {"error": f"Categoria '{categoria}' inválida. Escolha entre: {list(dork_templates.keys())}"}

    queries = [tpl.format(alvo=alvo) for tpl in templates]
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    async def fazer_busca(query):
        try:
            payload = {"q": query}
            response = await resilient_request("POST", url, json=payload, headers=headers)
            if response.status_code != 200:
                return {"query": query, "status": "error", "message": f"HTTP {response.status_code}"}
            
            data = response.json()
            achados = []
            for item in data.get("organic", []):
                achados.append({
                    "titulo": item.get("title"),
                    "url": item.get("link"),
                    "resumo": item.get("snippet")
                })
            return {
                "query": query,
                "status": "success",
                "total_encontrado": len(achados),
                "resultados": achados
            }
        except Exception as e:
            return {"query": query, "status": "error", "message": str(e)}

    async with get_semaphore("web"):
        tarefas = [fazer_busca(q) for q in queries]
        resultados = await asyncio.gather(*tarefas)

    return {
        "alvo": alvo,
        "categoria": categoria,
        "varredura": resultados
    }

async def serper_buscar_google(query: str) -> dict:
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}
        
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    
    async with get_semaphore("web"):
        try:
            response = await resilient_request("POST", url, json=payload, headers=headers)
            if response.status_code != 200:
                return {"error": f"Erro na busca Google (HTTP {response.status_code}): {response.text}"}
                
            data = response.json()
            achados = []
            for item in data.get("organic", []):
                achados.append({
                    "titulo": item.get("title"),
                    "url": item.get("link"),
                    "resumo": item.get("snippet")
                })
                
            return {
                "query": query,
                "total_encontrado": len(achados),
                "resultados": achados
            }
        except Exception as e:
            return {"error": f"Falha na consulta ao Google: {str(e)}"}

async def wayback_consultar_disponibilidade(url_alvo: str, timestamp: Optional[str] = None) -> dict:
    url = "https://archive.org/wayback/available"
    params = {"url": url_alvo}
    if timestamp: params["timestamp"] = timestamp
        
    async with get_semaphore("web"):
        try:
            response = await resilient_request("GET", url, params=params)
            if response.status_code != 200:
                return {"error": f"Erro na API do Wayback (HTTP {response.status_code}): {response.text}"}
            return response.json()
        except Exception as e:
            return {"error": f"Falha ao consultar o Wayback Machine: {str(e)}"}

async def wayback_listar_imagens(url_alvo: str, limite: int = 50) -> dict:
    url_consulta = url_alvo.strip()
    if not url_consulta.endswith("*") and not url_consulta.endswith("/") and "." in url_consulta:
        if "/" not in url_consulta or url_consulta.count("/") == 1:
            url_consulta = f"{url_consulta}/*"
        else:
            url_consulta = f"{url_consulta}*"

    url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url_consulta,
        "output": "json",
        "filter": "mimetype:image/.*",
        "limit": min(limite, 500),
        "fl": "original,timestamp,mimetype,statuscode"
    }
    
    async with get_semaphore("web"):
        try:
            response = await resilient_request("GET", url, params=params)
            if response.status_code != 200:
                return {"error": f"Erro na API CDX do Wayback (HTTP {response.status_code}): {response.text}"}
                
            data = response.json()
            if not data or len(data) <= 1:
                return {"url_alvo": url_alvo, "total_encontrado": 0, "imagens": []}
                
            rows = data[1:]
            imagens = []
            for row in rows:
                if len(row) < 4: continue
                original, timestamp, mimetype, statuscode = row[0], row[1], row[2], row[3]
                link_captura = f"http://web.archive.org/web/{timestamp}/{original}"
                imagens.append({
                    "url_original": original,
                    "timestamp": timestamp,
                    "tipo_mimetype": mimetype,
                    "status_http": statuscode,
                    "link_visualizacao": link_captura
                })
                
            return {
                "url_alvo": url_alvo,
                "total_encontrado": len(imagens),
                "imagens": imagens
            }
        except Exception as e:
            return {"error": f"Falha ao listar imagens no Wayback: {str(e)}"}

async def wayback_listar_snapshots(url_alvo: str, limite: int = 100, apenas_mudancas: bool = True) -> dict:
    url = "https://web.archive.org/cdx/search/cdx"
    params = {
        "url": url_alvo.strip(),
        "output": "json",
        "fl": "timestamp,original,statuscode,digest",
        "limit": min(limite, 1000)
    }
    if apenas_mudancas:
        params["collapse"] = "digest"
        
    async with get_semaphore("web"):
        try:
            response = await resilient_request("GET", url, params=params)
            if response.status_code != 200:
                return {"error": f"Erro na API CDX do Wayback (HTTP {response.status_code}): {response.text}"}
                
            data = response.json()
            if not data or len(data) <= 1:
                return {"url_alvo": url_alvo, "total_encontrado": 0, "snapshots": []}
                
            rows = data[1:]
            snapshots = []
            for row in rows:
                if len(row) < 4: continue
                timestamp, original, statuscode, digest = row[0], row[1], row[2], row[3]
                link_captura = f"http://web.archive.org/web/{timestamp}/{original}"
                snapshots.append({
                    "timestamp": timestamp,
                    "url_original": original,
                    "status_http": statuscode,
                    "checksum_digest": digest,
                    "link_visualizacao": link_captura
                })
                
            return {
                "url_alvo": url_alvo,
                "apenas_mudancas": apenas_mudancas,
                "total_encontrado": len(snapshots),
                "snapshots": snapshots
            }
        except Exception as e:
            return {"error": f"Falha ao listar snapshots no Wayback: {str(e)}"}
