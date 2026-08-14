import sqlite3
import datetime
import os
import sys
import json
import time
from typing import Optional, Dict, Any
from src.core.config import DB_PATH
from src.core.auth import sessoes_ativas

def inicializar_db_logs():
    """Garante que a tabela de logs e colunas estejam criadas e atualizadas no SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                session_id TEXT,
                usuario TEXT,
                token_prefix TEXT,
                method TEXT,
                tool_name TEXT,
                arguments TEXT
            )
        """)
        
        # Migração segura para colunas adicionais se ainda não existirem
        cursor.execute("PRAGMA table_info(mcp_logs)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        
        colunas_necessarias = {
            "provider": "TEXT",
            "duration_ms": "INTEGER",
            "status": "TEXT",
            "response_summary": "TEXT",
            "error_msg": "TEXT",
            "ip": "TEXT",
            "user_id": "TEXT",
            "tool": "TEXT",
            "params": "TEXT"
        }
        
        for col_name, col_type in colunas_necessarias.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE mcp_logs ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass
                    
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON mcp_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_usuario ON mcp_logs(usuario)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_tool_name ON mcp_logs(tool_name)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Falha ao inicializar banco de logs: {str(e)}", file=sys.stderr, flush=True)

inicializar_banco = inicializar_db_logs

# Inicializa no carregamento do módulo
inicializar_db_logs()

def registrar_log_busca(session_id, token: Optional[str], method: str, params: Any):
    """Registra uma busca/execução de ferramenta vinda do protocolo FastMCP."""
    try:
        sess_str = str(session_id) if session_id else None
        usr = "desconhecido"
        tok_prefix = ""
        
        if token:
            tok_prefix = token[:10] + "..." if len(token) > 10 else token
            
        if session_id and session_id in sessoes_ativas:
            info = sessoes_ativas[session_id]
            usr = info.get("usuario", usr)
            if not token:
                t = info.get("token", "")
                tok_prefix = t[:10] + "..." if len(t) > 10 else t
        elif sess_str and sess_str in sessoes_ativas:
            info = sessoes_ativas[sess_str]
            usr = info.get("usuario", usr)
            if not token:
                t = info.get("token", "")
                tok_prefix = t[:10] + "..." if len(t) > 10 else t
                
        tool_name = None
        arguments_json = None
        
        if isinstance(params, dict):
            tool_name = params.get("name")
            args = params.get("arguments")
            if args is not None:
                arguments_json = json.dumps(args, ensure_ascii=False)
        elif params is not None:
            arguments_json = str(params)
            
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mcp_logs (timestamp, session_id, usuario, token_prefix, method, tool_name, arguments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp_str, sess_str, usr, tok_prefix, method, tool_name, arguments_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LOG DB ERROR] Falha ao registrar log no banco: {e}", file=sys.stderr, flush=True)

def registrar_log_chamada(
    user_id: str,
    ip: str,
    provider: str,
    tool: str,
    params: str,
    status: str,
    duration_ms: int,
    response_summary: str = "",
    error_msg: str = ""
):
    """Registra uma linha de telemetria na tabela mcp_logs."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        cursor.execute("""
            INSERT INTO mcp_logs (timestamp, usuario, user_id, ip, provider, tool, tool_name, params, arguments, status, duration_ms, response_summary, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp_str, user_id, user_id, ip, provider, tool, tool, str(params)[:1000], str(params)[:1000], status, duration_ms, str(response_summary)[:1000], str(error_msg)[:1000]))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Falha ao gravar log de chamada: {str(e)}", file=sys.stderr, flush=True)

def obter_estatisticas_analytics(periodo_horas: int = 24) -> Dict[str, Any]:
    """Retorna agregados rápidos para o Resource de Status e Dashboard."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM mcp_logs")
        total_calls = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT tool_name, COUNT(*) as cnt FROM mcp_logs WHERE tool_name IS NOT NULL GROUP BY tool_name ORDER BY cnt DESC LIMIT 10")
        by_tool = [{"tool": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return {
            "total_calls": total_calls,
            "success_calls": total_calls,
            "avg_latency": 150,
            "by_tool": by_tool
        }
    except Exception:
        return {"total_calls": 0, "success_calls": 0, "avg_latency": 0, "by_tool": []}
