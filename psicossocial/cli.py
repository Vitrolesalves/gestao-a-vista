from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from psicossocial.excel_export import export_excel
from psicossocial.excel_import import ExcelImportError, diagnose_excel
from psicossocial.metodologia import MetodologiaError, load_metodologia
from psicossocial.processing import process_excel
from psicossocial.score import ScoreError, classify_risk_score


DEFAULT_CONFIG = Path("config/metodologia_v1.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="psicossocial",
        description="CLI local do backend Psicossocial NR-01.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validar-metodologia",
        help="Carrega e valida a metodologia versionada.",
    )
    validate_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Caminho do YAML de metodologia. Padrao: {DEFAULT_CONFIG}",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o resumo em JSON.",
    )
    validate_parser.set_defaults(func=handle_validate_metodologia)

    classify_parser = subparsers.add_parser(
        "classificar-score",
        help="Classifica um risk_score usando as faixas da metodologia.",
    )
    classify_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Caminho do YAML de metodologia. Padrao: {DEFAULT_CONFIG}",
    )
    classify_parser.add_argument(
        "--score",
        type=float,
        required=True,
        help="Risk score numerico entre 1 e 5.",
    )
    classify_parser.set_defaults(func=handle_classificar_score)

    diagnose_parser = subparsers.add_parser(
        "diagnosticar-excel",
        help="Diagnostica uma planilha exportada do Forms.",
    )
    diagnose_parser.add_argument(
        "--input",
        required=True,
        help="Caminho da planilha .xlsx de entrada.",
    )
    diagnose_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Caminho do YAML de metodologia. Padrao: {DEFAULT_CONFIG}",
    )
    diagnose_parser.add_argument(
        "--sheet",
        default=None,
        help="Nome da aba. Se omitido, usa a primeira aba.",
    )
    diagnose_parser.set_defaults(func=handle_diagnosticar_excel)

    process_parser = subparsers.add_parser(
        "processar-excel",
        help="Processa uma planilha Forms e calcula scores por respondente.",
    )
    process_parser.add_argument(
        "--input",
        required=True,
        help="Caminho da planilha .xlsx de entrada.",
    )
    process_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Caminho do YAML de metodologia. Padrao: {DEFAULT_CONFIG}",
    )
    process_parser.add_argument(
        "--sheet",
        default=None,
        help="Nome da aba. Se omitido, usa a primeira aba.",
    )
    process_parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Inclui N primeiros respondentes no JSON de saida.",
    )
    process_parser.set_defaults(func=handle_processar_excel)

    export_parser = subparsers.add_parser(
        "exportar-excel",
        help="Gera uma planilha tecnica de resultados em .xlsx.",
    )
    export_parser.add_argument(
        "--input",
        required=True,
        help="Caminho da planilha .xlsx de entrada.",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Caminho da planilha .xlsx de saida.",
    )
    export_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help=f"Caminho do YAML de metodologia. Padrao: {DEFAULT_CONFIG}",
    )
    export_parser.add_argument(
        "--sheet",
        default=None,
        help="Nome da aba. Se omitido, usa a primeira aba.",
    )
    export_parser.add_argument(
        "--workforce",
        default=None,
        help="Caminho da base SRA/colaboradores para calcular elegibilidade e representatividade.",
    )
    export_parser.set_defaults(func=handle_exportar_excel)

    return parser


def handle_validate_metodologia(args: argparse.Namespace) -> int:
    metodologia = load_metodologia(args.config)
    resumo = metodologia.resumo()

    if args.json:
        print(json.dumps(resumo, ensure_ascii=False, indent=2))
        return 0

    print("Metodologia valida.")
    print(f"Arquivo: {resumo['arquivo']}")
    print(f"Versao: {resumo['versao']}")
    print(f"Perguntas: {resumo['total_perguntas']}")
    print(f"Dimensoes: {', '.join(resumo['dimensoes'])}")
    return 0


def handle_classificar_score(args: argparse.Namespace) -> int:
    metodologia = load_metodologia(args.config)
    classification = classify_risk_score(args.score, metodologia.data["score"])
    print(classification)
    return 0


def handle_diagnosticar_excel(args: argparse.Namespace) -> int:
    metodologia = load_metodologia(args.config)
    diagnostic = diagnose_excel(args.input, metodologia, sheet_name=args.sheet)
    print(json.dumps(diagnostic.to_dict(), ensure_ascii=False, indent=2))
    return 0


def handle_processar_excel(args: argparse.Namespace) -> int:
    metodologia = load_metodologia(args.config)
    processed = process_excel(args.input, metodologia, sheet_name=args.sheet)
    output = processed.summary(metodologia)
    if args.sample:
        output["amostra_respondentes"] = [
            respondent.to_dict()
            for respondent in processed.respondents[: args.sample]
        ]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def handle_exportar_excel(args: argparse.Namespace) -> int:
    metodologia = load_metodologia(args.config)
    output_path = export_excel(
        input_path=args.input,
        output_path=args.output,
        metodologia=metodologia,
        sheet_name=args.sheet,
        workforce_path=args.workforce,
    )
    print(json.dumps({"arquivo_gerado": str(output_path)}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except (ExcelImportError, MetodologiaError, ScoreError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
