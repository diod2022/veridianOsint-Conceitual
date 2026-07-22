import httpx

def test_remote_handshake():
    url = "https://mcpserver.grupolink.com.br/sse/"
    key = "mcp_key_557831f6635d33d4ffc20f7ea92380f0ed6d481280600506"
    
    headers = {
        "X-API-Key": key
    }
    
    print(f"=== TESTE DE CONEXÃO SSE REMOTA ===")
    print(f"URL: {url}")
    print(f"Enviando requisição de handshake...")
    
    try:
        # Tenta conectar e ler a stream do SSE (usamos timeout de 10s para não travar)
        with httpx.stream("GET", url, headers=headers, timeout=10.0) as r:
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print("[SUCESSO] Conexão SSE estabelecida com sucesso!")
                print("[INFO] Lendo os primeiros eventos recebidos:")
                # Lê as primeiras 5 linhas da stream SSE
                count = 0
                for line in r.iter_lines():
                    if line:
                        print(f"  Event: {line}")
                        count += 1
                    if count >= 3:
                        break
            else:
                # Se der erro, tenta ler o corpo
                r.read()
                print(f"[FALHA] Servidor retornou erro HTTP: {r.status_code}")
                print(f"Detalhes: {r.text}")
                
    except Exception as e:
        print(f"[ERRO] Falha de conexão: {str(e)}")

if __name__ == "__main__":
    test_remote_handshake()
