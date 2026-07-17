from __future__ import annotations

from pathlib import Path

from .pipeline import INPUT_DIR


DATASET_FOLDERS = {
    "compras": "Compras Produto",
    "resultado": "Resultado RE X OR",
    "re_x_or": "Resultado RE X OR",
}

EXCEL_EXTENSIONS = {".xlsx", ".xls", ".xlsm"}

MONTH_LABELS = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def save_uploaded_planilha(
    content: bytes,
    original_name: str,
    dataset: str,
    month_label: str,
    base_dir: Path | None = None,
) -> Path:
    if base_dir is None:
        from .pipeline import get_input_dir
        base_dir = get_input_dir()

    extension = Path(original_name).suffix.lower()
    if extension not in EXCEL_EXTENSIONS:
        raise ValueError("Envie um arquivo Excel (.xlsx, .xls ou .xlsm).")

    folder_name = DATASET_FOLDERS.get(str(dataset).strip().lower())
    if not folder_name:
        raise ValueError("Tipo de planilha invalido. Use compras ou resultado.")

    safe_month = normalize_month_label(month_label)
    destination_dir = Path(base_dir) / folder_name
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{safe_month}{extension}"
    
    try:
        destination.write_bytes(content)
    except PermissionError:
        import time
        timestamp = int(time.time())
        destination = destination_dir / f"{safe_month}_{timestamp}{extension}"
        try:
            destination.write_bytes(content)
        except PermissionError:
            raise PermissionError("Não foi possível salvar o arquivo devido a restrições de permissão na pasta de upload do servidor.")
            
    return destination


def normalize_month_label(month_label: str) -> str:
    import re
    text = str(month_label or "").strip()
    if re.match(r"^\d{4}-\d{2}$", text):
        return text
    valid = {month.lower(): month for month in MONTH_LABELS}
    normalized = valid.get(text.lower())
    if not normalized:
        raise ValueError("Selecione um mes valido para salvar a planilha.")
    return normalized
