# Step By Step

Arquivo destinado a registrar, de forma cronológica, as principais etapas, decisões e aprendizados durante o desenvolvimento do BrandPulse.

## Etapas

### 1. Entendimento do problema

- Análise dos requisitos do desafio.
- Pesquisa sobre o problema de análise de menções em respostas de IA.
- Definição das principais funcionalidades da aplicação.
- Identificação das principais decisões técnicas do projeto.

### 2. Configuração inicial do projeto

- Criação da estrutura inicial do repositório.
- Configuração do ambiente de desenvolvimento.
- Definição das dependências iniciais.
- Configuração do Ruff para linting e formatação.
- Criação do `README.md`, `SECURITY.md` e `STEP_BY_STEP.md`.
- Definição das primeiras convenções de organização e qualidade.

### 3. Modelagem dos dados

- Definição das entidades `Resposta` e `Mencao`.
- Definição dos campos e tipos utilizados.
- Criação do relacionamento entre respostas e menções.
- Definição da quantidade de ocorrências de cada marca.
- Criação dos modelos SQLAlchemy.
- Criação dos schemas Pydantic.
- Criação dos primeiros arquivos JSON e fixtures para desenvolvimento e testes.

### 4. Testes da modelagem e do banco de dados

- Configuração do Pytest.
- Criação de testes para modelos e schemas.
- Testes de criação e relacionamento entre `Resposta` e `Mencao`.
- Configuração de SQLite em memória para os testes.
- Testes da conexão e criação das tabelas.
- Correção de problemas relacionados ao carregamento lazy do SQLAlchemy.
- Execução dos testes e verificações com Ruff.

### 5. Implementação da detecção de menções

- Definição das marcas monitoradas: `Acme`, `Zenith` e `Nimbus`.
- Implementação da busca case-insensitive.
- Tratamento de variações de escrita.
- Definição de regras para reduzir falsos positivos.
- Contagem das ocorrências de cada marca.
- Criação do serviço de detecção de menções.
- Criação de testes para diferentes tipos de ocorrência.

### 6. Implementação da ingestão de dados

- Implementação da leitura de arquivos JSON.
- Validação dos registros utilizando Pydantic.
- Tratamento de registros inválidos sem interromper todo o processamento.
- Validação do formato dos arquivos de entrada.
- Integração com o schema `RespostaCreate`.
- Criação de fixtures para dados válidos, inválidos e mínimos.
- Criação de testes para diferentes cenários de ingestão.

### 7. Implementação do pipeline de processamento

- Integração entre ingestão, validação e detecção de menções.
- Definição do fluxo de processamento de uma resposta.
- Criação das entidades `Mencao`.
- Integração com o `RespostaRepository`.
- Separação das responsabilidades entre as camadas.
- Permissão para processar respostas sem menções.
- Criação de testes para o fluxo completo.

### 8. Implementação da análise de Share of Voice

- Definição do cálculo de Share of Voice.
- Cálculo baseado na quantidade de respostas que mencionam a marca.
- Implementação do percentual geral.
- Implementação do percentual por plataforma.
- Criação dos schemas `PlatformShare` e `ShareOfVoiceResponse`.
- Implementação do serviço de analytics.
- Criação de testes para diferentes cenários de análise.

### 9. Implementação do serviço de Analytics

- Implementação do cálculo de Share of Voice.
- Implementação do cálculo do score de citação.
- Definição do critério utilizado para identificar citações fortes.
- Implementação do ranking de Top Citações.
- Filtro de respostas sem menções.
- Implementação do parâmetro `n`.
- Conversão dos resultados para os schemas de resposta.
- Criação de testes para cálculos, ordenação e limites do ranking.

### 10. Implementação e testes da API

- Criação da API utilizando FastAPI.
- Organização das rotas em routers.
- Implementação de `GET /share-of-voice`.
- Implementação de `GET /top-citacoes`.
- Implementação de `POST /respostas`.
- Integração das rotas com services e repositories.
- Validação das entradas e saídas com Pydantic.
- Definição dos códigos HTTP.
- Criação de testes utilizando `TestClient`.

### 11. Documentação e organização do projeto

- Documentação das principais partes da aplicação.
- Inclusão de docstrings nas classes e funções relevantes.
- Documentação das rotas, schemas, services e repository.
- Organização da documentação de acordo com as responsabilidades das camadas.
- Revisão da estrutura do projeto.
- Verificação de qualidade com Ruff.

### 12. Organização da documentação

- Criação da pasta `docs/`.
- Criação da pasta `docs/documentacoes/`.
- Organização da documentação técnica em arquivos Markdown.
- Criação da documentação da API.
- Documentação da estrutura do projeto.
- Documentação dos schemas.
- Padronização da linguagem e organização dos documentos.

### 13. Analytics, integração e testes automatizados

- Implementação do Share of Voice geral e por plataforma.
- Implementação do ranking de Top Citações.
- Implementação da busca de respostas por marca.
- Utilização de `distinct()` nas consultas por marca.
- Ajuste dos models e relacionamentos.
- Diferenciação entre ID interno e identificador externo.
- Validação individual das respostas recebidas pela API.
- Detecção automática de menções.
- Normalização das plataformas.
- Verificação de duplicidade antes da persistência.
- Ampliação dos testes de services, repositories, models e routes.
- Criação de fixtures e banco isolado para os testes.
- Criação de arquivo `.http` para testes manuais da API.

### 14. Dockerização

- Criação do `Dockerfile`.
- Criação do `.dockerignore`.
- Configuração da imagem Python 3.11.
- Configuração da execução com Uvicorn.
- Criação do `docker-compose.yml`.
- Exposição da API na porta `8000`.
- Configuração do acesso ao banco SQLite.
- Compartilhamento do diretório `data/` entre ambiente local e container.
- Garantia de que `uv run` e Docker Compose utilizem os mesmos dados persistidos.
- Testes de build, execução e persistência da aplicação em container.

### 15. Implementação de logs

- Adição de logging aos principais serviços.
- Registro de eventos importantes de analytics.
- Registro do processamento de Top Citações.
- Registro das marcas detectadas.
- Registro da normalização de plataformas.
- Utilização dos níveis `INFO` e `DEBUG`.
- Evitação da exposição do conteúdo completo das respostas nos logs.
- Padronização das mensagens para facilitar diagnóstico e acompanhamento.

### 16. Revisão e atualização da documentação

- Atualização da documentação da estrutura atual do projeto.
- Revisão da documentação dos endpoints.
- Atualização da documentação dos schemas Pydantic.
- Inclusão dos schemas de analytics.
- Atualização das regras de validação e tipos dos campos.
- Documentação da normalização de `data_hora`.
- Revisão dos exemplos de requisições e respostas.
- Remoção de informações desatualizadas.
- Redução de repetições entre os arquivos Markdown.
- Padronização da linguagem e estrutura da documentação.

### 17. Finalização dos detalhes do projeto

- Revisão geral da organização do projeto.
- Conferência da integração entre API, services, repositories e banco de dados.
- Revisão dos testes automatizados.
- Verificação das funcionalidades de ingestão, analytics e detecção de menções.
- Revisão dos logs e mecanismos de diagnóstico.
- Conferência da documentação em relação ao comportamento atual da aplicação.
- Preparação do projeto para entrega.

### 18. Arrumando erros gerais

- Terminado codigo de ingestao
- Adicionado CLI de ingestao
- Adicionado CLI de run da api
- Testes que possuiam erros arrumados
- API agora aceita tanto objetos individuais quanto multiplos objetos
- Melhorados testes em relaçao a duplicaçao de itens
- Adicionado Cl e pre-commit
- Terminado e arrumado erros dos arquivos README.md, STEP_BY_STEP.md, API_DOCS.md, ESTRUTURA_DOCS.md, SCHEMAS_DOCS.md
