from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, ENERGY_KILO_WATT_HOUR
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity

_LOGGER = logging.getLogger(__name__)

CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})

SCAN_INTERVAL = timedelta(minutes=60)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Falu Energi & Vatten sensor."""
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    api = FevSeAPI(username, password)
    async_add_entities([
        FevSeUsageSensor('Falu Energi & Vatten Usage', api)
    ], True)

class FevSeUsageSensor(SensorEntity):
    """Representation of a Falu Energi & Vatten usage sensor."""

    def __init__(self, name, api):
        """Initialize a Falu Energi & Vatten usage sensor."""
        self._name = name
        self._icon = 'mdi:power-socket-eu'
        self._unit_of_measurement = ENERGY_KILO_WATT_HOUR
        self._state_attributes = {}
        self._state = 0
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the extra attributes of the device."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        _LOGGER.debug('Fetching usage data...')
        data = []
        response = self._api.get_usage()
        if response:
            points = response.get('data', None)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days = 1)
            for point in points:
                usage = {
                    'date': datetime.fromisoformat(point['dateInterval']),
                    'usage': point['y']
                }

                if (usage['date'] == yesterday):
                    self._state_attributes['usage_yesterday'] = usage

                data.append(usage)

        self._state_attributes['usage_per_day'] = data

class FevSeAPI():
    """Falu Energi & Vatten API."""

    def __init__(self, username, password):
        """Initialize Falu Energi & Vatten API."""
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36'
        self._url_login = 'https://minasidor.fev.se/default.aspx'
        self._url_consumption = 'https://minasidor.fev.se/Consumption/Consumption.aspx'
        self._url_consumption_data = self._url_consumption + '/GetConsumptionViewModelOnLoad'
        self._url_contracts = 'https://minasidor.fev.se/Contract/Contracts.aspx'
        self._url_contracts_data = self._url_contracts + '/GetContractDetails'

    def get_usage(self):
        """Get usage data from the Falu Energi & Vatten API."""

        # Get the log in page
        response = self._session.get(self._url_login, headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'minasidor.fev.se',
            'Origin': 'https://minasidor.fev.se',
            'Pragma': 'no-cache',
            'User-Agent': self._userAgent
        })

        # Create the payload
        soup = BeautifulSoup(response.text, 'html.parser')
        payload = {
            'ctl00$MainContent$txtUser': self._username,
            'ctl00$MainContent$txtPassword': self._password,
            'ctl00$MainContent$btnLogin': 'Logga in',
            'chkRememberMe': 'on',
            '__VIEWSTATE': soup.find(id="__VIEWSTATE")['value'],
            '__VIEWSTATEGENERATOR': soup.find(id="__VIEWSTATEGENERATOR")['value']
        }

        # Post the payload to the site to log in
        self._session.post(self._url_login, data=payload)

        # Get the consumption page
        # TODO Maybe this can be removed if we send a complete payload with the post?
        #      Support for parameters would be a nice feature...
        self._session.get(self._url_consumption)

        # Get the data
        response = self._session.post(self._url_consumption_data, headers={
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Content-Type': 'application/json; charset=utf-8',
            'Host': 'minasidor.fev.se',
            'Origin': 'https://minasidor.fev.se',
            'Pragma': 'no-cache',
            'User-Agent': self._userAgent,
            'X-Requested-With': 'XMLHttpRequest'
        })

        if response.status_code == requests.codes.ok:
            data = response.json()
            return data['d']['DetailedConsumptionChart']['SeriesList'][0]
        else:
            _LOGGER.error('Failed to fetch usage data', response.text)
            return []
