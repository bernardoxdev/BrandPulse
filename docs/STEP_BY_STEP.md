# Step by Step

Este documento descreve o funcionamento do BrandPulse conforme a implementação atual, desde a entrada de dados até a persistência e as consultas analíticas.

## 1. Entrada dos dados

Existem dois caminhos principais para inserir respostas:

1. arquivo JSON pela CLI `brandpulse ingest arquivo.json`;
2. HTTP pelo `POST /respostas`.

Os dois caminhos recebem registros com a mesma estrutura conceitual e usam `RespostaCreate` para validar os dados.

A principal diferença está na organização do código: a CLI delega o processamento ao service `processar_respostas`, enquanto o endpoint POST executa diretamente na rota as etapas de validação, detecção, normalização, deduplicação e persistência.

### Arquivo JSON

`app/services/ingestao.py` abre o arquivo em UTF-8, executa `json.load()` e exige que o valor raiz seja uma lista.

Se o JSON raiz não for uma lista, a ingestão lança `ValueError`. JSON inválido também interrompe a execução porque o erro de parsing não é convertido em um resultado parcial.

## 2. Validação

A validação é feita por `RespostaCreate` em `app/schemas/respostas.py`.

Os campos são:

- `id`: string com pelo menos um caractere;
- `pergunta`: string com pelo menos um caractere;
- `plataforma`: string com pelo menos um caractere;
- `modelo`: string opcional;
- `resposta_texto`: string com pelo menos um caractere;
- `data_hora`: `datetime`;
- `sentimento`: string opcional.

### `data_hora`

Antes da validação final, o schema tenta converter explicitamente estes formatos:

```text
2026-09-22T10:00:00
2026-09-22 10:00:00
2026-09-22
22/09/2026
2026/09/22
```

Depois da etapa customizada, o Pydantic valida o valor como `datetime`.

### Registros inválidos

Na ingestão por arquivo, uma `ValidationError` incrementa `invalidas` e o loop continua com o próximo registro.

No `POST /respostas`, a mesma validação é feita individualmente. Os registros inválidos são armazenados em uma lista interna. Se houver pelo menos uma resposta válida que possa ser criada, as respostas válidas são retornadas e as inválidas não aparecem no payload de sucesso. Se nenhuma resposta for criada, a rota retorna `422` com a mensagem e a lista de registros inválidos.

## 3. Normalização

A plataforma é normalizada antes da criação da entidade `Resposta`.

O mapa explícito é:

```text
chatgpt   → ChatGPT
 gemini   → Gemini
perplexity → Perplexity
claude    → Claude
copilot   → Copilot
deepseek  → DeepSeek
```

O código primeiro converte o texto para minúsculas e remove grupos de caracteres não alfanuméricos. Em seguida, tenta recuperar a forma canônica do dicionário `PLATAFORMAS`.

Assim, valores como `ChatGPT`, `chatgpt` e `chat-gpt` resultam em `ChatGPT`.

Para uma plataforma que não esteja no mapa, o valor normalizado é a própria chave em minúsculas, sem separadores e sem caracteres não alfanuméricos.

Essa normalização também participa da deduplicação, porque ocorre antes da chamada de `repository.existe_duplicata`.

## 4. Detecção de menções

A detecção está em `app/services/mencoes.py`.

### Marcas monitoradas

```python
["Acme", "Zenith", "Nimbus"]
```

O conjunto é definido estaticamente no módulo.

### Estratégia

Para cada marca, o sistema monta uma regex a partir das letras alfanuméricas do nome. Entre as letras é permitido qualquer grupo de caracteres não alfanuméricos ou `_`.

O padrão recebe:

```text
(?<!\w)
...
(?!\w)
```

e é compilado com `re.IGNORECASE`.

Na prática, a estratégia permite reconhecer exemplos como:

```text
Acme
ACME
acme
AcMe
A.C.M.E.
A C M E
```

Ao mesmo tempo, os limites de palavra evitam que o padrão seja aceito no interior de outra sequência alfanumérica, portanto casos como `Acme123` e `AcmeLTDA` não são reconhecidos pela regra atual.

### Contagem

A função usa `findall()` e guarda, para cada marca encontrada, a quantidade de ocorrências.

Exemplo:

```text
"Acme é boa. Acme é conhecida. Zenith também."
```

gera conceitualmente:

```python
{
    "Acme": 2,
    "Zenith": 1,
}
```

Uma mesma resposta recebe uma `Mencao` por marca distinta encontrada. A quantidade de vezes que a marca aparece é armazenada em `Mencao.ocorrencias`.

### Limitação conhecida

A abordagem é simples e determinística, mas não resolve todos os casos de linguagem natural. Regexes podem aceitar texto que não deveria ser uma menção e rejeitar formas que deveriam ser aceitas. O próprio projeto registra como exemplos um caso semelhante a `parâmetros A, C, M e N` e outro como `AcmeLTDA`.

## 5. Construção da `Resposta`

Depois da validação e da detecção, o sistema constrói uma entidade ORM `Resposta`.

O campo externo recebido em `RespostaCreate.id` é armazenado como `Resposta.resposta_id`.

O objeto persistente possui ainda:

- pergunta;
- plataforma normalizada;
- modelo;
- texto da resposta;
- data/hora;
- sentimento;
- lista de `Mencao`.

A entidade `Resposta` também possui um `id` inteiro autoincremental, que é o identificador interno do banco.

## 6. Duplicidade

A deduplicação é implementada em `RespostaRepository.existe_duplicata`.

Uma resposta é considerada duplicada quando todos estes campos coincidem:

```text
pergunta
plataforma
modelo
resposta_texto
data_hora
sentimento
```

O `resposta_id` externo não participa da comparação.

Isso significa que duas respostas com IDs externos diferentes podem ser consideradas duplicadas se o restante do conteúdo for igual.

Também significa que diferenças apenas de formatação de plataforma podem desaparecer antes da comparação, porque a plataforma é normalizada primeiro.

Na CLI, uma duplicata incrementa `duplicadas` e não é persistida.

Na API, uma duplicata também é ignorada. Se existirem outras respostas válidas no mesmo request, elas podem ser criadas normalmente; se tudo for duplicado ou inválido, o endpoint retorna `422`.

## 7. Persistência

A persistência utiliza SQLAlchemy com SQLite.

### Banco

```text
sqlite:///./data/database.db
```

### Modelos

Existem duas tabelas principais:

- `respostas`;
- `mencoes`.

A relação é:

```text
Resposta 1 ─────── N Mencao
```

A relação ORM usa `back_populates` e `delete-orphan` no relacionamento de `Resposta.mencoes`.

### Repository

`RespostaRepository` encapsula as operações de acesso ao banco.

A criação é feita por:

```python
session.add(resposta)
session.commit()
session.refresh(resposta)
```

Cada chamada a `criar()` realiza seu próprio `commit`.

### Inicialização

No startup da aplicação, `create_tables()` é chamado. Essa função importa os models para registrar suas tabelas no metadata e depois executa `Base.metadata.create_all`.

Os testes não dependem do banco local: utilizam SQLite em memória e substituem as dependências de repository das rotas.

## 8. Analytics

As análises ficam em `app/services/analytics.py`.

### Share of Voice

A fórmula é:

```text
Share of Voice =
(respostas que mencionam a marca / total de respostas) × 100
```

O cálculo considera **respostas**, não ocorrências.

Se uma resposta mencionar `Acme` cinco vezes, ela conta uma vez no numerador.

#### Exemplo

Se existem 10 respostas e 3 possuem pelo menos uma menção a `Acme`:

```text
3 / 10 × 100 = 30%
```

### Caso de banco vazio

Quando não existem respostas, o serviço retorna:

```text
respostas_com_mencao = 0
total_respostas = 0
percentual = 0.0
por_plataforma = []
```

### Por plataforma

O serviço agrupa as respostas pela string armazenada em `Resposta.plataforma` e calcula, para cada grupo:

```text
respostas da plataforma que mencionam a marca
/
total de respostas da plataforma
× 100
```

Todas as plataformas presentes nas respostas entram no resultado, inclusive aquelas nas quais a marca não foi mencionada.

### Consulta da marca

A comparação da marca no service é case-insensitive:

```text
Acme
acme
ACME
```

são tratadas da mesma forma.

## 9. Score de citação

O ranking utiliza uma métrica própria implementada em `calcular_score_citacao`:

```text
score = (marcas distintas × 3) + ocorrências totais
```

### Exemplo

Uma resposta com:

```text
Acme → 2 ocorrências
Zenith → 1 ocorrência
```

tem:

```text
2 marcas distintas × 3 = 6
3 ocorrências = 3
score = 9
```

### Interpretação

O score combina dois sinais:

- diversidade: quantas marcas diferentes aparecem;
- frequência: quantas vezes as marcas aparecem ao todo.

O peso `3` dá mais importância à diversidade do que a uma ocorrência adicional isolada.

Essa é uma escolha específica desta implementação. Não existe uma fórmula universal para o conceito de “citação forte”; o projeto optou por uma métrica simples que pode ser explicada e testada.

### Trade-off

Uma resposta que cita várias marcas tende a subir mais no ranking do que uma resposta que repete somente uma marca, mesmo que a segunda tenha muitas ocorrências. Isso faz parte da definição atual do score.

## 10. Top Citações

`obter_top_citacoes` realiza três etapas:

1. remove respostas sem menções;
2. calcula o score de cada resposta restante;
3. ordena por score decrescente e aplica `[:n]`.

O parâmetro `n` é validado pelo FastAPI com `ge=1`.

Não existe limite superior explícito para `n`. Se `n` for maior do que a quantidade de respostas com menções, todas as respostas elegíveis são retornadas.

A implementação não define um critério secundário para empates; a ordenação considera apenas o score.

A resposta contém:

- `resposta_id` externo;
- plataforma;
- modelo;
- texto;
- lista de marcas distintas encontradas;
- score.

As quantidades de ocorrências não são retornadas diretamente no schema do ranking.

## 11. API

O `app/main.py` cria a aplicação FastAPI, registra os routers e expõe quatro rotas principais.

### `/health`

Retorna:

```json
{"status": "ok"}
```

É utilizado também pelo healthcheck do Docker Compose.

### `/share-of-voice`

A rota injeta um `RespostaRepository` e delega o cálculo a `calcular_share_of_voice`.

### `/top-citacoes`

A rota injeta um `RespostaRepository`, busca as respostas com `repository.listar()` e então chama `obter_top_citacoes`.

### `/respostas`

Aceita um objeto ou uma lista de objetos JSON e executa o processamento item a item diretamente na rota.

A validação usa `RespostaCreate`; a detecção usa `detectar_mencoes`; a plataforma passa por `normalizar_plataforma`; a persistência ocorre pelo `RespostaRepository`.

A documentação detalhada dos endpoints e erros está em `docs/documentacoes/API_DOCS.md`.

## 12. CLI

A CLI é criada em `app/cli.py` e registrada no `pyproject.toml` como:

```text
brandpulse = app.cli:main
```

### `brandpulse ingest arquivo.json`

O comando:

1. valida se o caminho existe;
2. valida se é um arquivo;
3. chama `processar_respostas`;
4. imprime as quatro estatísticas retornadas.

Exemplo:

```bash
uv run brandpulse ingest data/respostas_exemplo.json
```

Saída conceitual:

```text
Respostas recebidas: <total>
Respostas criadas: <criadas>
Respostas inválidas: <invalidas>
Respostas duplicadas: <duplicadas>
```

### `brandpulse run`

Executa:

```python
uvicorn.run("app.main:app", ...)
```

Parâmetros disponíveis:

```text
--host
--port
--reload
```

Os valores padrão são `127.0.0.1`, `8000` e reload desativado.

## 13. Testes

A suíte é organizada por camada.

### Validação e schemas

`tests/test_schemas.py` cobre:

- campos válidos;
- campos opcionais nulos;
- ausência de campos obrigatórios;
- conversão de `data_hora`.

### Models

`tests/test_models.py` verifica criação de `Resposta`, criação de `Mencao`, relacionamento e armazenamento da quantidade de ocorrências.

### Database

`tests/test_database.py` verifica conexão e criação das tabelas.

### Repository

`tests/test_repositories.py` cobre criação, busca por ID, listagem, busca por marca case-insensitive e deduplicação.

### Menções

`tests/test_mencoes.py` cobre:

- uma marca;
- várias marcas;
- várias ocorrências da mesma marca;
- case-insensitive;
- ausência de marcas;
- limite de palavra;
- pontuação;
- texto vazio;
- fixtures.

### Ingestão

`tests/test_ingestao.py` cobre:

- arquivos mínimos;
- arquivos de teste;
- arquivos válidos;
- registros inválidos;
- continuidade após registro inválido;
- raiz JSON diferente de lista;
- arquivo inexistente.

### Analytics

`tests/test_analytics.py` cobre:

- banco sem respostas;
- ausência de menções;
- 50% e 100% de Share of Voice;
- Share of Voice por plataforma;
- múltiplas ocorrências da mesma marca;
- case-insensitive;
- score com uma ou várias marcas;
- influência da diversidade;
- ordenação;
- limite `n`;
- exclusão de respostas sem menções;
- `n=1`;
- `n` maior que a quantidade disponível;
- modelo `None`;
- mesmo ID externo em respostas distintas;
- uso de um mesmo snapshot no cálculo.

### Rotas

`tests/test_routes.py` usa `TestClient` e cobre:

- criação com lista;
- criação com objeto individual;
- entradas inválidas;
- data inválida;
- duplicidade;
- detecção de menções;
- mistura de válidas e inválidas;
- Share of Voice;
- Top Citações;
- validação de `n`.

## 14. Execução automatizada de qualidade

O repositório contém pre-commit e GitHub Actions.

A CI atual instala Python 3.11, executa `uv sync --locked`, roda `pre-commit run --all-files` e depois `pytest`.

Os hooks de pre-commit incluem Ruff check, Ruff format e verificações de YAML, JSON, TOML, fim de arquivo e whitespace.
