# Relação de Consultas por Fonte — Agente Investigador

Este documento detalha todas as ferramentas de consulta disponíveis no servidor MCP do **Agente Investigador**, agrupadas por sua respectiva API/fonte, contendo os dados de entrada e a expectativa de saída para cada operação.

---

## Tabela Geral de Consultas

| Fonte (API/Serviço) | Ferramenta | Dado de Entrada | Expectativa de Saída (Expectativa de Retorno) |
| :--- | :--- | :--- | :--- |
| **WhoisXML API** | `whois_consultar` | `target`: Domínio (ex: `google.com`), IP (ex: `8.8.8.8`) ou E-mail | Informações completas de registro e propriedade do domínio (ou do domínio extraído do e-mail). Retorna país, estado, última atualização (updatedDate), data de criação, expiração, dados do registrador e DNS. |
| **BigDataCorp** | `bigdata_consultar_cpf` | `cpf`: CPF com/sem máscara<br>`datasets`: Lista de categorias (ex: `bdcbasicdata,bdcphones`) | Resumo da gravação e lista de chaves de dados que foram salvos em cache local. |
| **BigDataCorp** | `bigdata_ver_categoria` | `cpf`: CPF com/sem máscara<br>`dataset_code`: Código do dataset (ex: `bdclawsuits`) | Subconjunto bruto correspondente à categoria solicitada a partir do cache do CPF. |
| **BigDataCorp** | `bigdata_consultar_cnpj` | `cnpj`: CNPJ com/sem máscara<br>`datasets`: Lista de categorias (ex: `bdccompanybasicdata`) | Resumo da gravação e lista de chaves de dados que foram salvos em cache local da empresa. |
| **BigDataCorp** | `bigdata_ver_categoria_cnpj` | `cnpj`: CNPJ com/sem máscara<br>`dataset_code`: Código do dataset (ex: `bdccompanyphones`) | Subconjunto bruto correspondente à categoria solicitada a partir do cache do CNPJ. |
| **BigDataCorp** | `bigdata_consultar_processo` | `numero_processo`: Número do processo CNJ<br>`dataset_code`: Categoria do processo | Detalhes básicos do andamento, partes envolvidas e classe judicial do processo. |
| **BigDataCorp** | `bigdata_cnpj_alteracoes` | `cnpj`: CNPJ com/sem máscara | Timeline cronológica completa mostrando alterações de endereço, capital social, sócios e funcionários ao longo do tempo. |
| **CSINT.pro** | `csint_consultar_ip` | `ip`: Endereço IP (IPv4 ou IPv6) | Geolocalização (país, cidade), ISP (provedor), pontuação de risco e detecção de proxy/VPN/TOR. |
| **CSINT.pro** | `csint_busca_universal` | `query`: E-mail, telefone, username ou IP<br>`tipo`: Tipo de dado | Relação de vazamentos de dados históricos na Darknet em que o alvo foi listado (credenciais expostas). |
| **CSINT.pro** | `csint_consultar_telefone` | `telefone`: Telefone no padrão E.164 (ex: `+5511988887777`) | Operadora original, validação do número e indicação de contas ativas vinculadas (WhatsApp, Telegram, redes sociais). |
| **CSINT.pro** | `csint_consultar_email` | `email`: E-mail completo | Mapeamento SEON verificando a existência ativa do e-mail e perfis atrelados a +20 redes sociais (LinkedIn, Spotify, Netflix, etc.). |
| **UnitFour** | `unitfour_consultar_cpf` | `cpf`: CPF (apenas números) | Ficha cadastral básica completa (nomes, idade, filiação, endereços alternativos, telefones e e-mails mapeados). |
| **UnitFour** | `unitfour_pessoas_ligadas` | `cpf`: CPF (apenas números) | Mapeamento de possíveis parentes, vizinhos e pessoas relacionadas com indicação do grau de vínculo. |
| **UnitFour** | `unitfour_mandados_prisao` | `cpf`: CPF (apenas números) | Consulta direta ao BNMP do CNJ retornando mandados de prisão pendentes de cumprimento atrelados ao CPF. |
| **UnitFour** | `unitfour_antecedentes_criminais` | `cpf`: CPF (apenas números)<br>`nome`: Nome completo (opcional) | Certidão eletrônica de antecedentes criminais ativa emitida pela Polícia Federal. |
| **UnitFour** | `unitfour_consulta_pep` | `cpf`: CPF (apenas números) | Validação perante listas oficiais COAF para constatar se o alvo é Pessoa Exposta Politicamente. |
| **UnitFour** | `unitfour_consultar_cnpj` | `cnpj`: CNPJ (apenas números) | Dados cadastrais oficiais de registro de empresa, endereço físico, contatos e Classificação de Atividade (CNAE). |
| **UnitFour** | `unitfour_tomadores_decisao` | `cnpj`: CNPJ (apenas números) | Quadro de Sócios e Administradores (QSA) e executivos responsáveis pela empresa. |
| **UnitFour** | `unitfour_empresas_ligadas` | `cnpj`: CNPJ (apenas números) | Relação de filiais, coligadas ou empresas sob controle societário direto. |
| **UnitFour** | `unitfour_proprietario_veiculo_placa`| `placa`: Placa (ex: `ABC1D23`) | Detalhes do veículo (marca, ano, chassi, renavam) e CPF/CNPJ com nome do proprietário atual. |
| **UnitFour** | `unitfour_busca_avancada_nome` | `nome`: Nome ou correspondência parcial (`*`) <br>`uf`/`cidade`/`bairro`: Filtros opcionais | CPFs e registros de pessoas correspondentes ao nome pesquisado (busca reversa). |
| **UnitFour** | `unitfour_busca_avancada_telefone`| `ddd`: DDD de 2 dígitos<br>`telefone`: Número de telefone | CPFs e dados de pessoas físicas que registram vínculo histórico com o número de telefone (busca reversa). |
| **UnitFour** | `unitfour_busca_avancada_email` | `email`: E-mail completo | CPFs e dados de pessoas físicas vinculadas ao endereço de e-mail (busca reversa). |
| **UnitFour** | `unitfour_busca_avancada_cep` | `cep`: CEP (apenas números) | Listagem de moradores e CPFs associados ao endereço do CEP (busca reversa). |
| **HikerAPI (Instagram)**| `instagram_buscar_usuario` | `username`: Username do Instagram (sem `@`) | Perfil público resumido (nome, biografia, seguidores) e o `user_id` (necessário para demais consultas). |
| **HikerAPI (Instagram)**| `instagram_ver_seguidores` | `user_id`: ID de usuário do Instagram | Lista de perfis que seguem o alvo e contas que o alvo está seguindo. |
| **HikerAPI (Instagram)**| `instagram_ver_posts` | `user_id`: ID de usuário do Instagram | Posts recentes do feed, com legendas, hashtags e localizações marcadas. |
| **HikerAPI (Instagram)**| `instagram_ver_stories` | `user_id`: ID de usuário do Instagram | Mapeamento de stories que estão online no perfil no momento exato da requisição. |
| **Harvest API (LinkedIn)**| `linkedin_buscar_perfil` | `linkedin_url`: URL do perfil do LinkedIn | Perfil profissional detalhado contendo cargos atuais/passados, histórico escolar e habilidades. |
| **Harvest API (LinkedIn)**| `linkedin_consultar_endpoint`| `endpoint_name`: Nome do endpoint<br>`target_url`: URL do alvo | Retorno estruturado de comentários, postagens e interações em perfis ou páginas empresariais. |
| **Harvest API (LinkedIn)**| `linkedin_buscar_pessoas_por_nome`| `nome_completo`: Nome completo para busca | Sugestões de perfis de profissionais que correspondam ao nome buscado. |
| **Harvest API (LinkedIn)**| `linkedin_ver_comentarios_post` | `post_url`: URL da publicação no LinkedIn | Comentários e discussões públicas atreladas ao post informado. |
| **Harvest API (LinkedIn)**| `linkedin_ver_reacoes_post` | `post_url`: URL da publicação no LinkedIn | Perfis e reações (Curtir, Apoiar, Parabéns, etc.) efetuadas no post. |
| **Harvest API (LinkedIn)**| `linkedin_buscar_posts` | `termo_busca`: Termo de pesquisa nos posts | Publicações públicas indexadas no LinkedIn que citam o termo pesquisado. |
| **Harvest API (LinkedIn)**| `linkedin_ver_posts_usuario` | `profile_url`: URL do perfil | Relação de publicações feitas diretamente pelo usuário. |
| **Harvest API (LinkedIn)**| `linkedin_buscar_email_perfil` | `profile_url`: URL do perfil | Endereços de e-mail prováveis vinculados ao perfil, validados de forma ativa via protocolo SMTP. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_info` | `facebook_profile_uid`: ID numérico do perfil | Perfil cadastral público completo do Facebook atrelado ao UID. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_wall` | `facebook_profile_uid`: ID numérico do perfil | Histórico de publicações públicas no mural (linha do tempo) da conta. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_reposts` | `facebook_profile_uid`: ID numérico do perfil | Compartilhamentos efetuados pelo usuário na rede social. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_likes` | `facebook_profile_uid`: ID numérico do perfil | Curtidas que a conta deixou em postagens do mural. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_comments` | `facebook_profile_uid`: ID numérico do perfil | Comentários e interações escritas pelo perfil. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_friends` | `facebook_profile_uid`: ID numérico do perfil | Relação clássica de amigos adicionados na conta. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_full_friends`| `facebook_profile_uid`: ID numérico do perfil | Lista de amigos enriquecida com detalhes cadastrais extras de cada conta. |
| **Lighthouse (Facebook)**| `lighthouse_fb_phone_restore` | `phone`: Telefone E.164 | Identificação reversa de perfis do Facebook vinculados ao telefone (account mapping). |
| **Lighthouse (Facebook)**| `lighthouse_fb_email_restore` | `email`: E-mail completo | Identificação reversa de perfis do Facebook vinculados ao e-mail (account mapping). |
| **Lighthouse (Facebook)**| `lighthouse_fb_username_restore`| `username`: Nome de usuário/Nickname do Facebook| Conversão do nome de usuário para o UID correspondente. |
| **Lighthouse (Facebook)**| `lighthouse_fb_phone_darknet` | `phone`: Telefone E.164 | Busca na Darknet de senhas e credenciais vazadas ligadas ao telefone e conta Facebook. |
| **Lighthouse (Facebook)**| `lighthouse_fb_email_darknet` | `email`: E-mail completo | Busca na Darknet de senhas e credenciais vazadas ligadas ao e-mail e conta Facebook. |
| **Lighthouse (Facebook)**| `lighthouse_fb_uid_darknet` | `facebook_profile_uid`: ID numérico do perfil | Relação de vazamentos e senhas expostas diretamente vinculadas ao UID da conta. |
| **Lighthouse (Imagens)** | `lighthouse_image_facecheck` | `photo_url` / `photo_b64` / `photo_fileid` | Busca reversa de faces correlatas na internet aberta utilizando a API FaceCheck.ID. |
| **Lighthouse (Imagens)** | `lighthouse_image_geolocation` | `photo_url` / `photo_b64` / `photo_fileid` | Estimativa e dedução de geolocalização física (país, cidade, coordenadas) da foto enviada. |
| **Lighthouse (Imagens)** | `lighthouse_image_search4faces` | `photo_url` / `photo_b64` / `photo_fileid` | Busca e mapeamento de faces em redes sociais específicas (ex: VKontakte) via Search4Faces. |
| **SociaVault (TikTok)** | `tiktok_buscar_perfil` | `handle`: Username do TikTok (sem `@`) | Ficha cadastral pública do canal (bio, seguidores, número de vídeos, avatares). |
| **SociaVault (TikTok)** | `tiktok_listar_videos` | `handle`: Username do TikTok (sem `@`) | Lista de publicações/vídeos hospedados no canal do usuário. |
| **SociaVault (TikTok)** | `tiktok_listar_comentarios` | `url`: URL completa do vídeo | Relação de comentários deixados na publicação do TikTok. |
| **SociaVault (TikTok)** | `tiktok_listar_respostas_comentario`| `comment_id`: ID do comentário<br>`url`: URL do vídeo | Respostas encadeadas de um comentário específico do TikTok. |
| **SociaVault (TikTok)** | `tiktok_listar_seguindo` | `handle`: Username do TikTok (sem `@`) | Lista de perfis que a conta alvo segue. |
| **SociaVault (TikTok)** | `tiktok_listar_seguidores` | `handle`: Username do TikTok (sem `@`) | Contas públicas que seguem o canal do alvo. |
| **SociaVault (TikTok)** | `tiktok_buscar_usuarios` | `query`: Termo de busca textual | Contas do TikTok que correspondem à palavra-chave buscada. |
| **Escavador** | `escavador_buscar_processos_oab` / `veridian_buscar_processos_oab` | `oab_numero`: Número da OAB<br>`oab_estado`: UF (ex: `MS`) <br>`max_paginas`: Limite de páginas (padrão 1, ex: 10, 50) | Lista completa de processos judiciais vinculados ao advogado no Escavador. **ÚNICA ferramenta para busca por OAB.** |
| **Investigador Core** | `investigador_ler_cache` | `cache_id`: ID do cache<br>`chave`: Opcional<br>`slice_start`/`slice_end`: Paginação | Retorno de fatias paginadas de cache local de consultas grandes para evitar estouro de tokens da LLM. |
| **Investigador Core** | `investigador_limpar_cache` | `cache_id`: ID (opcional)<br>`limpar_tudo`: boolean | Remove arquivos de cache salvos em disco (específicos ou diretório completo). |
| **Investigador Core** | `investigador_obter_cache_compactado` | `cache_id`: ID do cache | Compacta arquivos do cache em um pacote ZIP e retorna o caminho físico e codificação Base64. |
| **Investigador Core** | `investigador_gerar_dossie` | `cpf`: CPF com/sem máscara | Dossiê consolidado, deduplicado e corroborado com cruzamento de todas as fontes consultadas. |
| **Investigador Core** | `investigador_enriquecer_dossie`| `cpf`: CPF com/sem máscara | Enriquecimento automático do dossiê consultando reputação SEON e vazamentos para todos os contatos. |
