from homeassistant.const import Platform

DOMAIN = "chronolavevaiselle"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_DURATION = "duration"
CONF_CYCLE_SENSOR = "cycle_sensor"
CONF_PERSONS = "persons"
CONF_COOLDOWN = "cooldown"

DEFAULT_DURATION = 120
DEFAULT_NAME = "Lave-vaisselle"
DEFAULT_PERSONS = "Chloe, Axel, Joelle, Jv"
DEFAULT_COOLDOWN = 6

SERVICE_START_CYCLE = "start_cycle"
SERVICE_EMPTY = "empty"
ATTR_DURATION = "duration"
ATTR_PERSON = "person"

EVENT_CYCLE_FINISHED = f"{DOMAIN}_cycle_finished"
EVENT_CYCLE_ENDED = f"{DOMAIN}_cycle_ended"
EVENT_EMPTIED = f"{DOMAIN}_emptied"
EVENT_EMPTY_DENIED = f"{DOMAIN}_empty_denied"
