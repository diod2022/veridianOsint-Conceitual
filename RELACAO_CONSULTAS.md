# Inventário Completo de Consultas e Recursos — Veridian OSINT MCP (v2.0)

Este documento é o **inventário canônico e detalhado** de todas as capacidades operacionais disponíveis no servidor **Veridian OSINT MCP (v2.0)**. Ele contempla as **79 Tools**, os **4 Recursos Nativos (Resources)** e os **6 Prompts Estruturados de Investigação (Prompts)**, correlacionando os nomes originais internos aos nomes expostos sob o namespace público **`veridian_*`** (White-labeling).

---

## 1. Visão Geral da Tríade MCP v2.0

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           VERIDIAN OSINT MCP (v2.0)                            │
├───────────────────────┬────────────────────────────┬───────────────────────────┤
│   79 MCP TOOLS        │      4 MCP RESOURCES       │       6 MCP PROMPTS       │
│   (Ações de Coleta,   │   (Acesso Direto a Dados   │    (Workflows & Guias     │
│   Processamento e     │    Sem Gasto de Tokens/    │     Estratégicos para     │
│     Investigação)     │      Tool Calls)           │           LLMs)           │
└───────────────────────┴────────────────────────────┴───────────────────────────┘
```

---

## 2. Inventário de Ferramentas (MCP Tools)

### 2.1. Gestão de Cache e Arquivos Locais

| Nome White-label (`MCP`) | Função Interna | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- |
| `veridian_ler_cache` | `investigador_ler_cache` | `cache_id` (str)<br>`chave` (str, opcional)<br>`slice_start` (int, padrão 0)<br>`slice_end` (int, padrão 20) | Permite inspecionar e paginar dados brutos massivos armazenados localmente sem sobrecarregar a janela de contexto do modelo. |
| `veridian_limpar_cache` | `investigador_limpar_cache` | `cache_id` (str, opcional)<br>`limpar_tudo` (bool, padrão False) | Exclui arquivos de cache específicos ou limpa todo o diretório de dados locais para forçar novas coletas. |
| `veridian_obter_cache_compactado` | `investigador_obter_cache_compactado` | `cache_id` (str) | Compacta os artefatos de um alvo (`.json` e `.md`) em um arquivo ZIP e retorna seu caminho e conteúdo em Base64. |

---

### 2.2. Pessoa Física — Qualificação Cadastral e Busca Reversa

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_consultar_cadastro_cpf` | `bigdata_consultar_cpf` | BigDataCorp | `cpf` (str/int)<br>`datasets` (str, padrão `bdcbasicdata`) | Consulta modular de dados cadastrais de PF. Salva os dados no cache local e retorna o índice de categorias coletadas. |
| `veridian_ver_categoria` | `bigdata_ver_categoria` | BigDataCorp | `cpf` (str/int)<br>`dataset_code` (str, ex: `bdcphones`, `bdclawsuits`) | Extrai uma fatia específica de dados (telefones, endereços, processos) do cache do CPF consultado. |
| `veridian_consultar_dados_cadastrais_cpf` | `unitfour_consultar_cpf` | Unitfour | `cpf` (str/int) | Ficha cadastral direta contendo qualificação civil, situação na Receita Federal, filiação, telefones e endereços. |
| `veridian_ver_parentes_e_socios_cpf` | `unitfour_pessoas_ligadas` | Unitfour | `cpf` (str/int) | Mapeia possíveis parentes (mãe, pai, irmãos, cônjuges) e vínculos pessoais com indicação do grau de relação. |
| `veridian_mandados_prisao` | `unitfour_mandados_prisao` | Unitfour | `cpf` (str/int) | Consulta o Banco Nacional de Mandados de Prisão (BNMP/CNJ) para identificar mandados ativos aguardando cumprimento. |
| `veridian_antecedentes_criminais` | `unitfour_antecedentes_criminais` | Unitfour | `cpf` (str/int)<br>`nome` (str, opcional) | Emite e valida a Certidão de Antecedentes Criminais da Polícia Federal para o CPF informado. |
| `veridian_consulta_pep` | `unitfour_consulta_pep` | Unitfour | `cpf` (str/int) | Verifica enquadramento como Pessoa Exposta Politicamente (PEP) perante os registros do COAF/Governo Federal. |
| `veridian_busca_avancada_nome` | `unitfour_busca_avancada_nome` | Unitfour | `nome` (str)<br>`bairro` / `cidade` / `uf` (opcionais) | **Busca Reversa por Nome**: Localiza CPFs, registros e pessoas correspondentes ao nome informado (aceita wildcard `*`). |
| `veridian_busca_avancada_telefone` | `unitfour_busca_avancada_telefone` | Unitfour | `ddd` (str/int)<br>`telefone` (str/int) | **Busca Reversa por Telefone**: Identifica o titular civil e pessoas atreladas a uma linha telefônica fixa ou móvel. |
| `veridian_busca_avancada_email` | `unitfour_busca_avancada_email` | Unitfour | `email` (str) | **Busca Reversa por E-mail**: Localiza CPFs e cadastros físicos associados ao endereço de e-mail pesquisado. |
| `veridian_busca_avancada_cep` | `unitfour_busca_avancada_cep` | Unitfour | `cep` (str/int) | **Busca Reversa por CEP**: Retorna a relação de moradores e CPFs registrados no logradouro informado. |
| `veridian_consultar_proprietario_placa` | `unitfour_proprietario_veiculo_placa` | Unitfour | `placa` (str, ex: `ABC1D23`) | **Inteligência Veicular**: Identifica marca, modelo, chassi, Renavam e o CPF/CNPJ com nome do proprietário atual. |

---

### 2.3. Pessoa Jurídica — Estrutura Societária, QSA e Timeline

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_consultar_cadastro_cnpj` | `bigdata_consultar_cnpj` | BigDataCorp | `cnpj` (str/int)<br>`datasets` (str) | Consulta dados cadastrais corporativos, CNAEs, filiais e quadro de funcionários. |
| `veridian_ver_categoria_cnpj` | `bigdata_ver_categoria_cnpj` | BigDataCorp | `cnpj` (str/int)<br>`dataset_code` (str) | Extrai do cache do CNPJ subconjuntos brutos específicos (evolução societária, processos, contatos). |
| `veridian_consultar_dados_cadastrais_cnpj` | `unitfour_consultar_cnpj` | Unitfour | `cnpj` (str/int) | Qualificação cadastral oficial da empresa na Receita Federal, atividade principal e endereço registrado. |
| `veridian_ver_tomadores_decisao_cnpj` | `unitfour_tomadores_decisao` | Unitfour | `cnpj` (str/int) | Quadro de Sócios e Administradores (QSA), procuradores e executivos com poderes de decisão. |
| `veridian_ver_empresas_ligadas_cnpj` | `unitfour_empresas_ligadas` | Unitfour | `cnpj` (str/int) | Identifica empresas coligadas, matriz/filiais e participações societárias diretas da pessoa jurídica. |
| `veridian_cnpj_alteracoes` | `bigdata_cnpj_alteracoes` | BigDataCorp | `cnpj` (str/int) | **Timeline Histórica**: Constrói a linha do tempo cronológica com alterações de razão social, capital, sócios e endereço. |

---

### 2.4. Inteligência Jurídica e Processos Judiciais

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_buscar_processos_oab` | `escavador_buscar_processos_oab` | Escavador | `oab_numero` (str/int)<br>`oab_estado` (str, ex: `MS`)<br>`oab_tipo` (str, padrão `ADVOGADO`)<br>`max_paginas` (int, padrão 50)<br>`ignore_cache` (bool) | **ÚNICA ferramenta para consulta por OAB**. Varre litígios e processos judiciais do advogado com paginação assíncrona automática em segundo plano. |
| `veridian_consultar_processos_judiciais` | `bigdata_consultar_processo` | BigDataCorp | `numero_processo` (str, CNJ)<br>`dataset_code` (str) | Consulta os dados completos de um processo judicial a partir do número único CNJ (partes, foro, valor, movimentações). |

---

### 2.5. Redes Sociais — Instagram, LinkedIn e TikTok

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_buscar_perfil_instagram` | `instagram_buscar_usuario` | HikerAPI | `username` (str, sem `@`) | Extrai bio, contagens, links externos e o `user_id` (pk) obrigatório para as demais consultas. |
| `veridian_pesquisar_perfis_instagram` | `instagram_pesquisar_perfis` | HikerAPI | `query` (str) | Pesquisa perfis no Instagram por nome aproximado, termo de busca ou palavra-chave. |
| `veridian_ver_seguidores_instagram` | `instagram_ver_seguidores` | HikerAPI | `user_id` (str/int)<br>`tipo` (`ambos`/`followers`/`following`)<br>`page_id` / `cursor` | Mapeia contas seguidas e/ou seguidores do perfil com suporte completo a paginação. |
| `veridian_ver_posts_instagram` | `instagram_ver_posts` | HikerAPI | `user_id` (str/int)<br>`page_id` (str, opcional) | Extrai postagens recentes do feed, com legendas, hashtags, comentários e geolocalizações marcadas. |
| `veridian_ver_stories_instagram` | `instagram_ver_stories` | HikerAPI | `user_id` (str/int) | Puxa os stories publicados e ativos no perfil no momento exato da consulta. |
| `veridian_buscar_perfil_linkedin` | `linkedin_buscar_perfil` | Harvest API | `linkedin_url` (str) | Perfil profissional completo: histórico de cargos, empresas anteriores, formação acadêmica e certificações. |
| `veridian_linkedin_consulta_direta` | `linkedin_consultar_endpoint` | Harvest API | `endpoint_name` (str)<br>`target_url` (str) | Consulta avançada a endpoints específicos da plataforma de dados do LinkedIn. |
| `veridian_buscar_pessoas_linkedin` | `linkedin_buscar_pessoas_por_nome` | Harvest API | `nome_completo` (str)<br>`nome` / `sobrenome` (opcionais) | Busca profissionais no LinkedIn por nome e palavras-chave corporativas. |
| `veridian_ver_comentarios_post_linkedin` | `linkedin_ver_comentarios_post` | Harvest API | `post_url` (str)<br>`sort_by` / `page` | Coleta comentários e discussões abertas em uma publicação do LinkedIn. |
| `veridian_ver_reacoes_post_linkedin` | `linkedin_ver_reacoes_post` | Harvest API | `post_url` (str)<br>`page` (int) | Relação de perfis que reagiram (curtidas, aplausos, etc.) a um post específico. |
| `veridian_buscar_posts_linkedin` | `linkedin_buscar_posts` | Harvest API | `termo_busca` (str)<br>`profile_url` / `company_url` / `posted_limit` | Pesquisa publicações públicas no LinkedIn por termo ou menção a empresas. |
| `veridian_ver_posts_usuario_linkedin` | `linkedin_ver_posts_usuario` | Harvest API | `profile_url` (str)<br>`posted_limit` / `page` | Histórico cronológico de postagens publicadas por um usuário específico no LinkedIn. |
| `veridian_buscar_email_perfil_linkedin` | `linkedin_buscar_email_perfil` | Harvest API | `profile_url` (str)<br>`skip_smtp` (bool) | Localiza e valida endereços de e-mail corporativos vinculados ao perfil via validação SMTP. |
| `veridian_buscar_perfil_tiktok` | `tiktok_buscar_perfil` | SociaVault | `handle` (str, sem `@`) | Ficha de perfil do TikTok: biografia, total de curtidas, seguidores e contadores. |
| `veridian_listar_videos_tiktok` | `tiktok_listar_videos` | SociaVault | `handle` (str)<br>`sort_by` (`latest`/`popular`)<br>`max_cursor` | Lista publicações em vídeo do canal do TikTok com ordenação e paginação. |
| `veridian_listar_comentarios_tiktok` | `tiktok_listar_comentarios` | SociaVault | `url` (str)<br>`cursor` (int) | Comentários públicos deixados em um vídeo específico do TikTok. |
| `veridian_listar_respostas_comentario_tiktok` | `tiktok_listar_respostas_comentario` | SociaVault | `comment_id` (str)<br>`url` (str) | Respostas encadeadas a um comentário específico do TikTok. |
| `veridian_listar_seguidos_tiktok` | `tiktok_listar_seguindo` | SociaVault | `handle` (str)<br>`min_time` (int) | Relação de contas que o perfil do TikTok está seguindo. |
| `veridian_listar_seguidores_tiktok` | `tiktok_listar_seguidores` | SociaVault | `handle` (str) ou `user_id` | Lista de seguidores públicos do perfil do TikTok. |
| `veridian_buscar_usuarios_tiktok` | `tiktok_buscar_usuarios` | SociaVault | `query` (str)<br>`cursor` (int) | Pesquisa de usuários no TikTok por nome ou termo de busca. |

---

### 2.6. Redes Sociais — Facebook & Biometria/Imagens (Lighthouse)

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_perfil_facebook_info` | `lighthouse_fb_uid_info` | Lighthouse | `facebook_profile_uid` (str/int) | Perfil cadastral estruturado do Facebook (nome, gênero, foto, biografia) a partir do UID. |
| `veridian_perfil_facebook_wall` | `lighthouse_fb_uid_wall` | Lighthouse | `facebook_profile_uid` (str/int) | Histórico de publicações públicas no mural (timeline) da conta do Facebook. |
| `veridian_perfil_facebook_reposts` | `lighthouse_fb_uid_reposts` | Lighthouse | `facebook_profile_uid` (str/int) | Compartilhamentos e reposts efetuados pelo perfil. |
| `veridian_perfil_facebook_likes` | `lighthouse_fb_uid_likes` | Lighthouse | `facebook_profile_uid` (str/int) | Páginas curtidas e interesses públicos demonstrados na conta. |
| `veridian_perfil_facebook_comments` | `lighthouse_fb_uid_comments` | Lighthouse | `facebook_profile_uid` (str/int) | Comentários públicos deixados pelo perfil em páginas e murais. |
| `veridian_perfil_facebook_friends` | `lighthouse_fb_uid_friends` | Lighthouse | `facebook_profile_uid` (str/int) | Lista de amigos públicos da conta do Facebook. |
| `veridian_perfil_facebook_photos` | `lighthouse_fb_uid_photos` | Lighthouse | `facebook_profile_uid` (str/int) | Fotos públicas publicadas e marcadas no perfil. |
| `veridian_perfil_facebook_albums` | `lighthouse_fb_uid_albums` | Lighthouse | `facebook_profile_uid` (str/int) | Álbuns de fotos públicos da conta. |
| `veridian_perfil_facebook_live_streams` | `lighthouse_fb_uid_live_streams` | Lighthouse | `facebook_profile_uid` (str/int) | Transmissões de vídeo ao vivo (lives) realizadas pelo perfil. |
| `veridian_perfil_facebook_games` | `lighthouse_fb_uid_games` | Lighthouse | `facebook_profile_uid` (str/int) | Jogos e aplicativos conectados à conta. |
| `veridian_perfil_facebook_groups` | `lighthouse_fb_uid_groups` | Lighthouse | `facebook_profile_uid` (str/int) | Grupos públicos em que o perfil participa. |
| `veridian_facebook_search_posts` | `lighthouse_fb_search_posts` | Lighthouse | `query` (str) | Pesquisa global de postagens públicas no Facebook por palavras-chave. |
| `veridian_facebook_search_comments` | `lighthouse_fb_search_comments` | Lighthouse | `query` (str) | Busca global por comentários abertos no Facebook por termo. |
| `veridian_facebook_search_places` | `lighthouse_fb_search_places` | Lighthouse | `query` (str) | Busca de check-ins e locais cadastrados no Facebook. |
| `veridian_facebook_search_events` | `lighthouse_fb_search_events` | Lighthouse | `query` (str) | Busca de eventos públicos criados no Facebook. |
| `veridian_facebook_email_restore` | `lighthouse_fb_email_restore` | Lighthouse | `email` (str) | **Busca Reversa FB por E-mail**: Identifica a conta e o UID do Facebook atrelado ao e-mail. |
| `veridian_facebook_phone_restore` | `lighthouse_fb_phone_restore` | Lighthouse | `phone` (str/int) | **Busca Reversa FB por Telefone**: Identifica a conta e o UID do Facebook atrelado ao telefone. |
| `veridian_perfil_facebook_darknet` | `lighthouse_fb_uid_darknet` | Lighthouse | `facebook_profile_uid` (str/int) | Cruza o UID do perfil com repositórios de vazamentos e credenciais da Darknet. |
| `veridian_facebook_phone_to_name` | `lighthouse_fb_phone_to_name` | Lighthouse | `phone` (str/int) | Localiza o nome civil cadastrado no Facebook a partir do número de telefone. |
| `veridian_reconhecimento_facial_amplo` | `lighthouse_image_facecheck` | FaceCheck.ID | `photo_url` / `photo_b64` / `photo_fileid` | **Reconhecimento Facial Aberto**: Varre a internet aberta e indexadores biométricos para localizar faces correlatas. |
| `veridian_reconhecimento_facial_redes_sociais` | `lighthouse_image_search4faces` | Search4Faces | `photo_url` / `photo_b64` / `photo_fileid` | **Reconhecimento Facial em Redes**: Busca correspondência biométrica em perfis de redes sociais (VKontakte, etc.). |
| `veridian_image_geolocation` | `lighthouse_image_geolocation` | Lighthouse | `photo_url` / `photo_b64` / `photo_fileid` | **Geolocalização Geoespacial por IA**: Deduz coordenadas, cidade e país a partir dos elementos visuais da imagem. |

---

### 2.7. Domínios, Infraestrutura, IP e Vazamentos (Whois & CSINT)

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_consultar` | `whois_consultar` | WhoisXML | `target` (domínio, IP ou e-mail)<br>`ignore_raw_text` (bool)<br>`hard_refresh` (bool) | Registro WHOIS completo: dados do registrante, organização, data de criação, expiração e servidores DNS. |
| `veridian_consultar_ip` | `csint_consultar_ip` | CSINT.pro | `ip` (str, IPv4/IPv6) | Informações de geolocalização do IP, ISP/ASN, score de risco de fraude e detecção de VPN/Proxy/TOR. |
| `veridian_busca_vazamentos` | `csint_busca_universal` | CSINT.pro | `query` (str)<br>`tipo` (`email`/`phone`/`username`/`ip`/`auto`) | **Breach Intelligence**: Varredura universal em múltiplos repositórios de vazamentos de credenciais da Darknet. |
| `veridian_consultar_telefone_vazamento` | `csint_consultar_telefone` | CSINT / SEON | `telefone` (str, formato E.164) | Validação do telefone, operadora e mapeamento de contas ativas vinculadas (WhatsApp, Telegram, redes sociais). |
| `veridian_consultar_email_vazamento` | `csint_consultar_email` | CSINT / SEON | `email` (str) | Validação de existência do e-mail, análise de score de fraude e mapeamento em +20 serviços online. |

---

### 2.8. Web OSINT, Google Dorks e Internet Archive

| Nome White-label (`MCP`) | Função Interna | Provedor Base | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- | :--- |
| `veridian_buscar_web` | `tavily_buscar_web` | Tavily | `query` (str)<br>`search_depth` (`basic`/`advanced`) | Busca otimizada na web com resposta direta sintetizada e fontes ordenadas por relevância. |
| `veridian_extrair_texto_site` | `firecrawl_raspar_pagina` | Firecrawl | `url_alvo` (str) | Raspa uma página web completa e a converte em Markdown limpo, sem poluição de HTML ou propagandas. |
| `veridian_pesquisa_dorks` | `serper_buscar_web_dorks` | Serper.dev | `alvo` (domínio/empresa)<br>`categoria` (`arquivos_expostos`, `credenciais_e_backups`, `infraestrutura_e_login`, `subdominios`) | Executa **Google Dorks automatizados** para descobrir arquivos confidenciais (PDF, SQL, ENV, BKP) e subdomínios. |
| `veridian_buscar_google` | `serper_buscar_google` | Serper.dev | `query` (str, aceita operadores avançados) | Pesquisa direta no Google permitindo operadores como `site:`, `filetype:`, `inurl:`, `intitle:`. |
| `veridian_pesquisa_historica_web` | `wayback_consultar_disponibilidade` | Wayback Machine | `url_alvo` (str)<br>`timestamp` (str, opcional) | Verifica capturas históricas preservadas no Internet Archive para uma determinada URL. |
| `veridian_listar_imagens_historicas` | `wayback_listar_imagens` | Wayback Machine | `url_alvo` (str)<br>`limite` (int, padrão 50) | Lista imagens e mídias históricas arquivadas de um site (inclusive arquivos apagados). |
| `veridian_listar_snapshots_historicos` | `wayback_listar_snapshots` | Wayback Machine | `url_alvo` (str)<br>`limite` (int)<br>`apenas_mudancas` (bool) | Histórico cronológico completo de versões capturadas da página web desde sua criação. |

---

### 2.9. Dossiê Canônico e Enriquecimento Automático

| Nome White-label (`MCP`) | Função Interna | Parâmetros de Entrada | Descrição & Retorno Esperado |
| :--- | :--- | :--- | :--- |
| `veridian_gerar_dossie` | `investigador_gerar_dossie` | `cpf` (str/int)<br>`salvar_laudo` (bool, padrão True) | **Consolidação Pericial (Zero Créditos)**: Cruza todas as consultas locais de um CPF, deduplica contatos, calcula pontuação de confiança e emite laudo em Markdown. |
| `veridian_enriquecer_dossie` | `investigador_enriquecer_dossie` | `cpf` (str/int)<br>`max_emails` / `max_telefones` / `max_cnpjs` (int)<br>`apenas_corroborados` (bool)<br>`incluir_vazamentos` (bool) | **Enriquecimento Autônomo**: Roda em lote análise de reputação SEON e vazamentos para todos os contatos do dossiê e gera timeline para empresas ligadas. |

---

## 3. Recursos Nativos MCP (MCP Resources)

Os recursos nativos permitem que LLMs leiam dados consolidados ou de status sem gastar chamadas de ferramentas (`tool_call`).

| URI do Recurso | Parâmetros na URI | Tipo de Conteúdo | Descrição & Utilidade |
| :--- | :--- | :--- | :--- |
| `osint://dossie/{cpf}` | `{cpf}`: CPF com 11 dígitos | `text/markdown` | Retorna diretamente o Laudo Pericial Consolidado do alvo em formato Markdown estruturado. |
| `osint://cache/{cache_id}` | `{cache_id}`: ID do cache (ex: `bigdata_12345678900`) | `application/json` | Permite inspecionar o JSON original de qualquer consulta previamente realizada. |
| `osint://status` | _Nenhum_ | `application/json` | Retorna o status em tempo real do servidor, versão do protocolo, provedores ativos e telemetria de 24h. |
| `osint://cpfs-em-cache` | _Nenhum_ | `application/json` | Lista todos os CPFs que possuem coletas de dados salvas no cache local. |

---

## 4. Prompts Estruturados MCP (MCP Prompts)

Templates de prompts guiados para direcionar LLMs na condução de investigações seguindo metodologias periciais:

| Nome do Prompt | Argumentos | Objetivo & Metodologia Executada |
| :--- | :--- | :--- |
| `investigar_pessoa_fisica` | `cpf` (obrigatório)<br>`prioridade` (opcional) | Conduz a triagem cadastral de PF, checagem de mandados de prisão, antecedentes criminais, enquadramento PEP, vínculos e geração de dossiê consolidado. |
| `investigar_pessoa_juridica` | `cnpj` (obrigatório) | Auditoria de CNPJ: consulta cadastral, mapeamento de sócios e tomadores de decisão (QSA), empresas ligadas e timeline de evolução societária. |
| `investigar_advogado_oab` | `oab_numero` (obrigatório)<br>`oab_estado` (obrigatório) | Instrução rigorosa para mapear processos judiciais no Escavador exclusivamente via número de OAB e UF. |
| `investigar_redes_sociais` | `alvo` (obrigatório)<br>`plataforma` (opcional) | Fluxo investigativo integrado cruzando presença digital no Instagram, LinkedIn, TikTok e Facebook. |
| `investigar_veiculo_placa` | `placa` (obrigatório) | Rastreamento veicular por placa com identificação do titular e subsequente qualificação patrimonial. |
| `investigar_vazamento_breach` | `dado_alvo` (obrigatório) | Triagem de segurança contra vazamentos de dados na Darknet, fraude de e-mail e reputação telefônica. |

---

## 5. Resumo Numérico das Capacidades

- **Total de Ferramentas (Tools):** 79
- **Total de Recursos Nativos (Resources):** 4
- **Total de Prompts Nativos (Prompts):** 6
- **Provedores de Inteligência Integrados:** BigDataCorp, Unitfour, Escavador, CSINT.pro, HikerAPI, Harvest API, Lighthouse / FaceCheck / Search4Faces, SociaVault, WhoisXML, Tavily, Firecrawl, Serper.dev e Internet Archive.
- **Protocolo Suportado:** FastMCP 1.2+ / Model Context Protocol Spec (transportes STDIO e SSE com autenticação por chave de API).
