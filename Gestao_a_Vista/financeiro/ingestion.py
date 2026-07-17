from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from .columns import detect_columns
from .config import PilotConfig


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm", ".xls"}


def list_input_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []

    files: list[Path] = []
    for path in input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS and not path.name.startswith("~$"):
            files.append(path)
    return sorted(files)


def read_financial_files(input_dir: Path, config: PilotConfig) -> pd.DataFrame:
    frames = [read_financial_file(path) for path in list_input_files(input_dir)]
    if not frames:
        return empty_financial_frame()

    data = pd.concat(frames, ignore_index=True)
    data = apply_pilot_filter(data, config)
    return data


def read_financial_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        raw = pd.read_csv(path, sep=None, engine="python")
    else:
        raw = pd.read_excel(path)

    raw = raw.dropna(how="all")
    mapping = detect_columns(list(raw.columns))

    data = pd.DataFrame()
    for target, source in mapping.items():
        data[target] = raw[source]

    data["arquivo_origem"] = path.name
    data["mes"] = data.get("mes")
    if "mes" not in mapping or data["mes"].isna().all():
        data["mes"] = infer_month_from_path(path)

    for optional in ("pec", "contrato", "descricao_conta", "fornecedor"):
        if optional not in data:
            data[optional] = ""

    data["orcado"] = data["orcado"].map(parse_money)
    data["realizado"] = data["realizado"].map(parse_money)
    data["conta_contabil"] = data["conta_contabil"].astype(str).str.strip()
    data["descricao_conta"] = data["descricao_conta"].fillna("").astype(str).str.strip()
    data["pec"] = data["pec"].fillna("").astype(str).str.strip()
    data["contrato"] = data["contrato"].fillna("").astype(str).str.strip()
    data["fornecedor"] = data["fornecedor"].fillna("").astype(str).str.strip()
    data["mes"] = data["mes"].map(normalize_month)

    return data[
        [
            "mes",
            "pec",
            "contrato",
            "conta_contabil",
            "descricao_conta",
            "fornecedor",
            "orcado",
            "realizado",
            "arquivo_origem",
        ]
    ]


def empty_financial_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "mes",
            "pec",
            "contrato",
            "conta_contabil",
            "descricao_conta",
            "fornecedor",
            "orcado",
            "realizado",
            "arquivo_origem",
        ]
    )


def apply_pilot_filter(data: pd.DataFrame, config: PilotConfig) -> pd.DataFrame:
    filtered = data
    if config.contratos and "contrato" in filtered:
        filtered = filtered[filtered["contrato"].isin(config.contratos)]
    if config.pecs and "pec" in filtered:
        filtered = filtered[filtered["pec"].isin(config.pecs)]
    return filtered.reset_index(drop=True)


def parse_money(value: object) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("R$", "").replace("%", "").replace(" ", "")
    text = text.replace("(", "").replace(")", "")

    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return 0.0

    result = float(text)
    return -abs(result) if negative else result


def infer_month_from_path(path: Path) -> str:
    for part in [path.parent.name, path.stem]:
        match = re.search(r"(20\d{2})[-_]?([01]\d)", part)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
    return ""


def normalize_month(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m")

    text = str(value).strip()
    match = re.search(r"(20\d{2})[-_/]?([01]\d)", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    match = re.search(r"([01]?\d)[-/](20\d{2})", text)
    if match:
        return f"{match.group(2)}-{int(match.group(1)):02d}"

    return text
