# -*- coding: utf-8 -*-
"""
dossie.py — Camada de consolidação de dossiê do Agente Investigador.

Objetivo (produtização): transformar as consultas atômicas espalhadas em
`cache_consultas/` num MODELO DE ENTIDADE CANÔNICO ("Subject") com:

  - Identificação unificada (nome, nascimento, filiação, situação cadastral)
  - Contatos deduplicados (telefones, e-mails) com CORROBORAÇÃO entre fontes
  - Endereços deduplicados
  - Vínculos (parentes / sócios / empresas)
  - Sinais de risco (PEP, mandados, antecedentes, processos)
  - PROVENIÊNCIA por achado (qual fonte, quando) e SCORE DE CONFIANÇA

Design principles:
  - Aditivo: NÃO altera nenhuma tool existente do server.py.
  - Puro/testável: as funções de normalização e consolidação não fazem I/O de
    rede — operam sobre dicts já salvos no cache, então dá para validar offline.
  - Determinístico: mesma entrada -> mesma saída (essencial para laudo).
"""

from __future__ import annotations

import os
import re
import json
import glob
from datetime import datetime, timezone

# Diretório de cache (mesmo usado pelo server.py)
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_consultas")


# ==============================================================================
# Helpers de normalização
# ==============================================================================

def so_digitos(valor) -> str:
    """Remove qualquer máscara, retornando apenas dígitos."""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def normalizar_cpf(cpf) -> str:
    """CPF canônico: 11 dígitos com zeros à esquerda."""
    return so_digitos(cpf).zfill(11)[-11:] if so_digitos(cpf) else ""


def normalizar_telefone(ddd=None, numero=None, completo=None) -> str:
    """
    Chave canônica de telefone: apenas dígitos, no formato nacional (DDD+numero).
    Aceita entrada em partes (ddd/numero) ou string completa.
    """
    if completo:
        dig = so_digitos(completo)
        # remove prefixo de país 55 quando presente e sobra número plausível
        if len(dig) >= 12 and dig.startswith("55"):
            dig = dig[2:]
        return dig
    return f"{so_digitos(ddd)}{so_digitos(numero)}"


def normalizar_email(email) -> str:
    return str(email).strip().lower() if email else ""


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==============================================================================
# Modelo de entidade canônico
# ==============================================================================

class Dossie:
    """
    Acumulador do dossiê de um alvo (pessoa física).

    Cada campo multivalorado (telefones, emails, enderecos, vinculos, riscos)
    é uma lista de dicts com:
        valor         -> o dado normalizado
        fontes        -> set de nomes de fonte que reportaram o dado
        detalhes      -> payload adicional específico da fonte
    A CORROBORAÇÃO é medida pelo tamanho de `fontes`: 2+ fontes = mais confiança.
    """

    def __init__(self, cpf: str):
        self.cpf = normalizar_cpf(cpf)
        self.identificacao: dict = {}          # nome, nascimento, mae, pai, sexo, situacao...
        self.telefones: dict[str, dict] = {}   # chave: telefone normalizado
        self.emails: dict[str, dict] = {}       # chave: email normalizado
        self.enderecos: list[dict] = []
        self.vinculos: dict[str, dict] = {}     # chave: documento do vinculado
        self.empresas: dict[str, dict] = {}     # chave: cnpj (participações)
        self.riscos: list[dict] = []            # PEP, mandados, antecedentes, processos
        self.fontes_consultadas: list[str] = []
        self._identificacao_fontes: dict[str, set] = {}  # campo -> fontes

    # ---- ingestão de campos ----

    def _set_id(self, campo: str, valor, fonte: str):
        if valor in (None, "", []):
            return
        # Primeira fonte a preencher "ganha" o valor; demais só corroboram.
        if campo not in self.identificacao:
            self.identificacao[campo] = valor
        self._identificacao_fontes.setdefault(campo, set()).add(fonte)

    def add_telefone(self, chave: str, fonte: str, detalhes: dict | None = None):
        if not chave:
            return
        reg = self.telefones.setdefault(chave, {"valor": chave, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if detalhes:
            reg["detalhes"].update({k: v for k, v in detalhes.items() if v not in (None, "")})

    def add_email(self, chave: str, fonte: str, detalhes: dict | None = None):
        chave = normalizar_email(chave)
        if not chave:
            return
        reg = self.emails.setdefault(chave, {"valor": chave, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if detalhes:
            reg["detalhes"].update({k: v for k, v in detalhes.items() if v not in (None, "")})

    def add_endereco(self, endereco: dict, fonte: str):
        # chave de dedup: logradouro+numero+cep (normalizados)
        chave = (
            f"{str(endereco.get('logradouro','')).strip().lower()}|"
            f"{so_digitos(endereco.get('numero',''))}|"
            f"{so_digitos(endereco.get('cep',''))}"
        )
        for e in self.enderecos:
            if e["_chave"] == chave:
                e["fontes"].add(fonte)
                return
        self.enderecos.append({**endereco, "_chave": chave, "fontes": {fonte}})

    def add_vinculo(self, documento: str, nome: str, tipo: str, fonte: str, extra: dict | None = None):
        doc = so_digitos(documento) or nome
        if not doc:
            return
        reg = self.vinculos.setdefault(doc, {
            "documento": so_digitos(documento), "nome": nome, "tipo": tipo,
            "fontes": set(), "detalhes": {}
        })
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update(extra)

    def add_empresa(self, cnpj: str, nome: str, fonte: str, extra: dict | None = None):
        c = so_digitos(cnpj)
        if not c:
            return
        reg = self.empresas.setdefault(c, {"cnpj": c, "nome": nome, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update(extra)

    def add_risco(self, categoria: str, descricao: str, fonte: str, gravidade: str = "media", detalhes=None):
        self.riscos.append({
            "categoria": categoria, "descricao": descricao, "gravidade": gravidade,
            "fonte": fonte, "detalhes": detalhes or {},
        })

    # ---- serialização ----

    @staticmethod
    def _dump_contatos(mapa: dict) -> list:
        saida = []
        for reg in mapa.values():
            saida.append({
                "valor": reg["valor"],
                "corroboracao": len(reg["fontes"]),
                "fontes": sorted(reg["fontes"]),
                "detalhes": reg["detalhes"],
            })
        # ordena: mais corroborado primeiro
        return sorted(saida, key=lambda x: -x["corroboracao"])

    def to_dict(self) -> dict:
        return {
            "cpf": self.cpf,
            "gerado_em": _agora_iso(),
            "fontes_consultadas": sorted(set(self.fontes_consultadas)),
            "confianca_geral": self.confianca_geral(),
            "identificacao": {
                **self.identificacao,
                "_corroboracao": {k: sorted(v) for k, v in self._identificacao_fontes.items()},
            },
            "telefones": self._dump_contatos(self.telefones),
            "emails": self._dump_contatos(self.emails),
            "enderecos": [
                {k: v for k, v in e.items() if k != "_chave"} | {"fontes": sorted(e["fontes"])}
                for e in self.enderecos
            ],
            "vinculos": [
                {**v, "fontes": sorted(v["fontes"])} for v in self.vinculos.values()
            ],
            "empresas": [
                {**c, "fontes": sorted(c["fontes"])} for c in self.empresas.values()
            ],
            "riscos": self.riscos,
        }

    def confianca_geral(self) -> dict:
        """
        Score simples e explicável: cobertura (quantas dimensões foram preenchidas)
        + corroboração (contatos confirmados por 2+ fontes).
        """
        dimensoes = {
            "identificacao": bool(self.identificacao),
            "telefones": bool(self.telefones),
            "emails": bool(self.emails),
            "enderecos": bool(self.enderecos),
            "vinculos": bool(self.vinculos),
            "riscos_avaliados": True,  # sempre avaliamos, mesmo que vazio
        }
        cobertura = sum(dimensoes.values()) / len(dimensoes)
        tel_corrob = sum(1 for r in self.telefones.values() if len(r["fontes"]) >= 2)
        email_corrob = sum(1 for r in self.emails.values() if len(r["fontes"]) >= 2)
        n_fontes = len(set(self.fontes_consultadas))
        return {
            "cobertura_pct": round(cobertura * 100),
            "num_fontes": n_fontes,
            "telefones_corroborados": tel_corrob,
            "emails_corroborados": email_corrob,
            "nivel": (
                "alta" if n_fontes >= 2 and cobertura >= 0.7
                else "media" if n_fontes >= 1 and cobertura >= 0.4
                else "baixa"
            ),
        }


# ==============================================================================
# Normalizadores por fonte
# ==============================================================================

def normalizar_bigdata(dossie: Dossie, dados: dict):
    """Mapeia o payload BigDataCorp (Result[0]) para o modelo canônico."""
    fonte = "BigDataCorp"
    dossie.fontes_consultadas.append(fonte)
    result = dados.get("Result") or []
    if not result:
        return
    r = result[0]

    bd = r.get("BasicData", {}) or {}
    dossie._set_id("nome", bd.get("Name"), fonte)
    dossie._set_id("nascimento", bd.get("BirthDate"), fonte)
    dossie._set_id("idade", bd.get("Age"), fonte)
    dossie._set_id("sexo", bd.get("Gender"), fonte)
    dossie._set_id("nome_mae", bd.get("MotherName"), fonte)
    dossie._set_id("nome_pai", bd.get("FatherName"), fonte)

    for ph in (r.get("ExtendedPhones", {}) or {}).get("Phones", []) or []:
        chave = normalizar_telefone(ph.get("AreaCode"), ph.get("Number"))
        dossie.add_telefone(chave, fonte, {
            "tipo": ph.get("Type"),
            "operadora": ph.get("CurrentCarrier"),
            "ativo": ph.get("IsActive"),
            "ultima_atualizacao": ph.get("LastUpdateDate"),
        })

    for em in (r.get("ExtendedEmails", {}) or {}).get("Emails", []) or []:
        dossie.add_email(em.get("EmailAddress"), fonte, {
            "tipo": em.get("Type"),
            "ativo": em.get("IsActive"),
            "dominio": em.get("Domain"),
        })

    for ad in (r.get("ExtendedAddresses", {}) or {}).get("Addresses", []) or []:
        dossie.add_endereco({
            "logradouro": ad.get("Street") or ad.get("AddressMain"),
            "numero": ad.get("Number"),
            "complemento": ad.get("Complement"),
            "bairro": ad.get("Neighborhood"),
            "cidade": ad.get("City"),
            "uf": ad.get("State"),
            "cep": ad.get("ZipCode"),
        }, fonte)


def normalizar_unitfour_cpf(dossie: Dossie, dados: dict):
    """Mapeia o payload Unitfour (resultado) de consulta de CPF."""
    fonte = "Unitfour"
    dossie.fontes_consultadas.append(fonte)
    res = dados.get("resultado")
    if not isinstance(res, dict):
        return

    dossie._set_id("nome", res.get("nome"), fonte)
    dossie._set_id("nascimento", res.get("dataNascimento"), fonte)
    dossie._set_id("idade", res.get("idade"), fonte)
    dossie._set_id("sexo", res.get("sexo"), fonte)
    dossie._set_id("nome_mae", res.get("nomeMae"), fonte)
    dossie._set_id("situacao_receita", res.get("situacaoReceita"), fonte)

    for tel in res.get("telefones", []) or []:
        chave = normalizar_telefone(tel.get("ddd"), tel.get("numero"))
        dossie.add_telefone(chave, fonte, {
            "operadora": tel.get("operadora"),
            "whatsapp": tel.get("whatsApp"),
            "valido": tel.get("telefoneValido"),
        })

    for em in res.get("emails", []) or []:
        dossie.add_email(em.get("email"), fonte)

    for end in res.get("enderecos", []) or []:
        dossie.add_endereco({
            "logradouro": end.get("logradouro"),
            "numero": end.get("numero"),
            "complemento": end.get("complemento"),
            "bairro": end.get("bairro"),
            "cidade": end.get("cidade"),
            "uf": end.get("uf"),
            "cep": end.get("cep"),
        }, fonte)

    for emp in res.get("participacaoEmpresa", []) or []:
        dossie.add_empresa(emp.get("documento"), emp.get("nome"), fonte, {
            "participacao": emp.get("porcentagemParticipacao"),
            "data_entrada": emp.get("dataEntrada"),
        })


def normalizar_unitfour_ligados(dossie: Dossie, dados: dict):
    fonte = "Unitfour"
    res = dados.get("resultado")
    if not isinstance(res, dict):
        return
    for p in res.get("pessoasLigadas", []) or []:
        dossie.add_vinculo(
            documento=p.get("documento", ""),
            nome=p.get("nome", ""),
            tipo=f"parente ({p.get('parentesco','?')})",
            fonte=fonte,
            extra={"idade": p.get("idade")},
        )


def normalizar_unitfour_pep(dossie: Dossie, dados: dict):
    fonte = "Unitfour"
    res = dados.get("resultado")
    if isinstance(res, dict) and res:
        dossie.add_risco(
            categoria="PEP",
            descricao="Pessoa Exposta Politicamente (COAF)",
            fonte=fonte, gravidade="alta", detalhes=res,
        )


def normalizar_unitfour_mandados(dossie: Dossie, dados: dict):
    fonte = "Unitfour"
    res = dados.get("resultado")
    if isinstance(res, (list, dict)) and res:
        dossie.add_risco(
            categoria="Mandado de Prisão",
            descricao="Mandado de prisão aguardando cumprimento (BNMP/CNJ)",
            fonte=fonte, gravidade="critica", detalhes=res,
        )


def normalizar_unitfour_antecedentes(dossie: Dossie, dados: dict):
    fonte = "Unitfour"
    res = dados.get("resultado")
    if isinstance(res, (list, dict)) and res:
        dossie.add_risco(
            categoria="Antecedentes Criminais",
            descricao="Registro encontrado na Certidão de Antecedentes (PF)",
            fonte=fonte, gravidade="alta", detalhes=res,
        )


# ==============================================================================
# Consolidador — varre o cache por CPF
# ==============================================================================

# Mapeia prefixo de arquivo de cache -> normalizador
_ROTEADOR = [
    ("bigdata_{cpf}", normalizar_bigdata),
    ("unitfour_cpf_{cpf}", normalizar_unitfour_cpf),
    ("unitfour_ligados_{cpf}", normalizar_unitfour_ligados),
    ("unitfour_pep_{cpf}", normalizar_unitfour_pep),
    ("unitfour_mandados_{cpf}", normalizar_unitfour_mandados),
    ("unitfour_antecedentes_{cpf}", normalizar_unitfour_antecedentes),
]


def _carregar_cache(nome: str, cache_dir: str) -> dict | None:
    caminho = os.path.join(cache_dir, f"{nome}.json")
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def consolidar_cpf(cpf: str, cache_dir: str = CACHE_DIR) -> Dossie:
    """
    Localiza todos os caches de um CPF, mescla no modelo canônico e retorna o Dossie.
    Testável offline: só depende dos arquivos em cache_dir.
    """
    cpf_norm = normalizar_cpf(cpf)
    # aceita tanto CPF com zeros à esquerda quanto sem (nomes de arquivo variam)
    variantes = {cpf_norm, cpf_norm.lstrip("0"), so_digitos(cpf)}
    dossie = Dossie(cpf_norm)

    for template, fn in _ROTEADOR:
        for var in variantes:
            dados = _carregar_cache(template.format(cpf=var), cache_dir)
            if dados:
                fn(dossie, dados)
                break
    return dossie


def cpfs_disponiveis_no_cache(cache_dir: str = CACHE_DIR) -> list[str]:
    """Lista CPFs que possuem ao menos um cache (útil para diagnóstico/testes)."""
    encontrados = set()
    for caminho in glob.glob(os.path.join(cache_dir, "*.json")):
        m = re.search(r"(\d{10,11})", os.path.basename(caminho))
        if m:
            encontrados.add(normalizar_cpf(m.group(1)))
    return sorted(encontrados)


# ==============================================================================
# Emissão de laudo (Markdown) — base para o padrão LIT/humanizer
# ==============================================================================

_GRAVIDADE_ORDEM = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}


def dossie_para_markdown(d: dict) -> str:
    """Renderiza o dossiê consolidado em Markdown pericial (rascunho para o humanizer-lit)."""
    ident = d.get("identificacao", {})
    conf = d.get("confianca_geral", {})
    linhas = []
    linhas.append(f"# Dossiê de Investigação — CPF {d['cpf']}")
    linhas.append("")
    linhas.append(f"*Gerado em {d['gerado_em']} · Fontes: {', '.join(d['fontes_consultadas']) or 'nenhuma'} "
                  f"· Confiança: **{conf.get('nivel','?')}** "
                  f"(cobertura {conf.get('cobertura_pct','?')}%, {conf.get('num_fontes','?')} fontes)*")
    linhas.append("")

    linhas.append("## 1. Identificação")
    for campo in ["nome", "nascimento", "idade", "sexo", "nome_mae", "nome_pai", "situacao_receita"]:
        if ident.get(campo):
            linhas.append(f"- **{campo.replace('_',' ').title()}:** {ident[campo]}")
    linhas.append("")

    riscos = sorted(d.get("riscos", []), key=lambda r: _GRAVIDADE_ORDEM.get(r.get("gravidade"), 9))
    linhas.append("## 2. Sinais de Risco")
    if riscos:
        for r in riscos:
            linhas.append(f"- **[{r['gravidade'].upper()}] {r['categoria']}** — {r['descricao']} _(fonte: {r['fonte']})_")
    else:
        linhas.append("- Nenhum sinal de risco (PEP, mandado, antecedente) identificado nas fontes consultadas.")
    linhas.append("")

    linhas.append("## 3. Telefones")
    if d.get("telefones"):
        for t in d["telefones"]:
            corr = "✔ corroborado" if t["corroboracao"] >= 2 else "1 fonte"
            op = t["detalhes"].get("operadora", "")
            linhas.append(f"- {t['valor']} — {corr} ({', '.join(t['fontes'])}){f' · {op}' if op else ''}")
    else:
        linhas.append("- Nenhum telefone encontrado.")
    linhas.append("")

    linhas.append("## 4. E-mails")
    if d.get("emails"):
        for e in d["emails"]:
            corr = "✔ corroborado" if e["corroboracao"] >= 2 else "1 fonte"
            linhas.append(f"- {e['valor']} — {corr} ({', '.join(e['fontes'])})")
    else:
        linhas.append("- Nenhum e-mail encontrado.")
    linhas.append("")

    linhas.append("## 5. Endereços")
    if d.get("enderecos"):
        for a in d["enderecos"]:
            partes = [a.get("logradouro"), a.get("numero"), a.get("bairro"),
                      a.get("cidade"), a.get("uf"), a.get("cep")]
            linhas.append(f"- {', '.join([str(p) for p in partes if p])} _(fontes: {', '.join(a['fontes'])})_")
    else:
        linhas.append("- Nenhum endereço encontrado.")
    linhas.append("")

    linhas.append("## 6. Vínculos (parentes/sócios)")
    if d.get("vinculos"):
        for v in d["vinculos"]:
            linhas.append(f"- {v['nome']} — {v['tipo']} (doc: {v['documento'] or 'n/d'})")
    else:
        linhas.append("- Nenhum vínculo encontrado.")
    linhas.append("")

    linhas.append("## 7. Participações Empresariais")
    if d.get("empresas"):
        for c in d["empresas"]:
            linhas.append(f"- {c['nome']} (CNPJ {c['cnpj']})")
    else:
        linhas.append("- Nenhuma participação empresarial encontrada.")
    linhas.append("")

    return "\n".join(linhas)


# ==============================================================================
# ENRIQUECIMENTO CSINT — folding de reputação/vazamentos por contato
# ==============================================================================

def _get_ci(d: dict, candidatos: list) -> any:
    """Busca a primeira chave (case-insensitive) presente no dict."""
    if not isinstance(d, dict):
        return None
    baixo = {str(k).lower(): k for k in d.keys()}
    for c in candidatos:
        if c.lower() in baixo:
            return d[baixo[c.lower()]]
    return None


def resumir_csint_seon(data: dict) -> dict:
    """
    Extrai, de forma DEFENSIVA, um resumo do payload SEON (email/telefone) do CSINT.
    As chaves reais podem variar; por isso tentamos vários nomes candidatos.
    """
    if not isinstance(data, dict):
        return {}
    # se veio o sumário de cache (não o dado bruto), sinaliza para ler do cache
    if data.get("cache_id") and "resumo_dos_dados" in data:
        return {"_ver_cache": data.get("cache_id")}

    out = {}
    existe = _get_ci(data, ["exists", "found", "valid", "deliverable", "is_valid"])
    if existe is not None:
        out["existe"] = existe

    score = _get_ci(data, ["score", "fraud_score", "risk_score", "reputation"])
    if score is not None:
        out["score"] = score

    contas = []
    acc = _get_ci(data, ["accounts", "account_details", "social_media", "accountDetails", "registered_profiles"])
    if isinstance(acc, dict):
        for plataforma, info in acc.items():
            reg = info.get("registered") if isinstance(info, dict) else info
            if reg:
                contas.append(plataforma)
    elif isinstance(acc, list):
        for it in acc:
            if isinstance(it, dict) and (it.get("registered") or it.get("exists")):
                contas.append(it.get("name") or it.get("platform") or it.get("site"))
    contas = sorted({c for c in contas if c})
    if contas:
        out["contas_vinculadas"] = contas
    return out


def resumir_csint_vazamentos(data: dict) -> dict:
    """Resumo defensivo do payload de busca universal (vazamentos)."""
    if not isinstance(data, dict):
        return {}
    if data.get("cache_id") and "resumo_dos_dados" in data:
        return {"_ver_cache": data.get("cache_id")}

    fontes = []
    total = 0
    # tenta achar listas de resultados por provedor
    for k, v in data.items():
        if isinstance(v, list) and v:
            fontes.append(k)
            total += len(v)
        elif isinstance(v, dict):
            res = _get_ci(v, ["results", "data", "entries", "found"])
            if isinstance(res, list) and res:
                fontes.append(k)
                total += len(res)
    resumo = {"total_registros": total}
    if fontes:
        resumo["fontes_com_achado"] = sorted(set(fontes))
    resumo["vazamento_encontrado"] = total > 0
    return resumo


def fold_csint_no_dossie(dossie: "Dossie", tipo: str, valor: str,
                         seon_data: dict | None = None, leak_data: dict | None = None):
    """
    Anexa os achados do CSINT ao registro de telefone/e-mail correspondente no dossiê.
    tipo: 'email' ou 'telefone'. valor: a chave normalizada do contato.
    """
    mapa = dossie.emails if tipo == "email" else dossie.telefones
    chave = normalizar_email(valor) if tipo == "email" else normalizar_telefone(completo=valor)
    reg = mapa.get(chave)
    if reg is None:
        return
    csint = reg["detalhes"].setdefault("csint", {})
    if seon_data is not None:
        resumo = resumir_csint_seon(seon_data)
        if resumo:
            csint["seon"] = resumo
    if leak_data is not None:
        vaz = resumir_csint_vazamentos(leak_data)
        if vaz:
            csint["vazamentos"] = vaz
            if vaz.get("vazamento_encontrado"):
                dossie.add_risco(
                    categoria="Vazamento de Dados",
                    descricao=f"{tipo.capitalize()} {valor} encontrado em base de vazamentos "
                              f"({vaz.get('total_registros', '?')} registros)",
                    fonte="CSINT", gravidade="media", detalhes=vaz,
                )


def alvos_para_enriquecer(dossie_dict: dict, apenas_corroborados: bool = False,
                          max_emails: int = 10, max_telefones: int = 10, max_cnpjs: int = 10) -> dict:
    """
    A partir de um dossiê consolidado (dict), lista os alvos de enriquecimento:
      - emails (str)
      - telefones em formato E.164 (+55...)
      - cnpjs (14 dígitos)
    """
    def _filtra(itens):
        if apenas_corroborados:
            itens = [i for i in itens if i.get("corroboracao", 0) >= 2]
        return itens

    emails = [e["valor"] for e in _filtra(dossie_dict.get("emails", []))][:max_emails]

    telefones = []
    for t in _filtra(dossie_dict.get("telefones", []))[:max_telefones]:
        dig = so_digitos(t["valor"])
        if dig and not dig.startswith("55"):
            dig = "55" + dig
        telefones.append("+" + dig)

    cnpjs = [so_digitos(c["cnpj"]).zfill(14) for c in dossie_dict.get("empresas", [])
             if so_digitos(c.get("cnpj", ""))][:max_cnpjs]

    return {"emails": emails, "telefones": telefones, "cnpjs": cnpjs}


# ==============================================================================
# TIMELINE DE ALTERAÇÕES DE CNPJ (BigDataCorp evolution/historical)
# ==============================================================================

_TL_DATE_KEYS = [
    "QueryDate", "ReferenceDate", "SnapshotDate", "Date", "DataConsulta", "Data",
    "LastUpdateDate", "CreationDate", "RegisterDate", "StatusDate", "Period", "Month",
]

# rótulo canônico -> possíveis chaves na fonte
_TL_CAMPOS = {
    "Razão Social": ["OfficialName", "Name", "RazaoSocial", "CompanyName", "TradeName2"],
    "Nome Fantasia": ["TradeName", "FantasyName", "NomeFantasia"],
    "Situação Cadastral": ["RegisterStatus", "Status", "SituacaoCadastral",
                            "CompanyRegisterStatus", "TaxRegimeStatus"],
    "Capital Social": ["ShareCapital", "Capital", "CapitalSocial"],
    "Natureza Jurídica": ["LegalNature", "NaturezaJuridica", "CompanyType"],
    "Atividade Principal": ["MainActivity", "PrimaryActivity", "AtividadePrincipal", "CNAE", "MainCnae"],
    "Nº de Funcionários": ["NumberOfEmployees", "Employees", "QuantidadeFuncionarios", "TotalEmployees"],
    "Porte": ["CompanySize", "Size", "Porte"],
    "Endereço": ["Address", "AddressMain", "Logradouro", "FullAddress"],
    "Cidade/UF": ["City", "Cidade"],
}


def _tl_parse_data(valor) -> str:
    """Normaliza uma data para chave ordenável (YYYY-MM-DD quando possível)."""
    if valor is None:
        return ""
    s = str(valor).strip()
    if not s:
        return ""
    # ISO / com hora
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # dd/mm/yyyy
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    # yyyymm ou yyyy-mm
    m = re.match(r"(\d{4})-?(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    m = re.match(r"(\d{4})$", s)
    if m:
        return f"{m.group(1)}-01-01"
    return s


def _tl_valor_str(v) -> str:
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v).strip()


def _tl_extrair_snapshots(data) -> list:
    """Extrai a lista de snapshots de um payload de evolução/histórico."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        # ignora a casca Result[0] do BigDataCorp se vier inteira
        if "Result" in data and isinstance(data["Result"], list) and data["Result"]:
            r0 = data["Result"][0]
            for chave in ["CompanyEvolutionData", "CompanyEvolution", "HistoryBasicData", "HistoryData"]:
                if chave in r0:
                    return _tl_extrair_snapshots(r0[chave])
        # procura a primeira lista de dicts
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        return [data]  # snapshot único
    return []


# --- Parser calibrado para o formato REAL do BigDataCorp (HistoryBasicData) ---
# Cada lista de histórico: rótulo + função que extrai o valor de uma entrada.
_HIST_LISTS_SIMPLES = {
    "NameHistoryList": ("Razão Social", lambda e: e.get("OfficialName") or e.get("Name")),
    "TradeNameHistoryList": ("Nome Fantasia", lambda e: e.get("TradeName")),
    "TaxRegimeHistoryList": ("Regime Tributário", lambda e: e.get("TaxRegime")),
    "TaxIdStatusHistoryList": ("Situação Cadastral", lambda e: e.get("TaxIdStatus")),
    "CapitalHistoryList": ("Capital Social", lambda e: e.get("Capital")),
    "LegalNatureHistoryList": ("Natureza Jurídica", lambda e: e.get("LegalNature")),
    "HeadquarterHistoryList": ("Sede/Endereço", lambda e: e.get("Address") or e.get("FullAddress")),
}


def _timeline_history_basic_data(h: dict) -> list:
    """Timeline a partir do HistoryBasicData (listas de alteração por atributo)."""
    eventos = []
    for lista, (rotulo, extrai) in _HIST_LISTS_SIMPLES.items():
        entradas = h.get(lista)
        if not isinstance(entradas, list):
            continue
        ordenadas = sorted(entradas, key=lambda e: _tl_parse_data(e.get("ChangeDate")))
        ultimo = None
        for e in ordenadas:
            val = extrai(e)
            if val in (None, "", []):
                continue
            atual = _tl_valor_str(val)
            data = _tl_parse_data(e.get("ChangeDate"))
            if ultimo is None:
                eventos.append({"data": data, "campo": rotulo, "tipo": "inicial", "de": None, "para": atual})
            elif atual != ultimo:
                eventos.append({"data": data, "campo": rotulo, "tipo": "alteracao", "de": ultimo, "para": atual})
            ultimo = atual

    # CNAE: cada entrada é uma atividade (podem coexistir). Registramos inclusões.
    cnae = h.get("CnaeHistoryList")
    if isinstance(cnae, list):
        for e in sorted(cnae, key=lambda x: _tl_parse_data(x.get("ChangeDate"))):
            code = e.get("Code")
            if not code:
                continue
            desc = e.get("Activity", "")
            principal = " [principal]" if e.get("IsMainEconomicActivity") else ""
            eventos.append({
                "data": _tl_parse_data(e.get("ChangeDate")),
                "campo": "Atividade Econômica (CNAE)", "tipo": "inclusao",
                "de": None, "para": f"{code} - {desc}{principal}",
            })
    return eventos


# Campos de contagem que vivem só no DataHistoryOverTime (evolução mensal).
_EVOL_CONTAGENS = {
    "Nº de Funcionários": ["QtyEmployees"],
    "Nº de Sócios (QSA)": ["QtyQSA"],
    "Nº de Filiais": ["QtySubsidiaries"],
}


def _timeline_evolution_over_time(ev: dict) -> list:
    """Timeline de contagens (funcionários/QSA/filiais) a partir de DataHistoryOverTime."""
    snaps = ev.get("DataHistoryOverTime")
    if not isinstance(snaps, list):
        return []
    ordenados = sorted(snaps, key=lambda s: _tl_parse_data(s.get("Reference")))
    eventos = []
    for rotulo, cands in _EVOL_CONTAGENS.items():
        ultimo = None
        for s in ordenados:
            val = _get_ci(s, cands)
            if val is None:
                continue
            atual = _tl_valor_str(val)
            data = _tl_parse_data(s.get("Reference"))
            if ultimo is None:
                eventos.append({"data": data, "campo": rotulo, "tipo": "inicial", "de": None, "para": atual})
            elif atual != ultimo:
                eventos.append({"data": data, "campo": rotulo, "tipo": "alteracao", "de": ultimo, "para": atual})
            ultimo = atual
    return eventos


def _timeline_generica(*fontes) -> list:
    """Fallback: diff de snapshots para formatos desconhecidos."""
    snapshots = []
    for fonte in fontes:
        for snap in _tl_extrair_snapshots(fonte):
            data = ""
            for dk in _TL_DATE_KEYS:
                val = _get_ci(snap, [dk])
                if val:
                    data = _tl_parse_data(val)
                    if data:
                        break
            snapshots.append((data, snap))
    snapshots.sort(key=lambda x: (x[0] == "", x[0]))
    eventos = []
    for rotulo, candidatos in _TL_CAMPOS.items():
        ultimo = None
        for data, snap in snapshots:
            val = _get_ci(snap, candidatos)
            if val in (None, "", []):
                continue
            atual = _tl_valor_str(val)
            if ultimo is None:
                eventos.append({"data": data, "campo": rotulo, "tipo": "inicial", "de": None, "para": atual})
                ultimo = atual
            elif atual != ultimo:
                eventos.append({"data": data, "campo": rotulo, "tipo": "alteracao", "de": ultimo, "para": atual})
                ultimo = atual
    return eventos


def construir_timeline_cnpj(*fontes) -> list:
    """
    Constrói a timeline cronológica de alterações de um CNPJ. Reconhece o formato
    REAL do BigDataCorp (HistoryBasicData + CompanyEvolutionData.DataHistoryOverTime)
    e cai para um motor genérico de diff em formatos desconhecidos.
    Cada evento: {data, campo, tipo: 'inicial'|'alteracao'|'inclusao', de, para}.
    Determinístico e puro (testável offline).
    """
    eventos = []
    usou_parser_especifico = False

    for fonte in fontes:
        # desembrulha Result[0] do BigDataCorp, se vier inteiro
        raiz = fonte
        if isinstance(fonte, dict) and "Result" in fonte and isinstance(fonte["Result"], list) and fonte["Result"]:
            raiz = fonte["Result"][0]

        if isinstance(raiz, dict):
            h = raiz.get("HistoryBasicData")
            if isinstance(h, dict):
                eventos += _timeline_history_basic_data(h)
                usou_parser_especifico = True
            ev = raiz.get("CompanyEvolutionData")
            if isinstance(ev, dict):
                eventos += _timeline_evolution_over_time(ev)
                usou_parser_especifico = True

    if not usou_parser_especifico:
        eventos = _timeline_generica(*fontes)

    eventos.sort(key=lambda e: (e["data"] == "", e["data"], e["campo"]))
    return eventos


def timeline_para_markdown(cnpj: str, nome: str, timeline: list) -> str:
    linhas = [f"### Timeline de Alterações — {nome or 'Empresa'} (CNPJ {cnpj})", ""]
    if not timeline:
        linhas.append("_Nenhuma alteração histórica identificada nas fontes consultadas._")
        return "\n".join(linhas)
    data_atual = None
    for ev in timeline:
        if ev["data"] != data_atual:
            data_atual = ev["data"]
            linhas.append(f"\n**{data_atual or 'data não informada'}**")
        if ev["tipo"] == "inicial":
            linhas.append(f"- {ev['campo']}: registro inicial → `{ev['para']}`")
        elif ev["tipo"] == "inclusao":
            linhas.append(f"- {ev['campo']}: incluída → `{ev['para']}`")
        else:
            linhas.append(f"- {ev['campo']}: `{ev['de']}` → `{ev['para']}`")
    return "\n".join(linhas)


if __name__ == "__main__":
    # Execução direta: gera dossiê de um CPF do cache para inspeção manual.
    import sys
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    if not alvo:
        print("CPFs disponíveis no cache:")
        for c in cpfs_disponiveis_no_cache():
            print("  ", c)
        sys.exit(0)
    d = consolidar_cpf(alvo).to_dict()
    print(dossie_para_markdown(d))
