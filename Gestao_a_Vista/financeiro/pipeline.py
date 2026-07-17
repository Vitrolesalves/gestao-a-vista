from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import PilotConfig, ROOT_DIR
from .dashboard_ingestion import read_dashboard_sources
from .finance import (
    aggregate_accounts,
    build_dashboard_accounts,
    build_monthly_closing_accounts,
    prepare_financial_view,
    summarize_kpis,
)
from .ingestion import read_financial_files


def _get_writable_dir(default_path: Path, fallback_name: str) -> Path:
    import os
    # 1. Try default path
    try:
        default_path.mkdir(parents=True, exist_ok=True)
        test_file = default_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return default_path
    except Exception:
        pass

    # 2. Try inside Django MEDIA_ROOT if configured
    try:
        from django.conf import settings
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if media_root:
            media_path = Path(media_root) / fallback_name
            media_path.mkdir(parents=True, exist_ok=True)
            return media_path
    except Exception:
        pass

    # 3. Fallback to project root
    fallback_path = ROOT_DIR / fallback_name
    try:
        fallback_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return fallback_path

INPUT_DIR = _get_writable_dir(ROOT_DIR / "Base de dados", "Base_de_dados_writable")
LEGACY_INPUT_DIR = ROOT_DIR / "data" / "input"
PROCESSED_DIR = _get_writable_dir(ROOT_DIR / "data" / "processed", "data_writable")

def get_dynamic_state_code() -> str | None:
    # 1. Try from request context
    try:
        from Gestao_a_Vista.signals import get_current_request
        request = get_current_request()
        if request and request.user and request.user.is_authenticated:
            if getattr(request.user, 'is_global_admin', False):
                active_regional = request.session.get('active_regional')
                if active_regional:
                    return active_regional.strip().lower()
            elif getattr(request.user, 'regional', None):
                # Usa sempre o db_slug (mesma chave usada pelo roteamento de
                # banco em middleware.py), com fallback pro estado apenas se
                # a regional nao tiver db_slug definido.
                regional = request.user.regional
                slug = (regional.db_slug or regional.estado or "").strip().lower()
                if slug:
                    return slug
    except Exception:
        pass

    # 2. Try from thread local database router state
    try:
        from Gestao_a_Vista.thread_local import get_current_db
        curr_db = get_current_db()
        if curr_db and curr_db.startswith("db_"):
            return curr_db[3:].lower()
    except Exception:
        pass

    return None

def get_input_dir() -> Path:
    state = get_dynamic_state_code()
    if state:
        path = INPUT_DIR / state
        path.mkdir(parents=True, exist_ok=True)
        return path
    return INPUT_DIR

def get_processed_dir() -> Path:
    state = get_dynamic_state_code()
    if state:
        path = PROCESSED_DIR / state
        path.mkdir(parents=True, exist_ok=True)
        return path
    return PROCESSED_DIR


def get_input_dir_for_read() -> Path:
    """Resolve o diretorio de entrada para LEITURA (rodar pipeline/preview).

    Se a regional ativa ainda nao tem planilhas proprias em
    'Base de dados/<regional>/', cai de volta pra pasta raiz (onde estao os
    dados historicos), em vez de operar sobre uma pasta vazia. Uma vez que
    alguem suba planilhas dentro da subpasta da regional, ela passa a ser
    usada normalmente.
    """
    root_dir = get_input_dir_root()
    state = get_dynamic_state_code()
    if not state:
        return root_dir
    regional_dir = root_dir / state
    if has_dashboard_sources(regional_dir):
        return regional_dir
    return root_dir


def get_processed_dir_for_read() -> Path:
    """Resolve o diretorio de dados processados para LEITURA (dashboard).

    Mesma logica de fallback de get_input_dir_for_read(): se a regional
    ativa ainda nao tem dados processados proprios, usa a pasta raiz em vez
    de mostrar o dashboard zerado.
    """
    root_dir = get_processed_dir_root()
    state = get_dynamic_state_code()
    if not state:
        return root_dir
    regional_dir = root_dir / state
    if (regional_dir / "contas_agregadas.csv").exists():
        return regional_dir
    return root_dir


def get_input_dir_root() -> Path:
    return INPUT_DIR


def get_processed_dir_root() -> Path:
    return PROCESSED_DIR


def run_pipeline(config: PilotConfig, input_dir: Path | None = None, processed_dir: Path | None = None) -> dict[str, object]:
    if input_dir is None:
        # Le com fallback: usa a pasta da regional ativa se ela ja tiver
        # planilhas proprias, senao cai pra pasta raiz (dados historicos).
        input_dir = get_input_dir_for_read()
    if processed_dir is None:
        # Escreve sempre no destino "de verdade" da regional ativa (ou raiz,
        # se nao houver regional ativa), preservando o isolamento por
        # regional para quem de fato subir planilhas por regional.
        processed_dir = get_processed_dir()

    if has_dashboard_sources(input_dir):
        compras, orcamento = read_dashboard_sources(input_dir, config)
        accounts = build_dashboard_accounts(compras, orcamento, config.limites_alerta)
        closing = build_monthly_closing_accounts(compras, orcamento, config.limites_alerta, config.meses_fechados)
        raw = compras
        budget_raw = orcamento
    else:
        raw = read_financial_files(LEGACY_INPUT_DIR, config)
        view = prepare_financial_view(raw, config.limites_alerta)
        accounts = aggregate_accounts(view, config.limites_alerta)
        closing = pd.DataFrame()
        budget_raw = None

    kpis = summarize_kpis(accounts)

    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_path = processed_dir / "compras_normalizadas.csv"
    budget_path = processed_dir / "orcamento_normalizado.csv"
    accounts_path = processed_dir / "contas_agregadas.csv"
    closing_path = processed_dir / "fechamento_mensal.csv"
    summary_path = processed_dir / "resumo.json"

    raw.to_csv(raw_path, index=False, encoding="utf-8-sig")
    if budget_raw is not None:
        budget_raw.to_csv(budget_path, index=False, encoding="utf-8-sig")
    accounts.to_csv(accounts_path, index=False, encoding="utf-8-sig")
    closing.to_csv(closing_path, index=False, encoding="utf-8-sig")
    summary_path.write_text(json.dumps(kpis, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "raw_rows": int(raw.shape[0]),
        "account_rows": int(accounts.shape[0]),
        "budget_rows": int(budget_raw.shape[0]) if budget_raw is not None else 0,
        "raw_path": raw_path,
        "budget_path": budget_path if budget_raw is not None else None,
        "accounts_path": accounts_path,
        "closing_path": closing_path,
        "closing_rows": int(closing.shape[0]),
        "summary_path": summary_path,
        "kpis": kpis,
    }


def load_processed_accounts(processed_dir: Path | None = None):
    if processed_dir is None:
        processed_dir = get_processed_dir_for_read()
    path = processed_dir / "contas_agregadas.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_processed_closing(processed_dir: Path | None = None):
    if processed_dir is None:
        processed_dir = get_processed_dir_for_read()
    path = processed_dir / "fechamento_mensal.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def has_dashboard_sources(input_dir: Path) -> bool:
    return (input_dir / "Compras Produto").exists() and (input_dir / "Resultado RE X OR").exists()
