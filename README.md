# BrandPulse

O **BrandPulse** é um serviço de análise de menções de marcas em respostas de ferramentas de Inteligência Artificial.

O projeto recebe respostas de diferentes plataformas de IA, identifica automaticamente as marcas monitoradas presentes nos textos e disponibiliza métricas para analisar a presença dessas marcas nas respostas.

## Objetivos

O projeto foi desenvolvido para:

- identificar menções de marcas em respostas de IA;
- contabilizar ocorrências de cada marca;
- armazenar respostas e suas respectivas menções;
- calcular **Share of Voice**;
- comparar a presença das marcas por plataforma;
- gerar um ranking de respostas com maior relevância de citação;
- permitir ingestão de respostas por arquivo JSON;
- disponibilizar os dados por uma API HTTP.

## Marcas monitoradas

Atualmente, o projeto trabalha com as seguintes marcas:

- `Acme`
- `Zenith`
- `Nimbus`

A detecção é case-insensitive e também contempla algumas variações de escrita definidas pelo serviço de menções.

## Arquitetura

A estrutura principal do projeto é:

```text
BrandPulse/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── analytics.py
│   │       └── respostas.py
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   │   ├── analytics.py
│   │   ├── ingestao.py
│   │   ├── mencoes.py
│   │   └── plataformas.py
│   ├── cli.py
│   └── main.py
├── data/
│   ├── respostas_exemplo.json
│   └── database.db
├── docs/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### Camadas

- **API**: expõe os endpoints HTTP.
- **Services**: concentra as regras de negócio.
- **Repositories**: centraliza o acesso ao banco.
- **Models**: representa as entidades persistidas.
- **Schemas**: valida e estrutura os dados de entrada e saída.
- **Database**: configura a persistência.
- **CLI**: fornece comandos para operação do projeto.
- **Tests**: contém os testes automatizados.

## Tecnologias

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Uvicorn
- pytest
- Ruff
- Docker / Docker Compose
- uv

## Instalação

Instale as dependências utilizando `uv`:

```bash
uv sync
```

Para executar os testes:

```bash
uv run pytest -v
```

Para verificar o código com Ruff:

```bash
uv run ruff check .
```

Para verificar a formatação:

```bash
uv run ruff format --check .
```

## Executando a API

A API pode ser iniciada pelo CLI:

```bash
uv run brandpulse run
```

Também é possível definir host, porta e hot reload:

```bash
uv run brandpulse run --host 127.0.0.1 --port 8000 --reload
```

A documentação interativa da API fica disponível no FastAPI em:

```text
http://127.0.0.1:8000/docs
```

## Ingestão de respostas

O BrandPulse possui um comando específico para importar respostas de um arquivo JSON:

```bash
uv run brandpulse ingest data/respostas_exemplo.json
```

A ingestão apresenta:

- quantidade total de registros recebidos;
- quantidade de respostas criadas;
- quantidade de registros inválidos;
- quantidade de respostas duplicadas.

Exemplo:

```text
Respostas recebidas: 10
Respostas criadas: 8
Respostas inválidas: 1
Respostas duplicadas: 1
```

Registros inválidos não interrompem o processamento dos demais registros.

Uma resposta é considerada duplicada de acordo com os critérios definidos no `RespostaRepository`.

## Formato de entrada

Os registros de entrada seguem o modelo `RespostaCreate`.

Exemplo:

```json
{
  "id": "r001",
  "pergunta": "Qual a melhor ferramenta de monitoramento?",
  "plataforma": "ChatGPT",
  "modelo": "gpt-5.1",
  "resposta_texto": "A Acme é uma opção.",
  "data_hora": "2026-01-15T10:00:00",
  "sentimento": "positivo"
}
```

O arquivo utilizado pela ingestão deve conter uma lista de objetos.

## API

### Share of Voice

```http
GET /share-of-voice?marca=Acme
```

Retorna a participação da marca entre as respostas armazenadas, incluindo a distribuição por plataforma.

O cálculo considera uma resposta como uma unidade: múltiplas ocorrências da mesma marca dentro da mesma resposta não fazem aquela resposta ser contabilizada mais de uma vez.

### Top citações

```http
GET /top-citacoes?n=5
```

Retorna as respostas com maior score de citação.

O score considera:

- quantidade de marcas distintas mencionadas;
- quantidade total de ocorrências das marcas.

## Testes

Os testes podem ser executados com:

```bash
uv run pytest -v
```

O projeto possui testes unitários, testes de rotas e testes de regressão para cenários importantes, incluindo:

- respostas sem menções;
- múltiplas ocorrências de uma marca;
- comparação case-insensitive;
- Share of Voice por plataforma;
- respostas com o mesmo identificador externo;
- cálculo de score;
- ranking de citações;
- ingestão de registros inválidos;
- detecção de duplicidades.

## Docker

Para executar o projeto com Docker Compose:

```bash
docker compose up --build
```

Para executar em segundo plano:

```bash
docker compose up --build -d
```

## Qualidade de código

O projeto utiliza Ruff para linting e formatação e pre-commit para automatizar verificações antes dos commits.

Antes de realizar um commit, é recomendado executar:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Documentação

A documentação complementar está organizada em `docs/`:

- [Passo a passo do projeto](docs/STEP_BY_STEP.md)
- [Documentação da API](docs/documentacoes/API_DOCS.md)
- [Estrutura da documentação](docs/documentacoes/ESTRUTURA_DOCS.md)
- [Documentação dos schemas](docs/documentacoes/SCHEMAS_DOCS.md)

## Limitações e melhorias futuras

### Detecção de marcas com regex

A detecção atual baseada em expressões regulares possui uma limitação conhecida: **regexes podem aceitar textos que não deveriam ser considerados menções**, como em casos semelhantes a `"parâmetros A, C, M e N"`, e também podem rejeitar textos que deveriam ser aceitos, como `"AcmeLTDA"`.

Uma melhoria futura desejável é tornar a identificação de marcas mais robusta, buscando uma estratégia pragmática que reduza falsos positivos e falsos negativos sem tornar excessivamente complexa a manutenção das regras de detecção.

Outras melhorias futuras podem incluir:

- evolução das regras de normalização de marcas;
- maior cobertura de casos de detecção;
- persistência em PostgreSQL para ambientes maiores;
- expansão das métricas de análise;
- melhorias no tratamento de concorrência durante ingestões.

## Licença

Consulte o arquivo `LICENSE` para obter os termos de utilização do projeto.
