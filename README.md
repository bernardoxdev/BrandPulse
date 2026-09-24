# BrandPulse

## Sobre o projeto

O **BrandPulse** é um serviço HTTP em Python para identificar e armazenar menções de marcas em respostas de ferramentas de Inteligência Artificial e, a partir desses dados, calcular métricas de presença por resposta e por plataforma.

A implementação atual trabalha com três marcas monitoradas:

- `Acme`
- `Zenith`
- `Nimbus`

As respostas podem entrar por arquivo JSON, por meio da CLI de ingestão, ou diretamente pela API em `POST /respostas`. Depois de persistidas, elas são utilizadas pelos endpoints de análise.

## Funcionalidades

- ingestão de respostas a partir de arquivo JSON;
- validação individual dos registros com Pydantic;
- processamento parcial de arquivos com registros inválidos;
- normalização de nomes de plataformas;
- detecção case-insensitive das marcas monitoradas;
- reconhecimento de algumas variações de escrita das marcas;
- contagem de ocorrências por marca dentro de cada resposta;
- persistência de respostas e menções em SQLite usando SQLAlchemy;
- deduplicação baseada no conteúdo da resposta;
- cálculo de Share of Voice geral e por plataforma;
- ranking de Top Citações por score;
- inclusão de novas respostas pela API;
- CLI para ingestão e execução da API;
- documentação OpenAPI gerada pelo FastAPI;
- testes unitários e de rotas;
- lint, formatação, pre-commit e CI.

## Arquitetura

A aplicação é dividida em rotas, schemas, services, repositories, models e infraestrutura de banco. A principal diferença entre os dois caminhos de entrada é que a CLI utiliza diretamente `app.services.ingestao.processar_respostas`, enquanto `POST /respostas` executa seu próprio fluxo de validação, detecção, normalização, deduplicação e persistência dentro da rota.

### Fluxo de ingestão pela CLI

```text
arquivo JSON
    ↓
carregar dados
    ↓
RespostaCreate / Pydantic
    ↓
normalização da plataforma
    ↓
detecção de menções
    ↓
criação de Resposta + Mencao
    ↓
verificação de duplicidade
    ↓
RespostaRepository
    ↓
SQLAlchemy / SQLite
```

### Fluxo da API

```text
HTTP
 ↓
Router
 ├── GET /share-of-voice
 │      ↓
 │   analytics service
 │      ↓
 │   repository
 │      ↓
 │   SQLite
 │
 ├── GET /top-citacoes
 │      ↓
 │   repository.listar()
 │      ↓
 │   analytics service
 │
 └── POST /respostas
        ↓
     RespostaCreate
        ↓
     detecção + normalização
        ↓
     deduplicação
        ↓
     repository
        ↓
     SQLite
```

A aplicação cria as tabelas durante o startup no `lifespan` do FastAPI. O arquivo SQLite utilizado é `data/database.db`.

A separação em camadas reduz a concentração de acesso ao banco nas rotas e permite que as principais regras analíticas e de processamento sejam testadas isoladamente. O fluxo do `POST /respostas`, porém, ainda contém lógica que também existe no service de ingestão da CLI; essa duplicação é uma limitação conhecida da estrutura atual.

## Por que essas tecnologias?

### Python 3.11

É a linguagem base da aplicação. O código utiliza recursos de tipagem e sintaxe compatíveis com Python 3.11.

**Papel no projeto:** implementação da API, CLI, services, persistência e testes.

**Por que:** mantém a aplicação pequena, tipada e direta de implementar para o escopo do projeto.

**Evolução possível:** manter a linguagem e evoluir apenas os componentes de infraestrutura caso o volume ou os requisitos mudem.

### FastAPI

É responsável pela camada HTTP, pelos routers, pelos códigos de resposta e pela geração da documentação OpenAPI.

**Papel no projeto:** expõe `/share-of-voice`, `/top-citacoes`, `/respostas` e `/health`.

**Por que:** oferece integração direta com Pydantic, validação de parâmetros e documentação interativa.

**Evolução possível:** continuar utilizando o mesmo framework mesmo em uma evolução maior, adicionando apenas requisitos adicionais de operação ou autenticação se eles forem necessários.

### Pydantic

É utilizado principalmente para validar entradas e estruturar saídas.

**Papel no projeto:** `RespostaCreate`, schemas de analytics e schemas de resposta da API.

**Por que:** centraliza regras simples de validação, como campos obrigatórios, tamanho mínimo e conversão de `data_hora`.

**Evolução possível:** criar contratos de entrada ainda mais explícitos diretamente nas assinaturas dos endpoints, aproveitando integralmente a documentação automática do FastAPI.

### SQLAlchemy

Faz a ponte entre os modelos Python e o banco relacional.

**Papel no projeto:** modelos ORM, sessões, consultas, relacionamentos e persistência.

**Por que:** permite separar o modelo de domínio persistente do código de infraestrutura do SQLite e evita SQL manual para as operações atuais.

**Evolução possível:** PostgreSQL pode substituir o SQLite com menor impacto sobre as regras de negócio porque o acesso está concentrado no repository.

### SQLite

É o mecanismo de persistência atual.

**Papel no projeto:** armazena `Resposta` e `Mencao` em `data/database.db`.

**Por que:** o escopo do projeto é local e não exige banco distribuído ou configuração de infraestrutura externa.

**Trade-off:** simplifica a execução, mas não é a escolha natural para cenários com maior concorrência ou múltiplas instâncias da aplicação.

**Evolução possível:** PostgreSQL para um ambiente maior ou com requisitos de concorrência mais altos.

### pytest

Executa os testes das camadas e dos endpoints.

**Papel no projeto:** cobre schemas, models, repository, ingestão, detecção de menções, analytics, rotas e banco.

**Por que:** permite validar as regras de negócio isoladamente e também exercitar a API com `TestClient`.

**Evolução possível:** aumentar principalmente os testes de integração do pipeline completo de ingestão.

### Ruff

Fornece linting e formatação.

**Papel no projeto:** `ruff check .` e `ruff format --check .`.

**Por que:** mantém o código consistente sem adicionar múltiplas ferramentas para funções semelhantes.

**Evolução possível:** manter a configuração atual e ampliar regras apenas quando houver necessidade real.

### pre-commit

Executa automaticamente verificações antes dos commits.

**Papel no projeto:** Ruff check/format e hooks de arquivos YAML, JSON, TOML, whitespace e fim de arquivo.

**Por que:** desloca verificações básicas de qualidade para antes do commit.

**Evolução possível:** incluir outras verificações apenas se trouxerem benefício concreto para o repositório.

### Docker / Docker Compose

Empacotam e executam a aplicação em um ambiente reproduzível.

**Papel no projeto:** o `Dockerfile` instala as dependências de produção e o Compose executa a API, mapeando as portas e os diretórios `data` e `logs`.

**Por que:** facilita iniciar a API sem configurar manualmente o ambiente Python.

**Evolução possível:** adicionar serviços externos somente se os requisitos do projeto exigirem isso.

### uv

É utilizado para gerenciamento do ambiente, dependências, lockfile e entry point da CLI.

**Papel no projeto:** `uv sync`, `uv run`, `uv.lock` e o script `brandpulse` definido em `pyproject.toml`.

**Por que:** centraliza instalação e execução em comandos curtos e reprodutíveis.

**Evolução possível:** manter o mesmo fluxo de dependências enquanto o projeto permanecer nesse porte.

## Estrutura do projeto

```text
BrandPulse/
├── .github/workflows/ci.yml
├── app/
│   ├── api/routes/
│   │   ├── analytics.py
│   │   └── respostas.py
│   ├── core/
│   │   ├── limiter.py
│   │   └── logging.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── init_db.py
│   │   └── tables.py
│   ├── models/
│   │   ├── mencao.py
│   │   └── resposta.py
│   ├── repositories/
│   │   └── respostas.py
│   ├── schemas/
│   │   ├── analytics.py
│   │   ├── ingestao.py
│   │   └── respostas.py
│   ├── services/
│   │   ├── analytics.py
│   │   ├── ingestao.py
│   │   ├── mencoes.py
│   │   └── plataformas.py
│   ├── cli.py
│   └── main.py
├── data/
│   ├── database.db
│   └── respostas_exemplo.json
├── docs/
├── tests/
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── README.md
├── SECURITY.md
├── pyproject.toml
└── uv.lock
```

A descrição detalhada das responsabilidades está em [`docs/documentacoes/ESTRUTURA_DOCS.md`](docs/documentacoes/ESTRUTURA_DOCS.md).

## Como executar

### Requisitos

- Python 3.11
- `uv`
- Docker e Docker Compose, caso prefira executar em contêiner

### Instalação

```bash
uv sync
```

### Inicialização da API

A forma prevista pela CLI é:

```bash
uv run brandpulse run
```

Por padrão, a API é iniciada em `127.0.0.1:8000`.

Também é possível informar host, porta e reload:

```bash
uv run brandpulse run --host 127.0.0.1 --port 8000 --reload
```

A documentação interativa do FastAPI fica em:

```text
http://127.0.0.1:8000/docs
```

### Ingestão pela CLI

```bash
uv run brandpulse ingest data/respostas_exemplo.json
```

O comando verifica se o caminho existe e se corresponde a um arquivo. Depois executa `processar_respostas` e exibe:

- total de registros recebidos;
- respostas criadas;
- registros inválidos;
- respostas duplicadas.

O arquivo de exemplo contém registros válidos, registros inválidos e uma duplicata intencional. Em um banco inicialmente vazio, o fluxo permite observar as quatro categorias.

### Testes

```bash
uv run pytest -v
```

### Lint

```bash
uv run ruff check .
```

### Formatação

Para verificar:

```bash
uv run ruff format --check .
```

Para formatar:

```bash
uv run ruff format .
```

### Docker Compose

```bash
docker compose up --build
```

Em segundo plano:

```bash
docker compose up --build -d
```

O Compose expõe a porta `8000` e monta os diretórios locais `data/` e `logs/` dentro do contêiner.

## API

| Método | Rota | Função |
|---|---|---|
| `GET` | `/health` | Verifica se a aplicação está respondendo. |
| `GET` | `/share-of-voice` | Calcula a presença de uma marca entre as respostas armazenadas e separa o cálculo por plataforma. |
| `GET` | `/top-citacoes` | Retorna as respostas com maior score de citação. |
| `POST` | `/respostas` | Valida, processa, detecta menções e persiste uma ou várias respostas. |

Detalhes de parâmetros, respostas e erros estão em [`docs/documentacoes/API_DOCS.md`](docs/documentacoes/API_DOCS.md).

## Testes

A suíte de testes é separada por responsabilidade. Há testes para:

- schemas e validações de entrada;
- criação e relacionamento dos models;
- conexão e criação das tabelas;
- repository e deduplicação;
- ingestão e validação de arquivos;
- detecção de marcas e contagem de ocorrências;
- Share of Voice e Top Citações;
- rotas da API e códigos HTTP.

Os arquivos de teste também cobrem casos como múltiplas ocorrências, múltiplas marcas, caixa de texto diferente, respostas sem menções, registros inválidos, duplicidades, `n` no ranking e respostas com o mesmo identificador externo.

Os testes de rota substituem os repositories por um banco SQLite em memória, evitando dependência do arquivo `data/database.db` durante a suíte.

## Decisões e trade-offs

### SQLite

Foi escolhido como persistência local porque a implementação não depende de um servidor de banco externo. A aplicação cria as tabelas com SQLAlchemy no startup.

O principal trade-off é operacional: SQLite simplifica a execução, mas não é uma solução orientada a múltiplas instâncias e alta concorrência.

### Repository Pattern

`RespostaRepository` concentra criação, consultas, listagem, deduplicação e busca por marca. Isso mantém a lógica de acesso ao banco fora das rotas e dos services analíticos.

O trade-off é adicionar uma camada extra para uma aplicação pequena. Neste projeto, a camada possui responsabilidades concretas e não é apenas uma abstração vazia.

### Validação com Pydantic

`RespostaCreate` concentra a estrutura mínima exigida para uma resposta e normaliza `data_hora` antes da validação final do tipo `datetime`.

Nos fluxos de ingestão, uma falha de validação de um registro não encerra o processamento dos outros registros.

### Detecção baseada em texto

A detecção usa regex pré-compiladas para as três marcas monitoradas. A abordagem é determinística, simples de testar e suficiente para o conjunto atual de regras.

O trade-off é precisão: variações artificiais podem introduzir falsos positivos ou falsos negativos.

### Score de citação

O ranking utiliza:

```text
score = (marcas distintas × 3) + ocorrências totais
```

A fórmula combina diversidade de marcas e frequência. O peso `3` faz com que mencionar uma marca adicional tenha mais impacto no score do que apenas uma ocorrência adicional.

A implementação ordena somente por score em ordem decrescente; não há um critério secundário explícito para empates.

### Dados inválidos

A ingestão via arquivo continua com os registros seguintes quando um item é inválido. Isso é coerente com a origem esperada dos dados, que pode conter registros inconsistentes.

No `POST /respostas`, o mesmo princípio é aplicado item a item: registros inválidos são acumulados e respostas válidas continuam sendo processadas. Se nenhuma resposta puder ser criada, o endpoint retorna `422`.

### Duplicidades

A regra atual não utiliza o identificador externo como chave de unicidade. Uma resposta é considerada duplicada quando `pergunta`, `plataforma`, `modelo`, `resposta_texto`, `data_hora` e `sentimento` coincidem.

Como a plataforma é normalizada antes da comparação, formas como `ChatGPT`, `chatgpt` e `chat-gpt` podem resultar na mesma plataforma armazenada.

## Limitações e melhorias futuras

### Detecção de marcas com regex

A estratégia atual permite reconhecer diferentes caixas e variações com separadores, mas não resolve todos os casos linguísticos. **Regexes podem aceitar texto que não deveriam, como parâmetros A, C, M e N, e rejeitar texto que deveriam aceitar, como AcmeLTDA. Uma evolução futura seria melhorar a estratégia de detecção para lidar melhor com limites de palavra, variações de escrita e falsos positivos/negativos, avaliando uma abordagem mais robusta conforme a necessidade do produto.**

### Centralização do pipeline de processamento

A ingestão pela CLI utiliza `app.services.ingestao`, enquanto `POST /respostas` repete parte do mesmo processamento na rota. Uma evolução natural seria extrair esse fluxo para um service compartilhado entre os dois pontos de entrada.

### Determinismo do ranking

O ranking é ordenado apenas por score. Uma evolução futura pode definir um segundo critério para desempates.

### Persistência

O SQLite é suficiente para o escopo atual. Em um cenário com mais concorrência, múltiplas instâncias ou maior volume, PostgreSQL pode ser avaliado.

### Concorrência na deduplicação

A checagem de duplicidade ocorre antes da inserção. Em concorrência, duas execuções poderiam consultar o mesmo estado antes de persistirem. Uma futura evolução pode transformar essa regra em uma garantia atômica do banco.

## Histórico

O projeto é versionado em Git e o repositório contém commits separados para implementação, testes, documentação, qualidade de código, infraestrutura e correções. O histórico faz parte do processo de desenvolvimento e permite acompanhar a evolução da aplicação, não apenas o estado final.
