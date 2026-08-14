# -*- coding: utf-8 -*-
"""
dossie.py — Camada de consolidação de dossiê do Agente Investigador.
(Compatibilidade retroativa: delega para src.providers.dossie_builder)
"""
from src.providers.dossie_builder import (
    CACHE_DIR,
    so_digitos,
    normalizar_cpf,
    normalizar_telefone,
    normalizar_email,
    normalizar_nome,
    ScoreConfianca,
    Dossie,
    normalizar_unitfour_cpf,
    normalizar_unitfour_parentes,
    normalizar_unitfour_pep,
    normalizar_unitfour_mandados,
    normalizar_unitfour_antecedentes,
    normalizar_bigdata_cpf,
    consolidar_cpf,
    dossie_para_markdown,
    cpfs_disponiveis_no_cache,
    alvos_para_enriquecer,
    fold_csint_no_dossie,
    construir_timeline_cnpj,
    timeline_para_markdown
)

__all__ = [
    "CACHE_DIR",
    "so_digitos",
    "normalizar_cpf",
    "normalizar_telefone",
    "normalizar_email",
    "normalizar_nome",
    "ScoreConfianca",
    "Dossie",
    "normalizar_unitfour_cpf",
    "normalizar_unitfour_parentes",
    "normalizar_unitfour_pep",
    "normalizar_unitfour_mandados",
    "normalizar_unitfour_antecedentes",
    "normalizar_bigdata_cpf",
    "consolidar_cpf",
    "dossie_para_markdown",
    "cpfs_disponiveis_no_cache",
    "alvos_para_enriquecer",
    "fold_csint_no_dossie",
    "construir_timeline_cnpj",
    "timeline_para_markdown"
]
