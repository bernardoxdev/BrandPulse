from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.tables import Base

if TYPE_CHECKING:
    from app.models.resposta import Resposta


class Mencao(Base):
    __tablename__ = "mencoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resposta_id: Mapped[str] = mapped_column(ForeignKey("respostas.id"), nullable=False)
    marca: Mapped[str] = mapped_column(String(100), nullable=False)
    ocorrencias: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    resposta: Mapped["Resposta"] = relationship(back_populates="mencoes")
