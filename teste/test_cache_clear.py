import asyncio
import httpx
import sys
import os
import json

PORT = 8009
BASE_URL = f"http://127.0.0.1:{PORT}"
KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_keys.json")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_config.json")

chave_admin = "mcp_admin_key_teste_secreto_9999"

async def iniciar_servidor_teste():
    env = os.environ.copy()
    env["FASTMCP_PORT"] = str(PORT)
    env["FASTMCP_TRANSPORT"] = "sse"
    env["ADMIN_API_KEY"] = chave_admin
    
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py")
    
    process = await asyncio.create_subprocess_exec(
        sys.executable, server_path, "--sse",
        env=env
    )
    return process

async def run_tests():
    print("=== INICIANDO SUÍTE DE TESTES EXCLUSIVA PARA API DE CACHE ===")
    
    backup_keys = None
    backup_config = None
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            backup_keys = f.read()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            backup_config = f.read()

    dados_keys = {
        "admin": {
            "key": chave_admin,
            "description": "Chave admin de teste",
            "permissoes": ["*"]
        }
    }
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados_keys, f, ensure_ascii=False, indent=2)

    process = None
    try:
        process = await iniciar_servidor_teste()
        print("[TESTE] Servidor subindo em segundo plano. Aguardando 2.5 segundos...")
        await asyncio.sleep(2.5)
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers_admin = {"X-Admin-Key": chave_admin}
            
            # 1. Obter status e verificar presença de cache_stats
            print("\n[PASSO 1] Verificando estatísticas de cache no endpoint /admin/api/status...")
            r = await client.get(f"{BASE_URL}/admin/api/status", headers=headers_admin)
            print(f"  Status response code: {r.status_code}")
            assert r.status_code == 200
            res = r.json()
            assert "cache_stats" in res, "Chave 'cache_stats' não encontrada no status!"
            assert "arquivos" in res["cache_stats"], "Campo 'arquivos' ausente em cache_stats!"
            assert "tamanho_bytes" in res["cache_stats"], "Campo 'tamanho_bytes' ausente em cache_stats!"
            print(f"  ✓ Passou! Estatísticas de cache atuais: {res['cache_stats']}")

            # 2. Testar acesso não autorizado ao endpoint de limpeza
            print("\n[PASSO 2] Validando que POST em /admin/api/cache/clear exige chave de Admin...")
            r = await client.post(f"{BASE_URL}/admin/api/cache/clear", json={"cache_id": "dummy_cache_id"})
            print(f"  POST sem chave: {r.status_code}")
            assert r.status_code == 401, "Permitiu acesso sem chave de Admin!"
            
            r = await client.post(f"{BASE_URL}/admin/api/cache/clear", headers={"X-Admin-Key": "chave_errada"}, json={"cache_id": "dummy_cache_id"})
            print(f"  POST com chave incorreta: {r.status_code}")
            assert r.status_code == 401, "Permitiu acesso com chave de Admin errada!"
            print("  ✓ Passou! Acesso bloqueado corretamente.")

            # 3. Testar limpeza de cache inexistente com autorização (deve retornar 404)
            print("\n[PASSO 3] Testando POST em /admin/api/cache/clear para cache_id inexistente...")
            r = await client.post(f"{BASE_URL}/admin/api/cache/clear", headers=headers_admin, json={"cache_id": "dummy_cache_id_nao_existente_12345"})
            print(f"  POST com cache_id inexistente: {r.status_code}")
            assert r.status_code == 404, "Esperado 404 para cache_id inexistente!"
            res = r.json()
            assert res["status"] == "erro"
            print("  ✓ Passou! Retornou erro 404 e status 'erro' conforme esperado.")
            
            print("\n✓ TODOS OS TESTES DE CACHE PASSARAM COM SUCESSO!")
            
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {e}")
        raise
    finally:
        print("\n[TESTE] Encerrando o servidor de testes...")
        if process:
            try:
                process.terminate()
                await process.wait()
                print("[TESTE] Servidor encerrado.")
            except Exception as e:
                print(f"[TESTE] Erro ao encerrar servidor: {e}")

        if backup_keys is not None:
            print("[TESTE] Restaurando backup de mcp_keys.json")
            with open(KEYS_FILE, "w", encoding="utf-8") as f:
                f.write(backup_keys)
        else:
            if os.path.exists(KEYS_FILE):
                os.remove(KEYS_FILE)
                
        if backup_config is not None:
            print("[TESTE] Restaurando backup de mcp_config.json")
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(backup_config)
        else:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)

if __name__ == "__main__":
    asyncio.run(run_tests())
