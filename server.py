# -*- coding: utf-8 -*-
"""
server.py — Servidor MCP Agente Investigador (Veridian OSINT) v2.0
Fachada de execução e compatibilidade retroativa para a arquitetura modular 'src/'.
"""
import sys
import os
import anyio
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Importa configurações e helpers de cache
from src.core.config import CACHE_DIR, DB_PATH, KEYS_FILE, FASTMCP_PORT
from src.core.cache import (
    obter_caminho_cache_seguro,
    obter_caminho_cache_seguro_ext,
    salvar_cache_universal,
    checar_cache_universal
)

# Importa o core FastMCP e registros de ferramentas, recursos e prompts
from src.app import mcp
import src.tools
import src.resources
import src.prompts
from src.core.auth import carregar_chaves_autorizadas
from src.admin.server import run_sse_with_auth

# Exporta ferramentas principais para compatibilidade retroativa com scripts legados
from src.tools.cache_tools import (
    investigador_ler_cache,
    investigador_limpar_cache,
    investigador_obter_cache_compactado
)
from src.tools.cadastrais_tools import (
    bigdata_cpf_dados_basicos,
    bigdata_cpf_telefones,
    bigdata_cpf_emails,
    bigdata_cpf_enderecos,
    bigdata_cpf_processos,
    bigdata_cpf_empresas_e_socios,
    bigdata_cpf_parentes_e_relacionados,
    bigdata_cpf_historico_cadastral,
    bigdata_cpf_dados_profissionais,
    bigdata_cpf_dados_politicos,
    bigdata_cpf_beneficios_sociais,
    bigdata_cpf_presenca_online,
    bigdata_cnpj_dados_basicos,
    bigdata_cnpj_telefones,
    bigdata_cnpj_emails,
    bigdata_cnpj_enderecos,
    bigdata_cnpj_quadro_societario,
    bigdata_cnpj_processos,
    bigdata_cnpj_evolucao_historica,
    unitfour_consultar_cpf,
    unitfour_pessoas_ligadas,
    unitfour_mandados_prisao,
    unitfour_antecedentes_criminais,
    unitfour_consulta_pep,
    unitfour_consultar_cnpj,
    unitfour_tomadores_decisao,
    unitfour_empresas_ligadas,
    unitfour_proprietario_veiculo_placa,
    unitfour_busca_avancada_nome,
    unitfour_busca_avancada_telefone,
    unitfour_busca_avancada_email,
    unitfour_busca_avancada_cep
)
from src.tools.judiciais_tools import (
    escavador_buscar_processos_oab,
    bigdata_consultar_processo
)
from src.tools.redes_sociais_tools import (
    instagram_buscar_usuario,
    instagram_pesquisar_perfis,
    instagram_ver_seguidores,
    instagram_ver_posts,
    instagram_ver_stories,
    linkedin_buscar_perfil,
    linkedin_consultar_endpoint,
    linkedin_buscar_pessoas_por_nome,
    linkedin_ver_comentarios_post,
    linkedin_ver_reacoes_post,
    linkedin_buscar_posts,
    linkedin_ver_posts_usuario,
    linkedin_buscar_email_perfil,
    tiktok_buscar_perfil,
    tiktok_listar_videos,
    tiktok_listar_comentarios,
    tiktok_listar_respostas_comentario,
    tiktok_listar_seguindo,
    tiktok_listar_seguidores,
    tiktok_buscar_usuarios,
    lighthouse_fb_uid_info,
    lighthouse_image_facecheck,
    lighthouse_image_search4faces,
    lighthouse_image_geolocation
)
from src.tools.osint_tools import (
    whois_consultar,
    csint_consultar_ip,
    csint_busca_universal,
    csint_consultar_telefone,
    csint_consultar_email,
    tavily_buscar_web,
    firecrawl_raspar_pagina,
    serper_buscar_web_dorks,
    serper_buscar_google,
    wayback_consultar_disponibilidade,
    wayback_listar_imagens,
    wayback_listar_snapshots
)
from src.tools.biometria_tools import (
    biometria_comparar_faces,
    biometria_detectar_faces
)

def main():
    transport_mode = os.environ.get("FASTMCP_TRANSPORT", "stdio")
    if "--sse" in sys.argv:
        transport_mode = "sse"
        
    print("Iniciando servidor MCP 'veridianOsint-Conceitual' v2.0 com CSINT, BigDataCorp, HikerAPI, Harvest API (LinkedIn), Unitfour, Lighthouse (Facebook e Imagens OSINT), SociaVault (TikTok OSINT), WhoisXML e Web OSINT...", file=sys.stderr, flush=True)
    
    if transport_mode == "sse":
        print(f"[MCP] Rodando em modo SSE (Web) protegido por Chave de API na porta: {mcp.settings.port}", file=sys.stderr, flush=True)
        carregar_chaves_autorizadas()
        anyio.run(run_sse_with_auth, mcp)
    else:
        print("[MCP] Rodando em modo STDIO.", file=sys.stderr, flush=True)
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
