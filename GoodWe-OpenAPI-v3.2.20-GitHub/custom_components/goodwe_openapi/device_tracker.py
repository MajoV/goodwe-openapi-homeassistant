"""Stationary GoodWe power plants on the Home Assistant map."""
import math
from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    known = set()

    def add_plants():
        new = []
        for pid in (coordinator.data or {}).get('plants', {}):
            if pid not in known:
                known.add(pid)
                new.append(GoodWePlantTracker(coordinator, pid))
        if new:
            async_add_entities(new)

    add_plants()
    entry.async_on_unload(coordinator.async_add_listener(add_plants))


class GoodWePlantTracker(CoordinatorEntity, TrackerEntity):
    _attr_should_poll = False
    _attr_icon = 'mdi:solar-power'

    def __init__(self, coordinator, plant_id):
        super().__init__(coordinator)
        self.plant_id = plant_id
        self._attr_unique_id = f'goodwe_plant_location_{plant_id}'

    @property
    def name(self):
        plant = self.coordinator.data.get('plants', {}).get(self.plant_id, {})
        plant_name = plant.get('plantName') or self.plant_id
        client_number = self.coordinator.entry.options.get('client_numbers', {}).get(self.plant_id, '')
        return f'{client_number} - {plant_name}' if client_number else plant_name

    @property
    def source_type(self):
        return SourceType.GPS

    @property
    def latitude(self):
        return self.coordinator.data.get('plants', {}).get(self.plant_id, {}).get('latitude')

    @property
    def longitude(self):
        return self.coordinator.data.get('plants', {}).get(self.plant_id, {}).get('longitude')

    @property
    def available(self):
        return super().available and self.latitude is not None and self.longitude is not None

    @property
    def extra_state_attributes(self):
        """Show the plant's inverter status and PV output in the map popup.

        Multiple inverters: producing wins over waiting; otherwise Other/Unknown.
        Missing realtime readings must never be treated as zero production.
        """
        data = self.coordinator.data or {}
        devices = data.get('devices', {})
        values = data.get('values', {})
        statuses = []
        pv_watts = []
        for key, info in devices.items():
            if info.get('plant_id') != self.plant_id or info.get('type') != 1:
                continue
            realtime = values.get(key)
            if not isinstance(realtime, dict):
                continue
            raw_status = realtime.get('deviceStatus')
            try:
                statuses.append(int(raw_status))
            except (TypeError, ValueError):
                pass
            raw_power = realtime.get('pvPower')
            try:
                power = float(raw_power)
                if math.isfinite(power):
                    pv_watts.append(power * 1000)  # GoodWe pvPower is in kW.
            except (TypeError, ValueError):
                pass
        if 1 in statuses:
            status = 'Producing power'
        elif 0 in statuses:
            status = 'Wait mode'
        elif statuses:
            status = 'Other (' + ', '.join(str(x) for x in sorted(set(statuses))) + ')'
        else:
            status = 'Unknown'
        attributes = {
            'plant_id': self.plant_id,
            'stationary': True,
            'device_status': status,
        }
        if pv_watts:
            attributes['pv_power'] = round(sum(pv_watts), 1)
            attributes['pv_power_unit'] = 'W'
        return attributes
