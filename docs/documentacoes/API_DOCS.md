# API Docs

## 1. Visão geral

A API do BrandPulse é implementada com FastAPI e registrada em `app/main.py` por meio dos routers de `analytics` e `respostas`.

Documentação interativa:

```text
http://127.0.0.1:8000/docs
```

### Fluxo geral

```text
HTTP request
    ↓
FastAPI Router
    ↓
Schema / validação de parâmetros
    ↓
Service e/ou Repository
    ↓
SQLite via SQLAlchemy
    ↓
Schema de resposta
    ↓
HTTP response
```

No `POST /respostas`, parte da lógica de negócio fica diretamente na rota. No `GET /share-of-voice`, o cálculo é delegado ao service. No `GET /top-citacoes`, a rota busca as respostas no repository e então chama o service de ranking.

## 2. Comportamento global

### Rate limiting

Os endpoints possuem limites configurados com SlowAPI e usam o endereço remoto do cliente como chave:

| Endpoint | Limite |
|---|---:|
| `GET /share-of-voice` | `10000/minute` |
| `GET /top-citacoes` | `10000/minute` |
| `POST /respostas` | `50000/minute` |

Quando o limite é excedido, a API retorna:

```http
429 Too Many Requests
```

```json
{
  "detail": "Rate limit exceeded"
}
```

### CORS

A aplicação permite CORS para as seguintes origens locais:

```text
http://127.0.0.1:5500
http://localhost:5500
http://127.0.0.1:5000
http://localhost:5000
```

Métodos e headers são aceitos de forma ampla nessas origens.

### Rota inexistente

Rotas não encontradas utilizam um handler próprio e retornam:

```http
404 Not Found
```

```json
{
  "error": "rota_nao_encontrada",
  "message": "A rota /exemplo não existe."
}
```

## 3. `GET /health`

### Objetivo

Verificar se a aplicação HTTP está respondendo.

### Request

```http
GET /health
```

Não possui parâmetros.

### Response `200`

```json
{
  "status": "ok"
}
```

Esse endpoint também é utilizado pelo healthcheck do `docker-compose.yml`.

## 4. `GET /share-of-voice`

### Objetivo

Calcular a participação de uma marca entre todas as respostas persistidas e apresentar o mesmo cálculo separado por plataforma.

### Request

```http
GET /share-of-voice?marca=Acme
```

### Parâmetro `marca`

- tipo: `string`;
- obrigatório;
- tamanho mínimo: `1`;
- tamanho máximo: `100`.

A busca da marca é case-insensitive.

Exemplos equivalentes:

```text
Acme
acme
ACME
```

O endpoint não restringe o parâmetro às três marcas monitoradas. Uma marca não encontrada resulta em contagem zero.

### Regra de cálculo

```text
percentual =
(respostas que possuem uma menção à marca / total de respostas) × 100
```

Múltiplas ocorrências da mesma marca em uma resposta contam como uma única resposta para Share of Voice.

### Caso sem respostas

Quando o banco não possui respostas:

```json
{
  "marca": "Acme",
  "respostas_com_mencao": 0,
  "total_respostas": 0,
  "percentual": 0.0,
  "por_plataforma": []
}
```

### Response `200`

```json
{
  "marca": "Acme",
  "respostas_com_mencao": 1,
  "total_respostas": 2,
  "percentual": 50.0,
  "por_plataforma": [
    {
      "plataforma": "ChatGPT",
      "respostas_com_mencao": 1,
      "total_respostas": 1,
      "percentual": 100.0
    },
    {
      "plataforma": "Gemini",
      "respostas_com_mencao": 0,
      "total_respostas": 1,
      "percentual": 0.0
    }
  ]
}
```

### `por_plataforma`

Cada plataforma presente nas respostas é incluída no resultado, mesmo que a marca não apareça nela.

### Erros

Sem `marca`:

```http
422 Unprocessable Entity
```

O FastAPI gera a resposta de validação do parâmetro.

Com `marca` vazia ou com mais de 100 caracteres, também ocorre `422`.

## 5. `GET /top-citacoes`

### Objetivo

Retornar as respostas que possuem maior score de citação.

### Request

```http
GET /top-citacoes?n=5
```

### Parâmetro `n`

- tipo: `integer`;
- opcional;
- padrão: `5`;
- mínimo: `1`;
- não existe limite superior explícito.

Exemplos:

```http
GET /top-citacoes
GET /top-citacoes?n=1
GET /top-citacoes?n=10
```

### Regra de elegibilidade

Respostas sem nenhuma `Mencao` são removidas antes da ordenação.

### Score

```text
score = (marcas distintas × 3) + ocorrências totais
```

Exemplo:

```text
Acme → 2 ocorrências
Zenith → 1 ocorrência

score = (2 × 3) + 3
score = 9
```

### Ordenação

As respostas são ordenadas por score em ordem decrescente e o resultado é limitado por `n`.

A implementação não possui critério secundário explícito para empates.

### Response `200`

```json
[
  {
    "resposta_id": "http-002",
    "plataforma": "Gemini",
    "modelo": "gemini-2.5-pro",
    "resposta_texto": "A Acme é uma boa opção. A Acme possui bons recursos. A Zenith também é interessante.",
    "marcas": [
      "Acme",
      "Zenith"
    ],
    "score": 9.0
  }
]
```

### Observação sobre ocorrências

O schema de Top Citações retorna as marcas distintas, mas não retorna separadamente o número de ocorrências de cada marca. A quantidade de ocorrências é utilizada internamente no score.

### Erros

Exemplos que retornam `422`:

```http
GET /top-citacoes?n=0
GET /top-citacoes?n=-1
GET /top-citacoes?n=abc
```

O FastAPI trata a validação do parâmetro.

## 6. `POST /respostas`

### Objetivo

Receber uma resposta ou uma lista de respostas, validar os registros, detectar marcas, normalizar a plataforma, verificar duplicidade e persistir os registros válidos.

### Corpo aceito

A implementação aceita:

- um objeto JSON;
- uma lista de objetos JSON.

Exemplo de objeto:

```json
{
  "id": "r001",
  "pergunta": "Qual a melhor ferramenta de monitoramento?",
  "plataforma": "ChatGPT",
  "modelo": "gpt-5",
  "resposta_texto": "A Acme é uma opção.",
  "data_hora": "2026-01-15T10:00:00",
  "sentimento": "positivo"
}
```

Exemplo de lista:

```json
[
  {
    "id": "r001",
    "pergunta": "Qual a melhor ferramenta?",
    "plataforma": "ChatGPT",
    "modelo": "gpt-5",
    "resposta_texto": "A Acme é uma opção.",
    "data_hora": "2026-01-15T10:00:00",
    "sentimento": "positivo"
  },
  {
    "id": "r002",
    "pergunta": "Compare marcas.",
    "plataforma": "Gemini",
    "modelo": "gemini-2.5-pro",
    "resposta_texto": "A Zenith é outra opção.",
    "data_hora": "2026-01-15T11:00:00",
    "sentimento": null
  }
]
```

### Validação

Cada item é validado individualmente por `RespostaCreate`.

Campos obrigatórios:

- `id`;
- `pergunta`;
- `plataforma`;
- `resposta_texto`;
- `data_hora`.

Campos opcionais:

- `modelo`;
- `sentimento`.

As strings obrigatórias possuem tamanho mínimo de um caractere.

### Processamento

Para cada item válido, a rota:

1. detecta menções;
2. cria os objetos `Mencao` com sua contagem de ocorrências;
3. normaliza a plataforma;
4. cria `Resposta`;
5. verifica duplicidade;
6. persiste se não houver duplicidade.

### Response `201`

Quando o request original é um objeto e a resposta é criada, o endpoint retorna um único `RespostaResponse`.

Quando o request original é uma lista e ao menos uma resposta é criada, retorna uma lista de `RespostaResponse`.

Exemplo simplificado:

```json
{
  "id": 1,
  "resposta_id": "r001",
  "pergunta": "Qual a melhor ferramenta?",
  "plataforma": "ChatGPT",
  "modelo": "gpt-5",
  "resposta_texto": "A Acme é uma opção.",
  "data_hora": "2026-01-15T10:00:00",
  "sentimento": "positivo",
  "mencoes": [
    {
      "id": 1,
      "resposta_id": 1,
      "marca": "Acme",
      "ocorrencias": 1
    }
  ]
}
```

### Registros inválidos em listas

Uma lista pode conter itens válidos e inválidos.

Nesse caso, os inválidos são ignorados e os válidos continuam sendo processados. Se pelo menos uma resposta for criada, a resposta HTTP é `201`.

### Duplicidades

Duplicatas são ignoradas e não são retornadas no payload de sucesso.

A regra considera iguais os campos:

```text
pergunta
plataforma normalizada
modelo
resposta_texto
data_hora
sentimento
```

O ID externo não participa da deduplicação.

### Quando nada é criado

Se todas as entradas forem inválidas ou duplicadas, a API retorna:

```http
422 Unprocessable Entity
```

com estrutura equivalente a:

```json
{
  "detail": {
    "message": "Todos os dados enviados já estão no banco de dados ou você enviou apenas dados inválidos.",
    "respostas_invalidas": []
  }
}
```

Se houver registros inválidos, `respostas_invalidas` contém seus dados e a mensagem de validação gerada durante o processamento.

### Erro durante persistência

Erros inesperados durante `repository.criar()` são registrados e propagados. Eles não são convertidos pela rota em um schema de erro próprio.

### Corpo com formato inválido

Um corpo que não seja objeto ou lista compatível com a assinatura `dict | list[dict]` é rejeitado pelo FastAPI antes da execução da lógica da rota, com `422`.

## 7. Relação com os schemas

A documentação completa dos contratos está em `SCHEMAS_DOCS.md`.

Resumo:

```text
POST /respostas
    ↓
RespostaCreate
    ↓
Resposta + Mencao
    ↓
RespostaResponse
```

Analytics:

```text
GET /share-of-voice
    ↓
ShareOfVoiceResponse

GET /top-citacoes
    ↓
list[TopCitacaoResponse]
```

## 8. Execução local

```bash
uv sync
uv run brandpulse run
```

Depois:

```text
http://127.0.0.1:8000/docs
```

## 9. Execução com Docker

```bash
docker compose up --build
```

O Compose publica `8000:8000` e usa `/health` como healthcheck.
