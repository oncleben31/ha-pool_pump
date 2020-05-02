"""Constants for blueprint."""
# Base component constants
NAME = "Pool Pump Manager"
DOMAIN = "pool_pump"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/oncleben31/ha-pool_pump/issues"
DOC_URL = "https://github.com/oncleben31/ha-pool_pump"

# Icons
ICON = "mdi:format-quote-close"

# Common constants
POOL_PUMP_MODE_AUTO = "Auto"
ATTR_POOL_PUMP_MODE_ENTITY_ID = "pool_pump_mode_entity_id"

ATTR_SWITCH_ENTITY_ID = "switch_entity_id"

# Constants for @oncleben31 mode
ATTR_POOL_TEMPERATURE_ENTITY_ID = "pool_temperature_entity_id"

# Constants for @exxamalte mode
ATTR_RUN_PUMP_IN_OFF_SEASON_ENTITY_ID = "run_pool_pump_hours_off_season_entity_id"
ATTR_RUN_PUMP_IN_SWIMMING_SEASON_ENTITY_ID = (
    "run_pool_pump_hours_swimming_season_entity_id"
)
ATTR_SWIMMING_SEASON_ENTITY_ID = "swimming_season_entity_id"
ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID = "water_level_critical_entity_id"

OFF_SEASON_RUN_1_AFTER_SUNRISE_OFFSET_MINUTES = 120
OFF_SEASON_BREAK_MINUTES = 60

SWIMMING_SEASON_RUN_1_AFTER_SUNRISE_OFFSET_MINUTES = 75
SWIMMING_SEASON_BREAK_MINUTES = 60


# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
