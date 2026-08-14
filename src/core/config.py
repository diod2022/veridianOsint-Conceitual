import os
import sys
from dotenv import load_dotenv

# Diretório raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega as variáveis do .env com override=True
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

# Diretórios e caminhos padrão
CACHE_DIR = os.path.join(BASE_DIR, "cache_consultas")
os.makedirs(CACHE_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "mcp_logs.db")
KEYS_FILE = os.path.join(BASE_DIR, "mcp_keys.json")
ADMIN_HTML_PATH = os.path.join(BASE_DIR, "admin.html")
CHART_JS_PATH = os.path.join(BASE_DIR, "chart.min.js")

# Portas e configurações de rede
FASTMCP_PORT = int(os.environ.get("FASTMCP_PORT", 8001))
ADMIN_PORT = int(os.environ.get("ADMIN_PORT", 0)) if os.environ.get("ADMIN_PORT") else None
FASTMCP_HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
FASTMCP_TRANSPORT = os.environ.get("FASTMCP_TRANSPORT", "stdio")

# API Keys de Provedores Externos
BIGDATA_TOKEN = os.environ.get("BIGDATA_TOKEN", "")
BIGDATA_TOKEN_ID = os.environ.get("BIGDATA_TOKEN_ID", "")
BIGDATA_ACCESS_TOKEN = os.environ.get("BIGDATA_ACCESS_TOKEN", "")
BIGDATA_TOKEN_ID_ENV = os.environ.get("BIGDATA_TOKEN_ID", "")

CSINT_API_KEY = os.environ.get("CSINT_API_KEY", "")
ESCAVADOR_API_KEY = os.environ.get("ESCAVADOR_API_KEY", "")
UNITFOUR_TOKEN = os.environ.get("UNITFOUR_TOKEN", "")
HIKER_API_KEY = os.environ.get("HIKER_API_KEY", "")
HARVEST_API_KEY = os.environ.get("HARVEST_API_KEY", "")
LIGHTHOUSE_API_KEY = os.environ.get("LIGHTHOUSE_API_KEY", "")
WHOIS_API_KEY = os.environ.get("WHOIS_API_KEY", "")
SOCIAVAULT_API_KEY = os.environ.get("SOCIAVAULT_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

def get_bigdata_token() -> str:
    return os.environ.get("BIGDATA_TOKEN") or os.environ.get("BIGDATA_ACCESS_TOKEN", "")

def get_bigdata_token_id() -> str:
    return os.environ.get("BIGDATA_TOKEN_ID", "")
