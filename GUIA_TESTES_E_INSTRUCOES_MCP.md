# Guia de Instruções e Testes — Veridian OSINT MCP v2.0

Este documento reúne todas as instruções de inicialização, configuração em clientes LLM (Claude Desktop, Cursor, bots autônomos) e um roteiro prático com prompts para testar todas as funcionalidades do servidor MCP.

---

## 1. Modos de Execução do Servidor MCP

O servidor MCP suporta dois modos de operação:

### A. Modo STDIO (Padrão para Clientes Locais / Claude Desktop)
Utilizado quando o cliente LLM executa o servidor como subprocesso direto via stdin/stdout:
```bash
/home/lit/veridianOsint-Conceitual/.venv/bin/python server.py
```
> *Nota: O servidor ficará aguardando mensagens JSON-RPC via stdin. Este é o comportamento padrão esperado.*

### B. Modo SSE (Web / Clientes Remotos e Painel Administrativo)
Utilizado para conexões via rede HTTP com Server-Sent Events e para acessar o painel de administração:
```bash
/home/lit/veridianOsint-Conceitual/.venv/bin/python server.py --sse
```
- **Porta padrão**: `8000` (configurável via `FASTMCP_PORT` no `.env`)
- **Painel Administrativo**: Acesse no navegador `http://SEU_IP:8000/admin`

---

## 2. Configuração em Clientes LLM

### Claude Desktop (`claude_desktop_config.json`)

#### Opção 1: Conexão Local via STDIO
```json
{
  "mcpServers": {
    "veridian": {
      "command": "/home/lit/veridianOsint-Conceitual/.venv/bin/python",
      "args": ["/home/lit/veridianOsint-Conceitual/server.py"]
    }
  }
}
```

#### Opção 2: Conexão Remota via SSE (com Chave de Autenticação)
```json
{
  "mcpServers": {
    "veridian": {
      "url": "http://SEU_IP_SERVIDOR:8000/sse",
      "headers": {
        "Authorization": "Bearer SUA_CHAVE_API"
      }
    }
  }
}
```

---

## 3. Roteiro Prático de Testes (Prompts Prontos)

### 🧪 Teste 1: Biometria Facial 1:1 (`veridian_comparar_faces`)
**Objetivo**: Comparar duas fotografias e verificar se pertencem ao mesmo indivíduo com score de similaridade e veredito analítico.

> **Prompt para a LLM:**
> *"Consulte o perfil de Instagram `@brian.benigno`, obtenha a foto de perfil e execute uma comparação biométrica facial 1:1 com ela mesma usando a ferramenta `veridian_comparar_faces`. Me informe a similaridade percentual, o nível de confiança e o veredito."*

**Comportamento Esperado:**
- Retorno com `status: "sucesso"`.
- `match: true`, `similaridade_percentual: ~99%`, `nivel_confianca: "ALTA"`.
- Veredito: *"Alta probabilidade de ser a mesma pessoa"*.

---

### 🧪 Teste 2: Detecção e Recorte Facial em Grupo (`veridian_detectar_faces`)
**Objetivo**: Localizar todos os rostos em uma foto, identificar bounding boxes e salvar recortes alinhados no cache local.

> **Prompt para a LLM:**
> *"Analise a imagem da foto de perfil do usuário `@brian.benigno` com a ferramenta `veridian_detectar_faces`. Me informe quantas faces foram detectadas, a qualidade da detecção e o ID do recorte salvo no cache local."*

**Comportamento Esperado:**
- Retorno com `total_faces_detectadas: 1`, `confianca_deteccao: > 0.90`.
- Campo `cache_id_recorte` contendo o nome do arquivo recortado (ex: `face_crop_...jpg`).

---

### 🧪 Teste 3: Consulta Granular de CPF (`veridian_cpf_*`)
**Objetivo**: Buscar apenas blocos específicos de informação de Pessoa Física sem onerar dados agregados.

> **Prompt para a LLM:**
> *"Consulte unicamente os dados cadastrais básicos e os telefones do CPF `233.022.348-05` usando as ferramentas granulares do Veridian. Não consulte processos judiciais nem empresas neste momento."*

**Comportamento Esperado:**
- A LLM deve acionar `veridian_cpf_dados_basicos` e `veridian_cpf_telefones`.
- Não deve tentar rodar consultas massivas agregadas legadas.

---

### 🧪 Teste 4: Consulta Granular de Empresa / CNPJ (`veridian_cnpj_*`)
**Objetivo**: Obter dados de quadro societário (QSA) e dados cadastrais de uma empresa.

> **Prompt para a LLM:**
> *"Consulte os dados cadastrais básicos e o quadro societário (QSA) do CNPJ `02.886.838/0001-50` utilizando as ferramentas granulares do Veridian."*

**Comportamento Esperado:**
- Chamada direta a `veridian_cnpj_dados_basicos` e `veridian_cnpj_quadro_societario`.

---

### 🧪 Teste 5: Consulta de Processo Judicial por CNJ (`veridian_consultar_processos_judiciais`)
**Objetivo**: Puxar os detalhes, partes e movimentações de um processo judicial a partir do número CNJ único.

> **Prompt para a LLM:**
> *"Consulte os detalhes do processo judicial número `0002153-17.2018.8.26.0053` utilizando a ferramenta `veridian_consultar_processos_judiciais`."*

**Comportamento Esperado:**
- Retorno estruturado do processo com partes, tribunal e histórico de movimentações sem erros de parâmetro inválido.

---

### 🧪 Teste 6: Leitura e Persistência de Cache White-Label (`veridian_ler_cache`)
**Objetivo**: Validar a leitura direta de dados brutos salvos em cache durante as consultas anteriores.

> **Prompt para a LLM:**
> *"Acesse o cache da última consulta utilizando a ferramenta `veridian_ler_cache` e me informe um resumo do conteúdo bruto."*

**Comportamento Esperado:**
- Leitura instantânea do cache local sem erros de *“Cache não encontrado ou caminho inválido”*.

---

## 4. Catálogo das Principais Ferramentas MCP (White-Label)

| Ferramenta White-Label | Domínio | Descrição |
| :--- | :--- | :--- |
| **`veridian_comparar_faces`** | Biometria | Face Match 1:1 entre duas fotos (score 0-100%, distância cosseno e veredito). |
| **`veridian_detectar_faces`** | Biometria | Detecção de faces em fotos de grupo/posts e extração de recortes. |
| **`veridian_cpf_dados_basicos`** | Cadastral | Nome, nascimento, mãe, situação na Receita Federal. |
| **`veridian_cpf_telefones`** | Cadastral | Telefones fixos e celulares vinculados com temporalidade. |
| **`veridian_cpf_emails`** | Cadastral | Histórico de e-mails vinculados. |
| **`veridian_cpf_enderecos`** | Cadastral | Histórico de logradouros, bairros e cidades. |
| **`veridian_cpf_processos`** | Judicial | Relação de processos judiciais vinculados ao CPF. |
| **`veridian_cpf_empresas_e_socios`** | Societário | Empresas em que o CPF figura como sócio ou administrador. |
| **`veridian_cpf_parentes_e_relacionados`** | Vínculos | Parentes de 1º/2º grau e pessoas ligadas. |
| **`veridian_cnpj_dados_basicos`** | Empresarial | Razão social, nome fantasia, abertura, CNAEs. |
| **`veridian_cnpj_quadro_societario`** | Societário | Sócios, administradores, participações e coligadas. |
| **`veridian_cnpj_evolucao_historica`** | Societário | Timeline histórica de alterações do CNPJ. |
| **`veridian_consultar_processos_judiciais`** | Judicial | Busca direta de processo pelo número CNJ. |
| **`veridian_buscar_processos_oab`** | Judicial | Busca de processos por inscrição da OAB e UF. |
| **`veridian_ler_cache`** | Cache | Leitura do conteúdo bruto salvo no cache local. |
| **`veridian_limpar_cache`** | Cache | Limpeza seletiva do cache de investigações. |
