from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


_file_path = Path(__file__).resolve()
ROOT_DIR = _file_path.parent if _file_path.parent.name == "financeiro" else _file_path.parents[1]
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "piloto.json"


@dataclass(frozen=True)
class AlertThresholds:
    atencao: float = 0.8
    critico: float = 0.95
    estourado: float = 1.0


@dataclass(frozen=True)
class PilotConfig:
    nome_carteira: str
    contratos: tuple[str, ...]
    pecs: tuple[str, ...]
    destinatario_padrao: str
    limites_alerta: AlertThresholds
    meses_fechados: tuple[str, ...] = ()


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> PilotConfig:
    path = Path(path)
    if not path.exists():
        return PilotConfig(
            nome_carteira="Carteira Guilherme",
            contratos=(),
            pecs=(),
            destinatario_padrao="",
            limites_alerta=AlertThresholds(),
            meses_fechados=(),
        )

    raw = json.loads(path.read_text(encoding="utf-8"))
    limites = raw.get("limites_alerta", {})
    return PilotConfig(
        nome_carteira=raw.get("nome_carteira", "Carteira Guilherme"),
        contratos=tuple(str(x).strip() for x in raw.get("contratos", []) if str(x).strip()),
        pecs=tuple(str(x).strip() for x in raw.get("pecs", []) if str(x).strip()),
        destinatario_padrao=raw.get("destinatario_padrao", ""),
        limites_alerta=AlertThresholds(
            atencao=float(limites.get("atencao", 0.8)),
            critico=float(limites.get("critico", 0.95)),
            estourado=float(limites.get("estourado", 1.0)),
        ),
        meses_fechados=tuple(str(x).strip() for x in raw.get("meses_fechados", []) if str(x).strip()),
    )
