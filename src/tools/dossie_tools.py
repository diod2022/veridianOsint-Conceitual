import os
import json
import sys
from typing import Union, Optional
from src.app import mcp
from src.core.config import CACHE_DIR
from src.core.cache import obter_caminho_cache_seguro
from src.providers import dossie_builder, csint, bigdatacorp

def _ler_cache_raw(chave: str):
    caminho = obter_caminho_cache_seguro(chave)
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

@mcp.tool()
async def investigador_gerar_dossie(cpf: Union[str, int], salvar_laudo: bool = True) -> dict:
    """
    Consolida TODAS as consultas já feitas sobre um CPF (presentes no cache local)
    em um DOSSIÊ ÚNICO e estruturado: identificação, telefones/e-mails deduplicados
    e CORROBORADOS entre fontes, endereços, vínculos, participações empresariais e
    sinais de risco (PEP, mandado de prisão, antecedentes). Não gasta créditos de API
    — apenas cruza o que já foi coletado.

    Args:
        cpf: O CPF do alvo (com ou sem máscara).
        salvar_laudo: Se True (padrão), grava o dossiê em JSON e um laudo em Markdown no cache.
    """
    d_obj = dossie_builder.consolidar_cpf(str(cpf), cache_dir=CACHE_DIR)
    d = d_obj.to_dict()

    if not d["fontes_consultadas"]:
        return {
            "status": "vazio",
            "cpf": d["cpf"],
            "mensagem": ("Nenhuma consulta encontrada no cache para este CPF. "
                         "Rode primeiro bigdata_consultar_cpf e/ou unitfour_consultar_cpf."),
        }

    laudo_md = dossie_builder.dossie_para_markdown(d)

    if salvar_laudo:
        try:
            base = os.path.join(CACHE_DIR, f"dossie_{d['cpf']}")
            with open(f"{base}.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            with open(f"{base}.md", "w", encoding="utf-8") as f:
                f.write(laudo_md)
        except Exception as e:
            print(f"[DOSSIE] Falha ao salvar laudo: {e}", file=sys.stderr, flush=True)

    return {
        "status": "sucesso",
        "cpf": d["cpf"],
        "confianca_geral": d["confianca_geral"],
        "fontes_consultadas": d["fontes_consultadas"],
        "identificacao": d["identificacao"],
        "contagens": {
            "telefones": len(d["telefones"]),
            "emails": len(d["emails"]),
            "enderecos": len(d["enderecos"]),
            "vinculos": len(d["vinculos"]),
            "empresas": len(d["empresas"]),
            "riscos": len(d["riscos"]),
        },
        "riscos": d["riscos"],
        "laudo_markdown": laudo_md,
        "cache_id": f"dossie_{d['cpf']}",
        "instrucao": ("Dossiê consolidado. Use 'investigador_ler_cache' com o cache_id "
                      f"'dossie_{d['cpf']}' para explorar telefones/e-mails/vínculos completos."),
    }

@mcp.tool()
async def investigador_enriquecer_dossie(
    cpf: Union[str, int],
    max_emails: int = 10,
    max_telefones: int = 10,
    max_cnpjs: int = 10,
    apenas_corroborados: bool = False,
    incluir_vazamentos: bool = True,
) -> dict:
    """
    Enriquece o dossiê de um CPF executando automaticamente:
      • Para CADA e-mail: reputação SEON + busca de vazamentos (opcional).
      • Para CADA telefone: reputação SEON, convertendo para E.164.
      • Para CADA CNPJ ligado: alterações históricas + TIMELINE de mudanças.
    Todas as chamadas são cache-first. Consolida os achados de volta no dossiê.

    Args:
        cpf: CPF do alvo (com ou sem máscara).
        max_emails/max_telefones/max_cnpjs: tetos de itens a enriquecer.
        apenas_corroborados: se True, só enriquece contatos confirmados por 2+ fontes.
        incluir_vazamentos: se True, roda também a busca universal de vazamentos por e-mail.
    """
    d_obj = dossie_builder.consolidar_cpf(str(cpf), cache_dir=CACHE_DIR)
    d = d_obj.to_dict()
    if not d["fontes_consultadas"]:
        return {"status": "vazio", "cpf": d["cpf"],
                "mensagem": "Nenhuma consulta base no cache. Rode bigdata_consultar_cpf/unitfour_consultar_cpf antes."}

    alvos = dossie_builder.alvos_para_enriquecer(
        d, apenas_corroborados=apenas_corroborados,
        max_emails=max_emails, max_telefones=max_telefones, max_cnpjs=max_cnpjs,
    )
    relatorio = {"emails": [], "telefones": [], "cnpjs": []}

    # E-mails
    for email in alvos["emails"]:
        try:
            await csint.consultar_email(email)
            leak = None
            if incluir_vazamentos:
                await csint.busca_universal(email, tipo="email")
                cid = "csint_busca_" + email.replace('@', '').replace('.', '').replace('+', '').replace('-', '').replace(' ', '')
                leak = _ler_cache_raw(cid)
            seon_cid = "csint_seon_email_" + email.replace("@", "_at_").replace(".", "_").replace("+", "").replace("-", "")
            seon = _ler_cache_raw(seon_cid)
            dossie_builder.fold_csint_no_dossie(d_obj, "email", email, seon_data=seon, leak_data=leak)
            relatorio["emails"].append({"email": email, "status": "ok"})
        except Exception as e:
            relatorio["emails"].append({"email": email, "status": "erro", "detalhe": str(e)})

    # Telefones
    for tel in alvos["telefones"]:
        try:
            await csint.consultar_telefone(tel)
            seon_cid = "csint_seon_phone_" + tel.replace('+', '').replace('-', '').replace(' ', '')
            seon = _ler_cache_raw(seon_cid)
            dossie_builder.fold_csint_no_dossie(d_obj, "telefone", tel, seon_data=seon)
            relatorio["telefones"].append({"telefone": tel, "status": "ok"})
        except Exception as e:
            relatorio["telefones"].append({"telefone": tel, "status": "erro", "detalhe": str(e)})

    # CNPJs
    timelines_md = []
    for cnpj in alvos["cnpjs"]:
        try:
            await bigdatacorp.consultar_cnpj(cnpj, datasets="bdccompanyevolution,bdccompanyhistorical")
            chave_cache = f"bigdata_cnpj_{cnpj}"
            cache_path = os.path.join(CACHE_DIR, f"{chave_cache}.json")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    dados_ev = json.load(f)
                nome = ""
                try:
                    r0 = (dados_ev.get("Result") or [{}])[0]
                    nome = (r0.get("BasicData") or {}).get("OfficialName") or ""
                except Exception:
                    pass
                tl = dossie_builder.construir_timeline_cnpj(dados_ev)
                md = dossie_builder.timeline_para_markdown(cnpj, nome, tl)
                timelines_md.append(md)
                relatorio["cnpjs"].append({"cnpj": cnpj, "nome": nome, "alteracoes": len(tl), "status": "ok"})
        except Exception as e:
            relatorio["cnpjs"].append({"cnpj": cnpj, "status": "erro", "detalhe": str(e)})

    d_final = d_obj.to_dict()
    laudo = dossie_builder.dossie_para_markdown(d_final)
    if timelines_md:
        laudo += "\n\n## 8. Alterações Históricas de Empresas Ligadas\n\n" + "\n\n".join(timelines_md)

    try:
        base = os.path.join(CACHE_DIR, f"dossie_{d_final['cpf']}_enriquecido")
        with open(f"{base}.json", "w", encoding="utf-8") as f:
            json.dump(d_final, f, ensure_ascii=False, indent=2)
        with open(f"{base}.md", "w", encoding="utf-8") as f:
            f.write(laudo)
    except Exception as e:
        print(f"[ENRIQUECER] Falha ao salvar laudo: {e}", file=sys.stderr, flush=True)

    return {
        "status": "sucesso",
        "cpf": d_final["cpf"],
        "confianca_geral": d_final["confianca_geral"],
        "enriquecimento": {
            "emails_processados": len(relatorio["emails"]),
            "telefones_processados": len(relatorio["telefones"]),
            "cnpjs_processados": len(relatorio["cnpjs"]),
        },
        "relatorio": relatorio,
        "riscos": d_final["riscos"],
        "laudo_markdown": laudo,
        "cache_id": f"dossie_{d_final['cpf']}_enriquecido",
    }
