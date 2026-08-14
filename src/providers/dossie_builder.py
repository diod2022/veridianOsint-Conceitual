# -*- coding: utf-8 -*-
"""
src/providers/dossie_builder.py — Camada de consolidação de dossiê do Agente Investigador.
Transforma consultas atômicas espalhadas em cache_consultas/ em MODELO DE ENTIDADE CANÔNICO ("Subject").
"""

from __future__ import annotations

import os
import re
import json
import glob
from datetime import datetime, timezone
from typing import Optional, Union, Dict, List, Any

from src.core.config import CACHE_DIR
from src.core.security import (
    so_digitos,
    normalizar_cpf,
    normalizar_telefone,
    normalizar_email
)

def normalizar_nome(nome: str) -> str:
    """Normaliza nomes próprios removendo espaços excessivos e capitalizando adequadamente."""
    if not nome:
        return ""
    partes = [p for p in str(nome).strip().split() if p]
    return " ".join(partes).upper()

class ScoreConfianca:
    """Calcula e avalia a pontuação de confiança de dados e fontes corroboradas."""
    def __init__(self, base: int = 50):
        self.score = base
        self.fontes: set = set()
        
    def adicionar_fonte(self, fonte: str, peso: int = 25):
        if fonte not in self.fontes:
            self.fontes.add(fonte)
            self.score = min(100, self.score + peso)
            
    @property
    def corroborado(self) -> bool:
        return len(self.fontes) >= 2
        
    @property
    def classificacao(self) -> str:
        if self.score >= 75:
            return "ALTA"
        elif self.score >= 50:
            return "MEDIA"
        return "BAIXA"

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
        self.telefones_map: dict[str, dict] = {}   # chave: telefone normalizado
        self.emails_map: dict[str, dict] = {}      # chave: email normalizado
        self.enderecos: list[dict] = []
        self.vinculos_map: dict[str, dict] = {}    # chave: documento do vinculado
        self.empresas_map: dict[str, dict] = {}    # chave: cnpj (participações)
        self.riscos: list[dict] = []           # PEP, mandados, antecedentes, processos
        self.fontes_consultadas: list[str] = []
        self._identificacao_fontes: dict[str, set] = {}  # campo -> fontes

    @property
    def telefones(self) -> list[dict]:
        return self._dump_contatos(self.telefones_map)

    @property
    def emails(self) -> list[dict]:
        return self._dump_contatos(self.emails_map)

    @property
    def vinculos(self) -> list[dict]:
        return [
            {**v, "fontes": sorted(v["fontes"])} for v in self.vinculos_map.values()
        ]

    @property
    def empresas(self) -> list[dict]:
        return [
            {**c, "fontes": sorted(c["fontes"])} for c in self.empresas_map.values()
        ]

    def _set_id(self, campo: str, valor, fonte: str):
        if valor in (None, "", []):
            return
        if campo not in self.identificacao:
            self.identificacao[campo] = valor
        self._identificacao_fontes.setdefault(campo, set()).add(fonte)

    def add_telefone(self, chave: str, fonte: str, detalhes: dict | None = None, dados_extras: dict | None = None):
        if not chave:
            return
        extra = detalhes or dados_extras or {}
        reg = self.telefones_map.setdefault(chave, {"valor": chave, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update({k: v for k, v in extra.items() if v not in (None, "")})

    adicionar_telefone = add_telefone

    def add_email(self, chave: str, fonte: str, detalhes: dict | None = None, dados_extras: dict | None = None):
        chave = normalizar_email(chave)
        if not chave:
            return
        extra = detalhes or dados_extras or {}
        reg = self.emails_map.setdefault(chave, {"valor": chave, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update({k: v for k, v in extra.items() if v not in (None, "")})

    adicionar_email = add_email

    def add_endereco(self, endereco: dict, fonte: str):
        chave = (
            f"{str(endereco.get('logradouro','')).strip().lower()}|"
            f"{so_digitos(endereco.get('numero',''))}|"
            f"{so_digitos(endereco.get('cep',''))}"
        )
        for e in self.enderecos:
            if e.get("_chave") == chave:
                e["fontes"].add(fonte)
                return
        self.enderecos.append({**endereco, "_chave": chave, "fontes": {fonte}})

    adicionar_endereco = add_endereco

    def add_vinculo(self, documento: str, nome: str, tipo: str, fonte: str, extra: dict | None = None):
        doc = so_digitos(documento) or nome
        if not doc:
            return
        reg = self.vinculos_map.setdefault(doc, {
            "documento": so_digitos(documento), "nome": nome, "tipo": tipo,
            "fontes": set(), "detalhes": {}
        })
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update(extra)

    adicionar_vinculo = add_vinculo

    def add_empresa(self, cnpj: str, nome: str, fonte: str, extra: dict | None = None):
        c = so_digitos(cnpj)
        if not c:
            return
        reg = self.empresas_map.setdefault(c, {"cnpj": c, "nome": nome, "fontes": set(), "detalhes": {}})
        reg["fontes"].add(fonte)
        if extra:
            reg["detalhes"].update(extra)

    adicionar_empresa = add_empresa

    def add_risco(self, categoria: str, descricao: str, fonte: str, gravidade: str = "media", detalhes=None):
        self.riscos.append({
            "categoria": categoria, "descricao": descricao, "gravidade": gravidade,
            "fonte": fonte, "detalhes": detalhes or {},
        })

    adicionar_risco = add_risco

    @staticmethod
    def _dump_contatos(mapa: dict) -> list:
        saida = []
        for reg in mapa.values():
            fontes = sorted(reg["fontes"])
            corrob = len(fontes) >= 2
            score = 50 + (25 * (len(fontes) - 1)) if corrob else 50
            saida.append({
                "valor": reg["valor"],
                "corroborado": corrob,
                "corroboracao": len(fontes),
                "score_confianca": min(100, score),
                "fontes": fontes,
                "detalhes": reg["detalhes"],
            })
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
            "telefones": self.telefones,
            "emails": self.emails,
            "enderecos": [
                {k: v for k, v in e.items() if k != "_chave"} | {"fontes": sorted(e["fontes"])}
                for e in self.enderecos
            ],
            "vinculos": self.vinculos,
            "empresas": self.empresas,
            "riscos": self.riscos,
        }

    def confianca_geral(self) -> dict:
        dimensoes = {
            "identificacao": bool(self.identificacao),
            "telefones": bool(self.telefones_map),
            "emails": bool(self.emails_map),
            "enderecos": bool(self.enderecos),
            "vinculos": bool(self.vinculos_map),
            "riscos_avaliados": True,
        }
        cobertura = sum(dimensoes.values()) / len(dimensoes)
        tel_corrob = sum(1 for r in self.telefones_map.values() if len(r["fontes"]) >= 2)
        email_corrob = sum(1 for r in self.emails_map.values() if len(r["fontes"]) >= 2)
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

def normalizar_bigdata_cpf(dossie: Dossie, dados: dict):
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

    for ad in res.get("enderecos", []) or []:
        dossie.add_endereco({
            "logradouro": ad.get("logradouro"),
            "numero": ad.get("numero"),
            "complemento": ad.get("complemento"),
            "bairro": ad.get("bairro"),
            "cidade": ad.get("cidade"),
            "uf": ad.get("uf"),
            "cep": ad.get("cep"),
        }, fonte)

def normalizar_unitfour_parentes(dossie: Dossie, dados: dict):
    fonte = "Unitfour (Parentes)"
    dossie.fontes_consultadas.append(fonte)
    res = dados.get("resultado") or []
    if isinstance(res, dict):
        res = [res]
    for p in res:
        doc = so_digitos(p.get("cpf") or p.get("documento"))
        nome = p.get("nome") or ""
        vinculo = p.get("vinculo") or p.get("grauParentesco") or "parente"
        dossie.add_vinculo(doc, nome, vinculo, fonte)

def normalizar_unitfour_pep(dossie: Dossie, dados: dict):
    fonte = "Unitfour (PEP)"
    dossie.fontes_consultadas.append(fonte)
    res = dados.get("resultado")
    if isinstance(res, dict) and res.get("constaPep"):
        dossie.add_risco("PEP", f"Enquadrado como PEP: {res.get('descricaoFuncao', '')}", fonte, gravidade="alta", detalhes=res)

def normalizar_unitfour_mandados(dossie: Dossie, dados: dict):
    fonte = "Unitfour (Mandados)"
    dossie.fontes_consultadas.append(fonte)
    res = dados.get("resultado") or []
    if isinstance(res, dict):
        res = [res]
    for m in res:
        if m.get("situacao") == "Aguardando Cumprimento" or m.get("mandadoAtivo"):
            dossie.add_risco("MANDADO_PRISAO", f"Mandado ativo: {m.get('numeroMandado', '')}", fonte, gravidade="critica", detalhes=m)

def normalizar_unitfour_antecedentes(dossie: Dossie, dados: dict):
    fonte = "Unitfour (Antecedentes PF)"
    dossie.fontes_consultadas.append(fonte)
    res = dados.get("resultado")
    if isinstance(res, dict) and res.get("constaAntecedentes"):
        dossie.add_risco("ANTECEDENTES", "Constam antecedentes na Polícia Federal", fonte, gravidade="alta", detalhes=res)

# ==============================================================================
# Consolidação e Laudo
# ==============================================================================

def consolidar_cpf(cpf: str, cache_dir: str = CACHE_DIR) -> Dossie:
    cpf_limpo = normalizar_cpf(cpf)
    d = Dossie(cpf_limpo)

    # BigDataCorp
    caminho_bdc = os.path.join(cache_dir, f"bigdata_{cpf_limpo}.json")
    if os.path.exists(caminho_bdc):
        try:
            with open(caminho_bdc, "r", encoding="utf-8") as f:
                normalizar_bigdata_cpf(d, json.load(f))
        except Exception:
            pass

    # Unitfour Cadastral
    caminho_u4 = os.path.join(cache_dir, f"unitfour_cpf_{cpf_limpo}.json")
    if os.path.exists(caminho_u4):
        try:
            with open(caminho_u4, "r", encoding="utf-8") as f:
                normalizar_unitfour_cpf(d, json.load(f))
        except Exception:
            pass

    # Parentes
    caminho_u4_par = os.path.join(cache_dir, f"unitfour_parentes_{cpf_limpo}.json")
    if os.path.exists(caminho_u4_par):
        try:
            with open(caminho_u4_par, "r", encoding="utf-8") as f:
                normalizar_unitfour_parentes(d, json.load(f))
        except Exception:
            pass

    # PEP
    caminho_u4_pep = os.path.join(cache_dir, f"unitfour_pep_{cpf_limpo}.json")
    if os.path.exists(caminho_u4_pep):
        try:
            with open(caminho_u4_pep, "r", encoding="utf-8") as f:
                normalizar_unitfour_pep(d, json.load(f))
        except Exception:
            pass

    # Mandados
    caminho_u4_mand = os.path.join(cache_dir, f"unitfour_mandados_{cpf_limpo}.json")
    if os.path.exists(caminho_u4_mand):
        try:
            with open(caminho_u4_mand, "r", encoding="utf-8") as f:
                normalizar_unitfour_mandados(d, json.load(f))
        except Exception:
            pass

    # Antecedentes
    caminho_u4_ant = os.path.join(cache_dir, f"unitfour_antecedentes_{cpf_limpo}.json")
    if os.path.exists(caminho_u4_ant):
        try:
            with open(caminho_u4_ant, "r", encoding="utf-8") as f:
                normalizar_unitfour_antecedentes(d, json.load(f))
        except Exception:
            pass

    return d

def cpfs_disponiveis_no_cache(cache_dir: str = CACHE_DIR) -> list[str]:
    cpfs = set()
    padroes = ["bigdata_*.json", "unitfour_cpf_*.json", "dossie_*.json"]
    for p in padroes:
        for f in glob.glob(os.path.join(cache_dir, p)):
            nome = os.path.basename(f)
            doc = re.search(r"\d{11}", nome)
            if doc:
                cpfs.add(doc.group(0))
    return sorted(cpfs)

def alvos_para_enriquecer(d: dict, apenas_corroborados: bool = False, max_emails: int = 10, max_telefones: int = 10, max_cnpjs: int = 10) -> dict:
    emails = [e["valor"] for e in d.get("emails", []) if not apenas_corroborados or e.get("corroborado")][:max_emails]
    telefones = [t["valor"] for t in d.get("telefones", []) if not apenas_corroborados or t.get("corroborado")][:max_telefones]
    cnpjs = [c["cnpj"] for c in d.get("empresas", [])][:max_cnpjs]
    return {"emails": emails, "telefones": telefones, "cnpjs": cnpjs}

def fold_csint_no_dossie(dossie: Dossie, tipo: str, valor: str, seon_data: dict | None = None, leak_data: dict | None = None):
    extra = {}
    if seon_data:
        extra["seon"] = seon_data
    if leak_data:
        extra["vazamentos"] = leak_data
    if tipo == "telefone":
        dossie.add_telefone(valor, "CSINT SEON", extra)
    elif tipo == "email":
        dossie.add_email(valor, "CSINT SEON", extra)

def construir_timeline_cnpj(dados: dict) -> list[dict]:
    timeline = []
    r = (dados.get("Result") or [{}])[0]
    for ev in r.get("CompanyEvolution", []) or []:
        timeline.append({
            "data": ev.get("Date") or ev.get("EventDate") or "N/D",
            "evento": ev.get("Event") or ev.get("Title") or "Alteração Cadastral",
            "detalhes": ev.get("Details") or ev.get("Description") or str(ev)
        })
    for h in r.get("HistoryBasicData", []) or []:
        timeline.append({
            "data": h.get("ChangeDate") or "N/D",
            "evento": f"Mudança em {h.get('FieldName', 'Campo')}",
            "detalhes": f"De: {h.get('OldValue')} -> Para: {h.get('NewValue')}"
        })
    return sorted(timeline, key=lambda x: str(x.get("data", "")))

def timeline_para_markdown(cnpj: str, nome: str, timeline: list[dict]) -> str:
    md = [f"### Timeline Cronológica — CNPJ {cnpj} ({nome or 'Empresa'})\n"]
    if not timeline:
        md.append("_Nenhuma alteração histórica registrada no período._\n")
    else:
        for item in timeline:
            md.append(f"- **{item['data']}**: {item['evento']}\n  _{item['detalhes']}_\n")
    return "\n".join(md)

def dossie_para_markdown(d: dict) -> str:
    md = [
        f"# Dossiê de Inteligência e Qualificação Pericial — CPF {d.get('cpf')}",
        f"\n**Gerado em:** {d.get('gerado_em', '')}",
        f"**Fontes Consultadas:** {', '.join(d.get('fontes_consultadas', [])) or 'Nenhuma'}",
        f"**Nível de Confiança Geral:** {d.get('confianca_geral', {}).get('nivel', '').upper()} ({d.get('confianca_geral', {}).get('cobertura_pct', 0)}% de cobertura)\n",
        "## 1. Identificação Cadastral",
    ]
    ident = d.get("identificacao", {})
    for k, v in ident.items():
        if not k.startswith("_"):
            md.append(f"- **{k.capitalize()}:** {v}")

    md.append("\n## 2. Telefones Identificados")
    for t in d.get("telefones", []):
        corrob = " [CORROBORADO 2+ FONTES]" if t.get("corroborado") else ""
        md.append(f"- **{t['valor']}**{corrob} — Fontes: {', '.join(t.get('fontes', []))}")

    md.append("\n## 3. Endereços de E-mail")
    for e in d.get("emails", []):
        corrob = " [CORROBORADO 2+ FONTES]" if e.get("corroborado") else ""
        md.append(f"- **{e['valor']}**{corrob} — Fontes: {', '.join(e.get('fontes', []))}")

    md.append("\n## 4. Endereços Físicos")
    for a in d.get("enderecos", []):
        md.append(f"- {a.get('logradouro', '')}, {a.get('numero', '')} - {a.get('bairro', '')}, {a.get('cidade', '')}/{a.get('uf', '')} CEP {a.get('cep', '')}")

    md.append("\n## 5. Vínculos e Pessoas Ligadas")
    for v in d.get("vinculos", []):
        md.append(f"- **{v.get('nome', '')}** ({v.get('tipo', '')}) — Doc: {v.get('documento', '')}")

    md.append("\n## 6. Sinais de Risco e Compliance")
    riscos = d.get("riscos", [])
    if not riscos:
        md.append("- _Nenhum alerta crítico ou mandado de prisão encontrado._")
    else:
        for r in riscos:
            md.append(f"- **[{r.get('gravidade', '').upper()}] {r.get('categoria', '')}:** {r.get('descricao', '')}")

    return "\n".join(md)
