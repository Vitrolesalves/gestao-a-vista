from __future__ import annotations

from pathlib import Path

from psicossocial.metodologia import (
    EXPECTED_DIMENSIONS,
    EXPECTED_QUESTIONS,
    load_metodologia,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "metodologia_v1.yaml"


def test_metodologia_carrega_com_perguntas_esperadas() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    assert tuple(metodologia.perguntas.keys()) == EXPECTED_QUESTIONS


def test_metodologia_carrega_com_dimensoes_esperadas() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    assert tuple(metodologia.dimensoes.keys()) == EXPECTED_DIMENSIONS


def test_q14_sag_e_q15_iti_sao_protetivas() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    q14 = metodologia.perguntas["Q14"]
    q15 = metodologia.perguntas["Q15"]

    assert q14["codigo_dimensao"] == "SAG"
    assert q14["regra_padrao"] == "protetivo_inverter"
    assert [item["direcao"] for item in q14["itens"]] == ["protetivo_inverter"] * 4
    assert q15["codigo_dimensao"] == "ITI"
    assert q15["regra_padrao"] == "protetivo_inverter"
    assert [item["direcao"] for item in q15["itens"]] == ["protetivo_inverter"] * 3


def test_vco_nao_compoe_score_medio() -> None:
    metodologia = load_metodologia(CONFIG_PATH)

    assert metodologia.data["vco"]["pergunta"] == "Q16"
    assert metodologia.data["vco"]["compoe_score_medio"] is False
    assert metodologia.perguntas["Q16"]["compoe_media_score"] is False
