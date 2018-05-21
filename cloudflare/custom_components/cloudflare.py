"""
A component which allows you to update the IP adderesses of your Cloudflare DNS records.
For more details about this component, please refer to the documentation at
https://github.com/HalfDecent/HA-Custom_components/cloudflare
"""
import time
import json
import asyncio
import logging
import requests
import voluptuous as vol
from datetime import timedelta
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval

DOMAIN = 'cloudflare'

CONF_EMAIL = 'email'
CONF_KEY = 'key'
CONF_ZONE = 'zone'
CONF_RECORDS = 'records'

INTERVAL = timedelta(minutes=60)
SERVICE_UPDATE = 'update_records'

COMPONENT_NAME = 'cloudflare'
COMPONENT_VERSION = '1.1.0'
BASE_URL = 'https://api.cloudflare.com/client/v4/zones'
EXT_IP_URL = 'https://api.ipify.org'

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

@asyncio.coroutine
def async_setup(hass, config):
    email = config[DOMAIN][CONF_EMAIL]
    key = config[DOMAIN][CONF_KEY]
    zone = config[DOMAIN][CONF_ZONE]
    records = config[DOMAIN][CONF_RECORDS]

    @asyncio.coroutine
    def update_domain_interval(now):
        result = yield from _update_cloudflare(email, key, zone, records)
        if not result:
            return False

    @asyncio.coroutine
    def update_domain_service(call):
        result = yield from _update_cloudflare(email, key, zone, records)
        if not result:
            return False

    async_track_time_interval(hass, update_domain_interval, INTERVAL)
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE, update_domain_service)
    return True

@asyncio.coroutine
def _update_cloudflare(email, key, zone, records):
    _LOGGER.info('Starting update for zone %s.', zone)
    headers = {
        'X-Auth-Email': email,
        'X-Auth-Key': key, 
        'Content-Type': 'application/json'
        }
    yield from _update_cloudflare_get_zone(headers, zone, records)
    _LOGGER.info('Update for zone %s is complete.', zone)
    return True
    
@asyncio.coroutine
def _update_cloudflare_get_zone(headers, zone, records):
    _LOGGER.debug('Starting function _update_cloudflare_get_zone')
    zoneIDurl = BASE_URL + '?name=' + zone
    zoneID = requests.get(zoneIDurl, headers=headers).json()['result'][0]['id']
    yield from _update_cloudflare_get_record(headers, zoneID, records, zone)
    return True
    
@asyncio.coroutine
def _update_cloudflare_get_record(headers, zoneID, records, zone):
    _LOGGER.debug('Starting function _update_cloudflare_get_record')
    if 'None' in records:
        _LOGGER.debug('Records not defined, scanning for records...')
        getRecordsUrl = BASE_URL + '/' + zoneID + '/dns_records&per_page=100'
        getRecords = requests.get(getRecordsUrl, headers=headers).json()['result']
        dev = []
        num = 0
        for items in getRecords:
            recordName = getRecords[num]['name']
            dev.append(recordName)
            num = num + 1
        records = dev
    for record in records:
        if zone in record:
            RecordFullname = record
        else:
            RecordFullname = record + '.' + zone
        recordIDurl = BASE_URL + '/' + zoneID + '/dns_records?name=' + RecordFullname
        recordInfo = requests.get(recordIDurl, headers=headers).json()['result'][0]
        RecordID = recordInfo['id']
        RecordType = recordInfo['type']
        RecordProxy = str(recordInfo['proxied'])
        RecordContent = recordInfo['content']
        if RecordProxy == 'True':
            proxied = True
        else:
            proxied = False
        yield from _update_cloudflare_update_record(headers, zoneID, RecordID, RecordType, RecordContent, proxied, RecordFullname)
    return True

@asyncio.coroutine
def _update_cloudflare_update_record(headers, zoneID, RecordID, RecordType, RecordContent, proxied, RecordFullname):
    _LOGGER.debug('Starting function _update_cloudflare_update_record for record %s', RecordFullname)
    IP = requests.get(EXT_IP_URL).text
    data = json.dumps({
        'id': zoneID,
        'type': RecordType,
        'name': RecordFullname,
        'content': IP,
        'proxied': proxied
        })

    fetchurl = BASE_URL + '/' + zoneID + '/dns_records/' + RecordID 
    if RecordContent != IP:
        if RecordType == 'A':
            result = requests.put(fetchurl, headers=headers, data=data).json()
            _LOGGER.debug('Update successfully: %s', result['success'])
        else:
            _LOGGER.debug('Record type for %s is not A, skipping update', RecordFullname)
    return True