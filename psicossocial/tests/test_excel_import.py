from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from psicossocial.excel_import import build_expected_columns, diagnose_excel
from psicossocial.metodologia import load_metodologia


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "metodologia_v1.yaml"


def test_build_expected_columns_tem_44_campos_do_formulario() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    expected = build_expected_columns(metodologia)

    assert len(expected) == 44
    assert expected[0].code == "Q1"
    assert expected[-1].code == "Q18"


def test_diagnostico_excel_mapeia_headers_e_detecta_respostas_likert(tmp_path: Path) -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Forms"
    worksheet.append(
        [
            "ID",
            "Preciso trabalhar sob pressão para realizar minhas atividades.",
            "Recebo apoio da minha liderança direta.",
            "O que mais gera desgaste no seu trabalho?",
        ]
    )
    worksheet.append([1, "À vezes", "Sempre", "Pressão por prazos.;"])
    path = tmp_path / "forms.xlsx"
    workbook.save(path)

    diagnostic = diagnose_excel(path, metodologia)

    assert diagnostic.total_data_rows == 1
    assert [match.code for match in diagnostic.matched_columns] == [
        "Q9_DEM_1",
        "Q12_REL_1",
        "Q17",
    ]
    assert diagnostic.metadata_columns == ("ID",)
    assert diagnostic.unknown_likert_values == {}


def test_diagnostico_excel_mapeia_formulario_nacional_revisado(tmp_path: Path) -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(
        [
            "ID",
            "Qual negócio e atividade você se enquadra?",
            "Em qual unidade ou contrato você trabalha?",
            "Tenho autonomia (liberdade) para realizar minhas atividades diárias. (Cumprimento de procedimentos operacionais)",
            "A empresa me proporciona oportunidade de crescimento profissional (Ex. cursos/treinamentos  de capacitação)",
            "Meu trabalho  corresponde às minhas expectativas.",
            "Ciente que, os resultados serão analisados de forma consolidada e anonimizada respeitando a LGPD, com classificação de risco para priorização de ações.",
        ]
    )
    worksheet.append([1, "INDIRETO", "Goiânia - GO", "Sempre", "Frequentemente", "Às vezes", "Ciente"])
    path = tmp_path / "forms_nacional.xlsx"
    workbook.save(path)

    diagnostic = diagnose_excel(path, metodologia)

    assert diagnostic.total_rows == 2
    assert diagnostic.total_data_rows == 1
    assert [match.code for match in diagnostic.matched_columns] == [
        "Q1",
        "Q2",
        "Q13_ORG_2",
        "Q13_ORG_3",
        "Q15_ITI_1",
    ]
    assert diagnostic.metadata_columns == ("ID",)
    assert diagnostic.unmapped_columns == (
        "Ciente que, os resultados serão analisados de forma consolidada e anonimizada respeitando a LGPD, com classificação de risco para priorização de ações.",
    )
    assert diagnostic.unknown_likert_values == {}
