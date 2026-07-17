from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


EXPECTED_QUESTIONS = tuple(f"Q{i}" for i in range(1, 19))
EXPECTED_DIMENSIONS = ("DEM", "EST", "CTV", "REL", "ORG", "ITI", "SAG")
EXPECTED_TOP_LEVEL_KEYS = (
    "metadata",
    "escala_likert",
    "score",
    "regras_gerais",
    "perguntas",
    "dimensoes",
    "vco",
    "qualitativas",
)
VALID_ITEM_DIRECTIONS = {"risco_direto", "protetivo_inverter"}


class MetodologiaError(ValueError):
    """Erro de carregamento ou validacao da metodologia."""


@dataclass(frozen=True)
class Metodologia:
    """Representa a metodologia versionada carregada do YAML."""

    path: Path
    data: dict[str, Any]

    @property
    def versao(self) -> str:
        return str(self.data["metadata"]["versao"])

    @property
    def perguntas(self) -> dict[str, Any]:
        return self.data["perguntas"]

    @property
    def dimensoes(self) -> dict[str, Any]:
        return self.data["dimensoes"]

    def resumo(self) -> dict[str, Any]:
        return {
            "arquivo": str(self.path),
            "versao": self.versao,
            "total_perguntas": len(self.perguntas),
            "dimensoes": list(self.dimensoes.keys()),
        }


def load_metodologia(path: str | Path) -> Metodologia:
    """Carrega e valida uma metodologia YAML."""

    config_path = Path(path)
    if not config_path.exists():
        raise MetodologiaError(f"Arquivo de metodologia nao encontrado: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise MetodologiaError(f"YAML invalido em {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise MetodologiaError("A metodologia deve ser um objeto YAML no nivel raiz.")

    metodologia = Metodologia(path=config_path, data=raw)
    validate_metodologia(metodologia)
    return metodologia


def validate_metodologia(metodologia: Metodologia) -> None:
    """Valida as regras estruturais minimas da metodologia."""

    data = metodologia.data
    _require_keys(data, EXPECTED_TOP_LEVEL_KEYS, "raiz da metodologia")
    _validate_questions(data["perguntas"])
    _validate_dimensions(data["dimensoes"], data["perguntas"])
    _validate_likert_scale(data["escala_likert"])
    _validate_score_rules(data["score"])
    _validate_vco(data["vco"], data["perguntas"])
    _validate_qualitativas(data["qualitativas"], data["perguntas"])


def _require_keys(obj: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise MetodologiaError(f"Campos ausentes em {context}: {', '.join(missing)}")


def _validate_questions(perguntas: Any) -> None:
    if not isinstance(perguntas, dict):
        raise MetodologiaError("'perguntas' deve ser um objeto.")

    missing = [question for question in EXPECTED_QUESTIONS if question not in perguntas]
    if missing:
        raise MetodologiaError(f"Perguntas ausentes: {', '.join(missing)}")

    extra = sorted(set(perguntas) - set(EXPECTED_QUESTIONS))
    if extra:
        raise MetodologiaError(f"Perguntas nao esperadas: {', '.join(extra)}")

    for codigo, pergunta in perguntas.items():
        if not isinstance(pergunta, dict):
            raise MetodologiaError(f"{codigo} deve ser um objeto.")
        if "tipo" not in pergunta:
            raise MetodologiaError(f"{codigo} nao possui campo 'tipo'.")

    for codigo in ("Q9", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15"):
        _validate_score_question(codigo, perguntas[codigo])


def _validate_score_question(codigo: str, pergunta: dict[str, Any]) -> None:
    _require_keys(
        pergunta,
        ("tipo", "codigo_dimensao", "titulo", "escala", "regra_padrao", "itens"),
        codigo,
    )

    if pergunta["tipo"] != "dimensao_score":
        raise MetodologiaError(f"{codigo} deveria ter tipo 'dimensao_score'.")

    itens = pergunta["itens"]
    if not isinstance(itens, list) or not itens:
        raise MetodologiaError(f"{codigo} deve possuir lista de itens.")

    for item in itens:
        _require_keys(item, ("codigo", "texto", "direcao"), f"item de {codigo}")
        if item["direcao"] not in VALID_ITEM_DIRECTIONS:
            raise MetodologiaError(
                f"Direcao invalida em {item['codigo']}: {item['direcao']}"
            )


def _validate_dimensions(dimensoes: Any, perguntas: dict[str, Any]) -> None:
    if not isinstance(dimensoes, dict):
        raise MetodologiaError("'dimensoes' deve ser um objeto.")

    missing = [dimension for dimension in EXPECTED_DIMENSIONS if dimension not in dimensoes]
    if missing:
        raise MetodologiaError(f"Dimensoes ausentes: {', '.join(missing)}")

    for codigo_dimensao, dimensao in dimensoes.items():
        _require_keys(dimensao, ("nome", "pergunta", "regra"), f"dimensao {codigo_dimensao}")
        pergunta_codigo = dimensao["pergunta"]
        if pergunta_codigo not in perguntas:
            raise MetodologiaError(
                f"Dimensao {codigo_dimensao} aponta para pergunta inexistente: {pergunta_codigo}"
            )
        pergunta = perguntas[pergunta_codigo]
        if pergunta.get("codigo_dimensao") != codigo_dimensao:
            raise MetodologiaError(
                f"Dimensao {codigo_dimensao} nao confere com {pergunta_codigo}."
            )


def _validate_likert_scale(escala: Any) -> None:
    if not isinstance(escala, dict):
        raise MetodologiaError("'escala_likert' deve ser um objeto.")
    respostas = escala.get("respostas")
    expected = {
        "Nunca": 1,
        "Raramente": 2,
        "As vezes": 3,
        "Frequentemente": 4,
        "Sempre": 5,
    }
    if respostas != expected:
        raise MetodologiaError("Escala Likert diferente da esperada.")


def _validate_score_rules(score: Any) -> None:
    if not isinstance(score, dict):
        raise MetodologiaError("'score' deve ser um objeto.")

    regra = score.get("regra_classificacao", {})
    if regra.get("score_oficial") != "risk_score":
        raise MetodologiaError("A classificacao deve usar 'risk_score'.")

    faixas = regra.get("faixas")
    if not isinstance(faixas, list) or len(faixas) != 4:
        raise MetodologiaError("Classificacao deve possuir 4 faixas.")

    classes = [faixa.get("classe") for faixa in faixas]
    if classes != ["Favoravel", "Atencao", "Critico", "Grave"]:
        raise MetodologiaError("Classes de classificacao fora da ordem esperada.")


def _validate_vco(vco: Any, perguntas: dict[str, Any]) -> None:
    if not isinstance(vco, dict):
        raise MetodologiaError("'vco' deve ser um objeto.")
    if vco.get("pergunta") != "Q16":
        raise MetodologiaError("VCO deve apontar para Q16.")
    if vco.get("compoe_score_medio") is not False:
        raise MetodologiaError("VCO nao deve compor score medio.")

    q16 = perguntas["Q16"]
    if q16.get("tipo") != "vco":
        raise MetodologiaError("Q16 deve ter tipo 'vco'.")
    if q16.get("compoe_media_score") is not False:
        raise MetodologiaError("Q16 nao deve compor media de score.")


def _validate_qualitativas(qualitativas: Any, perguntas: dict[str, Any]) -> None:
    if not isinstance(qualitativas, dict):
        raise MetodologiaError("'qualitativas' deve ser um objeto.")

    expected = {
        "causas_desgaste": "Q17",
        "melhorias_sugeridas": "Q18",
    }
    for nome, pergunta_codigo in expected.items():
        if qualitativas.get(nome, {}).get("pergunta") != pergunta_codigo:
            raise MetodologiaError(f"{nome} deve apontar para {pergunta_codigo}.")
        if perguntas[pergunta_codigo].get("maximo_opcoes") != 3:
            raise MetodologiaError(f"{pergunta_codigo} deve limitar a 3 opcoes.")
