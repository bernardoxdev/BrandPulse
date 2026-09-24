# Schemas Docs

## 1. Visão geral

Os schemas Pydantic ficam em `app/schemas/` e representam contratos de entrada e saída. Eles não são equivalentes aos models SQLAlchemy usados para persistência.

A separação atual é:

```text
Entrada HTTP / arquivo
        ↓
Pydantic schema
        ↓
Model SQLAlchemy
        ↓
SQLite
        ↓
Pydantic response schema
```

Essa separação permite que o contrato externo da API seja diferente da representação interna usada pelo banco.

## 2. `RespostaCreate`

Arquivo: `app/schemas/respostas.py`

### Finalidade

Validar e estruturar uma resposta recebida pela API ou pela ingestão do arquivo JSON.

### Campos

| Campo | Tipo | Obrigatório | Validação / comportamento |
|---|---|---:|---|
| `id` | `str` | Sim | `min_length=1` |
| `pergunta` | `str` | Sim | `min_length=1` |
| `plataforma` | `str` | Sim | `min_length=1` |
| `modelo` | `str \| None` | Não | Pode ser `null` |
| `resposta_texto` | `str` | Sim | `min_length=1` |
| `data_hora` | `datetime` | Sim | Passa por normalização customizada antes da validação |
| `sentimento` | `str \| None` | Não | Pode ser `null` |

### Normalização de `data_hora`

O schema tenta converter explicitamente:

```text
YYYY-MM-DDTHH:MM:SS
YYYY-MM-DD HH:MM:SS
YYYY-MM-DD
DD/MM/YYYY
YYYY/MM/DD
```

Caso o valor seja um `datetime`, ele é mantido. Caso não seja reconhecido por essa etapa, o valor segue para a validação final do tipo `datetime` pelo Pydantic.

### Exemplo

```json
{
  "id": "r001",
  "pergunta": "Qual a melhor ferramenta?",
  "plataforma": "ChatGPT",
  "modelo": "gpt-5",
  "resposta_texto": "A Acme é uma opção.",
  "data_hora": "2026-01-15T10:00:00",
  "sentimento": "positivo"
}
```

### Campos opcionais

Um objeto válido pode ter:

```json
{
  "modelo": null,
  "sentimento": null
}
```

## 3. `RespostasCreate`

Arquivo: `app/schemas/respostas.py`

### Finalidade

Representar uma estrutura composta por uma lista de `RespostaCreate`.

### Estrutura

```text
respostas: list[RespostaCreate]
```

### Exemplo

```json
{
  "respostas": [
    {
      "id": "r001",
      "pergunta": "Qual a melhor ferramenta?",
      "plataforma": "ChatGPT",
      "modelo": "gpt-5",
      "resposta_texto": "A Acme é uma opção.",
      "data_hora": "2026-01-15T10:00:00",
      "sentimento": null
    }
  ]
}
```

### Uso atual

O schema está definido no projeto, mas não é usado como contrato direto do `POST /respostas`. A rota recebe `dict | list[dict]` e valida cada item com `RespostaCreate`.

## 4. `MencaoResponse`

Arquivo: `app/schemas/respostas.py`

### Finalidade

Representar uma menção quando uma `RespostaResponse` é devolvida pela API.

### Configuração

O schema usa:

```python
ConfigDict(from_attributes=True)
```

para permitir criação a partir de atributos de objetos ORM.

### Campos

| Campo | Tipo | Obrigatório |
|---|---|---:|
| `id` | `int` | Sim |
| `resposta_id` | `int` | Sim |
| `marca` | `str` | Sim |
| `ocorrencias` | `int` | Sim |

### Exemplo

```json
{
  "id": 1,
  "resposta_id": 1,
  "marca": "Acme",
  "ocorrencias": 2
}
```

O `resposta_id` deste schema corresponde ao identificador interno inteiro da entidade `Resposta` no banco.

## 5. `RespostaResponse`

Arquivo: `app/schemas/respostas.py`

### Finalidade

Representar uma resposta persistida retornada pelo `POST /respostas`.

### Configuração

Também usa:

```python
ConfigDict(from_attributes=True)
```

### Campos

| Campo | Tipo | Obrigatório |
|---|---|---:|
| `id` | `int` | Sim |
| `resposta_id` | `str` | Sim |
| `pergunta` | `str` | Sim |
| `plataforma` | `str` | Sim |
| `modelo` | `str \| None` | Sim no schema, podendo ser `null` |
| `resposta_texto` | `str` | Sim |
| `data_hora` | `datetime` | Sim |
| `sentimento` | `str \| None` | Sim no schema, podendo ser `null` |
| `mencoes` | `list[MencaoResponse]` | Sim |

### Exemplo

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

## 6. `PlatformShare`

Arquivo: `app/schemas/analytics.py`

### Finalidade

Representar o Share of Voice de uma marca dentro de uma plataforma específica.

### Campos

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `plataforma` | `str` | Sim | sem restrição extra |
| `respostas_com_mencao` | `int` | Sim | `>= 0` |
| `total_respostas` | `int` | Sim | `>= 0` |
| `percentual` | `float` | Sim | entre `0` e `100` |

### Exemplo

```json
{
  "plataforma": "ChatGPT",
  "respostas_com_mencao": 2,
  "total_respostas": 4,
  "percentual": 50.0
}
```

## 7. `ShareOfVoiceResponse`

Arquivo: `app/schemas/analytics.py`

### Finalidade

Representar o resultado completo do endpoint `GET /share-of-voice`.

### Campos

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `marca` | `str` | Sim | sem restrição extra no schema |
| `respostas_com_mencao` | `int` | Sim | `>= 0` |
| `total_respostas` | `int` | Sim | `>= 0` |
| `percentual` | `float` | Sim | entre `0` e `100` |
| `por_plataforma` | `list[PlatformShare]` | Sim | lista de resultados por plataforma |

### Exemplo

```json
{
  "marca": "Acme",
  "respostas_com_mencao": 2,
  "total_respostas": 4,
  "percentual": 50.0,
  "por_plataforma": [
    {
      "plataforma": "ChatGPT",
      "respostas_com_mencao": 1,
      "total_respostas": 2,
      "percentual": 50.0
    },
    {
      "plataforma": "Gemini",
      "respostas_com_mencao": 1,
      "total_respostas": 2,
      "percentual": 50.0
    }
  ]
}
```

## 8. `TopCitacaoResponse`

Arquivo: `app/schemas/analytics.py`

### Finalidade

Representar uma resposta elegível para o ranking de Top Citações.

### Campos

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `resposta_id` | `str` | Sim | identificador externo |
| `plataforma` | `str` | Sim | sem restrição extra |
| `modelo` | `str \| None` | Sim no schema, podendo ser `null` |
| `resposta_texto` | `str` | Sim | sem restrição extra |
| `marcas` | `list[str]` | Sim | lista de marcas distintas encontradas |
| `score` | `float` | Sim | `>= 0` |

### Exemplo

```json
{
  "resposta_id": "r002",
  "plataforma": "Gemini",
  "modelo": "gemini-2.5-pro",
  "resposta_texto": "A Acme e a Zenith são alternativas.",
  "marcas": [
    "Acme",
    "Zenith"
  ],
  "score": 8.0
}
```

O score do exemplo acima representa duas marcas distintas e duas ocorrências:

```text
(2 × 3) + 2 = 8
```

## 9. `IngestaoResponseCLI`

Arquivo: `app/schemas/ingestao.py`

### Finalidade

Representar as estatísticas calculadas pelo processamento de ingestão.

### Campos

| Campo | Tipo | Obrigatório |
|---|---|---:|
| `total` | `int` | Sim |
| `criadas` | `int` | Sim |
| `invalidas` | `int` | Sim |
| `duplicadas` | `int` | Sim |

### Exemplo

```json
{
  "total": 10,
  "criadas": 7,
  "invalidas": 2,
  "duplicadas": 1
}
```

### Uso atual

O service `processar_respostas` retorna um `dict` com essas quatro chaves e `app/cli.py` imprime seus valores. O `IngestaoResponseCLI` está definido no código, mas não é utilizado como tipo de retorno pela implementação atual.

## 10. Schema de entrada × Model × Schema de resposta

### Entrada

`RespostaCreate` representa o dado que chega ao sistema.

```text
id: str
pergunta: str
plataforma: str
modelo: str | None
resposta_texto: str
data_hora: datetime
sentimento: str | None
```

### Persistência

`Resposta` acrescenta um identificador interno inteiro e contém o relacionamento com `Mencao`:

```text
id: int
resposta_id: str
pergunta: str
plataforma: str
modelo: str | None
resposta_texto: str
data_hora: datetime
sentimento: str | None
mencoes: list[Mencao]
```

`Mencao` é uma entidade persistente separada e armazena a quantidade de ocorrências de uma marca.

### Saída

`RespostaResponse` expõe a entidade persistida, incluindo suas menções, mas mantém o contrato HTTP separado do model ORM.

Nos analytics, `ShareOfVoiceResponse` e `TopCitacaoResponse` são respostas específicas das regras analíticas e não representam tabelas do banco.

## 11. Identificadores

Há dois níveis de identificador para `Resposta`:

- `id`: inteiro interno, gerado pelo banco;
- `resposta_id`: string recebida da fonte externa.

Essa distinção é importante porque o segundo não é utilizado pela regra de deduplicação.

Para `Mencao`, o schema de resposta utiliza o `id` interno e o `resposta_id` inteiro correspondente à chave estrangeira da tabela `respostas`.

## 12. Regras que não existem nos schemas

A implementação não define enumeração para:

- `sentimento`;
- `plataforma`;
- marcas permitidas no parâmetro de Share of Voice.

A plataforma é normalizada em um service, e as marcas monitoradas são definidas no service de detecção. Isso significa que validação estrutural e regras de domínio são responsabilidades diferentes no código atual.
