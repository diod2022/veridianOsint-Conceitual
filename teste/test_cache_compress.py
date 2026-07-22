import asyncio
import httpx
import sys
import os
import json
import io
import zipfile

PORT = 8009
BASE_URL = f"http://127.0.0.1:{PORT}"
KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_keys.json")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_config.json")
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache_consultas")

chave_admin = "mcp_admin_key_teste_secreto_9999"
test_cache_id = "dummy_test_compress"

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
    print("=== INICIANDO SUÍTE DE TESTES PARA COMPRESSÃO E DOWNLOAD DE CACHE ===")
    
    # Criar arquivos dummy de cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    json_path = os.path.join(CACHE_DIR, f"{test_cache_id}.json")
    md_path = os.path.join(CACHE_DIR, f"{test_cache_id}.md")
    
    json_data = {"teste": "dados_para_compressao", "numeros": [1, 2, 3]}
    md_data = "# Título de Teste\nEste é um markdown de teste."
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_data)
        
    print(f"[TESTE] Arquivos de cache dummy criados em:\n  - {json_path}\n  - {md_path}")
    
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
            
            # 1. Testar download sem chave (deve dar 401)
            print("\n[PASSO 1] Verificando download sem chaves válidas (bloqueio 401)...")
            r = await client.get(f"{BASE_URL}/admin/api/cache/download?cache_id={test_cache_id}")
            print(f"  Status response: {r.status_code}")
            assert r.status_code == 401
            
            # 2. Testar download com chave incorreta (deve dar 401)
            r = await client.get(f"{BASE_URL}/admin/api/cache/download?cache_id={test_cache_id}&admin_key=chave_errada")
            print(f"  Status com chave errada: {r.status_code}")
            assert r.status_code == 401
            print("  ✓ Passou! Acesso bloqueado corretamente.")

            # 3. Testar download com chave correta (deve dar 200 e retornar ZIP válido)
            print("\n[PASSO 2] Solicitando download do ZIP autenticado...")
            r = await client.get(f"{BASE_URL}/admin/api/cache/download?cache_id={test_cache_id}", headers=headers_admin)
            print(f"  Status com chave correta: {r.status_code}")
            assert r.status_code == 200
            assert r.headers.get("Content-Type") == "application/zip"
            print("  ✓ Conexão estabelecida e tipo de mídia application/zip confirmado.")
            
            # Validação do ZIP retornado
            zip_bytes = r.content
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                namelist = zf.namelist()
                print(f"  Arquivos dentro do ZIP: {namelist}")
                assert f"{test_cache_id}.json" in namelist
                assert f"{test_cache_id}.md" in namelist
                
                # Ler e verificar conteúdo dos arquivos dentro do ZIP
                with zf.open(f"{test_cache_id}.json") as jf:
                    extracted_json = json.loads(jf.read().decode("utf-8"))
                    assert extracted_json["teste"] == "dados_para_compressao"
                with zf.open(f"{test_cache_id}.md") as mf:
                    extracted_md = mf.read().decode("utf-8")
                    assert "Título de Teste" in extracted_md
                    
            print("  ✓ Passou! ZIP descompactado e dados validados com sucesso.")

            # 4. Testar a função MCP diretamente importando-a
            print("\n[PASSO 3] Importando e testando a ferramenta MCP diretamente...")
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from server import investigador_obter_cache_compactado
            
            # Chamar a ferramenta MCP
            res_mcp = await investigador_obter_cache_compactado(test_cache_id)
            print(f"  Status MCP: {res_mcp['status']}")
            assert res_mcp["status"] == "sucesso"
            assert res_mcp["arquivos_compactados"] == 2
            assert res_mcp["cache_id"] == test_cache_id
            assert "conteudo_base64" in res_mcp
            assert len(res_mcp["conteudo_base64"]) > 0
            
            # Verificar se gerou o arquivo ZIP no disco local
            caminho_zip_local = res_mcp["caminho_arquivo_zip"]
            print(f"  Caminho ZIP gravado no disco: {caminho_zip_local}")
            assert os.path.exists(caminho_zip_local)
            
            # Deletar o arquivo ZIP criado para não poluir
            os.remove(caminho_zip_local)
            print("  ✓ Passou! Ferramenta MCP gerou Base64 e arquivo ZIP local com sucesso.")
            
            print("\n✓ TODOS OS TESTES DE COMPRESSÃO E DOWNLOAD PASSARAM COM SUCESSO!")
            
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {e}")
        raise
    finally:
        # Remover arquivos dummy
        for p in [json_path, md_path]:
            if os.path.exists(p):
                os.remove(p)
                
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
