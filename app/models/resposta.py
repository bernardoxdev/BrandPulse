from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.tables import Base

if TYPE_CHECKING:
    from app.models.mencao import Mencao


class Resposta(Base):
    __tablename__ = "respostas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resposta_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    plataforma: Mapped[str] = mapped_column(String(100), nullable=False)
    modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resposta_texto: Mapped[str] = mapped_column(Text, nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sentimento: Mapped[str | None] = mapped_column(String(50), nullable=True)

    mencoes: Mapped[list["Mencao"]] = relationship(
        back_populates="resposta", cascade="all, delete-orphan"
    )
