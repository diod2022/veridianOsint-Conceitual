import re
import os
from typing import Optional, Tuple

def so_digitos(valor) -> str:
    """Remove qualquer caractere não numérico, retornando apenas dígitos."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))

def normalizar_cpf(cpf) -> str:
    """CPF canônico: 11 dígitos com zeros à esquerda."""
    d = so_digitos(cpf)
    return d.zfill(11)[-11:] if d else ""

def normalizar_cnpj(cnpj) -> str:
    """CNPJ canônico: 14 dígitos com zeros à esquerda."""
    d = so_digitos(cnpj)
    return d.zfill(14)[-14:] if d else ""

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
