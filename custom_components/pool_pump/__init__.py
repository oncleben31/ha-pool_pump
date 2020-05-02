"""
Custom integration to integrate a Pool Pump Manager with Home Assistant.

For more details about this integration, please refer to
https://github.com/oncleben31/ha-pool_pump
"""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sun import STATE_ABOVE_HORIZON
from homeassistant.const import (
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    STATE_ON,
    STATE_OFF,
    ATTR_ENTITY_ID,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.sun import get_astral_event_date, get_astral_event_next
from homeassistant.util import dt as dt_util
from homeassistant.core import Config, HomeAssistant


_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    STARTUP_MESSAGE,
    POOL_PUMP_MODE_AUTO,
    ATTR_SWITCH_ENTITY_ID,
    ATTR_POOL_PUMP_MODE_ENTITY_ID,
    ATTR_POOL_TEMPERATURE_ENTITY_ID,
    ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID,
    SWIMMING_SEASON_RUN_1_AFTER_SUNRISE_OFFSET_MINUTES,
    SWIMMING_SEASON_BREAK_MINUTES,
    OFF_SEASON_RUN_1_AFTER_SUNRISE_OFFSET_MINUTES,
    OFF_SEASON_BREAK_MINUTES,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(ATTR_SWITCH_ENTITY_ID): cv.entity_id,
                vol.Required(ATTR_POOL_PUMP_MODE_ENTITY_ID): cv.entity_id,
                vol.Required(ATTR_POOL_TEMPERATURE_ENTITY_ID): cv.entity_id,
                vol.Optional(
                    ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID, default=None
                ): vol.Any(cv.entity_id, None),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup(hass: HomeAssistant, config: Config):
    """Setup pool Pool Pump Mnanger using YAML."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    # Copy configuration values for later use.
    hass.data[DOMAIN][ATTR_POOL_TEMPERATURE_ENTITY_ID] = config[DOMAIN][
        ATTR_POOL_TEMPERATURE_ENTITY_ID
    ]
    hass.data[DOMAIN][ATTR_POOL_PUMP_MODE_ENTITY_ID] = config[DOMAIN][
        ATTR_POOL_PUMP_MODE_ENTITY_ID
    ]
    hass.data[DOMAIN][ATTR_SWITCH_ENTITY_ID] = config[DOMAIN][ATTR_SWITCH_ENTITY_ID]
    hass.data[DOMAIN][ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID] = config[DOMAIN][
        ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID
    ]

    async def check(call):
        """Service: Check if the pool pump should be running now."""
        # Use a fixed time reference.
        now = dt_util.now()
        mode = hass.states.get(hass.data[DOMAIN][ATTR_POOL_PUMP_MODE_ENTITY_ID])
        _LOGGER.debug("Pool pump mode: %s", mode.state)

        # Only check if pool pump is set to 'Auto'.
        if mode.state == POOL_PUMP_MODE_AUTO:
            manager = PoolPumpManager(hass, now)
            _LOGGER.debug("Manager initialised: %s", manager)
            # schedule = "Unknown"
            if await manager.is_water_level_critical():
                schedule = "Water Level Critical"
            else:
                run = manager.next_run()
                _LOGGER.debug("Next run: %s", run)
                if not run:
                    # Try tomorrow
                    tomorrow = now + timedelta(days=1)
                    next_midnight = tomorrow.replace(hour=0, minute=0, second=0)
                    _LOGGER.debug("Next midnight: %s", next_midnight)
                    manager_tomorrow = PoolPumpManager(hass, next_midnight)
                    _LOGGER.debug("Manager initialised: %s", manager_tomorrow)
                    run = manager_tomorrow.next_run()
                    _LOGGER.debug("Next run: %s", run)
                schedule = run.pretty_print()
            # Set time range so that this can be displayed in the UI.
            hass.states.async_set("{}.schedule".format(DOMAIN), schedule)
            # And now check if the pool pump should be running.
            await manager.check()
        else:
            hass.states.async_set("{}.schedule".format(DOMAIN), "Manual Mode")

    hass.services.async_register(DOMAIN, "check", check)

    # Return boolean to indicate that initialization was successfully.
    return True


class PoolPumpManager:
    """Manages the state of the pool pump."""

    def __init__(self, hass, now):
        """Initialise pool pump manager."""
        self._hass = hass
        self._now = now
        self._sun = self._hass.states.get("sun.sun")
        sunrise = get_astral_event_date(self._hass, SUN_EVENT_SUNRISE, self._now.date())
        self._first_run_offset_after_sunrise, self._durations = self._build_parameters()
        run_start_time = self._round_to_next_five_minutes(
            sunrise + timedelta(minutes=self._first_run_offset_after_sunrise)
        )
        self._runs = self.build_runs(run_start_time, self._durations)

    def __repr__(self):
        """Return string representation of this feed."""
        return "<{}(runs={})>".format(self.__class__.__name__, self._runs)

    def _build_parameters(self):
        """Build parameters for pool pump manager."""
        run_hours_total = (
            float(
                self._hass.states.get(
                    self._hass.data[DOMAIN][ATTR_POOL_TEMPERATURE_ENTITY_ID]
                ).state
            )
            / 2
        )
        offset = SWIMMING_SEASON_RUN_1_AFTER_SUNRISE_OFFSET_MINUTES
        break_duration = SWIMMING_SEASON_BREAK_MINUTES

        if 24 > run_hours_total:
            breaks_maximum = (24 - run_hours_total) * 60
            _LOGGER.debug(
                "Breaks maximum is %.1f for offset %s and break %s",
                breaks_maximum,
                offset,
                break_duration,
            )
            if breaks_maximum < break_duration + offset:
                # Re-arrange the breaks.
                offset = breaks_maximum / 2
                break_duration = breaks_maximum / 2
                _LOGGER.debug(
                    "Shortened offset to %.1f and break to %.1f", offset, break_duration
                )
        else:
            # No break, just run the pump while the sun is shining.
            break_duration = 0
            _LOGGER.debug("Break shortened to %.1f", break_duration)
        # Calculate durations of runs
        duration = run_hours_total * 60.0 * 0.5
        durations = [duration, break_duration, duration]
        return offset, durations

    def build_runs(self, run_start_time, durations):
        """Build the list of runs."""
        if not run_start_time:
            _LOGGER.error("Must provide start time for run")
            return None
        if not durations or not isinstance(durations, list):
            _LOGGER.error("Must provide durations for run")
            return None
        runs = []
        run_duration = durations[0]
        current_run = Run(run_start_time, run_duration)
        runs.append(current_run)
        remaining_durations = durations[1:]
        if len(remaining_durations) >= 2:
            next_start_time = self._round_to_next_five_minutes(
                current_run.stop_time + timedelta(minutes=remaining_durations.pop(0))
            )
            runs.extend(self.build_runs(next_start_time, remaining_durations))
        return runs

    async def check(self):
        """Check if the pool pump is supposed to run now."""
        if await self.is_water_level_critical():
            _LOGGER.debug("Water level critical - pump should be off")
        else:
            for run in self._runs:
                if run.run_now(self._now):
                    _LOGGER.debug("Pool pump should be on now: %s", run)
                    await self._switch_pool_pump(STATE_ON)
                    return
        # If we arrive here, the pool pump should be off.
        _LOGGER.debug("Pool pump should be off")
        await self._switch_pool_pump(STATE_OFF)

    def next_run(self):
        """Determine the next run - currently running or next to start."""
        for run in self._runs:
            # Because the runs are ordered, look for the first run where
            # stop_time is in the future.
            if run.is_next_run(self._now):
                return run
        # If we arrive here, no next run (today).
        return None

    async def is_water_level_critical(self):
        """Check if water level is critical at the moment."""
        entity_id = self._hass.data[DOMAIN][ATTR_WATER_LEVEL_CRITICAL_ENTITY_ID]
        return entity_id and self._hass.states.get(entity_id).state == STATE_ON

    @staticmethod
    def _round_to_next_five_minutes(now):
        """Rounds the provided time to the next 5 minutes."""
        matching_seconds = [0]
        matching_minutes = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
        matching_hours = dt_util.parse_time_expression("*", 0, 23)
        return dt_util.find_next_time_expression_time(
            now, matching_seconds, matching_minutes, matching_hours
        )

    async def _switch_pool_pump(self, target_state):
        switch_entity_id = self._hass.data[DOMAIN][ATTR_SWITCH_ENTITY_ID]
        if not switch_entity_id:
            _LOGGER.error("Switch entity id must be provided")
            return
        switch = self._hass.states.get(switch_entity_id)
        if switch:
            if switch.state == target_state:
                # Already in the correct state
                _LOGGER.debug("Switch is in correct state: %s", target_state)
            else:
                # Not in the correct state
                data = {ATTR_ENTITY_ID: switch_entity_id}
                if target_state == STATE_ON:
                    await self._hass.services.async_call(
                        "homeassistant", SERVICE_TURN_ON, data
                    )
                else:
                    await self._hass.services.async_call(
                        "homeassistant", SERVICE_TURN_OFF, data
                    )
                _LOGGER.info(
                    "Switching pool pump from '%s' to '%s'", switch.state, target_state
                )
        else:
            _LOGGER.warning("Switch unavailable: %s", switch_entity_id)


class Run:
    """Represents a single run of the pool pump."""

    def __init__(self, start_time, duration_in_minutes):
        """Initialise run."""
        self._start_time = dt_util.as_local(start_time)
        self._duration = duration_in_minutes

    def __repr__(self):
        """Return string representation of this feed."""
        return "<{}(start={}, stop={}, duration={})>".format(
            self.__class__.__name__, self.start_time, self.stop_time, self.duration
        )

    @property
    def duration(self):
        """Return duration of this run."""
        return self._duration

    @property
    def start_time(self):
        """Return start time of this run."""
        return self._start_time

    @property
    def stop_time(self):
        """Return stop time of this run."""
        return self.start_time + timedelta(minutes=self.duration)

    def run_now(self, time):
        """Check if the provided time falls within this run's timeframe."""
        return self.start_time <= time < self.stop_time

    def is_next_run(self, time):
        """Check if this is the next run after the provided time."""
        return time <= self.stop_time

    def pretty_print(self):
        """Provide a usable representation of start and stop time."""
        if self.start_time.day != dt_util.now().day:
            start = self.start_time.strftime("%a, %H:%M")
        else:
            start = self.start_time.strftime("%H:%M")
        end = self.stop_time.strftime("%H:%M")
        return "{} - {}".format(start, end)
