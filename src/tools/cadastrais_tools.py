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
