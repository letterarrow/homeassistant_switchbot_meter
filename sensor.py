"""Platform for sensor integration."""
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_MAC,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_TIMEOUT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

SENSOR_TYPES = {
    DEVICE_CLASS_BATTERY: ["Battery", "%"],
    DEVICE_CLASS_HUMIDITY: ["Humidity", "%"],
    DEVICE_CLASS_TEMPERATURE: ["Temperature", TEMP_CELSIUS]
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Required(CONF_MAC): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(SENSOR_TYPES)]
        )
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config.get(CONF_NAME)
    mac_addr = config.get(CONF_MAC)
    dev = []
    for key in config[CONF_MONITORED_CONDITIONS]:
        dev.append(SwitchBotMeterSensor(name, key))
    add_entities(dev, True)


class SwitchBotMeterSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, key):
        """Initialize the sensor."""
        self._state = None
        self._name = name + " " + SENSOR_TYPES[key][0]
        self._unit_of_measurement = SENSOR_TYPES[key][1]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = 23
