from django.contrib import admin
from .models import Brand, Campaign, Spend, DaypartingSchedule


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "daily_budget",
        "monthly_budget",
        "daily_spend",
        "monthly_spend",
        "is_active",
    )
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "status",
        "daily_budget",
        "monthly_budget",
        "daily_spend",
        "monthly_spend",
        "is_active",
    )
    search_fields = ("name", "brand__name")
    list_filter = ("status", "is_active", "brand")


@admin.register(Spend)
class SpendAdmin(admin.ModelAdmin):
    list_display = ("campaign", "amount", "date", "hour", "created_at")
    search_fields = ("campaign__name",)
    list_filter = ("date", "campaign")


@admin.register(DaypartingSchedule)
class DaypartingScheduleAdmin(admin.ModelAdmin):
    list_display = ("campaign", "day_of_week", "start_hour", "end_hour", "is_active")
    search_fields = ("campaign__name",)
    list_filter = ("day_of_week", "is_active", "campaign")
