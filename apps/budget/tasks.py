from __future__ import annotations

import random
from decimal import Decimal

from celery import shared_task
from django.utils import timezone
from .models import Brand, Campaign
from .service import process_ad_spend


@shared_task
def pause_campaigns_exceeding_budget() -> None:
    for campaign in Campaign.objects.filter(
        is_active=True, status=Campaign.Status.ACTIVE
    ):
        campaign.check_budget_limits()


@shared_task
def reset_daily_budgets() -> None:
    for brand in Brand.objects.all():
        brand.reset_daily_spend()
    for campaign in Campaign.objects.all():
        campaign.reset_daily_spend()


@shared_task
def reset_monthly_budgets() -> None:
    for brand in Brand.objects.all():
        brand.reset_monthly_spend()
    for campaign in Campaign.objects.all():
        campaign.reset_monthly_spend()


@shared_task
def reactivate_eligible_campaigns() -> None:
    for campaign in Campaign.objects.filter(status=Campaign.Status.PAUSED):
        if campaign.can_resume():
            campaign.status = Campaign.Status.ACTIVE
            campaign.pause_reason = None
            campaign.save(update_fields=["status", "pause_reason"])


@shared_task
def enforce_dayparting() -> None:
    """
    Pauses campaigns outside their allowed dayparting schedule,
    and reactivates them if they are eligible again.
    """
    now = timezone.now()

    for campaign in Campaign.objects.filter(is_active=True):
        if not campaign.dayparting_schedules.exists():
            continue  # No schedule, skip enforcing

        # Check if current time is within allowed range
        if not campaign.is_within_dayparting(now):
            if (
                campaign.status != Campaign.Status.PAUSED
                or campaign.pause_reason != "OUTSIDE_DAYPARTING_HOURS"
            ):
                campaign.status = Campaign.Status.PAUSED
                campaign.pause_reason = "OUTSIDE_DAYPARTING_HOURS"
                campaign.save(update_fields=["status", "pause_reason"])
        else:
            # Reactivate only if it was paused due to dayparting AND budgets allow
            if (
                campaign.status == Campaign.Status.PAUSED
                and campaign.pause_reason == "OUTSIDE_DAYPARTING_HOURS"
            ):
                if campaign.can_resume():
                    campaign.status = Campaign.Status.ACTIVE
                    campaign.pause_reason = None
                    campaign.save(update_fields=["status", "pause_reason"])


@shared_task
def simulate_ad_spend() -> None:
    now = timezone.now()
    campaigns = Campaign.objects.filter(is_active=True, status=Campaign.Status.ACTIVE)
    for campaign in campaigns:
        if not campaign.dayparting_schedules.exists():
            continue  # No schedule means we don't simulate this campaign

        if not campaign.is_within_dayparting(now):
            continue  # Skip campaigns outside allowed hours

        # Simulate spend
        amount = Decimal(random.uniform(1.0, 5.0))
        process_ad_spend(campaign, amount)
