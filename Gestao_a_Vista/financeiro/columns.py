from __future__ import annotations

import re
import unicodedata


CANONICAL_COLUMNS = {
    "mes": ["mes", "competencia", "periodo", "data", "referencia"],
    "pec": ["pec", "p e c", "projeto", "centro de custo", "centro custo"],
    "contrato": ["contrato", "num contrato", "numero contrato", "cod contrato"],
    "conta_contabil": [
        "conta contabil",
        "conta",
        "cod conta",
        "codigo conta",
        "classificacao contabil",
    ],
    "descricao_conta": [
        "descricao",
        "descricao conta",
        "nome conta",
        "conta descricao",
        "classe",
        "subclasse",
    ],
    "fornecedor": ["fornecedor", "credor", "prestador", "parceiro"],
    "orcado": ["orcado", "orcamento", "budget", "previsto", "vl orcado", "valor orcado"],
    "realizado": ["realizado", "gasto", "valor realizado", "vl realizado", "actual"],
}


def normalize_label(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_columns(columns: list[object]) -> dict[str, str]:
    normalized = {str(column): normalize_label(column) for column in columns}
    detected: dict[str, str] = {}

    for target, aliases in CANONICAL_COLUMNS.items():
        alias_labels = [normalize_label(alias) for alias in aliases]
        exact = next(
            (original for original, label in normalized.items() if label in alias_labels),
            None,
        )
        if exact:
            detected[target] = exact
            continue

        contains = next(
            (
                original
                for original, label in normalized.items()
                if any(alias in label for alias in alias_labels)
            ),
            None,
        )
        if contains:
            detected[target] = contains

    missing = [name for name in ("conta_contabil", "orcado", "realizado") if name not in detected]
    if missing:
        raise ValueError(
            "Nao encontrei colunas obrigatorias: "
            + ", ".join(missing)
            + ". Colunas recebidas: "
            + ", ".join(str(c) for c in columns)
        )

    return detected
