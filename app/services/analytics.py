import logging

from app.models.resposta import Resposta
from app.repositories.respostas import RespostaRepository
from app.schemas.analytics import (
    PlatformShare,
    ShareOfVoiceResponse,
    TopCitacaoResponse,
)

logger = logging.getLogger(__name__)


def calcular_share_of_voice(
    repository: RespostaRepository,
    marca: str,
) -> ShareOfVoiceResponse:
    logger.info(
        "Iniciando cálculo de Share of Voice para a marca '%s'",
        marca,
    )

    respostas = repository.listar()

    total_respostas = len(respostas)

    if total_respostas == 0:
        return ShareOfVoiceResponse(
            marca=marca,
            respostas_com_mencao=0,
            total_respostas=0,
            percentual=0.0,
            por_plataforma=[],
        )

    respostas_com_marca = [
        resposta
        for resposta in respostas
        if any(mencao.marca.lower() == marca.lower() for mencao in resposta.mencoes)
    ]

    quantidade_com_mencao = len(respostas_com_marca)

    percentual = (quantidade_com_mencao / total_respostas) * 100

    plataformas = {}

    for resposta in respostas:
        plataformas.setdefault(
            resposta.plataforma,
            [],
        ).append(resposta)

    por_plataforma = []

    for plataforma, respostas_plataforma in plataformas.items():
        total = len(respostas_plataforma)

        com_mencao = sum(
            1
            for resposta in respostas_plataforma
            if any(mencao.marca.lower() == marca.lower() for mencao in resposta.mencoes)
        )

        percentual_plataforma = (com_mencao / total) * 100

        por_plataforma.append(
            PlatformShare(
                plataforma=plataforma,
                respostas_com_mencao=com_mencao,
                total_respostas=total,
                percentual=percentual_plataforma,
            )
        )

    return ShareOfVoiceResponse(
        marca=marca,
        respostas_com_mencao=quantidade_com_mencao,
        total_respostas=total_respostas,
        percentual=percentual,
        por_plataforma=por_plataforma,
    )


def calcular_score_citacao(resposta: Resposta) -> float:
    """
    Calcula o score de uma resposta com base nas menções.

    O score considera dois fatores:
    - quantidade de marcas distintas mencionadas, multiplicada por 2;
    - quantidade total de ocorrências das marcas.

    Quanto maior o score, maior a relevância da resposta
    para o ranking de citações.
    """
    marcas_distintas = len(resposta.mencoes)

    ocorrencias_totais = sum(mencao.ocorrencias for mencao in resposta.mencoes)

    score = (marcas_distintas * 3) + ocorrencias_totais

    logger.debug(
        "Score calculado para resposta '%s': %.2f",
        resposta.resposta_id,
        score,
    )

    return score


def obter_top_citacoes(
    respostas: list[Resposta],
    n: int,
) -> list[TopCitacaoResponse]:
    """
    Retorna as respostas com maior score de citação.

    Apenas respostas que possuem pelo menos uma menção são
    consideradas no ranking.

    As respostas são ordenadas pelo score em ordem decrescente
    e limitadas à quantidade solicitada pelo parâmetro n.
    """
    logger.info(
        "Iniciando cálculo de top citações: %d respostas recebidas, limite n=%d",
        len(respostas),
        n,
    )

    respostas_com_mencoes = [resposta for resposta in respostas if resposta.mencoes]

    logger.info(
        "%d de %d respostas possuem menções",
        len(respostas_com_mencoes),
        len(respostas),
    )

    respostas_ordenadas = sorted(
        respostas_com_mencoes,
        key=calcular_score_citacao,
        reverse=True,
    )

    resultado = [
        TopCitacaoResponse(
            resposta_id=resposta.resposta_id,
            plataforma=resposta.plataforma,
            modelo=resposta.modelo,
            resposta_texto=resposta.resposta_texto,
            marcas=[mencao.marca for mencao in resposta.mencoes],
            score=calcular_score_citacao(resposta),
        )
        for resposta in respostas_ordenadas[:n]
    ]

    logger.info(
        "Top citações calculado com sucesso: %d resultados retornados",
        len(resultado),
    )

    return resultado
