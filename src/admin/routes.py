import os
import json
import time
import secrets
import sqlite3
import datetime
import zipfile
import io
import sys
from starlette.responses import JSONResponse, Response, HTMLResponse
from starlette.requests import Request
from dotenv import load_dotenv

from src.core.config import (
    KEYS_FILE,
    CACHE_DIR,
    DB_PATH,
    ENV_PATH,
    ADMIN_HTML_PATH,
    CHART_JS_PATH
)
from src.core.auth import (
    carregar_config_global,
    salvar_config_global,
    carregar_chaves_autorizadas,
    verificar_token,
    extrair_token
)
from src.core.cache import obter_caminho_cache_seguro_ext

def obter_chave_admin() -> Optional[str]:
    env_admin = os.environ.get("ADMIN_API_KEY", "").strip()
    if env_admin:
        return env_admin
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict) and "admin" in dados:
                info = dados["admin"]
                if isinstance(info, dict):
                    return info.get("key")
                elif isinstance(info, str):
                    return info
    except Exception:
        pass
    chaves = carregar_chaves_autorizadas()
    for token, info in chaves.items():
        if info.get("usuario") == "admin":
            return token
    return None

async def admin_api_auth(request: Request) -> bool:
    chave_admin = obter_chave_admin()
    if not chave_admin:
        return False
    auth_header = request.headers.get("authorization")
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("x-api-key")
    if not token:
        token = request.headers.get("x-admin-key")
    if not token:
        token = request.query_params.get("admin_key")
    return token == chave_admin

async def admin_api_status(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    config = carregar_config_global()
    chaves_brutas = {}
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                for usr, info in dados.items():
                    if isinstance(info, dict) and "key" in info:
                        chaves_brutas[info["key"]] = {
                            "usuario": usr,
                            "description": info.get("description", ""),
                            "permissoes": info.get("permissoes", ["*"])
                        }
                    elif isinstance(info, str):
                        chaves_brutas[info] = {"usuario": usr, "description": "", "permissoes": ["*"]}
    except Exception:
        pass
    
    cached = carregar_chaves_autorizadas()
    for token, info in cached.items():
        if token not in chaves_brutas:
            chaves_brutas[token] = {
                "usuario": info.get("usuario"),
                "description": info.get("description", ""),
                "permissoes": info.get("permissoes", ["*"])
            }
            
    cache_files = 0
    cache_size = 0
    try:
        if os.path.exists(CACHE_DIR):
            for item in os.listdir(CACHE_DIR):
                item_path = os.path.join(CACHE_DIR, item)
                if os.path.isfile(item_path) and not item.startswith('.'):
                    cache_files += 1
                    cache_size += os.path.getsize(item_path)
    except Exception:
        pass

    return JSONResponse({
        "fontes_ativas": config.get("fontes_ativas", {}),
        "consultas_ativas": config.get("consultas_ativas", {}),
        "chaves": chaves_brutas,
        "cache_stats": {
            "arquivos": cache_files,
            "tamanho_bytes": cache_size
        }
    })

async def admin_api_cache_clear(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    
    body = {}
    if request.method == "POST":
        try:
            body = await request.json() if await request.body() else {}
        except Exception:
            pass
            
    cache_id = body.get("cache_id")
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
        
        if deleted_count == 0 and not errors:
            return JSONResponse({"status": "erro", "mensagem": f"Cache '{cache_id}' não encontrado ou inválido."}, status_code=404)
    else:
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
                        
    cache_files = 0
    cache_size = 0
    try:
        if os.path.exists(CACHE_DIR):
            for item in os.listdir(CACHE_DIR):
                item_path = os.path.join(CACHE_DIR, item)
                if os.path.isfile(item_path) and not item.startswith('.'):
                    cache_files += 1
                    cache_size += os.path.getsize(item_path)
    except Exception:
        pass
        
    return JSONResponse({
        "status": "sucesso",
        "mensagem": f"Limpeza concluída. {deleted_count} arquivos removidos.",
        "detalhes": {
            "arquivos_deletados": deleted_count,
            "espaco_liberado_bytes": freed_bytes,
            "erros": errors
        },
        "cache_stats": {
            "arquivos": cache_files,
            "tamanho_bytes": cache_size
        }
    })

async def admin_api_cache_download(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        
    cache_id = request.query_params.get("cache_id")
    if not cache_id:
        return JSONResponse({"error": "cache_id parameter is required"}, status_code=400)
        
    cache_id_seguro = os.path.basename(cache_id)
    if not cache_id_seguro or cache_id_seguro in (".", ".."):
        return JSONResponse({"error": "Invalid cache_id"}, status_code=400)
        
    zip_buffer = io.BytesIO()
    arquivos_adicionados = 0
    
    for ext in [".json", ".md"]:
        file_path = obter_caminho_cache_seguro_ext(cache_id_seguro, ext)
        if file_path and os.path.exists(file_path):
            try:
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(file_path, arcname=f"{cache_id_seguro}{ext}")
                arquivos_adicionados += 1
            except Exception as e:
                print(f"[DOWNLOAD COMPRESS ERROR] {str(e)}", file=sys.stderr, flush=True)
                
    if arquivos_adicionados == 0:
        return JSONResponse({"error": f"Nenhum arquivo de cache encontrado para o cache_id '{cache_id}'"}, status_code=404)
        
    zip_data = zip_buffer.getvalue()
    return Response(
        zip_data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={cache_id_seguro}.zip",
            "Content-Length": str(len(zip_data))
        }
    )

async def admin_api_config(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    config_type = body.get("type", "source")
    name = body.get("name") or body.get("source")
    active = body.get("active")
    
    if not name or active is None:
        return JSONResponse({"error": "name/source and active are required"}, status_code=400)
        
    config = carregar_config_global()
    if config_type == "query":
        if "consultas_ativas" not in config:
            config["consultas_ativas"] = {}
        config["consultas_ativas"][name] = bool(active)
    else:
        if "fontes_ativas" not in config:
            config["fontes_ativas"] = {}
        config["fontes_ativas"][name] = bool(active)
        
    if salvar_config_global(config):
        return JSONResponse({"status": "success", "config": config})
    else:
        return JSONResponse({"error": "Failed to save configuration"}, status_code=500)

async def admin_api_keys_add(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    usuario = body.get("usuario")
    token = body.get("token")
    permissoes = body.get("permissoes", ["*"])
    if not usuario:
        return JSONResponse({"error": "usuario is required"}, status_code=400)
    if not token:
        token = "mcp_key_" + secrets.token_hex(20)
    dados = {}
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if not isinstance(dados, dict):
                dados = {}
        except Exception:
            dados = {}
    dados[usuario] = {
        "key": token,
        "description": f"Chave criada via Painel Administrativo",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "permissoes": permissoes
    }
    try:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        carregar_chaves_autorizadas()
        return JSONResponse({"status": "success", "token": token, "usuario": usuario})
    except Exception as e:
        return JSONResponse({"error": f"Failed to write keys file: {str(e)}"}, status_code=500)

async def admin_api_keys_delete(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    token = body.get("token")
    if not token:
        return JSONResponse({"error": "token is required"}, status_code=400)
    dados = {}
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if not isinstance(dados, dict):
                dados = {}
        except Exception:
            dados = {}
    usuario_removido = None
    for usr, info in list(dados.items()):
        if isinstance(info, dict) and info.get("key") == token:
            usuario_removido = usr
            del dados[usr]
            break
        elif isinstance(info, str) and info == token:
            usuario_removido = usr
            del dados[usr]
            break
    if not usuario_removido:
        return JSONResponse({"error": "Token not found in keys file"}, status_code=404)
    try:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        carregar_chaves_autorizadas()
        return JSONResponse({"status": "success", "usuario": usuario_removido})
    except Exception as e:
        return JSONResponse({"error": f"Failed to write keys file: {str(e)}"}, status_code=500)

async def admin_api_logs(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        
    usuario_filter = request.query_params.get("usuario")
    tool_filter = request.query_params.get("tool_name")
    limit_val = request.query_params.get("limit", "50")
    offset_val = request.query_params.get("offset", "0")
    
    try:
        limit = int(limit_val)
        offset = int(offset_val)
    except ValueError:
        limit = 50
        offset = 0
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT id, timestamp, session_id, usuario, token_prefix, method, tool_name, arguments FROM mcp_logs"
        params = []
        where_clauses = []
        
        if usuario_filter:
            where_clauses.append("usuario = ?")
            params.append(usuario_filter)
            
        if tool_filter:
            where_clauses.append("tool_name = ?")
            params.append(tool_filter)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        count_query = "SELECT COUNT(*) FROM mcp_logs"
        if where_clauses:
            count_query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(count_query, params[:-2])
        total_count = cursor.fetchone()[0]
        conn.close()
        
        logs_list = []
        for row in rows:
            logs_list.append({
                "id": row[0],
                "timestamp": row[1],
                "session_id": row[2],
                "usuario": row[3],
                "token_prefix": row[4],
                "method": row[5],
                "tool_name": row[6],
                "arguments": row[7]
            })
            
        return JSONResponse({
            "logs": logs_list,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return JSONResponse({"error": f"Failed to retrieve logs: {str(e)}"}, status_code=500)

async def admin_api_env_get(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    
    env_dict = {}
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_dict[k.strip()] = v.strip()
        except Exception as e:
            return JSONResponse({"error": f"Failed to read .env: {str(e)}"}, status_code=500)
    return JSONResponse({"status": "success", "env": env_dict})

async def admin_api_env_post(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
    new_env_data = body.get("env")
    if not isinstance(new_env_data, dict):
        return JSONResponse({"error": "Field 'env' dictionary is required"}, status_code=400)
        
    lines = []
    existing_keys = set()
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k, _ = stripped.split("=", 1)
                    k = k.strip()
                    if k in new_env_data:
                        lines.append(f"{k}={new_env_data[k]}\n")
                        existing_keys.add(k)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    for k, v in new_env_data.items():
        if k not in existing_keys:
            lines.append(f"{k}={v}\n")
            
    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        load_dotenv(ENV_PATH, override=True)
        return JSONResponse({"status": "success", "message": "Variáveis de ambiente (.env) atualizadas e recarregadas com sucesso!"})
    except Exception as e:
        return JSONResponse({"error": f"Failed to write .env: {str(e)}"}, status_code=500)

async def admin_api_analytics(request: Request):
    if not await admin_api_auth(request):
        return JSONResponse({"error": "Unauthorized admin key"}, status_code=401)
        
    period = request.query_params.get("period", "7d")
    date_start = request.query_params.get("date_start")
    date_end = request.query_params.get("date_end")
    usuario_filter = request.query_params.get("usuario")
    tool_filter = request.query_params.get("tool_name")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    sql_where = []
    params = []
    
    if period == "1d":
        cutoff = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sql_where.append("timestamp >= ?")
        params.append(cutoff)
    elif period == "7d":
        cutoff = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sql_where.append("timestamp >= ?")
        params.append(cutoff)
    elif period == "30d":
        cutoff = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sql_where.append("timestamp >= ?")
        params.append(cutoff)
    elif period == "custom" or (date_start or date_end):
        if date_start:
            sql_where.append("timestamp >= ?")
            params.append(f"{date_start}T00:00:00Z")
        if date_end:
            sql_where.append("timestamp <= ?")
            params.append(f"{date_end}T23:59:59Z")
            
    if usuario_filter:
        sql_where.append("usuario = ?")
        params.append(usuario_filter)
        
    if tool_filter:
        sql_where.append("tool_name = ?")
        params.append(tool_filter)
        
    where_clause = ""
    if sql_where:
        where_clause = " WHERE " + " AND ".join(sql_where)
        
    cache_where = f"{where_clause} AND (tool_name LIKE '%ler_cache%' OR arguments LIKE '%cache_id%')" if where_clause else " WHERE (tool_name LIKE '%ler_cache%' OR arguments LIKE '%cache_id%')"
    tool_not_null_where = f"{where_clause} AND tool_name IS NOT NULL AND tool_name != ''" if where_clause else " WHERE tool_name IS NOT NULL AND tool_name != ''"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM mcp_logs{where_clause}", params)
        total_queries = cursor.fetchone()[0] or 0
        
        cursor.execute(f"SELECT COUNT(DISTINCT usuario) FROM mcp_logs{where_clause}", params)
        active_users_count = cursor.fetchone()[0] or 0
        
        cursor.execute(f"SELECT COUNT(*) FROM mcp_logs{cache_where}", params)
        cache_hits_count = cursor.fetchone()[0] or 0
        
        cursor.execute(f"SELECT tool_name, COUNT(*) as cnt FROM mcp_logs{tool_not_null_where} GROUP BY tool_name ORDER BY cnt DESC LIMIT 1", params)
        row_top = cursor.fetchone()
        top_tool = row_top[0] if row_top and row_top[0] else "N/A"
        
        cursor.execute(f"SELECT SUBSTR(timestamp, 1, 10) as dt, COUNT(*) FROM mcp_logs{where_clause} GROUP BY dt ORDER BY dt ASC", params)
        timeline_rows = cursor.fetchall()
        timeline = [{"date": r[0], "count": r[1]} for r in timeline_rows]
        
        cursor.execute(f"SELECT usuario, COUNT(*) as cnt FROM mcp_logs{where_clause} GROUP BY usuario ORDER BY cnt DESC", params)
        user_rows = cursor.fetchall()
        by_user = [{"usuario": r[0] or "Desconhecido", "count": r[1]} for r in user_rows]
        
        cursor.execute(f"SELECT tool_name, COUNT(*) as cnt FROM mcp_logs{tool_not_null_where} GROUP BY tool_name ORDER BY cnt DESC LIMIT 10", params)
        tool_rows = cursor.fetchall()
        by_tool = [{"tool_name": r[0], "count": r[1]} for r in tool_rows]
        
        provider_counts = {}
        cursor.execute(f"SELECT tool_name, COUNT(*) FROM mcp_logs{tool_not_null_where} GROUP BY tool_name", params)
        for t_name, count in cursor.fetchall():
            prov = "Outros"
            t_lower = (t_name or "").lower()
            if "bigdata" in t_lower or "cadastro_cpf" in t_lower or "cadastro_cnpj" in t_lower or "processos_judiciais" in t_lower:
                prov = "BigDataCorp"
            elif "escavador" in t_lower or "oab" in t_lower:
                prov = "Escavador (OAB)"
            elif "unitfour" in t_lower or "parentes" in t_lower or "mandados" in t_lower or "placa" in t_lower:
                prov = "Unitfour"
            elif "csint" in t_lower or "vazamento" in t_lower or "breach" in t_lower:
                prov = "CSINT.pro"
            elif "instagram" in t_lower:
                prov = "Instagram (Hiker)"
            elif "linkedin" in t_lower:
                prov = "LinkedIn (Harvest)"
            elif "facebook" in t_lower or "lighthouse" in t_lower or "darknet" in t_lower or "facial" in t_lower:
                prov = "Lighthouse OSINT"
            elif "whois" in t_lower:
                prov = "WhoisXML"
            elif "serper" in t_lower or "google" in t_lower or "dorks" in t_lower or "tavily" in t_lower or "firecrawl" in t_lower:
                prov = "Pesquisa Web / Dorks"
            elif "cache" in t_lower:
                prov = "Cache Local"
                
            provider_counts[prov] = provider_counts.get(prov, 0) + count
            
        by_provider = [{"provider": k, "count": v} for k, v in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)]
        
        cursor.execute("SELECT DISTINCT usuario FROM mcp_logs WHERE usuario IS NOT NULL AND usuario != ''")
        all_users = [r[0] for r in cursor.fetchall() if r[0] and str(r[0]).strip()]
        
        cursor.execute("SELECT DISTINCT tool_name FROM mcp_logs WHERE tool_name IS NOT NULL AND tool_name != ''")
        all_tools = [r[0] for r in cursor.fetchall() if r[0] and str(r[0]).strip()]
        
        conn.close()
        cache_rate = round((cache_hits_count / total_queries * 100), 1) if total_queries > 0 else 0.0
        
        return JSONResponse({
            "status": "success",
            "kpis": {
                "total_queries": total_queries,
                "active_users_count": active_users_count,
                "cache_hits_count": cache_hits_count,
                "cache_rate_percent": cache_rate,
                "top_tool": top_tool
            },
            "timeline": timeline,
            "by_user": by_user,
            "by_tool": by_tool,
            "by_provider": by_provider,
            "all_users": all_users,
            "all_tools": all_tools
        })
    except Exception as e:
        return JSONResponse({"error": f"Failed to calculate analytics: {str(e)}"}, status_code=500)

async def serve_admin_page(scope, receive, send):
    if os.path.exists(ADMIN_HTML_PATH):
        with open(ADMIN_HTML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        response = HTMLResponse(content)
        await response(scope, receive, send)
    else:
        response = HTMLResponse("<h1>404 - admin.html não encontrado</h1>", status_code=404)
        await response(scope, receive, send)

async def serve_chart_js_endpoint(request: Request):
    if os.path.exists(CHART_JS_PATH):
        with open(CHART_JS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, media_type="application/javascript")
    return Response("// chart.js not found", media_type="application/javascript", status_code=404)
