from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ZenRefresh(hass.data[DOMAIN][entry.entry_id], entry)])

class ZenRefresh(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Actualiser"
    _attr_icon = "mdi:refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}
    async def async_press(self):
        await self.coordinator.async_request_refresh()
