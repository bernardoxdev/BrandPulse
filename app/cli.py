import argparse
import logging
from pathlib import Path

import uvicorn

from app.services.ingestao import processar_respostas

logger = logging.getLogger(__name__)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI do BrandPulse.")

    subparsers = parser.add_subparsers(
        dest="comando",
        required=True,
    )

    # Comando: ingest
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Importa respostas de um arquivo JSON.",
    )

    ingest_parser.add_argument(
        "arquivo",
        type=Path,
        help="Caminho para o arquivo JSON.",
    )

    # Comando: run
    run_parser = subparsers.add_parser(
        "run",
        help="Inicia a API do BrandPulse.",
    )

    run_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host onde a API será executada.",
    )

    run_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta onde a API será executada.",
    )

    run_parser.add_argument(
        "--reload",
        action="store_true",
        help="Ativa o hot reload durante o desenvolvimento.",
    )

    return parser


def executar_ingestao(arquivo: Path) -> None:
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    if not arquivo.is_file():
        raise ValueError(f"O caminho informado não é um arquivo: {arquivo}")

    resultado = processar_respostas(arquivo)

    print(f"Respostas recebidas: {resultado['total']}")
    print(f"Respostas criadas: {resultado['criadas']}")
    print(f"Respostas inválidas: {resultado['invalidas']}")
    print(f"Respostas duplicadas: {resultado['duplicadas']}")


def executar_api(
    host: str,
    port: int,
    reload: bool,
) -> None:
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()

    if args.comando == "ingest":
        executar_ingestao(args.arquivo)

    elif args.comando == "run":
        executar_api(
            host=args.host,
            port=args.port,
            reload=args.reload,
        )


if __name__ == "__main__":
    main()
