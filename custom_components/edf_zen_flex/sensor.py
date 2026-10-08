"""États EDF, tarifs et compteurs annuels vérifiables."""

from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .model import TARIFF_KEYS

DAY_ICONS = {
    "eco": "mdi:cash",
    "sobriete": "mdi:cash-multiple",
    "bonus": "mdi:piggy-bank",
}

DIAGNOSTIC_KEYS = {
    "known_days",
    "eco",
    "sobriete",
    "bonus",
    "history_quality",
    "last_success",
    "missing_days",
    "published_tariff_date",
    "contract_tariff_date",
    "tariff_last_checked",
}
SENSOR_ICONS = {
    "known_days": "mdi:calendar-check",
    "last_success": "mdi:update",
    "history_quality": "mdi:check-decagram",
    "missing_days": "mdi:calendar-question",
    "published_tariff_date": "mdi:calendar-clock",
    "contract_tariff_date": "mdi:calendar-check-outline",
    "tariff_last_checked": "mdi:clock-check-outline",
}
PERIOD_ICONS = {"hc": "mdi:weather-night", "hp": "mdi:weather-sunny"}
TARIFF_ICONS = {
    "eco_hc": "mdi:weather-night",
    "eco_hp": "mdi:weather-sunny",
    "sobriete_hc": "mdi:moon-waning-crescent",
    "sobriete_hp": "mdi:white-balance-sunny",
}

SENSORS = [
    ("today", "Aujourd’hui"),
    ("tomorrow", "Demain"),
    ("eco", "Jours Éco observés"),
    ("sobriete", "Jours Sobriété observés"),
    ("bonus", "Jours Bonus observés"),
    ("known_days", "Jours connus"),
    ("last_success", "Dernière actualisation"),
    ("published_tariff_date", "Date de la dernière grille EDF publiée"),
    ("contract_tariff_date", "Date d’application des tarifs du contrat"),
    ("tariff_last_checked", "Dernière vérification des tarifs EDF"),
    ("eco_hc", "Tarif Éco heures creuses"),
    ("eco_hp", "Tarif Éco heures pleines"),
    ("sobriete_hc", "Tarif Sobriété heures creuses"),
    ("sobriete_hp", "Tarif Sobriété heures pleines"),
    ("current_price", "Prix actuel du kWh"),
    ("period", "Période tarifaire"),
    ("sobriete_consumed", "Jours Sobriété consommés"),
    ("sobriete_remaining", "Jours Sobriété restants"),
    ("eco_consumed", "Jours Éco passés"),
    ("eco_remaining", "Jours Éco restants minimum"),
    ("bonus_consumed", "Jours Bonus passés"),
    ("history_quality", "Fiabilité du décompte"),
    ("missing_days", "Jours à compléter"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZenSensor(coordinator, entry, key, name) for key, name in SENSORS
    )


class ZenSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "EDF Zen Flex",
            "manufacturer": "EDF",
        }
        self._attr_icon = SENSOR_ICONS.get(
            key, DAY_ICONS.get(key.split("_")[0], "mdi:calendar")
        )
        if key in DIAGNOSTIC_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if key in ("published_tariff_date", "contract_tariff_date"):
            self._attr_device_class = SensorDeviceClass.DATE
        elif key in ("last_success", "tariff_last_checked"):
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif key in ("today", "tomorrow", "period", "history_quality"):
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = (
                ["eco", "sobriete", "bonus"]
                if key in ("today", "tomorrow")
                else ["hc", "hp"]
                if key == "period"
                else ["complet", "incomplet", "incoherent"]
            )
        elif key in (*TARIFF_KEYS, "current_price"):
            self._attr_native_unit_of_measurement = "EUR/kWh"
            self._attr_suggested_display_precision = 4
            self._attr_icon = TARIFF_ICONS.get(key, "mdi:help-circle-outline")

    @property
    def icon(self):
        """Icônes explicites, avec distinction heures creuses/heures pleines."""
        if self.key in ("today", "tomorrow"):
            status = self.coordinator.snapshot()[self.key]["status"]
            return DAY_ICONS.get(status, "mdi:calendar-question")
        if self.key == "history_quality":
            return {"complet": "mdi:check-circle", "incomplet": "mdi:alert-circle-outline", "incoherent": "mdi:alert-octagon"}.get(
                self.coordinator.snapshot()["history_quality"], "mdi:help-circle-outline"
            )
        if self.key == "current_price":
            data = self.coordinator.snapshot()
            if (
                not self.coordinator.last_update_success
                or data["tariffs"]["current_price"] is None
            ):
                return "mdi:help-circle-outline"
            status = data["today"]["status"]
            tariff_day = "eco" if status == "bonus" else status
            period = data["tariffs"]["period"]
            return TARIFF_ICONS.get(f"{tariff_day}_{period}", "mdi:help-circle-outline")
        if self.key == "period":
            return PERIOD_ICONS.get(
                self.coordinator.snapshot()["tariffs"]["period"], "mdi:clock-outline"
            )
        return self._attr_icon

    @property
    def available(self):
        # Les paramètres tarifaires et compteurs locaux restent consultables pendant une panne.
        if self.key in ("today", "tomorrow", "current_price"):
            return self.coordinator.last_update_success
        return True

    @property
    def native_value(self):
        data = self.coordinator.snapshot()
        if self.key in ("today", "tomorrow"):
            return data[self.key]["status"]
        if self.key in data["counts"]:
            return data["counts"][self.key]
        if self.key in TARIFF_KEYS:
            return data["tariffs"]["rates"][self.key]
        if self.key in ("current_price", "period"):
            return data["tariffs"][self.key]
        if self.key == "contract_tariff_date":
            from datetime import date
            value = self.coordinator.settings.get("tariff_date")
            return date.fromisoformat(value) if value else None
        if self.key == "published_tariff_date":
            from datetime import date
            value = data.get(self.key)
            return date.fromisoformat(value) if value else None
        if self.key == "tariff_last_checked":
            value = data.get("tariff_last_checked")
            return datetime.fromisoformat(value) if value else None
        if self.key == "last_success":
            return datetime.fromisoformat(data[self.key]) if data[self.key] else None
        return data[self.key]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.snapshot()
        attrs = {"year": data["year"], "known_days": data["known_days"]}
        if self.key in ("today", "tomorrow"):
            attrs.update(
                {
                    "raw_code": data[self.key]["raw"],
                    "date": data["date" if self.key == "today" else "tomorrow_date"],
                }
            )
        if self.key == "today":
            attrs.update(
                {
                    "zen_flex_card": True,
                    "tomorrow": data["tomorrow"]["status"],
                    **{
                        key: data[key]
                        for key in (
                            "tomorrow_date",
                            "history",
                            "counts",
                            "last_success",
                            "published_tariff_date",
                            "tariff_last_checked",
                            "tariffs",
                            "sobriete_consumed",
                            "sobriete_remaining",
                            "eco_consumed",
                            "eco_remaining",
                            "bonus_consumed",
                            "bonus_history_quality",
                            "history_quality",
                            "missing_days",
                            "edf_available",
                            "baseline_active",
                            "baseline_expired",
                            "baseline_date",
                            "baseline_count",
                        )
                    },
                }
            )
        if self.key in (*TARIFF_KEYS, "current_price", "period"):
            attrs.update(
                {
                    key: data["tariffs"][key]
                    for key in (
                        "source",
                        "effective_date",
                        "confirmed",
                        "active",
                        "hc_periods",
                    )
                }
            )
            attrs["taxes"] = "TTC"
        if self.key in (
            "eco_consumed",
            "eco_remaining",
            "bonus_consumed",
            "sobriete_consumed",
            "sobriete_remaining",
            "history_quality",
            "missing_days",
        ):
            attrs.update(
                {
                    key: data[key]
                    for key in (
                        "history_quality",
                        "missing_days",
                        "sobriete_confirmed_minimum",
                        "baseline_active",
                        "baseline_expired",
                        "baseline_date",
                        "baseline_count",
                    )
                }
            )
            attrs["counted_through"] = data["date"]
            attrs["annual_sobriety_quota"] = 20
            attrs["bonus_history_quality"] = data["bonus_history_quality"]
            if self.key == "eco_remaining":
                attrs["bound"] = "minimum"
        return attrs
