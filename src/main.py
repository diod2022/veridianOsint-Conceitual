import os
import sys

# Garante que a raiz do projeto esteja no sys.path mesmo em execução direta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import anyio
from src.app import mcp
import src.tools
import src.resources
import src.prompts
from src.core.auth import carregar_chaves_autorizadas
from src.admin.server import run_sse_with_auth

def main():
    transport_mode = os.environ.get("FASTMCP_TRANSPORT", "stdio")
    if "--sse" in sys.argv:
        transport_mode = "sse"
        
    print("Iniciando servidor MCP 'veridianOsint-Conceitual' modular v2.0 (CSINT, BigDataCorp, HikerAPI, Harvest API, Unitfour, Lighthouse, SociaVault, WhoisXML, Web OSINT)...", file=sys.stderr, flush=True)
    
    if transport_mode == "sse":
        print(f"[MCP] Rodando em modo SSE (Web) protegido por Chave de API na porta: {mcp.settings.port}", file=sys.stderr, flush=True)
        carregar_chaves_autorizadas()
        anyio.run(run_sse_with_auth, mcp)
    else:
        print("[MCP] Rodando em modo STDIO.", file=sys.stderr, flush=True)
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
