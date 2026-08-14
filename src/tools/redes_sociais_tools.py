from typing import Union, Optional
from src.app import mcp
from src.providers import instagram, linkedin, tiktok, lighthouse

# --- Instagram ---
@mcp.tool()
async def instagram_buscar_usuario(username: str) -> dict:
    """
    Busca os dados de um perfil do Instagram usando o @username (sem o @).
    Esta é a PRIMEIRA ferramenta que deve ser usada, pois ela retorna o 'user_id' (pk) 
    necessário para as outras consultas (seguidores, posts, etc).
    
    Args:
        username: O nome de usuário do Instagram (ex: 'neymarjr').
    """
    return await instagram.buscar_usuario(username)

@mcp.tool()
async def instagram_pesquisar_perfis(query: str) -> dict:
    """
    Pesquisa perfis de usuários no Instagram por nome completo, termo de busca ou nome aproximado.
    Retorna uma lista de contas correspondentes com seus respectivos usernames, nomes completos e IDs de usuário.
    
    Args:
        query: O nome completo, termo de pesquisa ou nome aproximado do perfil.
    """
    return await instagram.pesquisar_perfis(query)

@mcp.tool()
async def instagram_ver_seguidores(
    user_id: Union[str, int],
    page_id: Optional[str] = None,
    tipo: str = "ambos",
    page_id_followers: Optional[str] = None,
    page_id_following: Optional[str] = None,
    cursor: Optional[str] = None,
    max_id: Optional[str] = None
) -> dict:
    """
    Extrai seguidores e/ou contas seguidas de um perfil do Instagram usando o user_id, com suporte a paginação.
    
    Args:
        user_id: O ID interno do usuário (obtido com instagram_buscar_usuario).
        page_id: Opcional. Cursor de paginação.
        tipo: Opcional. 'ambos', 'followers' ou 'following'.
    """
    return await instagram.ver_seguidores(user_id, page_id, tipo, page_id_followers, page_id_following, cursor, max_id)

@mcp.tool()
async def instagram_ver_posts(
    user_id: Union[str, int],
    page_id: Optional[str] = None,
    end_cursor: Optional[str] = None
) -> dict:
    """
    Puxa os posts recentes do feed do usuário. Útil para análise de fotos, legendas e locais.
    Suporta paginação usando o parâmetro 'page_id' ou 'end_cursor'.
    
    Args:
        user_id: O ID interno do usuário.
        page_id: Opcional. O cursor para obter a próxima página de posts.
    """
    return await instagram.ver_posts(user_id, page_id, end_cursor)

@mcp.tool()
async def instagram_ver_stories(user_id: Union[str, int]) -> dict:
    """
    Puxa os stories que estão ativos/online neste exato momento para o usuário.
    
    Args:
        user_id: O ID interno do usuário.
    """
    return await instagram.ver_stories(user_id)

# --- LinkedIn ---
@mcp.tool()
async def linkedin_buscar_perfil(linkedin_url: str) -> dict:
    """
    Extrai o perfil completo de um usuário no LinkedIn usando a URL.
    
    Args:
        linkedin_url: A URL completa do perfil (ex: 'https://www.linkedin.com/in/williamhgates').
    """
    return await linkedin.buscar_perfil(linkedin_url)

@mcp.tool()
async def linkedin_consultar_endpoint(endpoint_name: str, target_url: str) -> dict:
    """
    Consulta endpoints avançados do LinkedIn na Harvest API (Posts, Comentários, Reações, etc).
    
    Args:
        endpoint_name: O nome final do endpoint (ex: 'profile/posts', 'post-comments').
        target_url: A URL alvo do LinkedIn.
    """
    return await linkedin.consultar_endpoint(endpoint_name, target_url)

@mcp.tool()
async def linkedin_buscar_pessoas_por_nome(nome_completo: str, nome: Optional[str] = None, sobrenome: Optional[str] = None) -> dict:
    """
    Busca perfis de pessoas no LinkedIn pelo nome ou palavras-chave.
    
    Args:
        nome_completo: O nome completo da pessoa ou termo de busca geral.
        nome: Opcional. Apenas o primeiro nome.
        sobrenome: Opcional. Apenas o sobrenome.
    """
    return await linkedin.buscar_pessoas_por_nome(nome_completo, nome, sobrenome)

@mcp.tool()
async def linkedin_ver_comentarios_post(post_url: str, sort_by: str = "relevance", page: int = 1) -> dict:
    """
    Recupera os comentários de uma publicação do LinkedIn a partir de sua URL.
    
    Args:
        post_url: A URL completa da publicação no LinkedIn.
        sort_by: Opcional. Ordenação ('relevance' ou 'date').
        page: Opcional. Número da página.
    """
    return await linkedin.ver_comentarios_post(post_url, sort_by, page)

@mcp.tool()
async def linkedin_ver_reacoes_post(post_url: str, page: int = 1) -> dict:
    """
    Recupera as reações de uma publicação do LinkedIn a partir de sua URL.
    
    Args:
        post_url: A URL completa da publicação no LinkedIn.
        page: Opcional. Número da página.
    """
    return await linkedin.ver_reacoes_post(post_url, page)

@mcp.tool()
async def linkedin_buscar_posts(termo_busca: str, profile_url: Optional[str] = None, company_url: Optional[str] = None, posted_limit: Optional[str] = None, page: int = 1) -> dict:
    """
    Busca publicações no LinkedIn com base em palavras-chave e filtros de autor ou data.
    
    Args:
        termo_busca: Palavras-chave ou tags pesquisadas nos posts.
        profile_url: Opcional. URL do perfil do autor.
        company_url: Opcional. URL da empresa do autor.
        posted_limit: Opcional. '24h', 'week', 'month'.
        page: Opcional. Número da página.
    """
    return await linkedin.buscar_posts(termo_busca, profile_url, company_url, posted_limit, page)

@mcp.tool()
async def linkedin_ver_posts_usuario(profile_url: str, posted_limit: Optional[str] = None, page: int = 1) -> dict:
    """
    Recupera todas as publicações postadas por um usuário específico no LinkedIn.
    
    Args:
        profile_url: A URL completa do perfil do LinkedIn.
        posted_limit: Opcional. '24h', 'week', 'month'.
        page: Opcional. Número da página.
    """
    return await linkedin.ver_posts_usuario(profile_url, posted_limit, page)

@mcp.tool()
async def linkedin_buscar_email_perfil(profile_url: str, skip_smtp: bool = False) -> dict:
    """
    Tenta localizar e validar os endereços de e-mail atrelados a um perfil do LinkedIn
    usando geração e validação de e-mails em tempo real da Harvest API.
    
    Args:
        profile_url: A URL completa do perfil do LinkedIn.
        skip_smtp: Opcional. Se True, pula validação SMTP.
    """
    return await linkedin.buscar_email_perfil(profile_url, skip_smtp)

# --- TikTok ---
@mcp.tool()
async def tiktok_buscar_perfil(handle: str) -> dict:
    """
    Busca informações detalhadas de um perfil público do TikTok pelo handle (username, sem '@').
    """
    return await tiktok.buscar_perfil(handle)

@mcp.tool()
async def tiktok_listar_videos(handle: str, user_id: Optional[Union[str, int]] = None, sort_by: str = "latest", max_cursor: Optional[str] = None, trim: bool = False) -> dict:
    """
    Recupera a lista de vídeos postados por um perfil do TikTok.
    """
    return await tiktok.listar_videos(handle, user_id, sort_by, max_cursor, trim)

@mcp.tool()
async def tiktok_listar_comentarios(url: str, cursor: Optional[int] = None, trim: bool = False) -> dict:
    """
    Recupera a lista de comentários de um vídeo do TikTok.
    """
    return await tiktok.listar_comentarios(url, cursor, trim)

@mcp.tool()
async def tiktok_listar_respostas_comentario(comment_id: str, url: str, cursor: Optional[int] = None) -> dict:
    """
    Recupera as respostas de um comentário específico em um vídeo do TikTok.
    """
    return await tiktok.listar_respostas_comentario(comment_id, url, cursor)

@mcp.tool()
async def tiktok_listar_seguindo(handle: str, min_time: Optional[int] = None, trim: bool = False) -> dict:
    """
    Lista as contas que um perfil do TikTok segue.
    """
    return await tiktok.listar_seguindo(handle, min_time, trim)

@mcp.tool()
async def tiktok_listar_seguidores(handle: Optional[str] = None, user_id: Optional[Union[str, int]] = None, min_time: Optional[int] = None, trim: bool = False) -> dict:
    """
    Lista os seguidores de um perfil do TikTok.
    """
    return await tiktok.listar_seguidores(handle, user_id, min_time, trim)

@mcp.tool()
async def tiktok_buscar_usuarios(query: str, cursor: Optional[int] = None, trim: bool = False) -> dict:
    """
    Pesquisa e lista usuários do TikTok que correspondam a um termo de busca.
    """
    return await tiktok.buscar_usuarios(query, cursor, trim)

# --- Facebook & Lighthouse Images ---
@mcp.tool()
async def lighthouse_fb_uid_info(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Busca informações detalhadas de perfil cadastral do Facebook a partir do UID do perfil.
    """
    return await lighthouse.fb_uid_info(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_wall(facebook_profile_uid: Union[str, int], options: Optional[dict] = None) -> dict:
    """
    Recupera as postagens e publicações do mural (timeline) de um usuário do Facebook pelo UID.
    """
    return await lighthouse.fb_uid_wall(facebook_profile_uid, options)

@mcp.tool()
async def lighthouse_fb_uid_reposts(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Recupera os reposts e compartilhamentos feitos por um perfil do Facebook.
    """
    return await lighthouse.fb_uid_reposts(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_likes(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Recupera curtidas de páginas e interesses de um perfil do Facebook.
    """
    return await lighthouse.fb_uid_likes(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_comments(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Recupera os comentários públicos deixados por um perfil do Facebook.
    """
    return await lighthouse.fb_uid_comments(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_friends(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Lista amigos públicos de um perfil do Facebook.
    """
    return await lighthouse.fb_uid_friends(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_photos(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Recupera fotos públicas de um perfil do Facebook.
    """
    return await lighthouse.fb_uid_photos(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_albums(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Lista álbuns de fotos de um perfil do Facebook.
    """
    return await lighthouse.fb_uid_albums(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_live_streams(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Busca transmissões ao vivo de um perfil do Facebook.
    """
    return await lighthouse.fb_uid_live_streams(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_games(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Lista jogos e aplicativos atrelados ao perfil do Facebook.
    """
    return await lighthouse.fb_uid_games(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_uid_groups(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Lista grupos públicos em que o perfil do Facebook participa.
    """
    return await lighthouse.fb_uid_groups(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_search_posts(query: str, options: Optional[dict] = None) -> dict:
    """
    Busca publicações globais abertas no Facebook por palavras-chave.
    """
    return await lighthouse.fb_search_posts(query, options)

@mcp.tool()
async def lighthouse_fb_search_comments(query: str, options: Optional[dict] = None) -> dict:
    """
    Busca comentários abertos no Facebook por palavras-chave.
    """
    return await lighthouse.fb_search_comments(query, options)

@mcp.tool()
async def lighthouse_fb_search_places(query: str, options: Optional[dict] = None) -> dict:
    """
    Busca locais e check-ins no Facebook.
    """
    return await lighthouse.fb_search_places(query, options)

@mcp.tool()
async def lighthouse_fb_search_events(query: str, options: Optional[dict] = None) -> dict:
    """
    Busca eventos públicos no Facebook.
    """
    return await lighthouse.fb_search_events(query, options)

@mcp.tool()
async def lighthouse_fb_email_restore(email: str) -> dict:
    """
    Busca reversa no Facebook por e-mail para encontrar o perfil e UID atrelado.
    """
    return await lighthouse.fb_email_restore(email)

@mcp.tool()
async def lighthouse_fb_phone_restore(phone: Union[str, int]) -> dict:
    """
    Busca reversa no Facebook por número de telefone para encontrar o perfil e UID.
    """
    return await lighthouse.fb_phone_restore(phone)

@mcp.tool()
async def lighthouse_fb_uid_darknet(facebook_profile_uid: Union[str, int]) -> dict:
    """
    Cruza o UID do perfil do Facebook com bases de inteligência da Darknet.
    """
    return await lighthouse.fb_uid_darknet(facebook_profile_uid)

@mcp.tool()
async def lighthouse_fb_phone_to_name(phone: Union[str, int]) -> dict:
    """
    Busca o nome registrado no Facebook a partir de um número de telefone.
    """
    return await lighthouse.fb_phone_to_name(phone)

@mcp.tool()
async def lighthouse_image_facecheck(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    """
    Realiza reconhecimento facial avançado na internet usando o FaceCheck.ID.
    """
    return await lighthouse.image_facecheck(photo_url, photo_b64, photo_fileid)

@mcp.tool()
async def lighthouse_image_search4faces(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    """
    Realiza reconhecimento facial em perfis de redes sociais (Search4Faces).
    """
    return await lighthouse.image_search4faces(photo_url, photo_b64, photo_fileid)

@mcp.tool()
async def lighthouse_image_geolocation(photo_url: Optional[str] = None, photo_b64: Optional[str] = None, photo_fileid: Optional[str] = None) -> dict:
    """
    Deduz a geolocalização estimada de uma foto através de inteligência artificial geoespacial.
    """
    return await lighthouse.image_geolocation(photo_url, photo_b64, photo_fileid)
