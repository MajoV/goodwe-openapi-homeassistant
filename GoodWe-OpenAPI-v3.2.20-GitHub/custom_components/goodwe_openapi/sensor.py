"""GoodWe OpenAPI sensors for the tested Porizek Adam plant."""
from dataclasses import dataclass
from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

@dataclass(frozen=True, kw_only=True)
class GWDescription(SensorEntityDescription):
    source: str = "inverter"
    field: str = ""
    multiplier: float = 1

SENSORS = [
    GWDescription(key='account_name', name='Account name', source='metadata', field='plant_name', icon='mdi:solar-power'),
    GWDescription(key='inverter_serial_number', name='Inverter serial number', source='metadata', field='sn', icon='mdi:identifier'),
    GWDescription(key='inverter_model', name='Inverter model', source='metadata', field='model', icon='mdi:information-outline'),
    GWDescription(key='pv_power', name='PV power', source='inverter', field='pvPower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='battery_power', name='Battery power', source='inverter', field='batteryPower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='battery_soc', name='Battery SOC', source='inverter', field='batterySoc1', native_unit_of_measurement='%', device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='battery_soh', name='Battery SOH', source='inverter', field='batterySoh1', native_unit_of_measurement='%', state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='battery_voltage', name='Battery voltage', source='inverter', field='batteryVoltage1', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='battery_current', name='Battery current', source='inverter', field='batteryCurrent1', native_unit_of_measurement='A', device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='battery_temperature', name='Battery temperature', source='inverter', field='batteryTemperature1', native_unit_of_measurement='°C', device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='max_charge_power', name='Max charge power', source='inverter', field='maxChargePower1', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='max_discharge_power', name='Max discharge power', source='inverter', field='maxDisChargePower1', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='load_power', name='Load power', source='inverter', field='loadpower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='ac_active_power', name='AC active power', source='inverter', field='acActivePower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='backup_power', name='Backup power', source='inverter', field='backupPower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='daily_generation', name='Daily generation', source='inverter', field='dailyGeneration', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL),
    GWDescription(key='total_generation', name='Total generation', source='inverter', field='totalGeneration', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    GWDescription(key='inner_temperature', name='Inverter temperature', source='inverter', field='innerTemperature', native_unit_of_measurement='°C', device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='device_status', name='Device status', source='inverter', field='deviceStatus'),
    GWDescription(key='grid_status', name='Grid connection status', source='inverter', field='gridConnStatus'),
    GWDescription(key='meter_active_power', name='Meter active power', source='meter', field='activePower', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='meter_frequency', name='Meter frequency', source='meter', field='frequency', native_unit_of_measurement='Hz', device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv1_voltage', name='PV1 voltage', source='inverter', field='dcVoltage1', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv1_current', name='PV1 current', source='inverter', field='dcCurrent1', native_unit_of_measurement='A', device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv2_voltage', name='PV2 voltage', source='inverter', field='dcVoltage2', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv2_current', name='PV2 current', source='inverter', field='dcCurrent2', native_unit_of_measurement='A', device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv3_voltage', name='PV3 voltage', source='inverter', field='dcVoltage3', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv3_current', name='PV3 current', source='inverter', field='dcCurrent3', native_unit_of_measurement='A', device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv4_voltage', name='PV4 voltage', source='inverter', field='dcVoltage4', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='pv4_current', name='PV4 current', source='inverter', field='dcCurrent4', native_unit_of_measurement='A', device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='ac_voltage_l1', name='AC voltage L1', source='inverter', field='acVoltage1', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='ac_voltage_l2', name='AC voltage L2', source='inverter', field='acVoltage2', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='ac_voltage_l3', name='AC voltage L3', source='inverter', field='acVoltage3', native_unit_of_measurement='V', device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    GWDescription(key='battery_total_charge', name='Battery total charge', source='inverter', field='batteryCharge1', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    GWDescription(key='battery_total_discharge', name='Battery total discharge', source='inverter', field='batteryDischarge1', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    GWDescription(key='meter_total_export', name='Meter total exported', source='meter', field='totalSellQ', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    GWDescription(key='meter_total_import', name='Meter total imported', source='meter', field='totalPurchaseQ', native_unit_of_measurement='kWh', device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
    GWDescription(key='battery_power_channel1', name='Battery channel 1 power', source='inverter', field='batteryPower1', native_unit_of_measurement='W', device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, multiplier=1000),
    GWDescription(key='battery_status', name='Battery status', source='inverter', field='batteryStatus1'),
    GWDescription(key='battery_connection', name='Battery connection', source='inverter', field='batteryConnection1'),
 ]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known = set()

    def meter_assignment(devices, pid):
        """Associate meters only with an unambiguous inverter serial number."""
        inverters = {key[2]: key for key, info in devices.items()
                     if key[0] == pid and info['type'] == 1}
        meters = [key for key, info in devices.items()
                  if key[0] == pid and info['type'] == 6]
        matches = {}
        for meter in meters:
            # GoodWe meter SN can have a prefix followed by the inverter SN.
            candidates = [sn for sn in inverters if meter[2].upper().endswith(sn.upper())]
            if len(candidates) == 1:
                matches.setdefault(candidates[0], []).append(meter)
        result = {sn: keys[0] for sn, keys in matches.items() if len(keys) == 1}
        # A single inverter and a single meter have an unambiguous plant-level
        # association even when GoodWe uses a different meter SN format.
        if len(inverters) == 1 and len(meters) == 1 and not result:
            result[next(iter(inverters))] = meters[0]
        return result

    def add_new():
        devices = (coordinator.data or {}).get('devices', {})
        inverters = sorted((key, info) for key, info in devices.items() if info['type'] == 1)
        created = []
        meter_maps = {pid: meter_assignment(devices, pid)
                      for pid, _, _ in (key for key, _ in inverters)}
        for key, info in inverters:
            pid, _, sn = key
            meter_key = meter_maps[pid].get(sn)
            for desc in SENSORS:
                source_key = meter_key if desc.source == 'meter' else key
                if source_key is None:
                    continue
                # Register all configured sensors regardless of realtime field availability.
                # Missing fields remain unknown; temporary fetch failures mark unavailable.
                identity = (pid, sn, desc.key)
                if identity not in known:
                    known.add(identity)
                    created.append(GoodWeSensor(coordinator, key, info, desc,
                                                meter_key if desc.source == 'meter' else None))
        if created:
            async_add_entities(created, update_before_add=False)

    async_add_entities([GoodWeDiscoverySensor(coordinator, entry)] + [
        GoodWeApiSensor(coordinator, entry, key) for key in (
            'today', 'hour', 'total', 'failed', 'last_call', 'by_endpoint')])
    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class GoodWeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, info, description, meter_key):
        super().__init__(coordinator)
        self.entity_description = description
        self.inverter_key = key
        self.meter_key = meter_key
        pid, _, sn = key
        self._attr_unique_id = f'{pid}_{sn}_{description.key}'
        model = info.get('model') or 'OpenAPI inverter'
        self._attr_device_info = {
            'identifiers': {(DOMAIN, f'{pid}:{sn}')},
            'name': sn,
            'manufacturer': 'GoodWe',
            'model': model,
            'serial_number': sn,
        }

    def _handle_coordinator_update(self):
        """Write to HA only when state or availability has changed."""
        current = (self.available, self.native_value)
        if getattr(self, '_last_published', object()) != current:
            self._last_published = current
            super()._handle_coordinator_update()

    @property
    def native_value(self):
        if self.entity_description.source == 'metadata':
            info = (self.coordinator.data or {}).get('devices', {}).get(self.inverter_key, {})
            if self.entity_description.field == 'plant_name':
                name = info.get('plant_name') or (self.coordinator.data or {}).get('plants', {}).get(self.inverter_key[0], {}).get('plantName')
                number = self.coordinator.entry.options.get('client_numbers', {}).get(self.inverter_key[0], '')
                return f'{number} - {name}' if number and name else name
            if self.entity_description.field == 'sn':
                return info.get('sn', self.inverter_key[2])
            if self.entity_description.field == 'model':
                realtime = (self.coordinator.data or {}).get('values', {}).get(self.inverter_key, {})
                return info.get('model') or next((realtime[k] for k in ('deviceModel', 'modelName', 'model', 'deviceTypeName', 'inverterModel') if isinstance(realtime.get(k), str) and realtime[k].strip()), None)
        values = (self.coordinator.data or {}).get('values', {})
        record = values.get(self.meter_key if self.meter_key else self.inverter_key, {})
        value = record.get(self.entity_description.field)
        if value is None or isinstance(value, (dict, list, bool)):
            return None
        # Translate only explicitly confirmed status codes; retain unknown codes unchanged.
        status_maps = {
            'battery_status': {'0': 'No battery', '1': 'Standby', '2': 'Discharge', '3': 'Charge'},
            'grid_status': {'1': 'Connected to grid'},
            'device_status': {'0': 'Wait mode', '1': 'Producing power'},
        }
        mapping = status_maps.get(self.entity_description.key)
        if mapping is not None:
            return mapping.get(str(value).strip(), value)
        if self.entity_description.key in ('battery_soc', 'battery_soh'):
            try:
                from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
                number = Decimal(str(value))
                if not number.is_finite():
                    return None
                return int(number.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            except (InvalidOperation, ValueError, TypeError):
                return None
        try:
            if self.entity_description.multiplier != 1:
                return round(float(value) * self.entity_description.multiplier, 3)
            return value
        except (ValueError, TypeError):
            return None

    @property
    def available(self):
        if self.entity_description.source == 'metadata':
            return self.inverter_key in (self.coordinator.data or {}).get('devices', {})
        values = (self.coordinator.data or {}).get('values', {})
        return self.coordinator.last_update_success and (self.meter_key if self.meter_key else self.inverter_key) in values


class GoodWeDiscoverySensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = False
    _attr_name = 'GoodWe Account Discovery'
    _attr_icon = 'mdi:cloud-search'

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f'{entry.entry_id}_discovery'

    def _handle_coordinator_update(self):
        current = (self.native_value, self.extra_state_attributes.get('message'),
                   self.extra_state_attributes.get('devices'))
        if getattr(self, '_last_published', object()) != current:
            self._last_published = current
            super()._handle_coordinator_update()

    @property
    def native_value(self):
        return len((self.coordinator.data or {}).get('plants', {}))

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {'message': data.get('discovery'), 'devices': len(data.get('devices', {})),
                'inverters': sum(d['type'] == 1 for d in data.get('devices', {}).values()),
                'meters': sum(d['type'] == 6 for d in data.get('devices', {}).values())}


class GoodWeApiSensor(CoordinatorEntity, SensorEntity):
    """Shared API counters, not per-inverter entities."""
    _attr_has_entity_name = False
    _attr_should_poll = False
    _NAMES = {
        'today': 'GoodWe API calls today',
        'hour': 'GoodWe API calls last hour',
        'total': 'GoodWe API calls total',
        'failed': 'GoodWe API calls failed',
        'last_call': 'GoodWe API last call',
        'by_endpoint': 'GoodWe API calls by endpoint',
    }

    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = self._NAMES[key]
        self._attr_unique_id = f'{entry.entry_id}_api_{key}'
        if key in ('today', 'hour', 'total', 'failed'):
            self._attr_native_unit_of_measurement = 'calls'
            self._attr_state_class = SensorStateClass.TOTAL if key in ('total', 'failed') else None
        if key == 'last_call':
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        stats = self.coordinator.api_stats()
        if self._key == 'last_call':
            return datetime.fromisoformat(stats['last_call']) if stats['last_call'] else None
        if self._key == 'by_endpoint':
            return sum(stats['by_endpoint'].values())
        return stats[self._key]

    @property
    def extra_state_attributes(self):
        if self._key == 'by_endpoint':
            return self.coordinator.api_stats()['by_endpoint']
        return None

    def _handle_coordinator_update(self):
        current = (self.native_value,
                   tuple(sorted((self.extra_state_attributes or {}).items())))
        if getattr(self, '_last_published', object()) != current:
            self._last_published = current
            super()._handle_coordinator_update()
