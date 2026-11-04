import json
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

DOMAIN = "who_did_it"

_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
with open(_MANIFEST_PATH, encoding="utf-8") as _f:
    INTEGRATION_VERSION: Final[str] = json.load(_f).get("version", "0.0.0")

URL_BASE: Final[str] = f"/{DOMAIN}"

JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Carte Who Did It",
        "filename": "who_did_it-card.js",
        "version": INTEGRATION_VERSION,
    },
]

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_TRIGGER_SENSOR = "trigger_sensor"
CONF_PERSONS = "persons"
CONF_COOLDOWN = "cooldown"

DEFAULT_NAME = "Tâche"
DEFAULT_ICON = "mdi:account-question"
DEFAULT_PERSONS = "Chloe, Axel, Joelle, Jv"
DEFAULT_COOLDOWN = 6

SERVICE_DONE = "done"
ATTR_PERSON = "person"

EVENT_PENDING = f"{DOMAIN}_pending"
EVENT_DONE = f"{DOMAIN}_done"
EVENT_DENIED = f"{DOMAIN}_denied"
