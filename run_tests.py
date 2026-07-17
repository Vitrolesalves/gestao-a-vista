#!/usr/bin/env python
"""
Script para executar testes do projeto Gestão à Vista
"""

import os
import subprocess
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar variável de ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test")


def run_tests(test_type="all", coverage=True, verbose=True):
    """
    Executa testes com diferentes configurações

    Args:
        test_type (str): Tipo de teste ('all', 'unit', 'integration', 'selenium')
        coverage (bool): Se deve gerar relatório de cobertura
        verbose (bool): Se deve executar em modo verboso
    """

    # Usar o Python do ambiente virtual se disponível
    python_exe = sys.executable
    cmd = [python_exe, "-m", "pytest"]

    # Configurações básicas
    if verbose:
        cmd.append("-v")

    cmd.extend(["--tb=short", "--disable-warnings"])

    # Cobertura
    if coverage:
        cmd.extend(
            [
                "--cov=Gestao_a_Vista",
                "--cov-report=html:htmlcov",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ]
        )

    # Tipo de teste
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "selenium":
        cmd.extend(["-m", "selenium"])
    elif test_type == "models":
        cmd.extend(["-m", "models"])
    elif test_type == "views":
        cmd.extend(["-m", "views"])
    elif test_type == "forms":
        cmd.extend(["-m", "forms"])

    # Executar comando
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Executar testes do projeto")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "selenium", "models", "views", "forms"],
        default="all",
        help="Tipo de teste a executar",
    )
    parser.add_argument(
        "--no-coverage", action="store_true", help="Não gerar relatório de cobertura"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Executar em modo silencioso"
    )

    args = parser.parse_args()

    exit_code = run_tests(
        test_type=args.type, coverage=not args.no_coverage, verbose=not args.quiet
    )

    sys.exit(exit_code)
