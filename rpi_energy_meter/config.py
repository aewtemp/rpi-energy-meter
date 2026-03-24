import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import tomli
import tomli_w
from box import Box


def load_config(path: Union[str, Path]) -> Box:
    """
    Lädt eine TOML-Konfigurationsdatei und gibt sie als dot-notierbares Box-Objekt zurück.

    Args:
        path (str | Path): Pfad zur TOML-Datei

    Returns:
        Box: Konfigurationsobjekt mit Dot-Zugriff
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {path}")

    with path.open("rb") as f:
        data = tomli.load(f)

    return Box(data, default_box=True, frozen_box=False)


def write_config(path: Union[str, Path], config: Box) -> None:
    path = Path(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            tomli_w.dump(config.to_dict(), f)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


def read_total_kwh(config) -> list:
    totals = [[{"Total": 0.00} for ct in range(6)] for phase in range(config.PHASES.COUNT)]

    for phase in range(config.PHASES.COUNT):
        for ct in range(config.CTS.get(str(phase + 1)).COUNT):
            totals[phase][ct]["Total"] = config.CTS.get(str(phase + 1)).get(str(ct + 1)).KWH

    return totals


def save_total_kwh(config, measurements):
    for phase in range(config.PHASES.COUNT):
        for ct in range(config.CTS.get(str(phase + 1)).COUNT):
            if (
                config.CTS.get(str(phase + 1)).get(str(ct + 1)).get("RESET_UTC") == "1970-1-1 00:00:00.000000"
                or float(config.CTS.get(str(phase + 1)).get(str(ct + 1)).KWH) > measurements[phase]._energy[ct]["Total"]
            ):
                # config.CTS.get(str(phase + 1)).get(str(ct + 1)).set("RESET_UTC", str(datetime.now(timezone.utc)))
                config.CTS[str(phase + 1)][str(ct + 1)].RESET_UTC = str(datetime.now(timezone.utc))

            # config.CTS.get(str(phase + 1)).get(str(ct + 1)).set("KWH", float(measurements[phase]._energy[ct]['Total']))
            config.CTS[str(phase + 1)][str(ct + 1)].KWH = float(measurements[phase]._energy[ct]["Total"])
