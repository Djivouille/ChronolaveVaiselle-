from homeassistant.const import Platform

DOMAIN = "chronolavevaiselle"

PLATFORMS = [Platform.SENSOR]

CONF_DURATION = "duration"
DEFAULT_DURATION = 120
DEFAULT_NAME = "Lave-vaisselle"

SERVICE_START_CYCLE = "start_cycle"
ATTR_DURATION = "duration"

EVENT_CYCLE_FINISHED = f"{DOMAIN}_cycle_finished"
