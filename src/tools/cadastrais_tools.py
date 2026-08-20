from typing import Union, Optional
from src.app import mcp
from src.providers import bigdatacorp, unitfour

@mcp.tool()
async def bigdata_consultar_cpf(cpf: Union[str, int], datasets: str = "bdcbasicdata") -> dict:
    """
    Realiza consulta de Pessoa Física (CPF) na BigDataCorp, buscando um ou mais datasets.
    O CPF pode ser enviado com qualquer tipo de máscara (pontos, traços, etc) e com/sem zeros à esquerda.
    Salva os dados massivos no cache local e retorna as chaves disponíveis.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
        datasets: Lista de datasets separados por vírgula (ex: 'bdcbasicdata,bdcphones').
    """
    return await bigdatacorp.consultar_cpf(cpf, datasets)

@mcp.tool()
async def bigdata_ver_categoria(cpf: Union[str, int], dataset_code: str) -> dict:
    """
    Retorna apenas a fatia de dados correspondente a um código específico do cache do CPF.
    O CPF pode ser enviado com qualquer tipo de máscara (pontos, traços, etc) e com/sem zeros à esquerda.
    
    Args:
        cpf: O CPF do investigado (com ou sem máscara).
        dataset_code: O código do dataset desejado (ex: 'bdcphones', 'bdcbasicdata', 'bdclawsuits').
    """
    return await bigdatacorp.ver_categoria_cpf(cpf, dataset_code)

# ==============================================================================
# FERRAMENTAS GRANULARES BIGDATACORP - PESSOA FÍSICA (CPF)
# ==============================================================================

@mcp.tool()
async def bigdata_cpf_dados_basicos(cpf: Union[str, int]) -> dict:
    """
    Consulta os dados cadastrais básicos de uma Pessoa Física (CPF).
    Retorna: Nome completo, CPF, Data de Nascimento, Idade, Situação Cadastral na Receita, Nome da Mãe, Sexo, Signo e Data de Atualização.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcbasicdata")

@mcp.tool()
async def bigdata_cpf_telefones(cpf: Union[str, int]) -> dict:
    """
    Consulta a lista de telefones fixos e celulares vinculados a um CPF.
    Retorna: Números com DDD, tipo (celular/fixo), operadora, data de observação e indicadores de atualidade.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcphones")

@mcp.tool()
async def bigdata_cpf_emails(cpf: Union[str, int]) -> dict:
    """
    Consulta a lista de e-mails vinculados a um CPF.
    Retorna: Endereços de e-mail, domínio, provedor e data de observação.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcemails")

@mcp.tool()
async def bigdata_cpf_enderecos(cpf: Union[str, int]) -> dict:
    """
    Consulta o histórico de endereços residenciais e comerciais vinculados a um CPF.
    Retorna: Tipo de logradouro, endereço, número, complemento, bairro, cidade, UF, CEP e data de observação.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcaddresses")

@mcp.tool()
async def bigdata_cpf_processos(cpf: Union[str, int]) -> dict:
    """
    Consulta todos os processos judiciais vinculados ao CPF (polo ativo, passivo ou terceiro).
    Retorna: Total de processos, número CNJ, tribunal, assunto, partes e histórico de andamentos.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdclawsuits")

@mcp.tool()
async def bigdata_cpf_empresas_e_socios(cpf: Union[str, int]) -> dict:
    """
    Consulta participações societárias, empresas vinculadas e relações comerciais de um CPF.
    Retorna: CNPJ, Razão Social, Nome Fantasia, Qualificação/Cargo societário, % de participação e situação cadastral das empresas.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcrelatedcompanies")

@mcp.tool()
async def bigdata_cpf_parentes_e_relacionados(cpf: Union[str, int]) -> dict:
    """
    Consulta parentes e possíveis pessoas ligadas a um CPF.
    Retorna: Nome, CPF mascarado e grau de parentesco (mãe, pai, cônjuge, irmãos, etc).
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcrelatedpeople")

@mcp.tool()
async def bigdata_cpf_historico_cadastral(cpf: Union[str, int]) -> dict:
    """
    Consulta o histórico de alterações cadastrais de um CPF (evolução de nomes, datas e registros).
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdchistorical")

@mcp.tool()
async def bigdata_cpf_dados_profissionais(cpf: Union[str, int]) -> dict:
    """
    Consulta histórico de vínculos empregatícios, ocupação profissional, CBO e faixa de renda estimada de um CPF.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcprofessional")

@mcp.tool()
async def bigdata_cpf_dados_politicos(cpf: Union[str, int]) -> dict:
    """
    Consulta histórico político e eleitoral de um CPF (candidaturas, doações, filiações partidárias).
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcpolitics")

@mcp.tool()
async def bigdata_cpf_beneficios_sociais(cpf: Union[str, int]) -> dict:
    """
    Consulta histórico de programas e benefícios sociais governamentais vinculados ao CPF (KYC / CadÚnico).
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdcfamilysocialbenefits")

@mcp.tool()
async def bigdata_cpf_presenca_online(cpf: Union[str, int]) -> dict:
    """
    Consulta presença digital, redes sociais e sites associados ao CPF.
    
    Args:
        cpf: O CPF a ser consultado (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cpf(cpf, "bdconlinepresence")

# ==============================================================================
# FERRAMENTAS BIGDATACORP - PESSOA JURÍDICA (CNPJ)
# ==============================================================================

@mcp.tool()
async def bigdata_consultar_cnpj(cnpj: Union[str, int], datasets: str = "bdccompanybasicdata") -> dict:
    """
    Realiza consulta de Pessoa Jurídica (CNPJ) na BigDataCorp, buscando um ou mais datasets.
    O CNPJ pode ser enviado com qualquer tipo de máscara (pontos, barras, traços, etc) e com/sem zeros à esquerda.
    Salva os dados massivos no cache local e retorna as chaves disponíveis.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
        datasets: Lista de datasets separados por vírgula (ex: 'bdccompanybasicdata,bdccompanyphones').
    """
    return await bigdatacorp.consultar_cnpj(cnpj, datasets)

@mcp.tool()
async def bigdata_ver_categoria_cnpj(cnpj: Union[str, int], dataset_code: str) -> dict:
    """
    Retorna apenas a fatia de dados correspondente a um código específico do cache do CNPJ.
    O CNPJ pode ser enviado com qualquer tipo de máscara (pontos, barras, traços, etc) e com/sem zeros à esquerda.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
        dataset_code: O código do dataset desejado (ex: 'bdccompanybasicdata', 'bdccompanyevolution').
    """
    return await bigdatacorp.ver_categoria_cnpj(cnpj, dataset_code)

@mcp.tool()
async def bigdata_cnpj_dados_basicos(cnpj: Union[str, int]) -> dict:
    """
    Consulta os dados cadastrais básicos de uma Empresa (CNPJ).
    Retorna: Razão Social, Nome Fantasia, CNPJ, Situação Cadastral na Receita, Data de Abertura, Capital Social, Natureza Jurídica e CNAE principal/secundários.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanybasicdata")

@mcp.tool()
async def bigdata_cnpj_telefones(cnpj: Union[str, int]) -> dict:
    """
    Consulta a lista de telefones corporativos vinculados a um CNPJ.
    Retorna: Telefones com DDD, tipo e atualidade.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanyphones")

@mcp.tool()
async def bigdata_cnpj_emails(cnpj: Union[str, int]) -> dict:
    """
    Consulta a lista de e-mails corporativos e de contato vinculados a um CNPJ.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanyemails")

@mcp.tool()
async def bigdata_cnpj_enderecos(cnpj: Union[str, int]) -> dict:
    """
    Consulta os endereços da sede e filiais de uma Empresa (CNPJ).
    Retorna: Logradouro, número, complemento, bairro, cidade, UF e CEP.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanyaddresses")

@mcp.tool()
async def bigdata_cnpj_quadro_societario(cnpj: Union[str, int]) -> dict:
    """
    Consulta o Quadro de Sócios e Administradores (QSA), participações e empresas coligadas de um CNPJ.
    Retorna: Nomes dos sócios, qualificações, % de participação e vínculos corporativos.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanyrelationships")

@mcp.tool()
async def bigdata_cnpj_processos(cnpj: Union[str, int]) -> dict:
    """
    Consulta processos judiciais nos quais a Pessoa Jurídica (CNPJ) figura como parte.
    Retorna: Quantidade total, número CNJ, tribunal, polos e movimentações.
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdclawsuits")

@mcp.tool()
async def bigdata_cnpj_evolucao_historica(cnpj: Union[str, int]) -> dict:
    """
    Consulta a evolução histórica cadastral da empresa (alterações de razão social, capital social, endereço e quadro societário).
    
    Args:
        cnpj: O CNPJ da empresa (com ou sem máscara).
    """
    return await bigdatacorp.consultar_categoria_cnpj(cnpj, "bdccompanyevolution")

@mcp.tool()
async def unitfour_consultar_cpf(cpf: Union[str, int]) -> dict:
    """
    Busca os dados cadastrais completos de uma Pessoa Física (CPF) utilizando a Unitfour.
    Retorna dados cadastrais principais, endereços, telefones e e-mails estruturados.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    return await unitfour.consultar_cpf(cpf)

@mcp.tool()
async def unitfour_pessoas_ligadas(cpf: Union[str, int]) -> dict:
    """
    Localiza parentes, possíveis pessoas ligadas e grau de parentesco a partir de um CPF.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    return await unitfour.pessoas_ligadas(cpf)

@mcp.tool()
async def unitfour_mandados_prisao(cpf: Union[str, int]) -> dict:
    """
    Consulta mandados de prisão vigentes ("Aguardando Cumprimento") no Banco Nacional 
    de Mandados de Prisão (CNJ) a partir do CPF informado.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    return await unitfour.mandados_prisao(cpf)

@mcp.tool()
async def unitfour_antecedentes_criminais(cpf: Union[str, int], nome: Optional[str] = None) -> dict:
    """
    Consulta a existência de registros criminais e emite a Certidão de Antecedentes Criminais 
    da Polícia Federal a partir do CPF (e opcionalmente do nome).
    
    Args:
        cpf: O CPF da pessoa (apenas números).
        nome: Opcional. O nome completo para refinar a busca na Polícia Federal.
    """
    return await unitfour.antecedentes_criminais(cpf, nome)

@mcp.tool()
async def unitfour_consulta_pep(cpf: Union[str, int]) -> dict:
    """
    Busca informações referentes a PEP (Pessoa Exposta Politicamente) Coaf a partir de um CPF.
    
    Args:
        cpf: O CPF da pessoa (apenas números).
    """
    return await unitfour.consulta_pep(cpf)

@mcp.tool()
async def unitfour_consultar_cnpj(cnpj: Union[str, int]) -> dict:
    """
    Busca os dados cadastrais completos de uma Empresa (CNPJ) utilizando a Unitfour.
    Retorna dados cadastrais de registro, endereço, contatos, atividades econômicas, etc.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    return await unitfour.consultar_cnpj(cnpj)

@mcp.tool()
async def unitfour_tomadores_decisao(cnpj: Union[str, int]) -> dict:
    """
    Localiza sócios, diretores e tomadores de decisão (QSA) associados a um CNPJ.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    return await unitfour.tomadores_decisao(cnpj)

@mcp.tool()
async def unitfour_empresas_ligadas(cnpj: Union[str, int]) -> dict:
    """
    Localiza empresas ligadas (participações societárias ou relações comerciais) a um determinado CNPJ.
    
    Args:
        cnpj: O CNPJ da empresa (apenas números).
    """
    return await unitfour.empresas_ligadas(cnpj)

@mcp.tool()
async def unitfour_proprietario_veiculo_placa(placa: str) -> dict:
    """
    Busca dados detalhados do veículo (Renavam, chassi, modelo) e dados de identificação 
    do proprietário atual a partir da placa do veículo.
    
    Args:
        placa: A placa do veículo (sem hífen, ex: ABC1D23 ou ABC1234).
    """
    return await unitfour.proprietario_veiculo_placa(placa)

@mcp.tool()
async def unitfour_busca_avancada_nome(nome: str, bairro: Optional[str] = None, cidade: Optional[str] = None, uf: Optional[str] = None) -> dict:
    """
    Localiza CPFs e pessoas físicas a partir do nome (busca reversa).
    O caractere '*' pode ser usado para realizar correspondências parciais.
    
    Args:
        nome: O nome completo ou parcial pesquisado (ex: 'João da Silva' ou 'João*').
        bairro: Opcional. Bairro para filtrar a busca.
        cidade: Opcional. Cidade para filtrar a busca.
        uf: Opcional. Estado (UF) com duas letras para filtrar a busca.
    """
    return await unitfour.busca_avancada_nome(nome, bairro, cidade, uf)

@mcp.tool()
async def unitfour_busca_avancada_telefone(ddd: Union[str, int], telefone: Union[str, int]) -> dict:
    """
    Localiza pessoas físicas associadas a um número de telefone específico (busca reversa por telefone).
    
    Args:
        ddd: O DDD do telefone (apenas 2 dígitos, ex: '11').
        telefone: O número do telefone (apenas números, ex: '988887777').
    """
    return await unitfour.busca_avancada_telefone(ddd, telefone)

@mcp.tool()
async def unitfour_busca_avancada_email(email: Union[str, int]) -> dict:
    """
    Localiza pessoas físicas associadas a um endereço de e-mail (busca reversa por e-mail).
    
    Args:
        email: O endereço de e-mail completo pesquisado.
    """
    return await unitfour.busca_avancada_email(email)

@mcp.tool()
async def unitfour_busca_avancada_cep(cep: Union[str, int]) -> dict:
    """
    Localiza pessoas físicas registradas em um determinado CEP (busca reversa por CEP).
    
    Args:
        cep: O CEP desejado (apenas números).
    """
    return await unitfour.busca_avancada_cep(cep)
