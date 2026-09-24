import logging

from fastapi import APIRouter, Depends, Query, Request

from app.core.limiter import limiter
from app.database.connection import SessionLocal
from app.repositories.respostas import RespostaRepository
from app.schemas.analytics import (
    ShareOfVoiceResponse,
    TopCitacaoResponse,
)
from app.services.analytics import (
    calcular_share_of_voice,
    obter_top_citacoes,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_repository():
    session = SessionLocal()

    try:
        yield RespostaRepository(session)
    finally:
        session.close()


@router.get(
    "/share-of-voice",
    response_model=ShareOfVoiceResponse,
    summary="Calcula o Share of Voice de uma marca",
    description=(
        "Retorna a participação de uma marca entre as respostas "
        "armazenadas na aplicação."
    ),
    response_description="Dados de Share of Voice da marca.",
)
@limiter.limit("10000/minute")
def share_of_voice(
    request: Request,
    marca: str = Query(
        min_length=1,
        max_length=100,
        description="Nome da marca que será analisada.",
        examples=["Acme"],
    ),
    repository: RespostaRepository = Depends(get_repository),
):
    logger.info(
        "Iniciando cálculo de Share of Voice para a marca '%s'",
        marca,
    )

    resultado = calcular_share_of_voice(
        repository=repository,
        marca=marca,
    )

    logger.info(
        "Share of Voice calculado para '%s': %.2f%% (%d de %d respostas)",
        marca,
        resultado.percentual,
        resultado.respostas_com_mencao,
        resultado.total_respostas,
    )

    return resultado


@router.get(
    "/top-citacoes",
    response_model=list[TopCitacaoResponse],
    summary="Retorna as respostas com mais citações",
    description=(
        "Retorna as respostas que possuem maior quantidade de "
        "citações de marcas, ordenadas de acordo com o score calculado."
    ),
    response_description="Lista das respostas com maior número de citações.",
)
@limiter.limit("10000/minute")
def top_citacoes(
    request: Request,
    n: int = Query(
        default=5,
        ge=1,
        description="Quantidade máxima de respostas a serem retornadas.",
        examples=[5],
    ),
    repository: RespostaRepository = Depends(get_repository),
):
    logger.info(
        "Iniciando consulta de top citações com limite n=%d",
        n,
    )

    respostas = repository.listar()

    logger.info(
        "Encontradas %d respostas para análise de top citações",
        len(respostas),
    )

    resultado = obter_top_citacoes(
        respostas=respostas,
        n=n,
    )

    logger.info(
        "Consulta de top citações concluída: %d resultados retornados",
        len(resultado),
    )

    return resultado
