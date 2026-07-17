from __future__ import annotations

from pathlib import Path

from psicossocial.metodologia import load_metodologia
from psicossocial.score import (
    build_response_scale,
    classify_risk_score,
    raw_score_from_response,
    risk_score_from_raw,
    score_dimension,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "metodologia_v1.yaml"


def test_converte_likert_com_variacao_de_acento() -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    scale = build_response_scale(metodologia.data["escala_likert"])

    assert raw_score_from_response("As vezes", scale) == 3
    assert raw_score_from_response("Às vezes", scale) == 3
    assert raw_score_from_response(" frequentemente ", scale) == 4


def test_inverte_item_protetivo() -> None:
    assert risk_score_from_raw(5, "protetivo_inverter") == 1
    assert risk_score_from_raw(1, "protetivo_inverter") == 5
    assert risk_score_from_raw(4, "risco_direto") == 4


def test_classifica_risk_score() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    assert classify_risk_score(1.5, metodologia.data["score"]) == "Favoravel"
    assert classify_risk_score(2.5, metodologia.data["score"]) == "Atencao"
    assert classify_risk_score(2.9905, metodologia.data["score"]) == "Atencao"
    assert classify_risk_score(3.5, metodologia.data["score"]) == "Critico"
    assert classify_risk_score(4.5, metodologia.data["score"]) == "Grave"


def test_calcula_dimensao_dem_risco_direto() -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    q9 = metodologia.perguntas["Q9"]
    responses = {item["codigo"]: "Frequentemente" for item in q9["itens"]}

    score = score_dimension(
        q9,
        responses,
        metodologia.data["escala_likert"],
        metodologia.data["score"],
    )

    assert score.dimension_code == "DEM"
    assert score.raw_score == 4
    assert score.risk_score == 4
    assert score.classification == "Grave"


def test_calcula_dimensao_rel_protetiva_invertida() -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    q12 = metodologia.perguntas["Q12"]
    responses = {item["codigo"]: "Sempre" for item in q12["itens"]}

    score = score_dimension(
        q12,
        responses,
        metodologia.data["escala_likert"],
        metodologia.data["score"],
    )

    assert score.dimension_code == "REL"
    assert score.raw_score == 5
    assert score.risk_score == 1
    assert score.classification == "Favoravel"


def test_calcula_q14_sag_protetiva() -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    q14 = metodologia.perguntas["Q14"]
    responses = {item["codigo"]: "Sempre" for item in q14["itens"]}

    score = score_dimension(
        q14,
        responses,
        metodologia.data["escala_likert"],
        metodologia.data["score"],
    )

    assert score.dimension_code == "SAG"
    assert score.raw_score == 5
    assert score.risk_score == 1
    assert score.classification == "Favoravel"


def test_calcula_q15_iti_protetiva() -> None:
    metodologia = load_metodologia(CONFIG_PATH)
    q15 = metodologia.perguntas["Q15"]
    responses = {item["codigo"]: "Sempre" for item in q15["itens"]}

    score = score_dimension(
        q15,
        responses,
        metodologia.data["escala_likert"],
        metodologia.data["score"],
    )

    assert score.dimension_code == "ITI"
    assert score.raw_score == 5
    assert score.risk_score == 1
    assert score.classification == "Favoravel"
