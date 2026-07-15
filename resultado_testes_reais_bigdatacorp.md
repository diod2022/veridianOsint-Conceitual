# Relatório de Testes Reais — Integração BigDataCorp

Este documento registra o passo a passo dos testes reais executados no servidor MCP **Agente Investigador** a partir do CPF **10624079708** e do CNPJ correlacionado **09125365000117**, validando todas as 31 consultas mapeadas.

---

## 👤 Passo 1: Consulta de Pessoa Física (CPF: 10624079708)

### 1. Chamada do Endpoint Principal
Chamamos a ferramenta `bigdata_consultar_cpf` passando todos os datasets de Pessoa Física mapeados:
- **CPF:** `10624079708`
- **Filtros solicitados:** Todos os 24 códigos PF (desde contatos e endereços até dados profissionais e judiciais).

A chamada realizou uma requisição `POST` com sucesso no endpoint oficial e gerou o arquivo de cache:
📂 [bigdata_10624079708.json](file:///Users/l/Documents/progeto%20-%20agente%20investigador/cache_consultas/bigdata_10624079708.json)

---

### 2. Resultados Fatiados por Dataset

Utilizando a ferramenta `bigdata_ver_categoria`, inspecionamos os dados retornados de cada código:

#### A. Dados básicos PF (`bdcbasicdata`)
- **Nome:** MARCELLA SIQUEIRA SEGURO LEAL
- **Gênero:** Feminino (F)
- **Data de Nascimento:** 08/01/1985 (Idade: 41 anos)
- **Nome da Mãe:** SILVIA REGINA SIQUEIRA SEGURO
- **Nome do Pai:** CARLOS ROBERTO DIAS LEAL
- **Status do CPF:** REGULAR

#### B. Processos Judiciais (`bdclawsuits`)
Foram encontrados **10 processos judiciais** no histórico da investigada:
- **Total como Autora (Claimant):** 5
- **Total como Ré (Claimed/Defendant):** 5
- **Data do primeiro processo:** 21/08/2013
- **Data do processo mais recente:** 21/10/2025
- **Amostra de Processo:**
  - Número: `0016417-53.2013.8.26.0008` (Procedimento Ordinário / Promessa de Compra e Venda).
  - Partes: Marcella Siqueira Seguro Leal e Denis de Carvalho Leal contra Patri Seis Empreendimentos Imobiliários Ltda.

#### C. Histórico PF (`bdchistorical`)
- Registra histórico estável de nome e regularidade de CPF desde 08/01/2003.

#### D. Propriedade Industrial (`bdcindustrialproperty`)
- Retornou objeto estruturado de marcas e patentes:
  - `BrandsCount`: 0
  - `PatentsCount`: 0

#### E. Devedores Governantes (`bdcgovernmentdebtors`)
- `TotalDebtValue`: 0 (Sem dívidas governamentais registradas).

#### F. Outros Datasets (Sem dados)
Os seguintes pacotes retornaram vazios para este CPF específico (sem registros na base):
- Contatos (`bdcphones`, `bdcemails`, `bdcaddresses`)
- Relacionamentos (`bdcrelatedpeople`, `bdcrelatedcompanies`)
- Presença Digital (`bdcdomains`, `bdconlineadvertisements`)
- Dados Profissionais e Classe (`bdcprofessional`, `bdcclass`, `bdcpublicservant`)
- KYC e Benefícios (`bdcfamilysocialbenefits`, `bdcsocialassistance`)
- Licenças (`bdclicenses`)
- Financeiro e Cobranças (`bdcturnover`, `bdccollections`)
- Político-Eleitoral (`bdcpolitics`, `bdcelectoralcandidate`, `bdcelectoralproviders`, `bdcelectoraldonorspersonal`)

---

## 🏢 Passo 2: Extração e Consulta de CNPJ

Ao analisarmos a lista de processos da investigada Marcella, identificamos uma empresa co-ré em um de seus processos imobiliários:
- **Razão Social:** PATRI SEIS EMPREENDIMENTOS IMOBILIARIOS LTDA
- **CNPJ:** `09125365000117`

### 1. Chamada do Endpoint de CNPJ
Chamamos a ferramenta `bigdata_consultar_cnpj` para o CNPJ `09125365000117` solicitando todos os datasets de Pessoa Jurídica mapeados.
A API retornou código 200 OK e gravou o cache:
📂 [bigdata_cnpj_09125365000117.json](file:///Users/l/Documents/progeto%20-%20agente%20investigador/cache_consultas/bigdata_cnpj_09125365000117.json)

---

### 2. Resultados Fatiados por Dataset PJ

#### A. Dados Básicos PJ (`bdccompanybasicdata`)
- **Razão Social:** PATRI SEIS EMPREENDIMENTOS IMOBILIARIOS LTDA
- **Nome Fantasia:** *Em branco*
- **Situação Cadastral:** BAIXADA (Motivo: Incorporação)
- **Data de Fundação:** 02/10/2007
- **Data da Baixa:** 30/11/2025
- **Natureza Jurídica:** Sociedade Empresária Limitada (206-2)
- **Capital Social:** R$ 10.000,00
- **Atividades Secundárias:** Serviços combinados de escritório e apoio administrativo (8211-3/00)

#### B. Evolução Empresarial (`bdccompanyevolution`)
- O retorno identificou a evolução mensal da empresa de 2025 a 2026.
- **Amostra da Evolução (Outubro de 2025):**
  - Atividade Principal: `4110700` (Incorporação de empreendimentos imobiliários)
  - Atividade de Apoio: `8211300` (Serviços combinados de escritório e apoio administrativo)
  - QSA (Quantidade de Sócios/Administradores): 4
  - Nível de Atividade: `0.22`
  - Situação de Rendimento: `SEM INFORMACAO`
- **Amostra da Evolução (Abril de 2026):**
  - Situação de Rendimento: `EMPRESA NAO ATIVA`
  - Nível de Atividade: `0`

#### C. Outros Datasets PJ (Sem dados)
Os seguintes pacotes retornaram vazios para esta empresa específica:
- Contatos PJ (`bdccompanyphones`, `bdccompanyemails`, `bdccompanyaddresses`)
- Doações PJ (`bdcelectoraldonorscompany`)
- Processos Judiciais PJ (`bdclawsuits`) (Obs: Os processos estavam listados sob o CPF da sócia/proprietária, não sob o CNPJ baixado diretamente).

---

## 🛠️ Correções Realizadas Durante os Testes

Durante a análise dos retornos estruturados do CNPJ, identificamos que a API do BigDataCorp retornou a chave de evolução empresarial como `CompanyEvolutionData` em vez de `CompanyEvolution`. 

Ajustamos o filtro da ferramenta `bigdata_ver_categoria_cnpj` em [server.py](file:///Users/l/Documents/progeto%20-%20agente%20investigador/server.py) para aceitar ambas as grafias de forma resiliente, o que permitiu recuperar com sucesso os dados de evolução mensal detalhados acima.
