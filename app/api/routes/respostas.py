import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.limiter import limiter
from app.database.connection import SessionLocal
from app.models.mencao import Mencao
from app.models.resposta import Resposta
from app.repositories.respostas import RespostaRepository
from app.schemas.respostas import RespostaCreate, RespostaResponse
from app.services.mencoes import detectar_mencoes
from app.services.plataformas import normalizar_plataforma

logger = logging.getLogger(__name__)
router = APIRouter()


def get_repository():
    session = SessionLocal()

    try:
        yield RespostaRepository(session)
    finally:
        session.close()


@router.post(
    "/respostas",
    response_model=RespostaResponse | list[RespostaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Cria novas respostas",
    description=(
        "Recebe uma resposta ou uma lista de respostas, valida cada item, "
        "descarta os dados inválidos, detecta automaticamente as menções "
        "de marcas presentes no texto e persiste as respostas válidas "
        "e suas respectivas menções."
    ),
    response_description="Lista das respostas válidas criadas.",
)
@limiter.limit("50000/minute")
def criar_respostas(
    request: Request,
    dados: dict | list[dict],
    repository: RespostaRepository = Depends(get_repository),
):
    entrada_individual = isinstance(dados, dict)
    itens = [dados] if entrada_individual else dados

    logger.info(
        "Iniciando processamento de %d respostas.",
        len(itens),
    )

    respostas = []
    respostas_invalidas = []
    duplicadas = 0

    for indice, dado in enumerate(itens, start=1):
        try:
            resposta_validada = RespostaCreate.model_validate(dado)

        except Exception as erro:
            logger.warning(
                "Resposta %d rejeitada durante a validação: %s",
                indice,
                str(erro),
            )

            respostas_invalidas.append(
                {
                    "dados": dado,
                    "erro": str(erro),
                }
            )

            continue

        logger.info(
            "Resposta %d validada com sucesso. resposta_id=%s",
            indice,
            resposta_validada.id,
        )

        mencoes_detectadas = detectar_mencoes(resposta_validada.resposta_texto)

        logger.info(
            "Menções detectadas para resposta_id=%s: %d marca(s).",
            resposta_validada.id,
            len(mencoes_detectadas),
        )

        mencoes = [
            Mencao(
                marca=marca,
                ocorrencias=ocorrencias,
            )
            for marca, ocorrencias in mencoes_detectadas.items()
        ]

        resposta = Resposta(
            resposta_id=resposta_validada.id,
            pergunta=resposta_validada.pergunta,
            plataforma=normalizar_plataforma(resposta_validada.plataforma),
            modelo=resposta_validada.modelo,
            resposta_texto=resposta_validada.resposta_texto,
            data_hora=resposta_validada.data_hora,
            sentimento=resposta_validada.sentimento,
            mencoes=mencoes,
        )

        if repository.existe_duplicata(resposta):
            duplicadas += 1

            logger.warning(
                "Resposta duplicada ignorada. resposta_id=%s",
                resposta_validada.id,
            )

            continue

        try:
            repository.criar(resposta)

        except Exception:
            logger.exception(
                "Erro ao persistir resposta. resposta_id=%s",
                resposta_validada.id,
            )
            raise

        respostas.append(resposta)

        logger.info(
            "Resposta criada com sucesso. resposta_id=%s",
            resposta_validada.id,
        )

    logger.info(
        "Processamento finalizado. Criadas=%d, inválidas=%d, duplicadas=%d.",
        len(respostas),
        len(respostas_invalidas),
        duplicadas,
    )

    if respostas:
        return respostas[0] if entrada_individual else respostas

    logger.warning(
        "Nenhuma resposta foi criada. Todas as entradas eram inválidas ou duplicadas."
    )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "message": (
                "Todos os dados enviados já estão no banco de dados "
                "ou você enviou apenas dados inválidos."
            ),
            "respostas_invalidas": respostas_invalidas,
        },
    )
