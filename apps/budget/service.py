from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.budget.models import Campaign, Spend


def process_ad_spend(campaign: Campaign, amount: Decimal) -> None:
    now = timezone.now()

    with transaction.atomic():
        # 1. Log new spend
        Spend.objects.create(
            campaign=campaign, amount=amount, date=now.date(), hour=now.hour
        )

        # 2. Update campaign totals
        campaign.daily_spend += amount
        campaign.monthly_spend += amount
        campaign.save(update_fields=["daily_spend", "monthly_spend"])

        # 3. Pause campaign if limits exceeded
        if campaign.daily_spend > campaign.daily_budget:
            campaign.status = Campaign.Status.PAUSED
            campaign.pause_reason = "DAILY_BUDGET_EXCEEDED"
            campaign.is_active = False
            campaign.save(update_fields=["status", "pause_reason", "is_active"])

        elif campaign.monthly_spend > campaign.monthly_budget:
            campaign.status = Campaign.Status.PAUSED
            campaign.pause_reason = "MONTHLY_BUDGET_EXCEEDED"
            campaign.is_active = False
            campaign.save(update_fields=["status", "pause_reason", "is_active"])
