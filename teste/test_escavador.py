import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ESCAVADOR_API_TOKEN = os.getenv("ESCAVADOR_API_TOKEN")

def test_oab_lookup():
    print("=== TESTE CONEXÃO API ESCAVADOR V2 ===")
    if not ESCAVADOR_API_TOKEN:
        print("[FAIL] ESCAVADOR_API_TOKEN não está configurada no .env!")
        return
        
    print(f"Token (truncado): {ESCAVADOR_API_TOKEN[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {ESCAVADOR_API_TOKEN}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }
    
    # Vamos consultar uma OAB de teste real/ativa
    params = {
        "oab_numero": "300000",
        "oab_estado": "SP",
        "oab_tipo": "ADVOGADO"
    }
    
    url = "https://api.escavador.com/api/v2/advogado/processos"
    
    print(f"Enviando GET para {url}...")
    try:
        r = httpx.get(url, headers=headers, params=params, timeout=20.0)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            dados = r.json()
            print("[SUCCESS] API respondeu com sucesso!")
            # Exibe resumo do retorno
            itens = dados.get("items", [])
            print(f"Total de processos encontrados no retorno: {len(itens)}")
            if len(itens) > 0:
                print("Amostra do primeiro processo:")
                p = itens[0]
                print(f" - CNJ: {p.get('numero_cnj')}")
                print(f" - Título: {p.get('titulo_polo_ativo')} VS {p.get('titulo_polo_passivo')}")
        else:
            print(f"[FAIL] Erro HTTP: {r.text}")
            
    except Exception as e:
        print(f"[FAIL] Erro de conexão/rede: {str(e)}")

if __name__ == "__main__":
    test_oab_lookup()
