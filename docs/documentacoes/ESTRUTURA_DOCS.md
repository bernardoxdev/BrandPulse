# Estrutura do projeto BrandPulse

## 1. Visão geral

O BrandPulse separa a aplicação em camadas com responsabilidades distintas: entrada HTTP, validação e serialização, regras de negócio, acesso ao banco, modelos persistentes e infraestrutura.

A divisão não é totalmente simétrica. O fluxo da CLI de ingestão está concentrado em `app/services/ingestao.py`, enquanto o `POST /respostas` ainda contém parte de seu processamento diretamente na rota.

## 2. Estrutura atual

A árvore abaixo representa a estrutura relevante do repositório atual, incluindo os componentes de qualidade e execução presentes no GitHub:

```text
BrandPulse/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── analytics.py
│   │       └── respostas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── limiter.py
│   │   └── logging.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── init_db.py
│   │   └── tables.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mencao.py
│   │   └── resposta.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── respostas.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── ingestao.py
│   │   └── respostas.py
│   ├── services/
│   │   ├── __init__.py
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
│   ├── STEP_BY_STEP.md
│   └── documentacoes/
│       ├── API_DOCS.md
│       ├── ESTRUTURA_DOCS.md
│       └── SCHEMAS_DOCS.md
├── tests/
│   ├── fixtures/
│   │   ├── respostas_exemplo.json
│   │   ├── respostas_invalidas.json
│   │   ├── respostas_minimas.json
│   │   ├── respostas_teste.json
│   │   └── respostas_validas.json
│   ├── conftest.py
│   ├── test_analytics.py
│   ├── test_database.py
│   ├── test_ingestao.py
│   ├── test_mencoes.py
│   ├── test_models.py
│   ├── test_repositories.py
│   ├── test_routes.py
│   ├── test_schemas.py
│   └── teste_api.http
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

## 3. Camada `app/api`

### Responsabilidade

Define a entrada HTTP da aplicação e a conversão dos resultados para respostas HTTP.

### Arquivos

#### `app/api/routes/analytics.py`

Implementa:

- `GET /share-of-voice`;
- `GET /top-citacoes`.

Cria a dependência que fornece `RespostaRepository` a partir de `SessionLocal` e aplica os limites de requisição configurados no `limiter`.

No Share of Voice, a rota chama diretamente `calcular_share_of_voice`. No Top Citações, primeiro obtém as respostas com `repository.listar()` e depois envia essa lista para `obter_top_citacoes`.

#### `app/api/routes/respostas.py`

Implementa `POST /respostas`.

A rota recebe um dicionário ou lista de dicionários, valida cada item com `RespostaCreate`, chama a detecção de menções, normaliza a plataforma, monta `Resposta` e `Mencao`, verifica duplicidade e persiste com `RespostaRepository`.

### Dependências

A camada de API depende de schemas, services, models e repositories.

### O que a API não deveria fazer

A camada de API não deveria concentrar regras de negócio que possam ser reutilizadas por outros pontos de entrada. Na implementação atual, `POST /respostas` ainda executa parte do processamento diretamente na rota; esse é um ponto de evolução arquitetural.

## 4. `app/core`

### `app/core/limiter.py`

Cria o objeto `Limiter` do SlowAPI usando o endereço remoto do cliente como chave.

É utilizado pelos endpoints para aplicar limites por cliente.

### `app/core/logging.py`

Centraliza a configuração de logging.

A função `sanitizar_log` limita o tamanho da representação registrada e substitui caracteres de controle como `\r`, `\n`, `\t` e escape ANSI. Os logs são enviados para o console e para `logs/app.log`.

### Dependências

`main.py` configura o logging no ciclo de vida da aplicação. As demais camadas apenas obtêm loggers do módulo `logging` padrão.

## 5. `app/database`

### Responsabilidade

Concentra a infraestrutura de persistência SQLAlchemy.

### Arquivos

#### `connection.py`

Define:

- `DATABASE_URL = "sqlite:///./data/database.db"`;
- `engine`;
- `SessionLocal`.

O engine usa `check_same_thread=False` para permitir o uso do SQLite com o contexto da aplicação web.

#### `tables.py`

Define a classe `Base`, derivada de `DeclarativeBase`, que é usada pelos models SQLAlchemy.

#### `init_db.py`

Importa `app.models` para registrar os modelos no metadata e expõe `create_tables()`, que executa `Base.metadata.create_all`.

`create_tables()` é chamado no startup da aplicação via `lifespan`.

### Dependências

Models dependem de `Base`; repositories dependem de `SessionLocal` e dos models; `main.py` chama a inicialização do banco.

### O que não deveria fazer

Essa camada não deve conter regra de negócio de marca, score ou analytics. Sua responsabilidade é infraestrutura de persistência.

## 6. `app/models`

Representa as entidades persistidas.

### `app/models/resposta.py`

Define `Resposta` com:

- `id`: identificador interno inteiro, autoincremental;
- `resposta_id`: identificador externo string;
- `pergunta`;
- `plataforma`;
- `modelo`, opcional;
- `resposta_texto`;
- `data_hora`;
- `sentimento`, opcional;
- relacionamento `mencoes`.

### `app/models/mencao.py`

Define `Mencao` com:

- `id` interno;
- `resposta_id`, chave estrangeira para `respostas.id`;
- `marca`;
- `ocorrencias`.

A relação é bidirecional e usa `back_populates`. Em `Resposta`, o relacionamento possui `cascade="all, delete-orphan"`.

### Dependências

Models dependem da base declarativa do banco. Repositories e schemas de resposta utilizam os models, mas as entidades persistentes não dependem das rotas.

## 7. `app/repositories`

### Responsabilidade

Concentrar as operações de acesso ao banco referentes a respostas.

### `app/repositories/respostas.py`

`RespostaRepository` implementa:

- `criar`;
- `buscar_por_id`;
- `buscar_por_resposta_id`;
- `listar`;
- `existe_duplicata`;
- `listar_por_marca`.

A deduplicação compara:

```text
pergunta
plataforma
modelo
resposta_texto
data_hora
sentimento
```

O `resposta_id` externo não participa dessa comparação.

`listar_por_marca` usa `JOIN` com `Mencao`, compara a marca com `lower()` e aplica `distinct()` para evitar repetição da mesma resposta.

### Dependências

O repository depende de SQLAlchemy e models.

### O que não deveria fazer

Não deve decidir como uma marca é detectada nem calcular métricas de negócio. Essas responsabilidades estão nos services.

## 8. `app/schemas`

Define contratos Pydantic para entrada e saída.

### `analytics.py`

Contém:

- `PlatformShare`;
- `ShareOfVoiceResponse`;
- `TopCitacaoResponse`.

### `respostas.py`

Contém:

- `RespostaCreate`;
- `RespostasCreate`;
- `MencaoResponse`;
- `RespostaResponse`.

`RespostaCreate` é o schema usado efetivamente para validar dados recebidos pela ingestão e pelo `POST /respostas`.

`RespostasCreate` está definido no projeto, mas o `POST /respostas` recebe atualmente `dict | list[dict]` e faz a validação item a item, portanto esse wrapper não é usado como contrato direto da rota.

### `ingestao.py`

Contém `IngestaoResponseCLI`, estrutura para as quatro estatísticas da ingestão. O comando atual da CLI recebe o dicionário retornado pelo service e imprime os valores diretamente; o schema não é utilizado como retorno da função.

### Dependências

Schemas são utilizados por API e services, mas não devem carregar acesso ao banco ou regra de persistência.

## 9. `app/services`

É a camada de regras de negócio.

### `analytics.py`

Implementa:

- `calcular_share_of_voice`;
- `calcular_score_citacao`;
- `obter_top_citacoes`.

`calcular_share_of_voice` lê todas as respostas do repository e determina quais possuem uma menção correspondente à marca consultada. O cálculo por plataforma usa o mesmo conjunto de respostas.

`obter_top_citacoes` filtra respostas sem menções, calcula o score e retorna somente as primeiras `n` respostas.

### `ingestao.py`

Implementa o fluxo completo da ingestão por arquivo:

1. carregar o JSON;
2. exigir uma lista de registros;
3. validar cada item com `RespostaCreate`;
4. contabilizar inválidos;
5. detectar menções;
6. normalizar a plataforma;
7. construir `Resposta` e `Mencao`;
8. verificar duplicidade;
9. persistir;
10. retornar estatísticas.

### `mencoes.py`

Contém:

- `MARCAS_MONITORADAS`;
- `criar_padrao_marca`;
- `PADROES_MARCAS`;
- `detectar_mencoes`.

A detecção é feita com regex pré-compilada e `re.IGNORECASE`.

### `plataformas.py`

Normaliza nomes de plataformas. Há um mapa explícito para `ChatGPT`, `Gemini`, `Perplexity`, `Claude`, `Copilot` e `DeepSeek`. Valores não conhecidos são reduzidos a letras/dígitos em minúsculas, removendo separadores e outros caracteres não alfanuméricos.

## 10. `app/cli.py`

Define o entry point `brandpulse`.

Possui dois subcomandos:

- `ingest` — importa um arquivo JSON usando `processar_respostas`;
- `run` — inicia o Uvicorn apontando para `app.main:app`.

A CLI não implementa a regra de negócio da ingestão; para `ingest`, ela delega o processamento ao service.

## 11. `app/main.py`

É o ponto de composição da aplicação FastAPI.

No `lifespan`:

1. configura o logging;
2. cria as tabelas do banco;
3. libera a aplicação para receber requisições.

Também configura:

- CORS para origens locais específicas;
- SlowAPI middleware;
- handler para limite de requisições (`429`);
- handler para rotas inexistentes (`404`);
- `GET /health`;
- inclusão dos routers de analytics e respostas.

## 12. `data`

### `database.db`

Arquivo SQLite utilizado pela aplicação.

### `respostas_exemplo.json`

Arquivo de exemplo para demonstrar o formato de entrada da ingestão.

O exemplo inclui registros válidos, registros inválidos e uma duplicata intencional, sendo útil tanto para execução manual quanto para reproduzir a lógica de ingestão.

## 13. `docs`

### `docs/STEP_BY_STEP.md`

Explica o funcionamento do sistema de ponta a ponta.

### `docs/documentacoes/API_DOCS.md`

Documenta a API e seu comportamento externo.

### `docs/documentacoes/ESTRUTURA_DOCS.md`

Documenta esta organização e o papel das camadas.

### `docs/documentacoes/SCHEMAS_DOCS.md`

Detalha os schemas Pydantic e diferencia contratos de entrada, modelos persistentes e respostas da API.

## 14. `tests`

A suíte está separada por responsabilidade e possui 74 funções de teste distribuídas nos arquivos coletados por pytest.

### Principais grupos

- `test_analytics.py` — 25 testes;
- `test_database.py` — 2 testes;
- `test_ingestao.py` — 7 testes;
- `test_mencoes.py` — 9 testes;
- `test_models.py` — 4 testes;
- `test_repositories.py` — 6 testes;
- `test_routes.py` — 14 testes;
- `test_schemas.py` — 7 testes.

`tests/conftest.py` define fixtures, não testes coletáveis.

### `tests/fixtures`

Fornece JSONs para cenários inválidos, mínimos, válidos, gerais e de exemplo.

### Estratégia de banco

Os testes de rota e repository usam SQLite em memória. O `TestClient` recebe repositories substituídos por dependency overrides, isolando a suíte do arquivo `data/database.db`.

### `tests/teste_api.http`

Contém exemplos manuais de chamadas HTTP para criação de respostas, Share of Voice e Top Citações, incluindo parâmetros inválidos.

## 15. Configuração e execução

### `pyproject.toml`

Define metadados do pacote, Python mínimo `3.11`, dependências, grupos de desenvolvimento, configuração do Ruff, configuração do pytest e o entry point `brandpulse`.

### `uv.lock`

Registra as versões resolvidas das dependências utilizadas pelo projeto.

### `.python-version`

Indica a versão de Python usada pelo projeto no ambiente de desenvolvimento.

### `.pre-commit-config.yaml`

Executa Ruff check, Ruff format e hooks básicos de validação de arquivos.

### `.github/workflows/ci.yml`

A CI atual:

1. faz checkout;
2. instala `uv`;
3. instala Python 3.11;
4. executa `uv sync --locked`;
5. executa `pre-commit` em todos os arquivos;
6. executa `pytest`.

### `Dockerfile`

Cria uma imagem baseada em `python:3.11-slim`, instala `uv`, sincroniza as dependências sem o grupo de desenvolvimento e inicia Uvicorn em `0.0.0.0:8000`.

### `docker-compose.yml`

Executa o serviço `api`, publica a porta `8000`, monta `./data` e `./logs` e verifica a aplicação pelo endpoint `/health`.

## 16. Fluxo de dependências

```text
                    ┌────────────────────┐
                    │     API Router     │
                    └─────────┬──────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
             Schemas                     Services
                │                           │
                │                 ┌─────────┴─────────┐
                │                 │                   │
                ▼                 ▼                   ▼
             Models          Analytics /         Menções /
                │             Ingestão          Plataformas
                │                 │
                └─────────────────┼───────────────────┐
                                  ▼                   │
                            Repository ◄─────────────┘
                                  │
                                  ▼
                              SQLAlchemy
                                  │
                                  ▼
                                SQLite
```

No fluxo específico da ingestão pela CLI, a entrada vai diretamente da CLI para o service de ingestão. No `POST /respostas`, o processamento equivalente permanece parcialmente dentro da própria rota.

Essa separação mantém o acesso ao banco no repository e as operações analíticas nos services, mas a lógica de processamento da resposta ainda pode ser centralizada em uma evolução futura.
