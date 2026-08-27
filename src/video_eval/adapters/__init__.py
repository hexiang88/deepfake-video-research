from __future__ import annotations

from .auvire import AuViReAdapter
from .dimodif import DiMoDifAdapter
from .lipforensics import LipForensicsAdapter
from .pwtf_dvd import PwtfDvdAdapter
from .realforensics import RealForensicsAdapter
from .vlaforge import VlaforgeAdapter

ADAPTERS = {
    "lipforensics": LipForensicsAdapter,
    "realforensics": RealForensicsAdapter,
    "pwtf_dvd": PwtfDvdAdapter,
    "vlaforge": VlaforgeAdapter,
    "auvire": AuViReAdapter,
    "dimodif": DiMoDifAdapter,
}


def get_adapter(name: str):
    if name not in ADAPTERS:
        raise KeyError(f"unknown model {name}; known: {sorted(ADAPTERS)}")
    return ADAPTERS[name]()
