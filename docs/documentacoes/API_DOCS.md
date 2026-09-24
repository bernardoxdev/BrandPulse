# Documentação da API

## Visão geral

O BrandPulse disponibiliza uma API HTTP construída com FastAPI.

Os endpoints principais são responsáveis por:

- inserir respostas;
- calcular Share of Voice;
- consultar o ranking de citações.

A documentação interativa pode ser acessada pelo FastAPI em `/docs` quando a aplicação estiver em execução.

---

## POST `/respostas`

Insere uma ou mais respostas.

### Entrada

O endpoint aceita um objeto ou uma lista de objetos.

Exemplo:

```json
{
  "id": "r001",
  "pergunta": "Qual a melhor ferramenta?",
  "plataforma": "ChatGPT",
  "modelo": "gpt-5.1",
  "resposta_texto": "A Acme é uma opção.",
  "data_hora": "2026-01-15T10:00:00",
  "sentimento": "positivo"
}
```

Durante o processamento:

1. o registro é validado;
2. as menções são detectadas;
3. a plataforma é normalizada;
4. a duplicidade é verificada;
5. a resposta é persistida.

Registros inválidos são descartados e respostas duplicadas não são inseridas.

---

## GET `/share-of-voice`

Calcula o Share of Voice de uma marca.

### Query parameter

`marca`

Exemplo:

```http
GET /share-of-voice?marca=Acme
```

### Resposta

O retorno contém:

- `marca`;
- `respostas_com_mencao`;
- `total_respostas`;
- `percentual`;
- `por_plataforma`.

Exemplo conceitual:

```json
{
  "marca": "Acme",
  "respostas_com_mencao": 4,
  "total_respostas": 10,
  "percentual": 40.0,
  "por_plataforma": [
    {
      "plataforma": "ChatGPT",
      "respostas_com_mencao": 2,
      "total_respostas": 5,
      "percentual": 40.0
    }
  ]
}
```

### Regra de contagem

Uma resposta é contabilizada uma única vez para a marca.

Assim, se `"Acme"` aparecer cinco vezes na mesma resposta, ela continua representando apenas uma resposta com menção.

---

## GET `/top-citacoes`

Retorna as respostas com maior score de citação.

### Query parameter

`n`

Define a quantidade máxima de resultados.

Exemplo:

```http
GET /top-citacoes?n=5
```

O valor padrão é `5`.

### Score

O score considera:

```text
quantidade de marcas distintas × 3
+
quantidade total de ocorrências
```

Exemplo:

```text
Acme: 2 ocorrências
Zenith: 1 ocorrência

2 marcas × 3 + 3 ocorrências = 9
```

---

## Rate limiting

Os endpoints de analytics possuem limite configurado pelo `slowapi`.

Os limites definidos atualmente são:

```text
/share-of-voice → 10000/minute
/top-citacoes   → 10000/minute
/respostas      → 50000/minute
```

---

## Tratamento de erros

A API utiliza os mecanismos de validação do Pydantic e as exceções HTTP do FastAPI.

Dados inválidos não devem ser interpretados como respostas válidas.

---

## Testando a API

Com a aplicação em execução:

```bash
uv run brandpulse run
```

A documentação interativa estará disponível em:

```text
http://127.0.0.1:8000/docs
```

Também é possível utilizar o arquivo:

```text
tests/teste_api.http
```

para executar requisições durante o desenvolvimento.
