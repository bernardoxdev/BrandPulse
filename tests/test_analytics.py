from datetime import datetime
from unittest.mock import Mock

import pytest

from app.models.mencao import Mencao
from app.models.resposta import Resposta
from app.schemas.analytics import ShareOfVoiceResponse
from app.services.analytics import (
    calcular_score_citacao,
    calcular_share_of_voice,
    obter_top_citacoes,
)


def criar_resposta(
    id: str,
    plataforma: str,
    resposta_texto: str = "Resposta de teste.",
) -> Resposta:
    return Resposta(
        resposta_id=id,
        pergunta="Qual a melhor marca?",
        plataforma=plataforma,
        modelo="gpt-5",
        resposta_texto=resposta_texto,
        data_hora=datetime(2026, 9, 22, 10, 0),
        sentimento=None,
    )


def criar_repository(respostas: list[Resposta]):
    repository = Mock()
    repository.listar.return_value = respostas
    return repository


# ---------------------------------------------------------------------------
# Share of Voice
# ---------------------------------------------------------------------------


def test_share_of_voice_sem_respostas():
    repository = criar_repository([])

    resultado = calcular_share_of_voice(repository, "Acme")

    assert isinstance(resultado, ShareOfVoiceResponse)
    assert resultado.marca == "Acme"
    assert resultado.total_respostas == 0
    assert resultado.respostas_com_mencao == 0
    assert resultado.percentual == 0.0
    assert resultado.por_plataforma == []


def test_share_of_voice_sem_mencoes():
    respostas = [
        criar_resposta("1", "ChatGPT"),
        criar_resposta("2", "Gemini"),
        criar_resposta("3", "Perplexity"),
    ]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "Acme")

    assert resultado.total_respostas == 3
    assert resultado.respostas_com_mencao == 0
    assert resultado.percentual == 0.0


def test_share_of_voice_50_por_cento():
    respostas = [
        criar_resposta("1", "ChatGPT", "A Acme é boa."),
        criar_resposta("2", "ChatGPT", "A Zenith é boa."),
        criar_resposta("3", "Gemini", "A Acme é conhecida."),
        criar_resposta("4", "Gemini", "A Nimbus é conhecida."),
    ]

    respostas[0].mencoes = [Mencao(marca="Acme", ocorrencias=1)]
    respostas[2].mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "Acme")

    assert resultado.total_respostas == 4
    assert resultado.respostas_com_mencao == 2
    assert resultado.percentual == 50.0


def test_share_of_voice_100_por_cento():
    respostas = [
        criar_resposta("1", "ChatGPT"),
        criar_resposta("2", "Gemini"),
        criar_resposta("3", "Perplexity"),
    ]

    for resposta in respostas:
        resposta.mencoes = [
            Mencao(
                marca="Acme",
                ocorrencias=1,
            )
        ]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "Acme")

    assert resultado.total_respostas == 3
    assert resultado.respostas_com_mencao == 3
    assert resultado.percentual == 100.0


def test_share_of_voice_por_plataforma():
    respostas = [
        criar_resposta("1", "ChatGPT"),
        criar_resposta("2", "ChatGPT"),
        criar_resposta("3", "ChatGPT"),
        criar_resposta("4", "Gemini"),
        criar_resposta("5", "Gemini"),
    ]

    respostas[0].mencoes = [Mencao(marca="Acme", ocorrencias=1)]
    respostas[1].mencoes = [Mencao(marca="Acme", ocorrencias=1)]
    respostas[3].mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "Acme")

    assert resultado.total_respostas == 5
    assert resultado.respostas_com_mencao == 3
    assert resultado.percentual == 60.0

    plataformas = {
        plataforma.plataforma: plataforma for plataforma in resultado.por_plataforma
    }

    assert plataformas["ChatGPT"].total_respostas == 3
    assert plataformas["ChatGPT"].respostas_com_mencao == 2
    assert plataformas["ChatGPT"].percentual == pytest.approx(66.6666666667)

    assert plataformas["Gemini"].total_respostas == 2
    assert plataformas["Gemini"].respostas_com_mencao == 1
    assert plataformas["Gemini"].percentual == 50.0


def test_multiplas_ocorrencias_da_marca_contam_como_uma_resposta():
    resposta = criar_resposta(
        "1",
        "ChatGPT",
        "A Acme é boa. A Acme também é conhecida.",
    )

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=2,
        )
    ]

    repository = criar_repository([resposta])

    resultado = calcular_share_of_voice(repository, "Acme")

    assert resultado.total_respostas == 1
    assert resultado.respostas_com_mencao == 1
    assert resultado.percentual == 100.0


def test_share_of_voice_marca_case_insensitive():
    respostas = [
        criar_resposta("1", "ChatGPT", "A Acme é uma boa marca."),
        criar_resposta("2", "Gemini", "A ACME possui bons produtos."),
        criar_resposta("3", "Perplexity", "A acme é bastante conhecida."),
        criar_resposta("4", "ChatGPT", "A Zenith é uma alternativa."),
    ]

    respostas[0].mencoes = [Mencao(marca="Acme", ocorrencias=1)]
    respostas[1].mencoes = [Mencao(marca="Acme", ocorrencias=1)]
    respostas[2].mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "acme")

    assert resultado.marca == "acme"
    assert resultado.total_respostas == 4
    assert resultado.respostas_com_mencao == 3
    assert resultado.percentual == 75.0


def test_share_of_voice_marca_case_insensitive_maiusculo():
    respostas = [
        criar_resposta("1", "ChatGPT", "A Acme é uma boa marca."),
        criar_resposta("2", "Gemini", "A acme possui bons produtos."),
    ]

    for resposta in respostas:
        resposta.mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "ACME")

    assert resultado.marca == "ACME"
    assert resultado.total_respostas == 2
    assert resultado.respostas_com_mencao == 2
    assert resultado.percentual == 100.0


def test_share_of_voice_marca_case_insensitive_misto():
    respostas = [
        criar_resposta("1", "ChatGPT", "A ACME é uma boa marca."),
        criar_resposta("2", "Gemini", "A acme possui bons produtos."),
        criar_resposta("3", "Perplexity", "A AcMe atua nesse mercado."),
    ]

    for resposta in respostas:
        resposta.mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    repository = criar_repository(respostas)

    resultado = calcular_share_of_voice(repository, "AcMe")

    assert resultado.marca == "AcMe"
    assert resultado.total_respostas == 3
    assert resultado.respostas_com_mencao == 3
    assert resultado.percentual == 100.0


# ---------------------------------------------------------------------------
# Score de citação
# ---------------------------------------------------------------------------


def test_score_citacao_com_uma_marca():
    resposta = criar_resposta("1", "ChatGPT")

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resultado = calcular_score_citacao(resposta)

    assert resultado == 4


def test_score_citacao_com_multiplas_marcas():
    resposta = criar_resposta("1", "ChatGPT")

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=2,
        ),
        Mencao(
            marca="Zenith",
            ocorrencias=1,
        ),
    ]

    resultado = calcular_score_citacao(resposta)

    assert resultado == 9


def test_score_citacao_com_multiplas_ocorrencias():
    resposta = criar_resposta("1", "ChatGPT")

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=5,
        )
    ]

    resultado = calcular_score_citacao(resposta)

    assert resultado == 8


def test_score_citacao_sem_mencoes():
    resposta = criar_resposta("1", "ChatGPT")
    resposta.mencoes = []

    resultado = calcular_score_citacao(resposta)

    assert resultado == 0


def test_score_prioriza_diversidade_com_peso_tres():
    resposta = criar_resposta("1", "ChatGPT")

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=2,
        ),
        Mencao(
            marca="Zenith",
            ocorrencias=1,
        ),
    ]

    assert calcular_score_citacao(resposta) == 9


# ---------------------------------------------------------------------------
# Top Citações
# ---------------------------------------------------------------------------


def test_obter_top_citacoes_ordena_por_score():
    resposta_1 = criar_resposta("1", "ChatGPT")
    resposta_1.mencoes = [Mencao(marca="Acme", ocorrencias=1)]

    resposta_2 = criar_resposta("2", "Gemini")
    resposta_2.mencoes = [
        Mencao(marca="Acme", ocorrencias=2),
        Mencao(marca="Zenith", ocorrencias=1),
    ]

    resultado = obter_top_citacoes(
        [resposta_1, resposta_2],
        5,
    )

    assert len(resultado) == 2
    assert resultado[0].resposta_id == "2"
    assert resultado[0].score == 9
    assert resultado[1].resposta_id == "1"
    assert resultado[1].score == 4


def test_obter_top_citacoes_respeita_limite_n():
    respostas = []

    for i in range(5):
        resposta = criar_resposta(
            str(i),
            "ChatGPT",
        )

        resposta.mencoes = [
            Mencao(
                marca="Acme",
                ocorrencias=i + 1,
            )
        ]

        respostas.append(resposta)

    resultado = obter_top_citacoes(
        respostas,
        2,
    )

    assert len(resultado) == 2
    assert resultado[0].resposta_id == "4"
    assert resultado[1].resposta_id == "3"


def test_obter_top_citacoes_ignora_respostas_sem_mencoes():
    resposta_com_mencao = criar_resposta("1", "ChatGPT")
    resposta_com_mencao.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resposta_sem_mencao = criar_resposta("2", "Gemini")
    resposta_sem_mencao.mencoes = []

    resultado = obter_top_citacoes(
        [
            resposta_com_mencao,
            resposta_sem_mencao,
        ],
        5,
    )

    assert len(resultado) == 1
    assert resultado[0].resposta_id == "1"


def test_obter_top_citacoes_retorna_marcas():
    resposta = criar_resposta(
        "resposta-001",
        "ChatGPT",
        "A Acme é uma excelente opção.",
    )

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resultado = obter_top_citacoes(
        [resposta],
        5,
    )

    assert len(resultado) == 1
    assert resultado[0].marcas == ["Acme"]


def test_obter_top_citacoes_retorna_dados_da_resposta():
    resposta = criar_resposta(
        "resposta-001",
        "ChatGPT",
        "A Acme é uma excelente opção.",
    )

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resultado = obter_top_citacoes(
        [resposta],
        5,
    )

    assert len(resultado) == 1
    assert resultado[0].resposta_id == "resposta-001"
    assert resultado[0].plataforma == "ChatGPT"
    assert resultado[0].modelo == "gpt-5"
    assert resultado[0].resposta_texto == "A Acme é uma excelente opção."
    assert resultado[0].marcas == ["Acme"]
    assert resultado[0].score == 4


def test_obter_top_citacoes_lista_vazia():
    resultado = obter_top_citacoes([], 5)

    assert resultado == []


def test_obter_top_citacoes_n_maior_que_quantidade_de_respostas():
    resposta = criar_resposta("1", "ChatGPT")

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resultado = obter_top_citacoes(
        [resposta],
        10,
    )

    assert len(resultado) == 1
    assert resultado[0].resposta_id == "1"


def test_obter_top_citacoes_n_igual_a_um():
    resposta_1 = criar_resposta("1", "ChatGPT")
    resposta_1.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resposta_2 = criar_resposta("2", "Gemini")
    resposta_2.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=5,
        )
    ]

    resultado = obter_top_citacoes(
        [resposta_1, resposta_2],
        1,
    )

    assert len(resultado) == 1
    assert resultado[0].resposta_id == "2"
    assert resultado[0].score == 8


def test_obter_top_citacoes_preserva_modelo_none():
    resposta = criar_resposta(
        "1",
        "ChatGPT",
    )

    resposta.modelo = None

    resposta.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resultado = obter_top_citacoes(
        [resposta],
        1,
    )

    assert resultado[0].resposta_id == "1"
    assert resultado[0].modelo is None


# ---------------------------------------------------------------------------
# Testes de regressão
# ---------------------------------------------------------------------------


def test_share_of_voice_por_plataforma_conta_respostas_com_mesmo_id():
    """
    Garante que respostas diferentes com o mesmo resposta_id
    sejam contabilizadas individualmente.
    """
    resposta_1 = criar_resposta(
        "123",
        "ChatGPT",
        "A Acme é uma opção.",
    )

    resposta_2 = criar_resposta(
        "123",
        "ChatGPT",
        "A Acme também é uma opção.",
    )

    resposta_2.data_hora = datetime(2026, 9, 23, 10, 0)

    for resposta in [resposta_1, resposta_2]:
        resposta.mencoes = [
            Mencao(
                marca="Acme",
                ocorrencias=1,
            )
        ]

    repository = criar_repository(
        [
            resposta_1,
            resposta_2,
        ]
    )

    resultado = calcular_share_of_voice(
        repository,
        "Acme",
    )

    plataforma = resultado.por_plataforma[0]

    assert plataforma.plataforma == "ChatGPT"
    assert plataforma.total_respostas == 2
    assert plataforma.respostas_com_mencao == 2
    assert plataforma.percentual == 100.0


def test_share_of_voice_usa_mesmo_snapshot_dos_dados():
    """
    Regressão para garantir que total e respostas com menção
    sejam calculados sobre o mesmo conjunto de dados.

    O serviço deve consultar o repository.listar() apenas uma vez.
    """
    resposta_1 = criar_resposta(
        "1",
        "ChatGPT",
        "A Acme é uma boa opção.",
    )

    resposta_2 = criar_resposta(
        "2",
        "ChatGPT",
        "A Zenith é uma boa opção.",
    )

    resposta_1.mencoes = [
        Mencao(
            marca="Acme",
            ocorrencias=1,
        )
    ]

    resposta_2.mencoes = []

    repository = criar_repository(
        [
            resposta_1,
            resposta_2,
        ]
    )

    resultado = calcular_share_of_voice(
        repository,
        "Acme",
    )

    assert resultado.total_respostas == 2
    assert resultado.respostas_com_mencao == 1
    assert resultado.percentual == 50.0

    plataforma = resultado.por_plataforma[0]

    assert plataforma.total_respostas == 2
    assert plataforma.respostas_com_mencao == 1
    assert plataforma.percentual == 50.0

    repository.listar.assert_called_once()
    repository.listar_por_marca.assert_not_called()
