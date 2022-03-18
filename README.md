# Home Assistant sensor for Falu Energi & Vatten
Custom component to get usage data from [Falu Energi & Vatten](https://fev.se/) for [Home Assistant](https://www.home-assistant.io/).

Falu Energi & Vatten doesn't have an open api, so we are acting as a Chrome user logging in with username (or customer number) and password.

Data is fetched every hour by default. This is kind of excessive since they only update the data once a day around 00:00.

## Installation
1. Navigate to your HA configuration folder (the one with `configuration.yaml` in it).
2. If you do not have a `custom_components` folder there, create it.
3. In the `custom_components` folder, create a new folder called `falu_energi_vatten`.
4. Download or clone the repository.
5. Place the files you downloaded in the new folder you created.

Using your HA configuration folder as a starting point, it should now look something like this:
```
custom_components/falu_energi_vatten/__init__.py
custom_components/falu_energi_vatten/manifest.json
custom_components/falu_energi_vatten/README.md
custom_components/falu_energi_vatten/sensor.py
```

## Setup
Add the sensor to `configuration.yaml`:

```yaml
sensor:
  - platform: falu_energi_vatten
    username: 123456 # Could be username or customer number
    password: password1
```

## Lovelace
Example chart with [ApexCharts Card](https://github.com/RomRider/apexcharts-card)

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Förbrukning per dag
graph_span: 30d
span:
  start: day
  offset: '-30d'
yaxis:
  - id: usage
    min: 0
apex_config:
  dataLabels:
    enabled: true
  stroke:
    width: 2
series:
  - entity: sensor.falu_energi_vatten_usage
    name: Förbrukning
    yaxis_id: usage
    type: line
    extend_to_end: false
    show:
      legend_value: false
    data_generator: |
      return entity.attributes.usage_per_day.map((entry) => {
        return [new Date(entry.date), entry.usage];
      });
```
