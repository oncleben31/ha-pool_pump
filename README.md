# Pool Pump Manager

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

[![Discord][discord-shield]][discord]
[![Discord francophone][discord-fr-shield]][discord-fr]
[![Community Forum][forum-shield]][forum]

_Component developped by using the amazing development template [blueprint][blueprint]._

This custom component for Home Assistant can be used to automatically control
a pool pump that is turned on/off by a switch that Home Assistant can control.

This component is based on the work of [@exxamalte](https://github.com/exxamalte/home-assistant-customisations/tree/master/pool-pump).
On top of the orignal version by @exxamalte, can be installed by HACS.
I will adapt it to my needs. At completion this plugin will compute the filtering
schedule taking into account the pool water temperature.

## Minimum requirements

* A switch supported in Home Assistant that can turn on/off power to your
  pool pump.

## Features

* Can control any switch that supports being turned on/off.
* Support for distinguishing three different switch modes:
** Auto: Turn switch on/off automatically based on rules and configuration.
** On: Turn switch on.
** Off: Turn switch off.
* Support for distinguishing between swimming season and off season.
* Separate target durations in hours configurable for each season type.
* Splits the target duration into two equal runs with a break in between.
* Automatically adjusts the runs to sunrise and sunset.
* Initialises an entity (`pool_pump.schedule`) that shows the current or next
  run of the pool pump.
* Optional: Support for a water level sensor to specify an entity that indicates if the
  pool has reached a critical water level in which case the pool pump should
  not run at all.

## Caveats

* Will limit the requested duration to the total amount of daylight
  (sunrise to sunset) available that day.
* Does not currently consider solar electricity production.

## Installation

### HACS installation

1. Install [HACS](https://hacs.xyz/). That way you get updates automatically.
2. Add this Github repository as custom repository in HACS settings.
3. search and install "Pool Pump Manger" in HACS and click `install`.
4. Modify your `configuration.yaml` as explain below.
5. Restart Home Assistant.

### Manual installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `pool_pump`.
4. Download _all_ the files from the `custom_components/pool_pump/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Modify your `configuration.yaml` as explain below
7. Restart Home Assistant

## Configuration

In the following examples we are assuming that you have a switch that is
connected to your pool pump and can turn that on/off already. That switch
is already integrated into Home Assistant with entity id `switch.pool_pump_switch`.

### Tri-state switch

The following configuration wraps the switch into a tri-state switch which
supports 3 modes - Auto, On, Off.
The automations are required to translate each state into an action on the
actual switch connected to the pool pump.

The last two automations are the ones that actually checks the pool pump state.
The first is triggered at regular intervals (5 minutes) from shortly before
sunrise to shortly after sunset. And the second automation is triggered by
certain events - the start of Home Assistant, immediately when you put the pool
pump into 'Auto' mode, and whenever several key levers and sensors change.

```yaml
input_select:
  pool_pump_mode:
    name: Pool Pump mode
    options:
      - 'Auto'
      - 'On'
      - 'Off'
    initial: 'Auto'
    icon: mdi:water-pump

automation:
  - alias: 'Pool Pump On'
    trigger:
      - platform: state
        entity_id: input_select.pool_pump_mode
        to: 'On'
    action:
      service: homeassistant.turn_on
      entity_id: switch.pool_pump_switch
  - alias: 'Pool Pump Off'
    trigger:
      - platform: state
        entity_id: input_select.pool_pump_mode
        to: 'Off'
    action:
      service: homeassistant.turn_off
      entity_id: switch.pool_pump_switch
  - alias: 'Check Pool Pump Periodically'
    trigger:
      - platform: time_pattern
        minutes: '/5'
        seconds: 00
    condition:
      condition: and
      conditions:
        - condition: sun
          after: sunrise
          after_offset: '-1:00:00'
        - condition: sun
          before: sunset
          before_offset: '1:30:00'
    action:
      service: pool_pump.check
  - alias: 'Check Pool Pump on Event'
    trigger:
      - platform: homeassistant
        event: start
      - platform: state
        entity_id: input_select.pool_pump_mode
        to: 'Auto'
      - platform: state
        entity_id:
          - input_boolean.swimming_season
          - input_number.run_pool_pump_hours_swimming_season
          - input_number.run_pool_pump_hours_off_season
          - binary_sensor.pool_water_level_critical
    action:
      service: pool_pump.check
```

### Swimming season

The following input boolean is there to distinguish between swimming season
and off season.

```yaml
input_boolean:
  swimming_season:
    name: Swimming Season
    icon: mdi:swim
```

### Number of hours to run the pool pump

The following configuration adds two sliders to select the number of hours
that the pool pump should run in swimming season and off season.
You may want to change min/max depending on your local needs.

```yaml
input_number:
  run_pool_pump_hours_swimming_season:
    name: Run Pool Pump in Swimming Season
    min: 1
    max: 8
    step: 1
  run_pool_pump_hours_off_season:
    name: Run Pool Pump in Off Season
    min: 1
    max: 6
    step: 1
```

### Critical Water Level

If the pool pump is fed through a skimmer then there is typically a minimum
water level under which the pool pump does not receive enough water anymore
and starts pulling in air which is not ideal.

The Pool Pump manager supports specifying an entity id using parameter
`water_level_critical_entity_id`. If that entity is `on` the pool pump will
not turn on, and if it is `off` then the manager will just follow its time/sun
based algorithm to turn the pool pump on or off.

## Pool Pump configuration

The pool pump component needs all the above entities as input to be able to
make the right decision and turn the pool pump on or off automatically.

```yaml
pool_pump:
  switch_entity_id: switch.pool_pump_switch
  pool_pump_mode_entity_id: input_select.pool_pump_mode
  swimming_season_entity_id: input_boolean.swimming_season
  run_pool_pump_hours_swimming_season_entity_id: input_number.run_pool_pump_hours_swimming_season
  run_pool_pump_hours_off_season_entity_id: input_number.run_pool_pump_hours_off_season
  water_level_critical_entity_id: binary_sensor.pool_water_level_critical
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[blueprint]: https://github.com/custom-components/blueprint
[commits-shield]: https://img.shields.io/github/commit-activity/y/oncleben31/ha-pool_pump.svg?style=for-the-badge
[commits]: https://github.com/oncleben31/ha-pool_pump/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-fr]: https://discord.gg/JeTFJzE$
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[discord-fr-shield]: https://img.shields.io/discord/542746125292273674?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/oncleben31/ha-pool_pump.svg?style=for-the-badge
[releases]: https://github.com/oncleben31/ha-pool_pump/releases
