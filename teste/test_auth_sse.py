import asyncio
import os
import sys
import json
import httpx
import shutil
from urllib.parse import urlparse, parse_qs

# Adiciona o diretório principal ao path para importar o server
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import obter_caminho_cache_seguro, CACHE_DIR

PORT_TESTE = 8009
BASE_URL = f"http://127.0.0.1:{PORT_TESTE}"
KEYS_FILE = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "mcp_keys.json")
BACKUP_KEYS_FILE = KEYS_FILE + ".bak"

async def iniciar_servidor_teste():
    """Inicia o servidor server.py em segundo plano no modo SSE."""
    # Define as variáveis de ambiente necessárias
    env = os.environ.copy()
    env["FASTMCP_TRANSPORT"] = "sse"
    env["FASTMCP_PORT"] = str(PORT_TESTE)
    
    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server.py"))
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "python"))
    
    # Se por acaso não achar o python do venv, usa o executável atual do sys
    python_exec = venv_python if os.path.exists(venv_python) else sys.executable
    
    print(f"[TESTE] Iniciando servidor com: {python_exec} {server_path}")
    process = await asyncio.create_subprocess_exec(
        python_exec, server_path, "--sse",
        env=env
    )
    return process

async def run_tests():
    print("=== INICIANDO SUÍTE DE TESTES DE SEGURANÇA E AUTENTICAÇÃO ===")
    
    # --- PARTE 1: TESTE DE MITIGAÇÃO DE PATH TRAVERSAL ---
    print("\n[TESTE 1] Validando mitigação de Path Traversal no cache...")
    
    # ID seguro
    p_safe = obter_caminho_cache_seguro("relatorio_investigacao_123")
    print(f"  ID seguro: {p_safe}")
    assert p_safe is not None
    assert p_safe.endswith("relatorio_investigacao_123.json")
    assert "cache_consultas" in p_safe
    
    # Path Traversal simples
    p_bad1 = obter_caminho_cache_seguro("../server.py")
    print(f"  Traversal '../server.py': {p_bad1}")
    assert p_bad1 is None
    
    # Path Traversal absoluto no linux/macos
    p_bad2 = obter_caminho_cache_seguro("/etc/passwd")
    print(f"  Traversal '/etc/passwd': {p_bad2}")
    assert p_bad2 is None
    
    # Pontos simples
    p_bad3 = obter_caminho_cache_seguro("..")
    print(f"  Traversal '..': {p_bad3}")
    assert p_bad3 is None
    
    # Espaços e caminhos vazios
    assert obter_caminho_cache_seguro("") is None
    assert obter_caminho_cache_seguro(None) is None
    
    print("✓ TESTE 1 PASSOU: Path Traversal devidamente mitigado.")
    
    # --- PARTE 2: TESTES DE INTEGRACÃO SSE E AUTENTICAÇÃO ---
    
    # Backup do mcp_keys.json se existir
    backup_criado = False
    if os.path.exists(KEYS_FILE):
        print(f"[TESTE] Fazendo backup de {KEYS_FILE}")
        shutil.copyfile(KEYS_FILE, BACKUP_KEYS_FILE)
        backup_criado = True
        
    # Escreve chaves de teste conhecidas
    chave_teste = "mcp_key_teste_secreto_12345"
    chaves_teste_dict = {
        "teste_user": {
            "key": chave_teste,
            "description": "Chave de teste automatizado",
            "created_at": "2026-07-15T12:00:00Z"
        }
    }
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(chaves_teste_dict, f, indent=2)
        
    process = None
    try:
        # Inicia o servidor em segundo plano
        process = await iniciar_servidor_teste()
        print("[TESTE] Servidor subindo em segundo plano. Aguardando 2.5 segundos...")
        await asyncio.sleep(2.5)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Teste 2: Conexão sem chaves
            print("\n[TESTE 2] Solicitando conexão SSE sem informar chave de API...")
            try:
                r = await client.get(f"{BASE_URL}/sse/")
                print(f"  Retorno: {r.status_code}")
                assert r.status_code == 401
                assert "error" in r.json()
                print("✓ TESTE 2 PASSOU: Acesso anônimo bloqueado com 401.")
            except Exception as e:
                print(f"❌ TESTE 2 FALHOU: {e}")
                raise
                
            # Teste 3: Conexão com chave inválida
            print("\n[TESTE 3] Solicitando conexão SSE com chave inválida...")
            try:
                r = await client.get(f"{BASE_URL}/sse/", headers={"X-API-Key": "chave_incorreta_qualquer"})
                print(f"  Retorno: {r.status_code}")
                assert r.status_code == 401
                print("✓ TESTE 3 PASSOU: Acesso com chave incorreta bloqueado com 401.")
            except Exception as e:
                print(f"❌ TESTE 3 FALHOU: {e}")
                raise

            # Teste 4: Conexão válida via X-API-Key header e leitura do session_id
            print("\n[TESTE 4] Solicitando conexão SSE com chave válida via Header X-API-Key...")
            session_id_capturado = None
            try:
                headers = {"X-API-Key": chave_teste}
                async with client.stream("GET", f"{BASE_URL}/sse/", headers=headers) as response:
                    print(f"  Status da conexão stream: {response.status_code}")
                    assert response.status_code == 200
                    
                    # Lê a primeira linha para obter o evento "endpoint" contendo o session_id
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            uri_post = line[5:].strip()
                            print(f"  Mensagem SSE recebida: {line}")
                            print(f"  URI de POST recebida: {uri_post}")
                            
                            # A URI deve ser parecida com: /messages/?session_id=UUID
                            parsed_url = urlparse(uri_post)
                            qs = parse_qs(parsed_url.query)
                            session_id_capturado = qs.get("session_id", [None])[0]
                            print(f"  Session ID capturado com sucesso: {session_id_capturado}")
                            break
                assert session_id_capturado is not None
                print("✓ TESTE 4 PASSOU: Conectado ao SSE e session_id extraído.")
            except Exception as e:
                print(f"❌ TESTE 4 FALHOU: {e}")
                raise
                
            # Teste 5: Envio de mensagem POST com session_id inexistente/não autorizado
            print("\n[TESTE 5] Enviando mensagem POST com session_id inválido...")
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 1
                }
                r = await client.post(f"{BASE_URL}/messages/?session_id=00000000000000000000000000000000", json=payload)
                print(f"  Retorno: {r.status_code}")
                assert r.status_code == 401
                print("✓ TESTE 5 PASSOU: POST com session_id desconhecido bloqueado com 401.")
            except Exception as e:
                print(f"❌ TESTE 5 FALHOU: {e}")
                raise

            # Teste 6: Envio de mensagem POST com session_id autorizado
            # Como a conexão SSE do Teste 4 já foi fechada na saída do "async with client.stream",
            # o session_id foi descartado das sessões autorizadas.
            # Vamos abrir uma nova stream SSE e mantê-la ativa para enviar a mensagem POST concorrentemente!
            print("\n[TESTE 6] Enviando mensagem POST em sessão ativa autorizada...")
            
            async def run_sse_reader(session_ready_event):
                headers = {"X-API-Key": chave_teste}
                nonlocal session_id_capturado
                try:
                    async with client.stream("GET", f"{BASE_URL}/sse/", headers=headers) as response:
                        async for line in response.aiter_lines():
                            if line.startswith("data:"):
                                uri_post = line[5:].strip()
                                parsed_url = urlparse(uri_post)
                                qs = parse_qs(parsed_url.query)
                                session_id_capturado = qs.get("session_id", [None])[0]
                                session_ready_event.set()
                except asyncio.CancelledError:
                    # Cancelamento normal esperado
                    pass
                except Exception as ex:
                    print(f"  Erro na thread de leitura SSE: {ex}")
            
            session_ready = asyncio.Event()
            reader_task = asyncio.create_task(run_sse_reader(session_ready))
            
            # Aguarda a sessão ser estabelecida
            await asyncio.wait_for(session_ready.wait(), timeout=5.0)
            
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    },
                    "id": 1
                }
                r = await client.post(f"{BASE_URL}/messages/?session_id={session_id_capturado}", json=payload)
                print(f"  Retorno do POST: {r.status_code}")
                # O protocolo MCP responde 202 Accepted indicando que a mensagem foi recebida e processada
                assert r.status_code == 202
                print("✓ TESTE 6 PASSOU: POST em sessão ativa aceito com 202.")
            finally:
                reader_task.cancel()
                try:
                    await reader_task
                except asyncio.CancelledError:
                    pass
                
            # Teste 7: Autenticação via Query Param
            print("\n[TESTE 7] Testando conexão SSE informando token via Query Param (?api_key=...)")
            try:
                async with client.stream("GET", f"{BASE_URL}/sse/?api_key={chave_teste}") as response:
                    print(f"  Retorno: {response.status_code}")
                    assert response.status_code == 200
                print("✓ TESTE 7 PASSOU: Autenticação via query param aceita.")
            except Exception as e:
                print(f"❌ TESTE 7 FALHOU: {e}")
                raise

            # Teste 8: Autenticação via Bearer Token
            print("\n[TESTE 8] Testando conexão SSE informando token via Bearer Token...")
            try:
                headers = {"Authorization": f"Bearer {chave_teste}"}
                async with client.stream("GET", f"{BASE_URL}/sse/", headers=headers) as response:
                    print(f"  Retorno: {response.status_code}")
                    assert response.status_code == 200
                print("✓ TESTE 8 PASSOU: Autenticação via Bearer token aceita.")
            except Exception as e:
                print(f"❌ TESTE 8 FALHOU: {e}")
                raise

    finally:
        # Encerra o processo do servidor
        if process:
            print("\n[TESTE] Encerrando o servidor de testes...")
            try:
                process.terminate()
                await process.wait()
                print("[TESTE] Servidor encerrado.")
            except Exception as e:
                print(f"[TESTE] Erro ao encerrar servidor: {e}")
                
        # Remove a chave de teste e restaura o backup
        if os.path.exists(KEYS_FILE):
            os.remove(KEYS_FILE)
            
        if backup_criado:
            print(f"[TESTE] Restaurando backup de {KEYS_FILE}")
            shutil.move(BACKUP_KEYS_FILE, KEYS_FILE)
            
    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
