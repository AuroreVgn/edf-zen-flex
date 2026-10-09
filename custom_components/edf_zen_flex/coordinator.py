"""Collecte EDF et calculs locaux, en heure de Paris."""
from datetime import datetime, timedelta
import hashlib
import json
import logging
from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from .api import fetch
from .tariffs import fetch_published_tariffs
from .model import TARIFF_KEYS
from homeassistant.components import persistent_notification
from .const import DOMAIN, DEFAULT_INTERVAL
from .model import PARIS, annual_summary, tariff_snapshot

class ZenCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.entry = entry
        super().__init__(hass, logging.getLogger(__name__), name=DOMAIN,
            update_interval=timedelta(minutes=self.settings.get("interval", DEFAULT_INTERVAL)))
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.history = {}
        self.last_success = None
        self.tariff_watch = {}

    @property
    def settings(self):
        """Lire les options enregistrées, sans copie périmée en mémoire."""
        return {**self.entry.data, **self.entry.options}

    async def async_load(self):
        stored = await self.store.async_load() or {}
        self.history = stored.get("history", {})
        self.last_success = stored.get("last_success")
        self.tariff_watch = stored.get("tariff_watch", {})

    async def _async_update_data(self):
        day = datetime.now(PARIS).date()
        try:
            result = await fetch(async_get_clientsession(self.hass), day)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"EDF indisponible ou réponse invalide: {err}") from err
        # Une requête chevauchant minuit reste associée à la date demandée.
        for key, target in (("today", day), ("tomorrow", day + timedelta(days=1))):
            if result[key]["status"] is not None:
                self.history[target.isoformat()] = {**result[key], "confirmed": key == "today"}
        cutoff = day.replace(year=day.year-2, day=1).isoformat()
        self.history = {key: value for key, value in self.history.items() if key >= cutoff}
        self.last_success = dt_util.utcnow().isoformat()
        await self.async_save_state()
        return {**result, "date": day.isoformat(), "tomorrow_date": (day+timedelta(days=1)).isoformat()}

    async def async_save_state(self):
        await self.store.async_save({"history": self.history,
                                     "last_success": self.last_success,
                                     "tariff_watch": self.tariff_watch})

    async def async_check_published_tariffs(self):
        """Check once per Paris day, independently from the EDF day-status API."""
        today = datetime.now(PARIS).date().isoformat()
        if self.tariff_watch.get("last_checked") == today:
            return
        try:
            published = await fetch_published_tariffs(async_get_clientsession(self.hass))
        except (ClientError, TimeoutError, ValueError, OSError) as err:
            logging.getLogger(__name__).warning("EDF tariff watch unavailable: %s", err)
            return  # Retry on the next scheduled run; never change contract rates.
        self.tariff_watch["last_checked"] = today
        self.tariff_watch["last_checked_at"] = dt_util.utcnow().isoformat()
        self.tariff_watch["published_date"] = published["tariff_date"]
        self.async_update_listeners()
        differences = [key for key in TARIFF_KEYS
                       if abs(float(published[key]) - float(self.settings[key])) > 0.0000001]
        changed = bool(differences) or published["tariff_date"] != self.settings.get("tariff_date")
        notification_id = f"{DOMAIN}_tariffs_{self.entry.entry_id}"
        if changed:
            fingerprint = hashlib.sha256(json.dumps({k: published[k] for k in (*TARIFF_KEYS, "tariff_date")}, sort_keys=True).encode()).hexdigest()
            if self.tariff_watch.get("last_notified") != fingerprint:
                lines = [f"- {key}: {self.settings[key]} → {published[key]} €/kWh" for key in differences]
                if published["tariff_date"] != self.settings.get("tariff_date"):
                    lines.append(f"- Date d'application : {published['tariff_date']}")
                persistent_notification.async_create(
                    self.hass,
                    "Une grille tarifaire publique EDF Zen Flex différente de celle enregistrée a été détectée. "
                    "Elle concerne potentiellement les nouvelles souscriptions : vérifiez votre contrat "
                    "avant toute modification.\n\n" + "\n".join(lines) +
                    "\n\nPour importer et confirmer : Paramètres → Appareils et services → "
                    "EDF Zen Flex → Configurer → Importer les tarifs.",
                    title="EDF Zen Flex : nouvelle grille tarifaire", notification_id=notification_id)
                self.tariff_watch["last_notified"] = fingerprint
        else:
            persistent_notification.async_dismiss(self.hass, notification_id)
            self.tariff_watch.pop("last_notified", None)
        await self.async_save_state()

    def snapshot(self, now=None):
        now = now or datetime.now(PARIS)
        day = now.astimezone(PARIS).date()
        tomorrow = (day + timedelta(days=1)).isoformat()
        unknown = {"status": None, "raw": None}
        today_value, tomorrow_value = unknown, unknown
        if self.last_update_success and self.data:
            for key, target in (("today", self.data["date"]), ("tomorrow", self.data["tomorrow_date"])):
                if target == day.isoformat():
                    today_value = self.data[key]
                if target == tomorrow:
                    tomorrow_value = self.data[key]
        return {"today": today_value, "tomorrow": tomorrow_value,
                "date": day.isoformat(), "tomorrow_date": tomorrow, "year": day.year,
                "history": self.history, "last_success": self.last_success,
                "edf_available": self.last_update_success,
                "published_tariff_date": self.tariff_watch.get("published_date"),
                "tariff_last_checked": self.tariff_watch.get("last_checked_at"),
                **annual_summary(self.history, day, self.settings),
                "tariffs": tariff_snapshot(self.settings, now, today_value["status"])}
