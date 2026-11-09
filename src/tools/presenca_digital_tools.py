from typing import Optional, List, Union
from src.app import mcp
from src.providers import ekycpro

# ==============================================================================
# FERRAMENTAS DE PRESENÇA DIGITAL EM REDES SOCIAIS E MENSAGEIROS
# ==============================================================================

@mcp.tool()
async def ekycpro_verificar_telefone_plataformas(
    telefone: Union[str, int],
    servicos: Optional[Union[List[str], str]] = None
) -> dict:
    """
    Verifica em lote se um número de telefone possui conta vinculada em redes sociais e mensageiros.
    Por padrão consulta: WhatsApp (ws), foto de perfil do WhatsApp (ws_avatar), WhatsApp Business (ws_business),
    Instagram, Facebook, Telegram, Threads, Twitter/X e Viber.

    Significado dos status retornados por plataforma:
    - 'cadastrado': conta confirmada/registrada na plataforma.
    - 'nao_cadastrado': nenhuma conta vinculada encontrada (no Telegram, também pode ocorrer em números banidos; somente 'banned: true' em 'dados' confirma banimento).
    - 'sem_registro': nenhum registro localizado nas bases consultadas (não prova ausência de conta ativa).
    - 'indeterminado_timeout': tempo limite excedido após tentativa de reconsulta individual; não prova ausência de conta.
    - 'nao_consultado_saldo': verificação não executada por indisponibilidade momentânea de saldo operacional.
    - 'indeterminado': não foi possível determinar o vínculo; não prova ausência de conta.

    Args:
        telefone: Número de telefone com ou sem máscara (números nacionais de 10/11 dígitos recebem +55 automaticamente).
        servicos: Lista opcional de códigos de plataformas a consultar (aceita aliases como 'whatsapp' -> 'ws' e 'x' -> 'twitter').
    """
    return await ekycpro.verificar_telefone(telefone, servicos)


@mcp.tool()
async def ekycpro_verificar_email_plataformas(
    email: str,
    servicos: Optional[Union[List[str], str]] = None
) -> dict:
    """
    Verifica em lote se um endereço de e-mail possui conta ou perfil vinculado em redes sociais e provedores.
    Por padrão consulta: Instagram (instagram_email), Facebook (facebook_email), Twitter/X (twitter_email),
    Perfil do Twitter/X (twitter_profile) e Avatar Público do E-mail (email_avatar).

    Significado dos status retornados por plataforma:
    - 'cadastrado': conta, perfil ou foto pública identificada para o e-mail.
    - 'nao_cadastrado': nenhum vínculo ativo encontrado na plataforma consultada.
    - 'sem_registro': sem registro na base consultada (não prova ausência de conta ativa).
    - 'indeterminado_timeout': tempo limite excedido após reconsulta individual; não prova ausência de conta.
    - 'nao_consultado_saldo': verificação não realizada por limite operacional momentâneo.
    - 'indeterminado': resultado inconclusivo no momento; não prova ausência de conta.

    Args:
        email: Endereço de e-mail do alvo.
        servicos: Lista opcional de códigos de plataformas compatíveis com e-mail (aceita aliases 'instagram', 'facebook', 'twitter', 'x').
    """
    return await ekycpro.verificar_email(email, servicos)


@mcp.tool()
async def ekycpro_perfil_twitter_por_email(email: str) -> dict:
    """
    Consulta dados de perfil do Twitter / X (nome de exibição e URL do perfil em 'dados') vinculados a um endereço de e-mail.

    Significado dos status retornados:
    - 'cadastrado': perfil localizado com campos 'name' e 'url' em 'dados'.
    - 'sem_registro': nenhum perfil encontrado na base consultada (não prova ausência de conta no Twitter / X).
    - 'nao_cadastrado': e-mail sem vínculo identificado.
    - 'indeterminado' / 'indeterminado_timeout': falha temporária na verificação; não prova ausência de conta.

    Args:
        email: Endereço de e-mail a pesquisar.
    """
    return await ekycpro.perfil_twitter_por_email(email)


@mcp.tool()
async def ekycpro_verificar_servico(identificador: Union[str, int], servico: str) -> dict:
    """
    Verifica individualmente uma única plataforma de presença digital para um telefone ou endereço de e-mail.
    Aceita qualquer código do catálogo Veridian compatível com o tipo de identificador informado.

    Significado dos status retornados:
    - 'cadastrado': vínculo confirmado na plataforma.
    - 'nao_cadastrado': vínculo não encontrado na plataforma.
    - 'sem_registro': ausência de registro na base consultada (não comprova inexistência de conta).
    - 'indeterminado_timeout': tempo limite excedido; não comprova inexistência de conta.
    - 'nao_consultado_saldo': não consultado por limite operacional.
    - 'indeterminado': resultado inconclusivo; não comprova inexistência de conta.

    Args:
        identificador: Número de telefone (nacional ou E.164) ou endereço de e-mail.
        servico: Código do serviço a verificar (ex.: 'ws', 'ws_avatar', 'ws_business', 'telegram', 'instagram', 'instagram_email', 'twitter_profile', 'linkedin_profile').
    """
    return await ekycpro.verificar_servico(identificador, servico)


@mcp.tool()
async def ekycpro_listar_servicos() -> dict:
    """
    Lista todas as plataformas e códigos de serviços disponíveis para verificação de presença digital por telefone e e-mail,
    incluindo os pacotes padrão configurados e os aliases aceitos.

    Status possíveis nas consultas de presença digital:
    - 'cadastrado', 'nao_cadastrado', 'sem_registro', 'indeterminado_timeout', 'nao_consultado_saldo' e 'indeterminado'.
    """
    return await ekycpro.listar_servicos()

