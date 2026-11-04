from homeassistant.const import Platform

DOMAIN = "who_did_it"

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
