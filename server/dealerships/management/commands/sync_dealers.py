import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dealerships.models import Dealer


STATE_CODES = {"Kansas": "KS", "KS": "KS"}


class Command(BaseCommand):
    help = "Import real car-dealership records tagged shop=car from OpenStreetMap."

    def add_arguments(self, parser):
        parser.add_argument("--state", default="Kansas", help="US state to import (currently Kansas).")

    def handle(self, *args, **options):
        state = options["state"].strip()
        state_code = STATE_CODES.get(state) or STATE_CODES.get(state.upper())
        if not state_code:
            raise CommandError("This importer currently supports Kansas (Kansas or KS).")
        query = (
            '[out:json][timeout:45];'
            f'area["ISO3166-2"="US-{state_code}"]["admin_level"="4"]->.state;'
            '('
            'node["shop"="car"](area.state);'
            'way["shop"="car"](area.state);'
            'relation["shop"="car"](area.state);'
            ');out center tags;'
        )
        try:
            response = requests.post(
                settings.OVERPASS_URL,
                data={"data": query},
                headers={
                    "Accept": "application/json",
                    "User-Agent": "car-dealership-capstone/1.0 (OpenStreetMap data importer)",
                },
                timeout=(10, 90),
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])
        except (requests.RequestException, ValueError) as exc:
            raise CommandError(f"OpenStreetMap Overpass request failed: {exc}") from exc

        created = updated = skipped = 0
        for element in elements:
            tags = element.get("tags", {})
            name = tags.get("name") or tags.get("brand") or tags.get("operator")
            if not name:
                skipped += 1
                continue
            address_parts = [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
                tags.get("addr:postcode", ""),
            ]
            address = " ".join(part.strip() for part in address_parts if part.strip())
            website = tags.get("contact:website") or tags.get("website") or ""
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            center = element.get("center", {})
            latitude = element.get("lat", center.get("lat"))
            longitude = element.get("lon", center.get("lon"))
            source_type = element.get("type", "unknown")
            source_id = f"osm:{source_type}:{element['id']}"
            source_url = f"https://www.openstreetmap.org/{source_type}/{element['id']}"
            _, was_created = Dealer.objects.update_or_create(
                source_id=source_id,
                defaults={
                    "name": name[:200],
                    "city": (
                        tags.get("addr:city") or tags.get("addr:town")
                        or tags.get("addr:suburb") or tags.get("addr:village") or ""
                    )[:120],
                    "state": "Kansas",
                    "state_code": state_code,
                    "address": address[:300],
                    "phone": (tags.get("contact:phone") or tags.get("phone") or "")[:80],
                    "website": website[:500],
                    "latitude": latitude,
                    "longitude": longitude,
                    "source_url": source_url,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"OpenStreetMap sync complete for Kansas: {created} created, {updated} updated, "
            f"{skipped} skipped without a name."
        ))
