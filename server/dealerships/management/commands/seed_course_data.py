import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

from dealerships.models import Dealer, Review


DATA_DIR = Path(__file__).resolve().parents[3] / "database" / "data"


class Command(BaseCommand):
    help = "Load the official course dealer, review, and car catalog fixtures."

    def handle(self, *args, **options):
        dealerships = json.loads((DATA_DIR / "dealerships.json").read_text(encoding="utf-8"))["dealerships"]
        reviews = json.loads((DATA_DIR / "reviews.json").read_text(encoding="utf-8"))["reviews"]

        for record in dealerships:
            Dealer.objects.update_or_create(
                pk=record["id"],
                defaults={
                    "source_id": f"course:{record['id']}",
                    "name": record["full_name"],
                    "city": record["city"],
                    "state": record["state"],
                    "state_code": record["st"],
                    "address": record["address"],
                    "zip_code": record["zip"],
                    "short_name": record["short_name"],
                    "full_name": record["full_name"],
                    "latitude": record["lat"],
                    "longitude": record["long"],
                    "source_url": "",
                },
            )

        for record in reviews:
            purchase_date = datetime.strptime(record["purchase_date"], "%m/%d/%Y").date()
            Review.objects.update_or_create(
                pk=record["id"],
                defaults={
                    "dealer_id": record["dealership"],
                    "author": None,
                    "name": record["name"],
                    "text": record["review"],
                    "purchase": record["purchase"],
                    "purchase_date": purchase_date,
                    "car_make": record["car_make"],
                    "car_model": record["car_model"],
                    "car_year": record["car_year"],
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {len(dealerships)} course dealerships and {len(reviews)} reviews."
        ))
