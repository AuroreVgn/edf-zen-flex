"""Calculs purs : tarifs, plages horaires et couverture annuelle."""
from datetime import date, datetime, timedelta
import math
import re
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
TARIFF_KEYS = ("eco_hc", "eco_hp", "sobriete_hc", "sobriete_hp")
REFERENCE_RATES = {"eco_hc": 0.1595, "eco_hp": 0.2142, "sobriete_hc": 0.2142, "sobriete_hp": 0.7467}
REFERENCE_SOURCE = "https://particulier.edf.fr/fr/accueil/electricite-gaz/zen-flex.html"
DEFAULT_HC = "00:00-08:00,13:00-18:00,20:00-24:00"
STATUSES = ("eco", "sobriete", "bonus")


def parse_hc(value):
    """Intervalles [début, fin[, y compris ceux traversant minuit."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Renseigner au moins une plage HC")
    intervals = []
    for part in value.split(","):
        match = re.fullmatch(r"\s*(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})\s*", part)
        if not match:
            raise ValueError("Format attendu : 00:00-08:00,13:00-18:00,20:00-24:00")
        sh, sm, eh, em = map(int, match.groups())
        if sh > 23 or sm > 59 or eh > 24 or em > 59 or (eh == 24 and em):
            raise ValueError("Horaire invalide")
        start, end = sh * 60 + sm, eh * 60 + em
        if start == end:
            raise ValueError("Plage vide : début et fin identiques")
        if end > start:
            intervals.append((start, end))
        else:
            intervals.append((start, 1440))
            if end:
                intervals.append((0, end))
    intervals.sort()
    if any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
        raise ValueError("Les plages HC se chevauchent")
    return intervals


def period_at(now, hc):
    local = now.astimezone(PARIS)
    minute = local.hour * 60 + local.minute
    return "hc" if any(start <= minute < end for start, end in parse_hc(hc)) else "hp"


def validate_settings(settings, today):
    """Valide uniquement les réglages saisis, sans accès réseau."""
    parse_hc(settings.get("hc_periods", DEFAULT_HC))
    for key in TARIFF_KEYS:
        price = settings.get(key, REFERENCE_RATES[key])
        if not isinstance(price, (int, float)) or not math.isfinite(price) or not 0 <= price <= 10:
            raise ValueError("Tarif invalide")
    date.fromisoformat(settings.get("tariff_date", "2026-09-15"))
    if settings.get("baseline_enabled"):
        until = date.fromisoformat(settings["baseline_date"])
        count = settings["baseline_count"]
        if until.year != today.year or until > today:
            raise ValueError("Le compteur initial doit concerner l’année en cours et une date passée ou aujourd’hui")
        if not isinstance(count, int) or not 0 <= count <= min(20, (until - date(today.year, 1, 1)).days + 1):
            raise ValueError("Compteur initial invalide")

        bonus = settings.get("baseline_bonus_count")
        if bonus is not None and (not isinstance(bonus, int) or not 0 <= bonus <= (until-date(today.year,1,1)).days+1-count):
            raise ValueError("Compteur Bonus initial invalide")


def tariff_snapshot(settings, now, status):
    rates = {key: settings.get(key, REFERENCE_RATES[key]) for key in TARIFF_KEYS}
    period = period_at(now, settings.get("hc_periods", DEFAULT_HC))
    confirmed = bool(settings.get("tariffs_confirmed", False))
    effective = settings.get("tariff_date", "2026-09-15")
    active = confirmed and date.fromisoformat(effective) <= now.astimezone(PARIS).date()
    kind = "eco" if status == "bonus" else status
    price = rates[f"{kind}_{period}"] if active and kind in ("eco", "sobriete") else None
    return {"rates": rates, "period": period, "current_price": price, "confirmed": confirmed,
            "active": active, "effective_date": effective,
            "source": settings.get("tariff_source", REFERENCE_SOURCE),
            "hc_periods": settings.get("hc_periods", DEFAULT_HC)}


def annual_summary(history, today, settings):
    """Solde après aujourd’hui ; les prévisions seules ne valident pas une journée."""
    first = date(today.year, 1, 1)
    valid = {key: record for key, record in history.items()
             if first.isoformat() <= key <= today.isoformat() and record.get("status") in STATUSES}
    counts = {kind: sum(record["status"] == kind for record in valid.values()) for kind in STATUSES}
    start, initial, baseline_active = first, 0, False
    until = None
    if settings.get("baseline_enabled"):
        until = date.fromisoformat(settings["baseline_date"])
        if until.year == today.year and until <= today:
            baseline_active = True
            initial = settings["baseline_count"]
            start = until + timedelta(days=1)
    tail = {key: record for key, record in valid.items() if key >= start.isoformat()}
    confirmed = {key: record for key, record in tail.items() if record.get("confirmed") is True}
    expected = max(0, (today - start).days + 1)
    missing = expected - len(confirmed)
    known_sobriete = initial + sum(record["status"] == "sobriete" for record in confirmed.values())
    conflict = known_sobriete > 20
    if baseline_active:
        prefix = {key: record for key, record in valid.items()
                  if key <= until.isoformat() and record.get("confirmed") is True}
        seen_red = sum(record["status"] == "sobriete" for record in prefix.values())
        covered_days = (until-first).days + 1
        conflict |= seen_red > initial or initial > covered_days - len(prefix) + seen_red
    reliable = missing == 0 and not conflict
    remaining = 20 - known_sobriete if reliable else None
    elapsed = (today-first).days + 1
    calendar_remaining = (date(today.year,12,31)-today).days
    bonus_initial = settings.get("baseline_bonus_count") if baseline_active else 0
    bonus_conflict = False
    if baseline_active and bonus_initial is not None:
        seen_bonus = sum(record["status"] == "bonus" for record in prefix.values())
        bonus_conflict = seen_bonus > bonus_initial or bonus_initial > covered_days-len(prefix)+seen_bonus
    bonus_reliable = reliable and bonus_initial is not None and not bonus_conflict
    bonus_consumed = bonus_initial + sum(record["status"] == "bonus" for record in confirmed.values()) if bonus_reliable else None
    return {"eco_consumed": elapsed-known_sobriete-bonus_consumed if bonus_reliable else None,
            "eco_remaining": max(0, calendar_remaining-remaining) if reliable else None,
            "bonus_consumed": bonus_consumed,
            "bonus_history_quality": "incoherent" if bonus_conflict else "complet" if bonus_reliable else "incomplet",
            "counts": counts, "known_days": len(valid), "missing_days": missing,
            "history_quality": "incoherent" if conflict else "complet" if reliable else "incomplet",
            "sobriete_consumed": known_sobriete if reliable else None,
            "sobriete_remaining": remaining, "sobriete_confirmed_minimum": known_sobriete,
            "baseline_active": baseline_active, "baseline_expired": bool(settings.get("baseline_enabled")) and not baseline_active,
            "baseline_date": until.isoformat() if until else None,
            "baseline_count": initial if baseline_active else None}
