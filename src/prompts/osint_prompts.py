from src.app import mcp

@mcp.prompt("investigar_pessoa_fisica")
def prompt_investigar_pessoa_fisica(cpf: str, prioridade: str = "completa") -> str:
    """Gera um plano de investigação pericial estruturado para Pessoa Física (CPF)."""
    return f"""
Você é um analista de inteligência pericial e OSINT encarregado de investigar o alvo CPF: '{cpf}'.

Siga RIGOROSAMENTE esta metodologia:
1. **Validação e Cache**: Verifique se já existem dados locais consultando 'veridian_consultar_cadastro_cpf' ou lendo o resource `osint://dossie/{cpf}`.
2. **Dados Básicos e Cadastrais**: Se necessário nova coleta, consulte dados básicos e contatos com 'veridian_consultar_cadastro_cpf' ou 'veridian_consultar_dados_cadastrais_cpf'.
3. **Avaliação de Riscos e Compliance**:
   - Verifique mandados de prisão com 'veridian_mandados_prisao'.
   - Verifique antecedentes criminais com 'veridian_antecedentes_criminais'.
   - Verifique enquadramento como PEP (Pessoa Exposta Politicamente) com 'veridian_verificar_pep_cpf'.
4. **Vínculos e Sociedades**: Mapeie pessoas ligadas e empresas associadas com 'veridian_ver_parentes_e_socios_cpf'.
5. **Processos Judiciais**: Se houver indícios de litígios, fatie a categoria 'bdclawsuits'.
6. **Consolidação Final**: Execute 'veridian_gerar_dossie' para emitir o laudo consolidado com pontuação de confiança e fontes corroboradas.
"""

@mcp.prompt("investigar_pessoa_juridica")
def prompt_investigar_pessoa_juridica(cnpj: str) -> str:
    """Gera um plano de investigação corporativa, societária e compliance para Empresa (CNPJ)."""
    return f"""
Você é um auditor de inteligência corporativa encarregado de investigar a empresa CNPJ: '{cnpj}'.

Siga esta metodologia:
1. **Dados de Registro**: Consulte os dados cadastrais da empresa com 'veridian_consultar_cadastro_cnpj'.
2. **Quadro Societário (QSA)**: Identifique sócios e tomadores de decisão com 'veridian_ver_tomadores_decisao_cnpj' e 'veridian_ver_empresas_ligadas_cnpj'.
3. **Histórico e Evolução**: Analise alterações contratuais, histórico de capital social e regime tributário com 'veridian_cnpj_alteracoes'.
4. **Risco e Compliance**: Verifique processos judiciais atrelados ao CNPJ e, se necessário, submeta os sócios principais à investigação de Pessoa Física.
"""

@mcp.prompt("investigar_advogado_oab")
def prompt_investigar_advogado_oab(oab_numero: str, oab_estado: str) -> str:
    """Gera o fluxo correto para mapeamento processual de advogado por OAB."""
    return f"""
Você deve mapear os processos judiciais do advogado inscrito na OAB {oab_numero}/{oab_estado.upper()}.

REGRAS CRÍTICAS:
1. Use EXCLUSIVAMENTE 'veridian_buscar_processos_oab' informando `oab_numero='{oab_numero}'` e `oab_estado='{oab_estado}'`.
2. NUNCA tente inventar ferramentas inexistentes ou buscar OAB no BigDataCorp.
3. Se a ferramenta retornar `_paginacao_em_andamento: true`, aguarde de 30 a 60 segundos e consulte novamente para resgatar todas as páginas do cache local sem gastar novas requisições.
4. Apresente um sumário executivo agrupando a contagem de processos por Tribunal e destacando os 10 litígios mais recentes.
"""

@mcp.prompt("investigar_redes_sociais")
def prompt_investigar_redes_sociais(alvo: str, plataforma: str = "todas") -> str:
    """Gera o fluxo de investigação de presença digital e redes sociais."""
    return f"""
Inicie o levantamento de inteligência em redes sociais para o alvo: '{alvo}' (Plataforma: {plataforma}).

Metodologia recomendada:
1. **Instagram**: Comece com 'veridian_buscar_perfil_instagram' para obter o user_id (pk) e bio. Em seguida mapeie seguidores e posts recentes.
2. **LinkedIn**: Busque pelo perfil com 'veridian_buscar_perfil_linkedin' e localize e-mails corporativos com 'veridian_buscar_email_perfil_linkedin'.
3. **TikTok**: Mapeie atividades e perfis públicos com 'veridian_buscar_perfil_tiktok'.
4. **Facebook e Reconhecimento Facial**: Faça a busca reversa por e-mail/telefone e, se possuir foto, execute 'veridian_reconhecimento_facial_amplo'.
"""

@mcp.prompt("investigar_veiculo_placa")
def prompt_investigar_veiculo_placa(placa: str) -> str:
    """Gera o fluxo de rastreamento de veículos e proprietário por placa."""
    return f"""
Rastreie o patrimônio veicular e proprietário da placa '{placa}'.
1. Execute 'veridian_consultar_proprietario_placa' passando a placa sem traços.
2. Extraia modelo, ano, chassi, Renavam e CPF/CNPJ do proprietário.
3. Inicie o fluxo de investigação cadastral sobre o documento do proprietário para mapear solvência e patrimônio.
"""

@mcp.prompt("investigar_vazamento_breach")
def prompt_investigar_vazamento_breach(dado_alvo: str) -> str:
    """Gera o fluxo de triagem de vazamentos de dados e reputação de contatos."""
    return f"""
Execute a triagem de segurança e vazamentos para o dado: '{dado_alvo}'.
1. Se for e-mail ou telefone, consulte 'veridian_consultar_email_vazamento' ou 'veridian_consultar_telefone_vazamento' para análise de fraude e contas atreladas.
2. Execute 'veridian_busca_vazamentos' para cruzar o alvo com múltiplos repositórios de breach data.
3. Resuma as bases comprometidas e o nível de exposição de credenciais do alvo.
"""
