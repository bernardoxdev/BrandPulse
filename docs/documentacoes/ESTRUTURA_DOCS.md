# Estrutura da Documentação

A documentação do BrandPulse está organizada para separar visão geral, fluxo de desenvolvimento, API e schemas.

```text
docs/
├── STEP_BY_STEP.md
└── documentacoes/
    ├── API_DOCS.md
    ├── ESTRUTURA_DOCS.md
    └── SCHEMAS_DOCS.md
```

## `STEP_BY_STEP.md`

Apresenta o fluxo de desenvolvimento e execução do projeto.

Inclui:

- preparação do ambiente;
- estrutura da aplicação;
- modelos;
- validação;
- detecção de menções;
- persistência;
- analytics;
- API;
- CLI;
- testes;
- Docker;
- melhorias futuras.

## `documentacoes/API_DOCS.md`

Documenta os endpoints HTTP do BrandPulse.

Inclui:

- métodos;
- parâmetros;
- exemplos;
- regras de negócio;
- rate limiting;
- tratamento de erros.

## `documentacoes/SCHEMAS_DOCS.md`

Documenta os schemas Pydantic usados na validação e na comunicação da aplicação.

## Organização

A documentação segue a separação das responsabilidades do código:

```text
Projeto
│
├── README
│   └── visão geral e início rápido
│
└── docs
    ├── fluxo de desenvolvimento
    ├── API
    └── schemas
```

O README funciona como ponto de entrada. Os documentos em `docs/` detalham aspectos específicos sem duplicar desnecessariamente as informações introdutórias.
