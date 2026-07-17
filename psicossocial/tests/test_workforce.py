from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from psicossocial.workforce import build_representativity_summary


def test_representatividade_cruza_respondentes_com_sra_por_local_e_ghe(tmp_path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "SRA 11-06-26"
    worksheet.append([
        "Nome",
        "Dt Demissao",
        "Municipio",
        "Estado",
        "Negocio",
    ])
    worksheet.append(["Pessoa 1", None, "GOIANIA", "GO", "INDIRETO - ADMINISTRATIVO"])
    worksheet.append(["Pessoa 2", None, "GOIANIA", "GO", "INDIRETO - ADMINISTRATIVO"])
    worksheet.append(["Pessoa 3", None, "ANAPOLIS", "GO", "SEG. ELETRONICA - MANUTENCAO"])
    worksheet.append(["Pessoa desligada", "01/06/2026", "GOIANIA", "GO", "INDIRETO - ADMINISTRATIVO"])
    workforce_path = tmp_path / "sra.xlsx"
    workbook.save(workforce_path)

    respondents = [
        {"Q1": "INDIRETO (ADMINISTRATIVO / CORPORATIVO)", "Q2": "Goiânia - GO"},
        {"Q1": "INDIRETO (ADMINISTRATIVO / CORPORATIVO)", "Q2": "Goiânia - GO"},
        {"Q1": "SEGURANÇA ELETRÔNICA", "Q2": "Anápolis - GO"},
    ]

    summary = build_representativity_summary(workforce_path, respondents)

    local_ghe = [row for row in summary if row["recorte"] == "Local_GHE"]
    assert local_ghe == [
        {
            "recorte": "Local_GHE",
            "local": "Anapolis - GO",
            "ghe": "SEGURANCA ELETRONICA",
            "colaboradores_total": 1,
            "respondentes_validos": 1,
            "adesao_percentual": 1.0,
            "representativo_60": "Sim",
            "analise_segmentada_permitida": "Nao - agrupar para preservar anonimato",
        },
        {
            "recorte": "Local_GHE",
            "local": "Goiania - GO",
            "ghe": "INDIRETO (ADMINISTRATIVO / CORPORATIVO)",
            "colaboradores_total": 2,
            "respondentes_validos": 2,
            "adesao_percentual": 1.0,
            "representativo_60": "Sim",
            "analise_segmentada_permitida": "Nao - agrupar para preservar anonimato",
        },
    ]

    goiania = next(row for row in summary if row["recorte"] == "Local" and row["local"] == "Goiania - GO")
    assert goiania["colaboradores_total"] == 2
    assert goiania["respondentes_validos"] == 2

    indireto = next(row for row in summary if row["recorte"] == "GHE" and row["ghe"] == "INDIRETO (ADMINISTRATIVO / CORPORATIVO)")
    assert indireto["colaboradores_total"] == 2
    assert indireto["respondentes_validos"] == 2
