"""
A component which allows you to update the IP adderesses of your Cloudflare DNS records.
For more details about this component, please refer to the documentation at
https://github.com/HalfDecent/HA-Custom_components/cloudflare
"""
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

REQUIREMENTS = ['pycfdns==0.0.1']

DOMAIN = 'cloudflare'

CONF_EMAIL = 'email'
CONF_KEY = 'key'
CONF_ZONE = 'zone'
CONF_RECORDS = 'records'

INTERVAL = timedelta(minutes=60)
TIMEOUT = 10
SERVICE_UPDATE = 'update_records'
COMPONENT_NAME = 'cloudflare'
COMPONENT_VERSION = '2.0.0'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_KEY): cv.string,
        vol.Required(CONF_ZONE): cv.string,
        vol.Optional(CONF_RECORDS, default='None'): 
            vol.All(cv.ensure_list, [cv.string]),
})
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Set up the component."""
    from pycfdns import CloudflareUpdater
    cfupdate = CloudflareUpdater()
    email = config[DOMAIN][CONF_EMAIL]
    key = config[DOMAIN][CONF_KEY]
    zone = config[DOMAIN][CONF_ZONE]
    records = config[DOMAIN][CONF_RECORDS]      

    def update_domain_interval(now):
        """Set up recuring update."""
        _update_cloudflare(cfupdate, email, key, zone, records)

    def update_domain_service(call):
        """Set up service for manual trigger."""
        _update_cloudflare(cfupdate, email, key, zone, records)

    track_time_interval(hass, update_domain_interval, INTERVAL)
    hass.services.register(
        DOMAIN, SERVICE_UPDATE, update_domain_service)
    return True

def _update_cloudflare(cfupdate, email, key, zone, records):
    """Update DNS records for a given zone."""
    _LOGGER.debug('Starting update for zone %s.', zone)
    #Set headers:
    headers = cfupdate.set_header(email,key)
    _LOGGER.debug('header data defined as: %s.', headers)
    #Get zoneID:
    zoneID = cfupdate.get_zoneID(headers, zone)
    _LOGGER.debug('zoneID is set to: %s.', zoneID)
    #Get records to update:
    updateRecords = cfupdate.get_recordInfo(headers, zoneID, zone, records)
    _LOGGER.debug('records: %s.', updateRecords)
    #Update records:
    result = cfupdate.update_records(headers, zoneID, updateRecords)
    _LOGGER.debug('Update for zone %s is complete.', zone)
    if result == True:
        result = "Update complete."
    _LOGGER.info(result)
    return True