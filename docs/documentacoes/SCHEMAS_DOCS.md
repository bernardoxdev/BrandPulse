# Documentação dos Schemas

Os schemas do BrandPulse utilizam Pydantic para validação e estruturação dos dados.

Os principais schemas estão no diretório:

```text
app/schemas/
```

## RespostaCreate

`RespostaCreate` representa uma resposta recebida pela aplicação.

Os dados de entrada incluem:

- `id`;
- `pergunta`;
- `plataforma`;
- `modelo`;
- `resposta_texto`;
- `data_hora`;
- `sentimento`.

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

A validação ocorre antes da criação do modelo de banco.

## RespostaResponse

`RespostaResponse` representa uma resposta retornada pela API após a persistência.

Ele estrutura os dados necessários para que o cliente receba a resposta armazenada.

## Analytics

Os schemas de analytics estão em:

```text
app/schemas/analytics.py
```

### PlatformShare

Representa o Share of Voice de uma marca em uma plataforma.

Campos:

```text
plataforma
respostas_com_mencao
total_respostas
percentual
```

### ShareOfVoiceResponse

Representa o resultado completo do cálculo de Share of Voice.

Campos:

```text
marca
respostas_com_mencao
total_respostas
percentual
por_plataforma
```

### TopCitacaoResponse

Representa uma resposta no ranking de citações.

Inclui informações como:

```text
resposta_id
plataforma
modelo
resposta_texto
marcas
score
```

## Ingestão

O schema relacionado ao resultado da ingestão está em:

```text
app/schemas/ingestao.py
```

Ele permite estruturar as estatísticas produzidas pelo processo de importação.

As métricas da ingestão são:

```text
total
criadas
invalidas
duplicadas
```

## Responsabilidade dos schemas

Os schemas não executam regras de negócio.

Sua responsabilidade é:

1. validar dados de entrada;
2. estruturar dados;
3. definir contratos de entrada e saída da aplicação.

As regras de negócio permanecem nos services e repositories correspondentes.
