# ---------------------------------------------------------------------------
# POST /respostas
# ---------------------------------------------------------------------------


def test_criar_respostas_com_sucesso(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é uma excelente marca.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        }
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    resultado = response.json()

    assert len(resultado) == 1

    resposta = resultado[0]

    assert resposta["id"] == 1
    assert resposta["resposta_id"] == "r001"
    assert resposta["pergunta"] == "Qual a melhor marca?"
    assert resposta["plataforma"] == "ChatGPT"
    assert resposta["modelo"] == "gpt-5"
    assert resposta["resposta_texto"] == "A Acme é uma excelente marca."
    assert resposta["sentimento"] == "positivo"

    assert len(resposta["mencoes"]) == 1
    assert resposta["mencoes"][0]["marca"] == "Acme"
    assert resposta["mencoes"][0]["ocorrencias"] == 1


def test_criar_uma_resposta_com_objeto_json(client):
    dado = {
        "id": "r-individual",
        "pergunta": "Qual marca aparece?",
        "plataforma": "chat-gpt",
        "modelo": "gpt-5",
        "resposta_texto": "A A.C.M.E. aparece nesta resposta.",
        "data_hora": "2026-09-22T10:00:00",
        "sentimento": None,
    }

    response = client.post("/respostas", json=dado)

    assert response.status_code == 201
    assert response.json()["resposta_id"] == "r-individual"
    assert response.json()["plataforma"] == "ChatGPT"
    assert response.json()["mencoes"][0]["marca"] == "Acme"


def test_criar_respostas_com_dados_invalidos(client):
    dados = [
        {
            "id": "",
            "pergunta": "Pergunta inválida",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "Texto",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": None,
        }
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 422

    resultado = response.json()

    assert "message" in resultado["detail"]
    assert "respostas_invalidas" in resultado["detail"]

    assert len(resultado["detail"]["respostas_invalidas"]) == 1


def test_criar_respostas_com_data_invalida(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é uma excelente marca.",
            "data_hora": "data-invalida",
            "sentimento": "positivo",
        }
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 422


def test_criar_respostas_ignora_duplicada(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é uma excelente marca.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        }
    ]

    primeira = client.post("/respostas", json=dados)

    assert primeira.status_code == 201

    segunda = client.post("/respostas", json=dados)

    assert segunda.status_code == 422

    resultado = segunda.json()

    assert (
        resultado["detail"]["message"]
        == "Todos os dados enviados já estão no banco de dados "
        "ou você enviou apenas dados inválidos."
    )


def test_criar_respostas_detecta_mencoes(client):
    dados = [
        {
            "id": "r002",
            "pergunta": "Compare as marcas.",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": (
                "A Acme é boa. "
                "A Acme possui bons produtos. "
                "A Zenith também é uma alternativa."
            ),
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        }
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    resultado = response.json()

    assert len(resultado) == 1

    resposta = resultado[0]

    assert len(resposta["mencoes"]) == 2

    mencoes = {mencao["marca"]: mencao["ocorrencias"] for mencao in resposta["mencoes"]}

    assert mencoes["Acme"] == 2
    assert mencoes["Zenith"] == 1


def test_criar_respostas_processa_validas_e_ignora_invalidas(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é excelente.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        },
        {
            "id": "",
            "pergunta": "Pergunta inválida",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "Texto inválido.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": None,
        },
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    resultado = response.json()

    assert len(resultado) == 1

    assert resultado[0]["resposta_id"] == "r001"


# ---------------------------------------------------------------------------
# GET /share-of-voice
# ---------------------------------------------------------------------------


def test_share_of_voice(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é excelente.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        },
        {
            "id": "r002",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "Gemini",
            "modelo": "gemini-2",
            "resposta_texto": "A Zenith é excelente.",
            "data_hora": "2026-09-22T11:00:00",
            "sentimento": "positivo",
        },
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    response = client.get("/share-of-voice?marca=Acme")

    assert response.status_code == 200

    resultado = response.json()

    assert resultado["marca"] == "Acme"
    assert resultado["total_respostas"] == 2
    assert resultado["respostas_com_mencao"] == 1
    assert resultado["percentual"] == 50.0


def test_share_of_voice_marca_case_insensitive(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é excelente.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        }
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    response = client.get("/share-of-voice?marca=acme")

    assert response.status_code == 200

    resultado = response.json()

    assert resultado["marca"] == "acme"
    assert resultado["total_respostas"] == 1
    assert resultado["respostas_com_mencao"] == 1
    assert resultado["percentual"] == 100.0


def test_share_of_voice_sem_marca(client):
    response = client.get("/share-of-voice")

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /top-citacoes
# ---------------------------------------------------------------------------


def test_top_citacoes(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Compare marcas.",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "Acme e Zenith são boas.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        },
        {
            "id": "r002",
            "pergunta": "Compare marcas.",
            "plataforma": "Gemini",
            "modelo": "gemini-2",
            "resposta_texto": "Acme, Zenith e Nimbus são boas.",
            "data_hora": "2026-09-22T11:00:00",
            "sentimento": "positivo",
        },
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    response = client.get("/top-citacoes")

    assert response.status_code == 200

    resultado = response.json()

    assert len(resultado) == 2

    assert resultado[0]["resposta_id"] == "r002"
    assert resultado[1]["resposta_id"] == "r001"


def test_top_citacoes_respeita_n(client):
    dados = [
        {
            "id": f"r00{i}",
            "pergunta": "Compare marcas.",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "Acme é uma boa marca.",
            "data_hora": f"2026-09-22T1{i}:00:00",
            "sentimento": "positivo",
        }
        for i in range(1, 5)
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    response = client.get("/top-citacoes?n=2")

    assert response.status_code == 200

    resultado = response.json()

    assert len(resultado) == 2


def test_top_citacoes_n_deve_ser_maior_que_zero(client):
    response = client.get("/top-citacoes?n=0")

    assert response.status_code == 422


def test_top_citacoes_ignora_respostas_sem_mencoes(client):
    dados = [
        {
            "id": "r001",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "ChatGPT",
            "modelo": "gpt-5",
            "resposta_texto": "A Acme é excelente.",
            "data_hora": "2026-09-22T10:00:00",
            "sentimento": "positivo",
        },
        {
            "id": "r002",
            "pergunta": "Qual a melhor marca?",
            "plataforma": "Gemini",
            "modelo": "gemini-2",
            "resposta_texto": "Não há marcas mencionadas aqui.",
            "data_hora": "2026-09-22T11:00:00",
            "sentimento": "neutro",
        },
    ]

    response = client.post("/respostas", json=dados)

    assert response.status_code == 201

    response = client.get("/top-citacoes")

    assert response.status_code == 200

    resultado = response.json()

    assert len(resultado) == 1
    assert resultado[0]["resposta_id"] == "r001"
