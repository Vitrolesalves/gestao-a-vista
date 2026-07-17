from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import pandas as pd

from .config import PilotConfig
from .ingestion import parse_money


DEFAULT_YEAR = 2026

MONTHS = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
}


def read_dashboard_sources(base_dir: Path, config: PilotConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    compras_dir = base_dir / "Compras Produto"
    resultado_dir = base_dir / "Resultado RE X OR"
    compras = read_compras_folder(compras_dir)
    resultado = read_resultado_folder(resultado_dir)
    return apply_pilot_filter(compras, config), apply_pilot_filter(resultado, config)


def read_compras_folder(folder: Path) -> pd.DataFrame:
    frames = []
    if folder.exists():
        for path in sorted(folder.glob("*.xls*")):
            try:
                if path.stat().st_size == 0:
                    continue
                df = read_compras_file(path)
                if not df.empty:
                    frames.append(df)
            except Exception:
                continue
    return pd.concat(frames, ignore_index=True) if frames else empty_compras()


def read_resultado_folder(folder: Path) -> pd.DataFrame:
    frames = []
    if folder.exists():
        for path in sorted(folder.glob("*.xls*")):
            try:
                if path.stat().st_size == 0:
                    continue
                df = read_resultado_file(path)
                if not df.empty:
                    frames.append(df)
            except Exception:
                continue
    return pd.concat(frames, ignore_index=True) if frames else empty_resultado()


def read_compras_file(path: Path) -> pd.DataFrame:
    stem = path.stem
    year_match = re.search(r"(20\d{2})", stem)
    target_year = int(year_match.group(1)) if year_match else DEFAULT_YEAR

    raw = read_exported_matrix(path)
    value_col = find_column(raw, ["tot vl contabil", "valor contabil", "vl contabil"])
    data = pd.DataFrame(
        {
            "mes": raw.get("DS_MES_ANO_CR", infer_month_from_path(path)).map(lambda x: normalize_month(x, target_year))
            if "DS_MES_ANO_CR" in raw
            else infer_month_from_path(path),
            "conta": raw["CONTA"].fillna("").astype(str).str.strip(),
            "fornecedor": raw["FORNECEDOR"].fillna("").astype(str).str.strip(),
            "pec": raw["PEC"].fillna("").astype(str).str.strip(),
            "valor_compra": raw[value_col].map(parse_money),
            "arquivo_origem": path.name,
        }
    )
    data[["conta_codigo", "conta_desc"]] = data["conta"].apply(lambda value: pd.Series(split_code_desc(value)))
    data[["pec_codigo", "pec_desc"]] = data["pec"].apply(lambda value: pd.Series(split_code_desc(value)))
    return data


def read_resultado_file(path: Path) -> pd.DataFrame:
    stem = path.stem
    year_match = re.search(r"(20\d{2})", stem)
    target_year = int(year_match.group(1)) if year_match else DEFAULT_YEAR

    raw = read_exported_matrix(path)
    month_col = find_optional_column(raw, ["dt mes ano", "mes", "competencia"])
    data = pd.DataFrame(
        {
            "mes": raw[month_col].map(lambda x: normalize_month(x, target_year)) if month_col else infer_month_from_path(path),
            "cc_sup": raw["CC. SUP"].fillna("").astype(str).str.strip(),
            "conta": raw["CONTA"].fillna("").astype(str).str.strip(),
            "pec": raw["PEC"].fillna("").astype(str).str.strip(),
            "vl_realizado": money_column(raw, ["vl realizado"]),
            "ajustes": money_column(raw, ["ajustes"]),
            "re_ajustado": money_column(raw, ["re ajustado"]),
            "valor_or": money_column(raw, ["valor or", "vl orcado", "vl orçado", "valor orcado", "valor orçado"]),
            "perc_re_x_or": money_column(raw, ["% re x or", "%"]),
            "dif_re_x_or": money_column(raw, ["dif re x or"]),
            "receita_liquida": money_column(raw, ["receita liquida", "receita líquida"]),
            "arquivo_origem": path.name,
        }
    )
    data[["cc_sup_codigo", "cc_sup_desc"]] = data["cc_sup"].apply(lambda value: pd.Series(split_code_desc(value)))
    data[["conta_codigo", "conta_desc"]] = data["conta"].apply(lambda value: pd.Series(split_code_desc(value)))
    data[["pec_codigo", "pec_desc"]] = data["pec"].apply(lambda value: pd.Series(split_code_desc(value)))
    return data


def read_exported_matrix(path: Path) -> pd.DataFrame:
    for h in [2, 0, 1, 3]:
        try:
            raw = pd.read_excel(path, header=h).dropna(how="all")
            raw.columns = [str(column).strip() for column in raw.columns]
            normalized_cols = {normalize_label(c) for c in raw.columns}
            if "conta" in normalized_cols or "pec" in normalized_cols or "cc sup" in normalized_cols:
                return raw
        except Exception:
            continue

    raw = pd.read_excel(path, header=2).dropna(how="all")
    raw.columns = [str(column).strip() for column in raw.columns]
    return raw


def find_column(data: pd.DataFrame, candidates: list[str]) -> str:
    normalized = {column: normalize_label(column) for column in data.columns}
    for candidate in candidates:
        candidate_text = str(candidate).strip().lower()
        for column in data.columns:
            if str(column).strip().lower() == candidate_text:
                return column

        candidate_label = normalize_label(candidate)
        if not candidate_label:
            continue
        for column, label in normalized.items():
            if candidate_label in label:
                return column
    raise ValueError(f"Nao encontrei coluna entre {candidates}. Colunas: {list(data.columns)}")


def find_optional_column(data: pd.DataFrame, candidates: list[str]) -> str | None:
    try:
        return find_column(data, candidates)
    except ValueError:
        return None


def money_column(data: pd.DataFrame, candidates: list[str]) -> pd.Series:
    column = find_optional_column(data, candidates)
    if column is None:
        return pd.Series(0.0, index=data.index)
    return data[column].map(parse_money)


def split_code_desc(value: object) -> tuple[str, str]:
    text = str(value or "").strip()
    if " - " not in text:
        return text, ""
    code, desc = text.split(" - ", 1)
    return code.strip(), desc.strip()


def normalize_label(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_month(value: object, target_year: int = None) -> str:
    text = normalize_label(value)
    year_match = re.search(r"(20\d{2})", text)
    year = target_year if target_year is not None else (int(year_match.group(1)) if year_match else DEFAULT_YEAR)

    for token, month in sorted(MONTHS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{token}\b", text):
            return f"{year}-{month:02d}"

    match = re.search(r"(20\d{2})\s*([01]\d)", text)
    if match:
        y = target_year if target_year is not None else int(match.group(1))
        return f"{y}-{match.group(2)}"
    match = re.search(r"\b([01]?\d)\s*(20\d{2})\b", text)
    if match:
        month = int(match.group(1))
        if 1 <= month <= 12:
            y = target_year if target_year is not None else int(match.group(2))
            return f"{y}-{month:02d}"

    try:
        val_int = int(float(text))
        if 1 <= val_int <= 12:
            y = target_year if target_year is not None else DEFAULT_YEAR
            return f"{y}-{val_int:02d}"
    except ValueError:
        pass

    return str(value or "").strip()


def infer_month_from_path(path: Path) -> str:
    stem = path.stem
    year_match = re.search(r"(20\d{2})", stem)
    target_year = int(year_match.group(1)) if year_match else DEFAULT_YEAR
    return normalize_month(stem, target_year)


def apply_pilot_filter(data: pd.DataFrame, config: PilotConfig) -> pd.DataFrame:
    filtered = data
    if config.pecs and "pec_codigo" in filtered:
        filtered = filtered[filtered["pec_codigo"].isin(config.pecs) | filtered["pec"].isin(config.pecs)]
    return filtered.reset_index(drop=True)


def empty_compras() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "mes",
            "conta",
            "conta_codigo",
            "conta_desc",
            "fornecedor",
            "pec",
            "pec_codigo",
            "pec_desc",
            "valor_compra",
            "arquivo_origem",
        ]
    )


def empty_resultado() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "mes",
            "cc_sup",
            "cc_sup_codigo",
            "cc_sup_desc",
            "conta",
            "conta_codigo",
            "conta_desc",
            "pec",
            "pec_codigo",
            "pec_desc",
            "vl_realizado",
            "ajustes",
            "re_ajustado",
            "valor_or",
            "perc_re_x_or",
            "dif_re_x_or",
            "receita_liquida",
            "arquivo_origem",
        ]
    )
