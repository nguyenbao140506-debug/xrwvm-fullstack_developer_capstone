from django.contrib import admin

from .models import Dealer, Review


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "source_id")
    list_filter = ("state",)
    search_fields = ("name", "city", "address")
    readonly_fields = ("source_id", "source_url", "updated_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("dealer", "author", "created_at")
    search_fields = ("dealer__name", "author__username", "text")
    readonly_fields = ("created_at",)
