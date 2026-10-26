from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("dealerships", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dealer",
            name="zip_code",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="dealer",
            name="short_name",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="dealer",
            name="full_name",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AlterField(
            model_name="review",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="dealer_reviews",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="review",
            name="name",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="review",
            name="purchase",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="review",
            name="purchase_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="review",
            name="car_make",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="review",
            name="car_model",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="review",
            name="car_year",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
