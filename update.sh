#!/bin/bash

# Configurações Padrão (Edite se necessário)
MCP_PORT=${FASTMCP_PORT:-8001}
ADMIN_PORT_CONFIG=${ADMIN_PORT:-8080}
LOG_FILE="server.log"

echo "=== INICIANDO ATUALIZAÇÃO E REINICIALIZAÇÃO ==="

# 1. Puxar novidades do GitHub
echo "[GIT] Buscando atualizações no repositório..."
git pull
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao executar git pull. Verifique a conexão ou conflitos."
    exit 1
fi

# 2. Ativar Ambiente Virtual e Atualizar Dependências
if [ -d ".venv" ]; then
    echo "[VENV] Ativando ambiente virtual..."
    source .venv/bin/activate
    echo "[PIP] Atualizando dependências (requirements.txt)..."
    pip install -r requirements.txt
else
    echo "[VENV] Ambiente virtual '.venv' não encontrado na raiz."
    echo "[VENV] Criando ambiente virtual..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "[PIP] Instalando dependências..."
    pip install -r requirements.txt
fi

# 3. Encerrar processo antigo que está usando a porta do MCP
echo "[PROCESS] Procurando processos rodando na porta ${MCP_PORT}..."
PID=$(lsof -t -i:${MCP_PORT})

if [ -not -z "$PID" ] || [ ! -z "$PID" ]; then
    echo "[PROCESS] Encontrado processo(s) com PID(s): ${PID}"
    echo "[PROCESS] Encerrando processos antigos..."
    kill -15 ${PID} 2>/dev/null
    sleep 2
    # Força a parada caso ainda esteja ativo
    kill -9 ${PID} 2>/dev/null
else
    echo "[PROCESS] Nenhum processo ativo encontrado na porta ${MCP_PORT}."
fi

# 4. Iniciar o novo servidor em segundo plano (nohup)
echo "[START] Iniciando servidor MCP (Porta: ${MCP_PORT}) e Admin (Porta: ${ADMIN_PORT_CONFIG})..."
echo "[START] Logs serão direcionados para o arquivo: ${LOG_FILE}"

export FASTMCP_PORT=${MCP_PORT}
export ADMIN_PORT=${ADMIN_PORT_CONFIG}
export PYTHONUNBUFFERED=1

nohup .venv/bin/python server.py --sse > ${LOG_FILE} 2>&1 &

NEW_PID=$!
sleep 2

# 5. Verificar se o processo de fato permaneceu rodando
if kill -0 ${NEW_PID} 2>/dev/null; then
    echo "[SUCESSO] Servidor reiniciado com sucesso!"
    echo "[SUCESSO] Novo PID: ${NEW_PID}"
    echo "[SUCESSO] MCP rodando na porta ${MCP_PORT}"
    echo "[SUCESSO] Admin rodando na porta ${ADMIN_PORT_CONFIG}"
    echo ""
    echo "=== Últimas linhas do log de inicialização (${LOG_FILE}) ==="
    tail -n 10 ${LOG_FILE}
else
    echo "[ERRO] O servidor não conseguiu inicializar. Verifique os logs em ${LOG_FILE}:"
    tail -n 20 ${LOG_FILE}
    exit 1
fi
