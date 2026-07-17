from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from psicossocial.metodologia import load_metodologia
from psicossocial.processing import (
    classify_matrix_risk,
    dimension_exposure_summary,
    process_excel,
    representativeness_to_severity_level,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "metodologia_v1.yaml"


def test_process_excel_calcula_scores_e_separa_campos(tmp_path: Path) -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Forms"

    headers = []
    values = []
    for question_code, question in metodologia.perguntas.items():
        if question["tipo"] == "caracterizacao":
            headers.append(question["texto"])
            values.append(f"valor {question_code}")
        elif question["tipo"] == "dimensao_score":
            for item in question["itens"]:
                headers.append(item["texto"])
                if item["direcao"] == "protetivo_inverter":
                    values.append("Sempre")
                else:
                    values.append("Frequentemente")
        elif question["tipo"] == "vco":
            for item in question["itens"]:
                headers.append(item["texto"])
                values.append("Não")
        elif question["tipo"] == "qualitativa_estruturada":
            headers.append(question["texto"])
            values.append("Pressão por prazos.;Outra;")

    worksheet.append(["ID", *headers])
    worksheet.append([123, *values])
    path = tmp_path / "forms.xlsx"
    workbook.save(path)

    processed = process_excel(path, metodologia)
    respondent = processed.respondents[0]
    summary = processed.summary(metodologia)

    assert len(processed.respondents) == 1
    assert respondent.respondent_id == "123"
    assert respondent.dimensions["DEM"].risk_score == 4
    assert respondent.dimensions["REL"].risk_score == 1
    assert respondent.dimensions["SAG"].risk_score == 1
    assert respondent.vco["Q16_VCO_1"] == "Não"
    assert respondent.causes == ("Pressão por prazos", "Outra")
    assert summary["total_respondentes"] == 1
    assert summary["dimensoes"]["DEM"]["classificacao"] == "Grave"

    exposure = dimension_exposure_summary(processed.respondents, "DEM")
    assert exposure.probability_level == 4
    assert exposure.probability_label == "Intensa / Continua"
    assert exposure.distribution_by_level == {1: 0, 2: 0, 3: 0, 4: 1}
    assert exposure.impacted_count == 1
    assert exposure.impacted_percent == 1
    assert exposure.severity_level == 4
    assert exposure.severity_label == "Critica"
    assert exposure.matrix_risk_level == 16
    assert exposure.matrix_risk_classification == "Critico"


def test_classifica_matriz_4x4() -> None:
    assert classify_matrix_risk(probability_level=1, severity_level=1) == (1, "Baixo")
    assert classify_matrix_risk(probability_level=3, severity_level=1) == (3, "Baixo")
    assert classify_matrix_risk(probability_level=2, severity_level=3) == (6, "Moderado")
    assert classify_matrix_risk(probability_level=3, severity_level=3) == (9, "Alto")
    assert classify_matrix_risk(probability_level=4, severity_level=4) == (16, "Critico")


def test_converte_representatividade_ghe_em_severidade() -> None:
    assert representativeness_to_severity_level(0.25) == 1
    assert representativeness_to_severity_level(0.50) == 2
    assert representativeness_to_severity_level(0.75) == 3
    assert representativeness_to_severity_level(0.7501) == 4
