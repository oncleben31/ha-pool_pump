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

On top of the orignal version by @exxamalte, this version can be installed by HACS
and you can use the [blueprint][blueprint] feature to quickly fork this repo and
have a working development environment in a container.

I will adapt it to my needs. At completion this plugin will compute the filtering
schedule taking into account the pool water temperature.

## Minimum requirements

* A switch supported in Home Assistant that can turn on/off power to your
  pool pump.

## Features

* Can control any switch that supports being turned on/off.
* Support for distinguishing three different switch modes:
    * Auto: Turn switch on/off automatically based on rules and configuration.
    * On: Turn switch on.
    * Off: Turn switch off.
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

1. Click `install`.
2. Modify your `configuration.yaml` as explain below.
3. Restart Home Assistant.


## Configuration is done in in configuration.yaml file

Minimal content in your `configuration.yaml` file is:

```yaml
pool_pump:
  switch_entity_id: input_boolean.fake_pump_switch
  pool_pump_mode_entity_id: input_select.pool_pump_mode
  swimming_season_entity_id: input_boolean.swimming_season
  run_pool_pump_hours_swimming_season_entity_id: input_number.run_pool_pump_hours_swimming_season
  run_pool_pump_hours_off_season_entity_id: input_number.run_pool_pump_hours_off_season
  # optional:
  water_level_critical_entity_id: input_boolean.fake_water_level_critical
```

All parameters are required except the last one `water_level_critical_entity_id`.

You will need to set some automations and inputs (input_boolean, input_select and input_numbers)
to use it. Please read [README.md](README.md) for additional documentation.

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
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge&label=HA%20Discord
[discord-fr-shield]: https://img.shields.io/discord/542746125292273674?style=for-the-badge&label=Discord%20francophone
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/custom-components/blueprint.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/oncleben31/ha-pool_pump.svg?style=for-the-badge
[releases]: https://github.com/oncleben31/ha-pool_pump/releases
