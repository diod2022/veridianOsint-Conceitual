import os
import json
from src.app import mcp
from src.core.config import CACHE_DIR
from src.core.cache import obter_caminho_cache_seguro
from src.core.db import obter_estatisticas_analytics
from src.core.auth import carregar_config_global

@mcp.resource("osint://cache/{cache_id}")
async def obter_cache_resource(cache_id: str) -> str:
    """Permite a leitura direta de qualquer arquivo de cache sem necessidade de tool call."""
    caminho = obter_caminho_cache_seguro(cache_id)
    if not caminho or not os.path.exists(caminho):
        return json.dumps({"error": f"Cache '{cache_id}' não encontrado."}, ensure_ascii=False, indent=2)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return json.dumps(dados, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Falha ao ler cache: {str(e)}"}, ensure_ascii=False, indent=2)

@mcp.resource("osint://status")
async def obter_status_servidor() -> str:
    """Retorna o status operacional, provedores ativos e estatísticas de telemetria do servidor."""
    config = carregar_config_global()
    analytics = obter_estatisticas_analytics(periodo_horas=24)
    status_info = {
        "servidor": "veridianOsint-Conceitual",
        "versao": "2.0.0",
        "protocolo": "FastMCP 1.2+ / MCP Spec",
        "provedores_ativos": config.get("fontes_ativas", {}),
        "estatisticas_24h": {
            "total_chamadas": analytics.get("total_calls", 0),
            "taxa_sucesso": f"{(analytics.get('success_calls', 0) / max(1, analytics.get('total_calls', 1)) * 100):.1f}%",
            "latencia_media_ms": analytics.get("avg_latency", 0),
            "top_ferramentas": analytics.get("by_tool", [])[:5]
        }
    }
    return json.dumps(status_info, ensure_ascii=False, indent=2)
