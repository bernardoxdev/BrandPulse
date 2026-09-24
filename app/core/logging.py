import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


def sanitizar_log(valor: object, limite: int = 500) -> str:
    """
    Sanitiza valores antes de serem registrados nos logs.
    """
    texto = str(valor)[:limite]

    return (
        texto.replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\x1b", "\\x1b")
    )


class SanitizarLogFilter(logging.Filter):
    """
    Sanitiza a mensagem antes que ela seja enviada aos handlers.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = sanitizar_log(record.getMessage())
        record.args = ()

        return True


def configurar_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    sanitizar_filter = SanitizarLogFilter()

    arquivo_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )
    arquivo_handler.setLevel(logging.INFO)
    arquivo_handler.setFormatter(formatter)
    arquivo_handler.addFilter(sanitizar_filter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sanitizar_filter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            console_handler,
            arquivo_handler,
        ],
    )
