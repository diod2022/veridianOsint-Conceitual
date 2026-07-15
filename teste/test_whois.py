import asyncio
import os
import sys

# Adiciona o diretório principal ao path para importar o server.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import whois_consultar, CACHE_DIR

async def run_tests():
    print("=== INICIANDO TESTES DO WHOISXML API ===")
    
    # 1. Testar consulta de domínio
    print("\n1. Testando consulta de domínio: google.com")
    res_domain = await whois_consultar("google.com")
    print(f"Status: {res_domain.get('status')}")
    if res_domain.get("status") == "sucesso":
        print(f"Cache ID: {res_domain.get('cache_id')}")
        print("Sucesso! Resumo retornado:")
        print(res_domain.get("resumo_dos_dados"))
    else:
        print(f"Erro no teste 1: {res_domain}")
        return

    # 2. Testar consulta de IP
    print("\n2. Testando consulta de IP: 8.8.8.8")
    res_ip = await whois_consultar("8.8.8.8")
    print(f"Status: {res_ip.get('status')}")
    if res_ip.get("status") == "sucesso":
        print(f"Cache ID: {res_ip.get('cache_id')}")
        print("Sucesso! Resumo retornado:")
        print(res_ip.get("resumo_dos_dados"))
    else:
        print(f"Erro no teste 2: {res_ip}")
        return

    # 3. Testar consulta a partir de E-mail
    print("\n3. Testando extração de domínio a partir de e-mail: test@github.com")
    res_email = await whois_consultar("test@github.com")
    print(f"Status: {res_email.get('status')}")
    if res_email.get("status") == "sucesso":
        # O cache ID deve corresponder a github_com
        print(f"Cache ID: {res_email.get('cache_id')} (deve ser whois_github_com)")
        print("Sucesso! Resumo retornado:")
        print(res_email.get("resumo_dos_dados"))
        if res_email.get("cache_id") != "whois_github_com":
            print(f"AVISO: Cache ID esperado era 'whois_github_com', mas obteve '{res_email.get('cache_id')}'")
    else:
        print(f"Erro no teste 3: {res_email}")
        return

    # 4. Testar funcionamento do cache (segunda chamada)
    print("\n4. Testando recuperação de cache para: google.com")
    res_cache = await whois_consultar("google.com")
    print(f"Status: {res_cache.get('status')}")
    print(f"Mensagem: {res_cache.get('mensagem')}")
    if "cache local" in res_cache.get("mensagem", "").lower():
        print("Sucesso! Cache local interceptado perfeitamente.")
    else:
        print(f"Erro no teste 4: {res_cache}")
        return

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    # Garante que o loop de eventos seja fechado corretamente
    asyncio.run(run_tests())
