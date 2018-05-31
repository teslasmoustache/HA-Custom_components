# custom_component to get info from alerts.weather.gov
![Version](https://img.shields.io/badge/version-1.0.0-green.svg?style=for-the-badge)

A component which allows you to get information from alerts.weather.gov. 

To get started:   
Put `/custom_components/sensor/weatheralerts.py` here:  
`<config directory>/custom_components/sensor/weatheralerts.py`  


Example configuration.yaml:  
```yaml
sensor:
  - platform: weatheralerts
    sameid: 2190400
```
 #### Sample overview
![Sample overview](overview.png)  
[Demo](https://ha-test-weatheralerts.halfdecent.io)
  
To find the sameid go to [http://www.nws.noaa.gov/nwr/coverage/county_coverage.html](http://www.nws.noaa.gov/nwr/coverage/county_coverage.html).