import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.database.connection import SessionLocal
from app.database.init_db import create_tables
from app.models.mencao import Mencao
from app.models.resposta import Resposta
from app.repositories.respostas import RespostaRepository
from app.schemas.respostas import RespostaCreate
from app.services.mencoes import detectar_mencoes
from app.services.plataformas import normalizar_plataforma

logger = logging.getLogger(__name__)


def _carregar_dados(caminho: str | Path) -> list[dict]:
    """
    Carrega os dados brutos de um arquivo JSON.

    Os registros permanecem sem validação para que a ingestão
    consiga contabilizar os dados inválidos individualmente.
    """
    caminho = Path(caminho)

    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, list):
        raise ValueError("O arquivo JSON deve conter uma lista de respostas.")

    return dados


def carregar_respostas(caminho: str | Path) -> list[RespostaCreate]:
    """
    Carrega e valida respostas armazenadas em um arquivo JSON.

    Registros inválidos são ignorados.
    """
    dados = _carregar_dados(caminho)

    respostas = []

    for registro in dados:
        try:
            resposta = RespostaCreate.model_validate(registro)
        except ValidationError:
            continue

        respostas.append(resposta)

    return respostas


def processar_respostas(caminho: str | Path) -> dict:
    """
    Importa respostas de um arquivo JSON para o banco de dados.

    O banco e suas tabelas são criados automaticamente caso ainda
    não existam.

    Registros inválidos e duplicados são ignorados e contabilizados
    separadamente.

    Retorna:
        total: quantidade total de registros recebidos;
        criadas: quantidade de respostas inseridas;
        invalidas: quantidade de registros inválidos;
        duplicadas: quantidade de respostas duplicadas.
    """
    dados = _carregar_dados(caminho)

    total = len(dados)
    criadas = 0
    invalidas = 0
    duplicadas = 0

    # O CLI não passa pelo lifespan do FastAPI.
    # Por isso, a ingestão precisa garantir que o banco exista.
    create_tables()

    with SessionLocal() as session:
        repository = RespostaRepository(session)

        for dado in dados:
            try:
                resposta_validada = RespostaCreate.model_validate(dado)

            except ValidationError as erro:
                invalidas += 1

                logger.warning(
                    "Registro inválido ignorado durante a ingestão: %s",
                    erro,
                )

                continue

            mencoes_detectadas = detectar_mencoes(resposta_validada.resposta_texto)

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

            repository.criar(resposta)
            criadas += 1

            logger.info(
                "Resposta criada com sucesso. resposta_id=%s",
                resposta_validada.id,
            )

    logger.info(
        "Ingestão finalizada. Total=%d, criadas=%d, inválidas=%d, duplicadas=%d.",
        total,
        criadas,
        invalidas,
        duplicadas,
    )

    return {
        "total": total,
        "criadas": criadas,
        "invalidas": invalidas,
        "duplicadas": duplicadas,
    }
