"""Platform for sensor integration."""
from bluepy import btle
from datetime import timedelta
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_MAC,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

DEFAULT_INTERVAL = timedelta(seconds = 300)

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
    interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_INTERVAL)
    switchbot_data = SwitchBotData(mac_addr, interval)
    dev = []
    for key in config[CONF_MONITORED_CONDITIONS]:
        dev.append(SwitchBotMeterSensor(name, key, switchbot_data))
    add_entities(dev, True)


class SwitchBotMeterSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, key, switchbot_data):
        """Initialize the sensor."""
        self._key = key
        self._name = name + " " + SENSOR_TYPES[key][0]
        self._unit_of_measurement = SENSOR_TYPES[key][1]
        self._switchbot_data = switchbot_data

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._switchbot_data.get(self._key)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self._switchbot_data.update()

RX_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"
TX_UUID = "cba20003-224d-11e6-9fb8-0002a5d5c51b"
COMMAND_READ_DEV_INFO = b"\x57\x02"
COMMAND_READ_DATA = b"\x57\x0f\x31"
BYTE_BATTERY = 1
BYTE_HUMIDITY = 3
BYTE_TEMP_DEC = 1
BYTE_TEMP_INT = 2
BYTE_TEMP_SIG = 2
MASK_HUMIDITY = 0x7f
MASK_TEMP_DEC = 0x0f
MASK_TEMP_INT = 0x7f
MASK_TEMP_SIG = 0x80
class SwitchBotData:
    """Representation of a SwitchBot Meter data object."""

    def __init__(self, mac_addr, interval):
        self._mac_addr = mac_addr
        self.update = Throttle(interval)(self._update)
        self._data = {}
    
    def _update(self):
        peripheral = btle.Peripheral(self._mac_addr, btle.ADDR_TYPE_RANDOM)
        rx = peripheral.getCharacteristics(uuid = RX_UUID)[0]
        tx = peripheral.getCharacteristics(uuid = TX_UUID)[0]
        
        rx.write(COMMAND_READ_DEV_INFO, True)
        res = tx.read()
        self._data[DEVICE_CLASS_BATTERY] = res[BYTE_BATTERY]

        rx.write(COMMAND_READ_DATA, True)
        res = tx.read()
        self._data[DEVICE_CLASS_HUMIDITY] = res[BYTE_HUMIDITY] & MASK_HUMIDITY
        temp_dec = res[BYTE_TEMP_DEC] & MASK_TEMP_DEC
        temp_int = res[BYTE_TEMP_INT] & MASK_TEMP_INT
        is_temp_positive = res[BYTE_TEMP_SIG] & MASK_TEMP_SIG  == MASK_TEMP_SIG

        if is_temp_positive:
            self._data[DEVICE_CLASS_TEMPERATURE] = temp_int + temp_dec / 10
        else:
            self._data[DEVICE_CLASS_TEMPERATURE] = -(temp_int + temp_dec / 10)

        peripheral.disconnect()

    def get(self, key):
        return self._data.get(key)