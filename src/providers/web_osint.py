import os
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from src.core.config import TAVILY_API_KEY, FIRECRAWL_API_KEY, SERPER_API_KEY
from src.core.http_client import resilient_request, get_semaphore
from src.core.cache import salvar_cache_universal, checar_cache_universal
from src.core.security import normalizar_email

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

import io
try:
    import pypdf
except ImportError:
    pypdf = None

from src.core.security import validar_url_segura_ssrf
from src.core.http_client import http_client

async def _extrair_texto_pdf_direto(url_alvo: str) -> str:
    """Download direto com streaming limitado (max 15MB) e extração de texto via pypdf."""
    if pypdf is None:
        return f"### Documento PDF: {url_alvo}\n\nAviso: A biblioteca 'pypdf' não está instalada no ambiente do servidor para extração de texto em PDF."
        
    try:
        max_bytes = 15 * 1024 * 1024  # 15 MB
        conteudo_bytes = bytearray()
        
        async with http_client.stream("GET", url_alvo, follow_redirects=True, timeout=20.0) as resp:
            if resp.status_code != 200:
                return f"Falha ao baixar documento PDF (HTTP {resp.status_code}): {resp.reason_phrase}"
                
            async for chunk in resp.aiter_bytes(chunk_size=65536):
                conteudo_bytes.extend(chunk)
                if len(conteudo_bytes) > max_bytes:
                    return f"Documento PDF excede o limite máximo de segurança (15 MB). Download abortado."
                    
        pdf_stream = io.BytesIO(conteudo_bytes)
        reader = pypdf.PdfReader(pdf_stream)
        total_paginas = len(reader.pages)
        
        if total_paginas == 0:
            return f"### Documento PDF: {url_alvo}\n\nO arquivo PDF baixado não contém nenhuma página válida."
            
        paginas_texto = []
        max_paginas_ler = min(total_paginas, 50)
        
        for idx in range(max_paginas_ler):
            p = reader.pages[idx]
            txt = (p.extract_text() or "").strip()
            if txt:
                paginas_texto.append(f"#### Página {idx + 1}\n{txt}")
                
        texto_completo = "\n\n".join(paginas_texto)
        
        if not texto_completo.strip():
            return (
                f"### Documento PDF: {url_alvo}\n\n"
                f"O arquivo possui {total_paginas} página(s) ({len(conteudo_bytes)} bytes), porém é um "
                f"PDF rasterizado/escaneado composto exclusivamente por imagens, sem camada de texto OCR detectável."
            )
            
        header = f"### Documento PDF Extraído: {url_alvo}\n*Total de páginas: {total_paginas} (exibindo primeiras {len(paginas_texto)})*\n\n"
        resultado = header + texto_completo
        
        limite_caracteres = 40000
        if len(resultado) > limite_caracteres:
            resultado = resultado[:limite_caracteres] + "\n\n...[Conteúdo truncado para evitar estouro de contexto]..."
            
        return resultado
    except Exception as e:
        return f"Falha na extração de texto do PDF: {str(e)}"

async def firecrawl_raspar_pagina(url_alvo: str) -> str:
    url_limpa = (url_alvo or "").strip()
    if not url_limpa:
        return "Erro: Nenhuma URL informada para raspagem."

    # Validação de segurança contra SSRF
    eh_segura, motivo_ssrf = validar_url_segura_ssrf(url_limpa)
    if not eh_segura:
        return f"Erro de Segurança (SSRF Bloqueado): {motivo_ssrf}"

    # Se a URL aponta explicitamente para um PDF, usa o extrator de PDF nativo
    if url_limpa.lower().split("?")[0].endswith(".pdf"):
        return await _extrair_texto_pdf_direto(url_limpa)

    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        # Fallback para download direto caso não haja chave do Firecrawl
        return await _extrair_texto_pdf_direto(url_limpa)
        
    url_firecrawl = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url_limpa,
        "formats": ["markdown"]
    }
    
    async with get_semaphore("web"):
        try:
            response = await resilient_request("POST", url_firecrawl, json=payload, headers=headers)
            if response.status_code != 200:
                # Tenta fallback de extração direta
                fallback = await _extrair_texto_pdf_direto(url_limpa)
                if fallback and not fallback.startswith("Falha"):
                    return fallback
                return f"Erro ao raspar com Firecrawl (HTTP {response.status_code}): {response.text}"
                
            data = response.json()
            if not data.get("success"):
                fallback = await _extrair_texto_pdf_direto(url_limpa)
                if fallback and not fallback.startswith("Falha"):
                    return fallback
                return f"Falha na raspagem Firecrawl: {data.get('error', 'Erro desconhecido')}"
                
            markdown_content = (data.get("data", {}).get("markdown") or "").strip()
            
            # Se o Firecrawl retornou vazio, tenta o fallback local
            if not markdown_content:
                fallback = await _extrair_texto_pdf_direto(url_limpa)
                if fallback and not fallback.startswith("Falha") and not "PDF" in fallback:
                    return fallback
                return f"### Raspagem Web: {url_limpa}\n\nA página foi acessada com sucesso (HTTP 200), porém não retornou conteúdo textual legível (página vazia ou renderizada dinamicamente no navegador)."
                
            limite_caracteres = 40000
            if len(markdown_content) > limite_caracteres:
                return markdown_content[:limite_caracteres] + "\n\n...[Conteúdo truncado para evitar estouro de contexto]..."
                
            return markdown_content
        except Exception as e:
            fallback = await _extrair_texto_pdf_direto(url_limpa)
            if fallback and not fallback.startswith("Falha"):
                return fallback
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

async def serper_buscar_avaliacoes_empresa(
    empresa_ou_local: str,
    termo_filtro: Optional[str] = None,
    ordenacao: str = "newest",
    pagina: int = 1
) -> dict:
    """
    Busca avaliações (reviews) de estabelecimentos e empresas no Google Maps através do Serper.dev.
    Localiza o estabelecimento (Places), obtém o CID e recupera as avaliações com notas, texto, autor e réplica.
    
    Args:
        empresa_ou_local: Nome da empresa/local (ex: 'Hospital Albert Einstein Morumbi') ou CID numérico direto.
        termo_filtro: Termo opcional para filtrar apenas reviews com certas palavras (ex: nome de médico, reclamação, 'péssimo').
        ordenacao: 'newest' (mais recentes), 'highestRating' (melhores notas), 'lowestRating' (piores notas/reclamações).
        pagina: Número da página (padrão 1).
    """
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}

    termo_limpo = empresa_ou_local.strip()
    cache_id = termo_limpo.replace(" ", "_").replace("/", "_").replace(":", "_").lower()
    filtro_id = termo_filtro.replace(" ", "_").lower() if termo_filtro else "all"
    cache_key = f"serper_reviews_{cache_id}_{filtro_id}_{ordenacao}_p{pagina}"

    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    async with get_semaphore("web"):
        try:
            place_info = {}
            cid = None

            # Se for apenas dígitos com 15+ caracteres, assume ser o CID diretamente
            if termo_limpo.isdigit() and len(termo_limpo) >= 15:
                cid = termo_limpo
            else:
                # 1. Localiza o estabelecimento via Google Places
                url_places = "https://google.serper.dev/places"
                resp_places = await resilient_request(
                    "POST",
                    url_places,
                    json={"q": termo_limpo, "gl": "br", "hl": "pt-br"},
                    headers=headers
                )
                if resp_places.status_code != 200:
                    return {"error": f"Erro ao buscar local no Google Places (HTTP {resp_places.status_code}): {resp_places.text}"}

                places_data = resp_places.json().get("places", [])
                if not places_data:
                    return {"error": f"Nenhum estabelecimento encontrado no Google Maps para '{termo_limpo}'."}

                top_place = places_data[0]
                cid = top_place.get("cid")
                place_info = {
                    "titulo": top_place.get("title"),
                    "endereco": top_place.get("address"),
                    "categoria": top_place.get("category"),
                    "rating_geral": top_place.get("rating"),
                    "total_avaliacoes": top_place.get("ratingCount"),
                    "telefone": top_place.get("phoneNumber"),
                    "website": top_place.get("website"),
                    "cid": cid
                }

            if not cid:
                return {"error": f"Não foi possível obter o identificador (CID) do estabelecimento '{termo_limpo}'."}

            # 2. Busca as avaliações no endpoint /reviews
            url_reviews = "https://google.serper.dev/reviews"
            payload_rev = {
                "cid": str(cid),
                "gl": "br",
                "hl": "pt-br",
                "sort": ordenacao,
                "page": pagina
            }
            if termo_filtro:
                payload_rev["q"] = termo_filtro

            resp_rev = await resilient_request(
                "POST",
                url_reviews,
                json=payload_rev,
                headers=headers
            )
            if resp_rev.status_code != 200:
                return {"error": f"Erro ao consultar reviews no Google (HTTP {resp_rev.status_code}): {resp_rev.text}"}

            rev_json = resp_rev.json()
            raw_reviews = rev_json.get("reviews", [])
            reviews_processados = []

            for r in raw_reviews:
                user_info = r.get("user", {})
                reviews_processados.append({
                    "autor": user_info.get("name"),
                    "link_perfil": user_info.get("link"),
                    "foto_perfil": user_info.get("thumbnail"),
                    "estrelas": r.get("rating"),
                    "data_relativa": r.get("date"),
                    "texto": r.get("snippet"),
                    "likes": r.get("likes"),
                    "resposta_empresa": r.get("response", {}).get("snippet") if r.get("response") else None
                })

            resultado = {
                "estabelecimento": place_info,
                "termo_filtro": termo_filtro,
                "ordenacao": ordenacao,
                "pagina": pagina,
                "total_reviews_pagina": len(reviews_processados),
                "tem_proxima_pagina": bool(rev_json.get("nextPageToken")),
                "reviews": reviews_processados
            }

            return salvar_cache_universal(cache_key, resultado)

        except Exception as e:
            return {"error": f"Falha na consulta de avaliações do Google: {str(e)}"}

async def serper_buscar_reviews_por_email(
    email: str,
    incluir_username: bool = True
) -> dict:
    """
    Realiza varredura investigativa multivetorial para localizar avaliações, reclamações e depoimentos
    associados a um endereço de e-mail (e seu username) em portais de consumo, Google Maps e web.
    
    Args:
        email: O endereço de e-mail do alvo a ser investigado.
        incluir_username: Se True, também pesquisa o identificador/usuário do e-mail em portais de reclamação.
    """
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        return {"error": "Erro: Chave SERPER_API_KEY não configurada no .env"}

    email_limpo = normalizar_email(email)
    if not email_limpo or "@" not in email_limpo:
        return {"error": f"E-mail inválido para busca de reviews: '{email}'."}

    username = email_limpo.split("@")[0]
    cache_id = email_limpo.replace("@", "_at_").replace(".", "_")
    cache_key = f"serper_email_reviews_{cache_id}"

    cache_hit = checar_cache_universal(cache_key)
    if cache_hit:
        return cache_hit

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }

    # Vetores direcionados de busca OSINT por reputação e consumo
    vetores_busca = [
        {"categoria": "Google Maps Contribuições", "query": f'site:google.com/maps/contrib "{username}"'},
        {"categoria": "Google Maps Menções", "query": f'"{email_limpo}" site:google.com/maps'},
        {"categoria": "Reclame Aqui (E-mail)", "query": f'site:reclameaqui.com.br "{email_limpo}"'},
        {"categoria": "Trustpilot", "query": f'site:trustpilot.com "{email_limpo}"'},
        {"categoria": "Consumidor.gov", "query": f'site:consumidor.gov.br "{email_limpo}"'},
        {"categoria": "Glassdoor / Avaliações Corporativas", "query": f'site:glassdoor.com.br "{email_limpo}"'},
        {"categoria": "Avaliações & Reclamações Gerais Web", "query": f'"{email_limpo}" (avaliação OR avaliou OR review OR reclamação OR "minha experiência")'}
    ]

    if incluir_username and len(username) >= 5:
        vetores_busca.append({
            "categoria": "Reclame Aqui (Usuário)",
            "query": f'site:reclameaqui.com.br "{username}"'
        })

    url = "https://google.serper.dev/search"

    async def consultar_vetor(vetor):
        try:
            payload = {"q": vetor["query"], "gl": "br", "hl": "pt-br"}
            resp = await resilient_request("POST", url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                achados = []
                for item in data.get("organic", []):
                    achados.append({
                        "titulo": item.get("title"),
                        "url": item.get("link"),
                        "resumo": item.get("snippet"),
                        "data": item.get("date")
                    })
                return {
                    "categoria": vetor["categoria"],
                    "query": vetor["query"],
                    "total": len(achados),
                    "resultados": achados
                }
            return {
                "categoria": vetor["categoria"],
                "query": vetor["query"],
                "total": 0,
                "resultados": []
            }
        except Exception as exc:
            return {
                "categoria": vetor["categoria"],
                "query": vetor["query"],
                "total": 0,
                "erro": str(exc),
                "resultados": []
            }

    async with get_semaphore("web"):
        tarefas = [consultar_vetor(v) for v in vetores_busca]
        varredura = await asyncio.gather(*tarefas)

    # Consolidação e deduplicação de resultados encontrados
    links_vistos = set()
    achados_consolidados = []

    for grupo in varredura:
        for item in grupo.get("resultados", []):
            url_item = item.get("url")
            if url_item and url_item not in links_vistos:
                links_vistos.add(url_item)
                achados_consolidados.append({
                    "plataforma": grupo.get("categoria"),
                    "titulo": item.get("titulo"),
                    "url": url_item,
                    "resumo": item.get("resumo"),
                    "data": item.get("data")
                })

    resultado_final = {
        "email_alvo": email_limpo,
        "username_pesquisado": username,
        "total_registros_unicos": len(achados_consolidados),
        "achados": achados_consolidados,
        "detalhamento_por_vetor": varredura
    }

    return salvar_cache_universal(cache_key, resultado_final)

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
