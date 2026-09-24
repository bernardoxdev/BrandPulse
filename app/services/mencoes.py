import logging
import re

logger = logging.getLogger(__name__)

MARCAS_MONITORADAS = ["Acme", "Zenith", "Nimbus"]


def criar_padrao_marca(marca: str) -> str:
    letras = list(marca)

    return r"[\W_]*".join(re.escape(letra) for letra in letras if letra.isalnum())


PADROES_MARCAS = {
    marca: re.compile(
        rf"(?<!\w){criar_padrao_marca(marca)}(?!\w)",
        re.IGNORECASE,
    )
    for marca in MARCAS_MONITORADAS
}


def detectar_mencoes(texto: str) -> dict[str, int]:
    logger.debug(
        "Iniciando detecção de menções em texto com %d caracteres",
        len(texto),
    )

    mencoes = {}

    for marca, padrao in PADROES_MARCAS.items():
        ocorrencias = len(padrao.findall(texto))

        if ocorrencias > 0:
            mencoes[marca] = ocorrencias

            logger.info(
                "Marca '%s' detectada: %d ocorrência(s)",
                marca,
                ocorrencias,
            )

    logger.debug(
        "Detecção de menções finalizada: %d marca(s) encontrada(s)",
        len(mencoes),
    )

    return mencoes
