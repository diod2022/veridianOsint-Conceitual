import re
import os
import ipaddress
import urllib.parse
from typing import Optional, Tuple, Union

def so_digitos(valor) -> str:
    """Remove qualquer caractere não numérico, retornando apenas dígitos."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))

def normalizar_cpf(cpf) -> str:
    """CPF canônico: 11 dígitos com zeros à esquerda."""
    d = so_digitos(cpf)
    return d.zfill(11)[-11:] if d else ""

def validar_cpf(cpf) -> bool:
    """Valida se o CPF possui 11 dígitos válidos e dígitos verificadores corretos (Módulo 11)."""
    d = normalizar_cpf(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    # Primeiro dígito
    s1 = sum(int(d[i]) * (10 - i) for i in range(9))
    r1 = (s1 * 10) % 11
    if r1 == 10: r1 = 0
    if r1 != int(d[9]):
        return False
    # Segundo dígito
    s2 = sum(int(d[i]) * (11 - i) for i in range(10))
    r2 = (s2 * 10) % 11
    if r2 == 10: r2 = 0
    return r2 == int(d[10])

def normalizar_cnpj(cnpj) -> str:
    """CNPJ canônico: 14 dígitos com zeros à esquerda."""
    d = so_digitos(cnpj)
    return d.zfill(14)[-14:] if d else ""

def validar_cnpj(cnpj) -> bool:
    """Valida se o CNPJ possui 14 dígitos válidos e dígitos verificadores corretos (Módulo 11)."""
    d = normalizar_cnpj(cnpj)
    if len(d) != 14 or len(set(d)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(int(d[i]) * pesos1[i] for i in range(12))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    if d1 != int(d[12]):
        return False
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(int(d[i]) * pesos2[i] for i in range(13))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    return d2 == int(d[13])

def normalizar_cnj(cnj: Union[str, int]) -> Tuple[str, str]:
    """
    Normaliza o número de processo CNJ.
    Retorna tupla: (cnj_formatado, cnj_apenas_digitos).
    Se tiver 20 dígitos, formata: NNNNNNN-DD.AAAA.J.TR.OOOO.
    """
    digitos = so_digitos(cnj)
    if len(digitos) == 20:
        formatado = f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.{digitos[16:20]}"
        return formatado, digitos
    return str(cnj).strip(), digitos

def validar_cnj(cnj: Union[str, int]) -> bool:
    """
    Valida se o número CNJ possui 20 dígitos e satisfaz a fórmula oficial de 
    dígitos verificadores da Resolução nº 65/2008 do CNJ (ISO 7064 Módulo 97-10).
    """
    digitos = so_digitos(cnj)
    if len(digitos) != 20:
        return False
    num = digitos[:7]
    dv = digitos[7:9]
    ano = digitos[9:13]
    j = digitos[13:14]
    tr = digitos[14:16]
    orig = digitos[16:20]
    
    # Formula oficial CNJ: (NNNNNNN + AAAA + J + TR + OOOO + DD) mod 97 == 1
    try:
        full_check = int(num + ano + j + tr + orig + dv) % 97
        return full_check == 1
    except Exception:
        return False

def normalizar_telefone(ddd=None, numero=None, completo=None) -> str:
    """
    Chave canônica de telefone: apenas dígitos, no formato nacional (DDD+numero).
    Aceita entrada em partes (ddd/numero) ou string completa.
    """
    if completo:
        dig = so_digitos(completo)
        if len(dig) >= 12 and dig.startswith("55"):
            dig = dig[2:]
        return dig
    
    if ddd is not None and numero is None:
        dig = so_digitos(ddd)
        if len(dig) >= 12 and dig.startswith("55"):
            dig = dig[2:]
        return dig

    d = so_digitos(ddd)
    n = so_digitos(numero)
    comb = f"{d}{n}"
    if len(comb) >= 12 and comb.startswith("55"):
        comb = comb[2:]
    return comb

def normalizar_email(email) -> str:
    """E-mail normalizado: lower case e sem espaços laterais."""
    return str(email).strip().lower() if email else ""

def normalizar_oab(oab_numero: str, oab_estado: str = "") -> Tuple[str, str]:
    """Retorna (numero_limpo, uf_maiuscula_2_letras)."""
    raw = str(oab_numero).strip()
    uf = (oab_estado or "").strip().upper()[:2]
    
    if not uf:
        match_uf = re.search(r"[/ ]([A-Za-z]{2})", raw) or re.search(r"OAB/([A-Za-z]{2})", raw, re.IGNORECASE)
        if match_uf:
            uf = match_uf.group(1).upper()
            
    num = so_digitos(raw).lstrip("0")
    return num, uf

def validar_url_segura_ssrf(url: str) -> Tuple[bool, str]:
    """
    Valida se a URL é segura para requisições externas (proteção contra SSRF).
    Bloqueia schemes não-HTTP/HTTPS, loopback, redes locais privadas e metadados cloud.
    """
    if not url or not isinstance(url, str):
        return False, "URL não informada ou formato inválido."
        
    url_limpa = url.strip()
    parsed = urllib.parse.urlparse(url_limpa)
    
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Esquema de URL inválido: '{parsed.scheme}'. Apenas HTTP e HTTPS são permitidos."
        
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL inválida: hostname ausente."
        
    # Bloqueio explícito de loopback e domínios locais
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "local", "internal"):
        return False, "Acesso a endereços locais/loopback não é permitido."
        
    # Bloqueio de endpoint de metadados cloud AWS/GCP/Azure
    if hostname == "169.254.169.254" or hostname.startswith("169.254."):
        return False, "Acesso a endpoints de metadados cloud não é permitido."
        
    # Se o hostname for um endereço IP direto, valida ranges privados (RFC 1918 / RFC 4193)
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
            return False, "Acesso a endereços de rede privada/interna não é permitido."
    except ValueError:
        # É um domínio regular (ex: www.site.com.br)
        pass
        
    return True, "URL segura."

def eh_caminho_seguro(cache_id: str) -> bool:
    """Verifica se uma chave de cache é segura contra Path Traversal."""
    if not cache_id or not isinstance(cache_id, str):
        return False
    if "/" in cache_id or "\\" in cache_id or ".." in cache_id:
        return False
    if os.path.basename(cache_id) != cache_id:
        return False
    return True

def validar_caminho_seguro(caminho_base: str, caminho_alvo: str) -> bool:
    """Verifica se caminho_alvo reside estritamente sob caminho_base (previne Path Traversal)."""
    base = os.path.abspath(caminho_base)
    alvo = os.path.abspath(caminho_alvo)
    return alvo == base or alvo.startswith(base + os.sep)
