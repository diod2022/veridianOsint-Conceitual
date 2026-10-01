from typing import Union, Optional
from src.app import mcp
from src.providers import deltafox

# ==============================================================================
# FERRAMENTAS VEICULARES, TRÂNSITO E CONDUTORES (RENACH / RENAJUD / RENAVAM)
# ==============================================================================

@mcp.tool()
async def deltafox_cnh_prontuario(cpf: Union[str, int]) -> dict:
    """
    Consulta o prontuário CNH / RENACH completo de um condutor através do CPF.
    Retorna: Dados da CNH (número de registro, CNH, Renach, categoria, validade, data da 1ª habilitação,
    UF, situação, impedimentos, observações), filiação (nome da mãe e do pai), documento de identidade (RG e órgão expedidor),
    e endereço residencial completo cadastrado junto ao Detran (logradouro, número, complemento, bairro, CEP, município, UF e código SIAFI).
    
    Args:
        cpf: O CPF do condutor (com ou sem máscara/pontuação).
    """
    return await deltafox.consultar_renach_prontuario(cpf)

@mcp.tool()
async def deltafox_veiculo_restricoes_renajud(placa: str) -> dict:
    """
    Consulta restrições judiciais ativas via RENAJUD associadas a um veículo através da Placa.
    Retorna: Placa, código Renavam, lista de restrições registradas, bloco de processos judiciais
    (com penhora, busca e apreensão ou impedimento de circulação) e quantidade de registros.
    
    Args:
        placa: A placa do veículo (padrão antigo AAA-9999 ou padrão Mercosul AAA9A99).
    """
    return await deltafox.consultar_renajud_restricoes(placa)

@mcp.tool()
async def deltafox_veiculo_endereco_proprietario(placa: str) -> dict:
    """
    Consulta os dados cadastrais do veículo e o endereço oficial do proprietário atual através da Placa.
    Retorna: Placa, chassi, código Renavam, código de marca/modelo, ano de fabricação, nome completo do proprietário,
    endereço residencial/comercial (logradouro, número, complemento, bairro, CEP, município e UF) e indicador de comunicação de venda.
    
    Args:
        placa: A placa do veículo (padrão antigo ou Mercosul).
    """
    return await deltafox.consultar_renavam_endereco(placa)

@mcp.tool()
async def deltafox_frota_veiculos(documento: Union[str, int]) -> dict:
    """
    Localiza a frota de veículos registrados no RENAVAM em nome de uma Pessoa Física (CPF) ou Jurídica (CNPJ).
    Retorna: Quantidade total de veículos e a lista completa de automóveis, utilitários, motocicletas e caminhões vinculados ao documento.
    
    Args:
        documento: O CPF (11 dígitos) ou CNPJ (14 dígitos) do proprietário (com ou sem pontuação).
    """
    return await deltafox.consultar_renavam_frota(documento)

@mcp.tool()
async def deltafox_veiculo_historico_crv(placa: str) -> dict:
    """
    Consulta o histórico de emissões e transferências de CRV (Certificado de Registro de Veículo) pela Placa.
    Retorna: Histórico detalhado de transferências de propriedade, datas de emissão e quantidade de registros de CRV.
    
    Args:
        placa: A placa do veículo (padrão antigo ou Mercosul).
    """
    return await deltafox.consultar_renavam_historico_crv(placa)

@mcp.tool()
async def deltafox_servicos_disponiveis() -> dict:
    """
    Verifica os serviços veiculares e de condutores contratados e disponíveis no provedor de trânsito.
    Retorna a lista de serviços ativos, parâmetros de entrada e status de liberação do contrato.
    """
    return await deltafox.consultar_servicos_disponiveis()
