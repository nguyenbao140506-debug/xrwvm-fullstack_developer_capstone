from django.conf import settings
from django.db import models


class Dealer(models.Model):
    """A dealership imported from OpenStreetMap with its source ID retained."""

    source_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=80, default="Kansas")
    state_code = models.CharField(max_length=2, default="KS")
    address = models.CharField(max_length=300, blank=True)
    zip_code = models.CharField(max_length=12, blank=True)
    short_name = models.CharField(max_length=160, blank=True)
    full_name = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=80, blank=True)
    website = models.URLField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Review(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="dealer_reviews",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=160, blank=True)
    text = models.CharField(max_length=2000)
    purchase = models.BooleanField(default=False)
    purchase_date = models.DateField(null=True, blank=True)
    car_make = models.CharField(max_length=80, blank=True)
    car_model = models.CharField(max_length=100, blank=True)
    car_year = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Review for {self.dealer} by {self.author}"
