from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.mencao import Mencao
from app.models.resposta import Resposta


class RespostaRepository:
    """
    Repositório responsável pelo acesso aos dados de respostas.

    Centraliza as operações de criação, consulta e listagem de
    respostas e suas respectivas menções no banco de dados.
    """

    def __init__(self, session: Session):
        """
        Inicializa o repositório com uma sessão do SQLAlchemy.
        """
        self.session = session

    def criar(self, resposta: Resposta) -> Resposta:
        """
        Persiste uma resposta no banco de dados.
        """
        self.session.add(resposta)
        self.session.commit()
        self.session.refresh(resposta)

        return resposta

    def buscar_por_id(self, resposta_id: int) -> Resposta | None:
        """
        Busca uma resposta pelo ID interno do banco.
        """
        return self.session.get(Resposta, resposta_id)

    def buscar_por_resposta_id(self, resposta_id: str) -> Resposta | None:
        statement = select(Resposta).where(Resposta.resposta_id == resposta_id)

        return self.session.scalar(statement)

    def listar(self) -> list[Resposta]:
        """
        Retorna todas as respostas cadastradas no banco de dados.
        """
        statement = select(Resposta)

        return list(self.session.scalars(statement).all())

    def existe_duplicata(self, resposta: Resposta) -> bool:
        """
        Verifica se já existe no banco uma resposta com o mesmo conteúdo.

        O identificador externo da resposta não é considerado na
        deduplicação. Dessa forma, respostas com IDs diferentes,
        mas com os mesmos dados, também são consideradas duplicadas.
        """
        mesmo_conteudo = (
            (Resposta.pergunta == resposta.pergunta)
            & (Resposta.plataforma == resposta.plataforma)
            & (Resposta.modelo == resposta.modelo)
            & (Resposta.resposta_texto == resposta.resposta_texto)
            & (Resposta.data_hora == resposta.data_hora)
            & (Resposta.sentimento == resposta.sentimento)
        )

        statement = select(Resposta).where(mesmo_conteudo)

        return self.session.scalar(statement) is not None

    def listar_por_marca(self, marca: str) -> list[Resposta]:
        """
        Retorna as respostas que possuem menção à marca informada.

        A consulta utiliza o relacionamento entre Resposta e Mencao
        e remove possíveis duplicidades com distinct().
        """
        statement = (
            select(Resposta)
            .join(Resposta.mencoes)
            .where(func.lower(Mencao.marca) == marca.lower())
            .distinct()
        )

        return list(self.session.scalars(statement).all())


if __name__ == "__main__":
    pass
