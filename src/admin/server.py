import os
import sys
import json
import uvicorn
import anyio
from uuid import UUID
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.types import ASGIApp, Scope, Receive, Send
from mcp.server.sse import SseServerTransport
import anyio.from_thread

from src.core.db import inicializar_db_logs, registrar_log_busca
from src.core.auth import (
    extrair_token,
    verificar_token,
    carregar_chaves_autorizadas,
    sessoes_ativas,
    sessoes_autorizadas
)
from src.admin.routes import (
    admin_api_status,
    admin_api_config,
    admin_api_keys_add,
    admin_api_keys_delete,
    admin_api_logs,
    admin_api_env_get,
    admin_api_env_post,
    admin_api_analytics,
    admin_api_cache_clear,
    admin_api_cache_download,
    serve_chart_js_endpoint,
    serve_admin_page
)

class ForceHTTPSMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            x_proto = headers.get(b"x-forwarded-proto", b"").decode("latin1")
            host = headers.get(b"host", b"").decode("latin1")
            if x_proto == "https" or ("localhost" not in host and "127.0.0.1" not in host and "0.0.0.0" not in host):
                scope["scheme"] = "https"
        await self.app(scope, receive, send)

class LoggingReceiveStream:
    def __init__(self, original_stream, session_id=None, token=None):
        self._stream = original_stream
        self._session_id = session_id
        self._token = token

    async def receive(self):
        message = await self._stream.receive()
        try:
            msg_obj = getattr(message, "root", message)
            method = getattr(msg_obj, "method", None)
            params = getattr(msg_obj, "params", None)
            if method:
                params_dict = None
                if params:
                    if hasattr(params, "model_dump"):
                        params_dict = params.model_dump(mode="json")
                    elif hasattr(params, "dict"):
                        params_dict = params.dict()
                    elif isinstance(params, dict):
                        params_dict = params
                registrar_log_busca(self._session_id, self._token, method, params_dict)
        except Exception as e:
            print(f"[LOG DB ERROR] Erro ao registrar log assíncrono: {e}", file=sys.stderr, flush=True)
        return message

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self.receive()
        except anyio.EndOfStream:
            raise StopAsyncIteration

    async def aclose(self):
        if hasattr(self._stream, "aclose"):
            await self._stream.aclose()

async def run_sse_with_auth(self_mcp) -> None:
    inicializar_db_logs()
    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        request = Request(scope, receive)
        
        if request.method == "POST":
            req_id = None
            try:
                body = await request.body()
                json_data = json.loads(body)
                method = json_data.get("method")
                req_id = json_data.get("id")
                params = json_data.get("params", {})
                
                token = extrair_token(request)
                if not verificar_token(token):
                    response = JSONResponse({"error": "Unauthorized. Invalid or missing API key."}, status_code=401)
                    await response(scope, receive, send)
                    return
                
                response_data = None
                if method == "initialize":
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "experimental": {},
                                "prompts": {"listChanged": False},
                                "resources": {"subscribe": False, "listChanged": False},
                                "tools": {"listChanged": False}
                            },
                            "serverInfo": {
                                "name": "veridianOsint-Conceitual",
                                "version": "2.0.0"
                            }
                        }
                    }
                elif method == "notifications/initialized":
                    response = Response("", status_code=204)
                    await response(scope, receive, send)
                    return
                elif method == "ping":
                    response_data = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                elif method == "tools/list":
                    tools = await self_mcp.list_tools()
                    tools_json = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tools]
                    response_data = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_json}}
                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})
                    registrar_log_busca(None, token, method, params)
                    result = await self_mcp.call_tool(tool_name, tool_args)
                    result_json = [r.model_dump(mode="json", by_alias=True, exclude_none=True) for r in result]
                    response_data = {"jsonrpc": "2.0", "id": req_id, "result": {"content": result_json}}
                elif method == "resources/list":
                    resources = await self_mcp.list_resources()
                    resources_json = [r.model_dump(mode="json", by_alias=True, exclude_none=True) for r in resources]
                    response_data = {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resources_json}}
                elif method == "prompts/list":
                    prompts = await self_mcp.list_prompts()
                    prompts_json = [p.model_dump(mode="json", by_alias=True, exclude_none=True) for p in prompts]
                    response_data = {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": prompts_json}}
                else:
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }
                
                response = JSONResponse(response_data, status_code=200)
                await response(scope, receive, send)
                return
            except Exception as e:
                response_data = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }
                response = JSONResponse(response_data, status_code=500)
                await response(scope, receive, send)
                return
        
        proto = request.headers.get("x-forwarded-proto") or request.url.scheme
        host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
        if "localhost" not in host and "127.0.0.1" not in host and "0.0.0.0" not in host:
            proto = "https"
            
        base_url = f"{proto}://{host}"
        sse._endpoint = f"{base_url}/messages/"
        
        token = extrair_token(request)
        if not verificar_token(token):
            response = JSONResponse({"error": "Unauthorized. Invalid or missing API key."}, status_code=401)
            await response(scope, receive, send)
            return
        
        sessoes_antes = set(sse._read_stream_writers.keys())
        
        async with sse.connect_sse(scope, receive, send) as streams:
            sessoes_depois = set(sse._read_stream_writers.keys())
            novas_sessoes = sessoes_depois - sessoes_antes
            
            novo_session_id = None
            if novas_sessoes:
                novo_session_id = list(novas_sessoes)[0]
                sessoes_autorizadas.add(novo_session_id)
                sessoes_autorizadas.add(novo_session_id.hex)
                sessoes_autorizadas.add(str(novo_session_id))
                
                chaves = carregar_chaves_autorizadas()
                usr_info = chaves.get(token, {"usuario": "desconhecido", "permissoes": ["*"]})
                
                sess_data = {
                    "usuario": usr_info["usuario"],
                    "permissoes": usr_info.get("permissoes", ["*"]),
                    "token": token
                }
                sessoes_ativas[novo_session_id] = sess_data
                sessoes_ativas[novo_session_id.hex] = sess_data
                sessoes_ativas[str(novo_session_id)] = sess_data
            
            try:
                logging_stream = LoggingReceiveStream(streams[0], novo_session_id, token)
                await self_mcp._mcp_server.run(
                    logging_stream,
                    streams[1],
                    self_mcp._mcp_server.create_initialization_options(),
                )
            finally:
                if novo_session_id:
                    sessoes_autorizadas.discard(novo_session_id)
                    sessoes_autorizadas.discard(novo_session_id.hex)
                    sessoes_autorizadas.discard(str(novo_session_id))
                    sessoes_ativas.pop(novo_session_id, None)
                    sessoes_ativas.pop(novo_session_id.hex, None)
                    sessoes_ativas.pop(str(novo_session_id), None)

    async def handle_messages(scope, receive, send):
        request = Request(scope, receive)
        session_id_param = request.query_params.get("session_id")
        if not session_id_param:
            response = Response("session_id is required", status_code=400)
            await response(scope, receive, send)
            return
        
        try:
            session_id = UUID(hex=session_id_param)
        except ValueError:
            response = Response("Invalid session ID", status_code=400)
            await response(scope, receive, send)
            return

        if session_id not in sessoes_autorizadas and session_id_param not in sessoes_autorizadas:
            response = JSONResponse({"error": "Unauthorized session."}, status_code=403)
            await response(scope, receive, send)
            return
            
        await sse.handle_post_message(scope, receive, send)

    admin_port_env = os.environ.get("ADMIN_PORT")
    admin_port = None
    if admin_port_env:
        try:
            admin_port = int(admin_port_env)
        except ValueError:
            admin_port = None

    if admin_port:
        mcp_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )
        
        admin_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Route("/admin/api/status", endpoint=admin_api_status, methods=["GET"]),
                Route("/admin/api/config", endpoint=admin_api_config, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_add, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_delete, methods=["DELETE"]),
                Route("/admin/api/logs", endpoint=admin_api_logs, methods=["GET"]),
                Route("/admin/api/env", endpoint=admin_api_env_get, methods=["GET"]),
                Route("/admin/api/env", endpoint=admin_api_env_post, methods=["POST"]),
                Route("/admin/api/analytics", endpoint=admin_api_analytics, methods=["GET"]),
                Route("/admin/api/cache/clear", endpoint=admin_api_cache_clear, methods=["POST"]),
                Route("/admin/api/cache/download", endpoint=admin_api_cache_download, methods=["GET"]),
                Route("/admin/chart.min.js", endpoint=serve_chart_js_endpoint, methods=["GET"]),
                Route("/chart.min.js", endpoint=serve_chart_js_endpoint, methods=["GET"]),
                Mount("/admin", app=serve_admin_page),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )

        mcp_config = uvicorn.Config(
            mcp_app,
            host=self_mcp.settings.host,
            port=self_mcp.settings.port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        
        admin_config = uvicorn.Config(
            admin_app,
            host=self_mcp.settings.host,
            port=admin_port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )

        mcp_server = uvicorn.Server(mcp_config)
        admin_server = uvicorn.Server(admin_config)

        print(f"[MCP] Servidor MCP rodando na porta: {self_mcp.settings.port}", file=sys.stderr, flush=True)
        print(f"[ADMIN] Painel Administrativo rodando na porta: {admin_port}", file=sys.stderr, flush=True)

        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp_server.serve)
            tg.start_soon(admin_server.serve)
    else:
        starlette_app = Starlette(
            debug=self_mcp.settings.debug,
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
                Route("/admin/api/status", endpoint=admin_api_status, methods=["GET"]),
                Route("/admin/api/config", endpoint=admin_api_config, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_add, methods=["POST"]),
                Route("/admin/api/keys", endpoint=admin_api_keys_delete, methods=["DELETE"]),
                Route("/admin/api/logs", endpoint=admin_api_logs, methods=["GET"]),
                Route("/admin/api/env", endpoint=admin_api_env_get, methods=["GET"]),
                Route("/admin/api/env", endpoint=admin_api_env_post, methods=["POST"]),
                Route("/admin/api/analytics", endpoint=admin_api_analytics, methods=["GET"]),
                Route("/admin/api/cache/clear", endpoint=admin_api_cache_clear, methods=["POST"]),
                Route("/admin/api/cache/download", endpoint=admin_api_cache_download, methods=["GET"]),
                Route("/admin/chart.min.js", endpoint=serve_chart_js_endpoint, methods=["GET"]),
                Route("/chart.min.js", endpoint=serve_chart_js_endpoint, methods=["GET"]),
                Mount("/admin", app=serve_admin_page),
            ],
            middleware=[
                Middleware(ForceHTTPSMiddleware),
                Middleware(
                    CORSMiddleware,
                    allow_origin_regex="https?://.*",
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ]
        )

        config = uvicorn.Config(
            starlette_app,
            host=self_mcp.settings.host,
            port=self_mcp.settings.port,
            log_level=self_mcp.settings.log_level.lower(),
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        server = uvicorn.Server(config)
        await server.serve()
