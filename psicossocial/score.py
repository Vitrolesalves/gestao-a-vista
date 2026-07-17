from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unicodedata import combining, normalize


DIRECT_RISK = "risco_direto"
PROTECTIVE_INVERT = "protetivo_inverter"
VALID_DIRECTIONS = {DIRECT_RISK, PROTECTIVE_INVERT}


class ScoreError(ValueError):
    """Erro de conversao, calculo ou classificacao de score."""


@dataclass(frozen=True)
class ItemScore:
    item_code: str
    raw_response: str
    raw_score: float
    risk_score: float
    direction: str


@dataclass(frozen=True)
class DimensionScore:
    dimension_code: str
    raw_score: float
    risk_score: float
    classification: str
    items: tuple[ItemScore, ...]


def normalize_label(value: str) -> str:
    """Normaliza texto para comparar respostas do Forms com seguranca."""

    without_accents = "".join(
        char for char in normalize("NFKD", value) if not combining(char)
    )
    return " ".join(without_accents.strip().casefold().split())


def build_response_scale(scale_config: dict[str, Any]) -> dict[str, float]:
    responses = scale_config.get("respostas")
    if not isinstance(responses, dict) or not responses:
        raise ScoreError("Escala de respostas invalida.")

    response_scale = {
        normalize_label(str(label)): float(value) for label, value in responses.items()
    }

    # A base real exportada pelo Forms apareceu com grafia equivalente a
    # "A vezes"; mantemos esse alias como resposta valida.
    if "as vezes" in response_scale:
        response_scale["a vezes"] = response_scale["as vezes"]

    return response_scale


def raw_score_from_response(response: str, response_scale: dict[str, float]) -> float:
    key = normalize_label(response)
    if key not in response_scale:
        valid = ", ".join(sorted(response_scale))
        raise ScoreError(f"Resposta Likert desconhecida: {response!r}. Esperadas: {valid}")
    return response_scale[key]


def risk_score_from_raw(raw_score: float, direction: str) -> float:
    if direction == DIRECT_RISK:
        return raw_score
    if direction == PROTECTIVE_INVERT:
        return 6 - raw_score
    raise ScoreError(f"Direcao de score invalida: {direction}")


def classify_risk_score(risk_score: float, score_config: dict[str, Any]) -> str:
    faixas = score_config.get("regra_classificacao", {}).get("faixas")
    if not isinstance(faixas, list) or not faixas:
        raise ScoreError("Faixas de classificacao ausentes.")

    score_for_classification = round(float(risk_score), 2)
    for faixa in faixas:
        minimum = float(faixa["minimo"])
        maximum = float(faixa["maximo"])
        if minimum <= score_for_classification <= maximum:
            return str(faixa["classe"])

    raise ScoreError(f"Score fora das faixas de classificacao: {risk_score}")


def score_item(
    item_config: dict[str, Any],
    response: str,
    response_scale: dict[str, float],
) -> ItemScore:
    item_code = str(item_config["codigo"])
    direction = str(item_config["direcao"])
    if direction not in VALID_DIRECTIONS:
        raise ScoreError(f"Direcao invalida em {item_code}: {direction}")

    raw_score = raw_score_from_response(response, response_scale)
    risk_score = risk_score_from_raw(raw_score, direction)

    return ItemScore(
        item_code=item_code,
        raw_response=response,
        raw_score=raw_score,
        risk_score=risk_score,
        direction=direction,
    )


def score_dimension(
    question_config: dict[str, Any],
    responses_by_item: dict[str, str],
    scale_config: dict[str, Any],
    score_config: dict[str, Any],
) -> DimensionScore:
    """Calcula raw_score, risk_score e classificacao de uma dimensao."""

    if question_config.get("tipo") != "dimensao_score":
        raise ScoreError("A pergunta informada nao e uma dimensao de score.")

    response_scale = build_response_scale(scale_config)
    item_scores = []

    for item_config in question_config["itens"]:
        item_code = str(item_config["codigo"])
        if item_code not in responses_by_item:
            raise ScoreError(f"Resposta ausente para item {item_code}.")
        item_scores.append(
            score_item(item_config, responses_by_item[item_code], response_scale)
        )

    raw_score = _average(item.raw_score for item in item_scores)
    risk_score = _average(item.risk_score for item in item_scores)
    classification = classify_risk_score(risk_score, score_config)

    return DimensionScore(
        dimension_code=str(question_config["codigo_dimensao"]),
        raw_score=raw_score,
        risk_score=risk_score,
        classification=classification,
        items=tuple(item_scores),
    )


def _average(values: Any) -> float:
    numbers = tuple(float(value) for value in values)
    if not numbers:
        raise ScoreError("Nao e possivel calcular media sem valores.")
    return round(sum(numbers) / len(numbers), 4)
