from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.budget.models import Campaign, Spend
from apps.budget.service import process_ad_spend


class TestProcessAdSpend:
    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_basic(self, active_campaign: Campaign) -> None:
        initial_daily_spend = active_campaign.daily_spend
        initial_monthly_spend = active_campaign.monthly_spend
        amount = Decimal("10.00")

        process_ad_spend(active_campaign, amount)

        # Check spend record was created
        spend = Spend.objects.get(campaign=active_campaign)
        assert spend.amount == amount
        assert spend.date == timezone.now().date()
        assert spend.hour == 14

        # Check campaign totals were updated
        active_campaign.refresh_from_db()
        assert active_campaign.daily_spend == initial_daily_spend + amount
        assert active_campaign.monthly_spend == initial_monthly_spend + amount

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_daily_budget_exceeded(
        self, campaign_near_daily_limit: Campaign
    ) -> None:
        amount = Decimal("10.00")  # This will exceed the 50.00 daily budget
        process_ad_spend(campaign_near_daily_limit, amount)

        campaign_near_daily_limit.refresh_from_db()
        assert campaign_near_daily_limit.status == Campaign.Status.PAUSED
        assert campaign_near_daily_limit.pause_reason == "DAILY_BUDGET_EXCEEDED"
        assert campaign_near_daily_limit.is_active is False

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_monthly_budget_exceeded(
        self, campaign_near_monthly_limit: Campaign
    ) -> None:
        amount = Decimal("10.00")  # This will exceed the 500.00 monthly budget
        process_ad_spend(campaign_near_monthly_limit, amount)

        campaign_near_monthly_limit.refresh_from_db()
        assert campaign_near_monthly_limit.status == Campaign.Status.PAUSED
        assert campaign_near_monthly_limit.pause_reason == "MONTHLY_BUDGET_EXCEEDED"
        assert campaign_near_monthly_limit.is_active is False

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_transaction_atomicity(
        self, active_campaign: Campaign
    ) -> None:
        initial_daily_spend = active_campaign.daily_spend
        initial_monthly_spend = active_campaign.monthly_spend

        # Process a valid spend
        amount = Decimal("10.00")
        process_ad_spend(active_campaign, amount)

        # Verify both spend record and campaign totals were updated
        spend_count = Spend.objects.filter(campaign=active_campaign).count()
        assert spend_count == 1

        active_campaign.refresh_from_db()
        assert active_campaign.daily_spend == initial_daily_spend + amount
        assert active_campaign.monthly_spend == initial_monthly_spend + amount

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_multiple_spends(self, active_campaign: Campaign) -> None:
        amounts = [Decimal("5.00"), Decimal("10.00"), Decimal("15.00")]

        for amount in amounts:
            process_ad_spend(active_campaign, amount)

        # Check all spend records were created
        spends = Spend.objects.filter(campaign=active_campaign).order_by("created_at")
        assert len(spends) == 3

        for spend, amount in zip(spends, amounts):
            assert spend.amount == amount

        # Check campaign totals
        active_campaign.refresh_from_db()
        expected_total = sum(amounts)
        assert active_campaign.daily_spend == expected_total
        assert active_campaign.monthly_spend == expected_total

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_zero_amount(self, active_campaign: Campaign) -> None:
        initial_daily_spend = active_campaign.daily_spend
        initial_monthly_spend = active_campaign.monthly_spend
        amount = Decimal("0.00")

        process_ad_spend(active_campaign, amount)

        # Check spend record was created
        spend = Spend.objects.get(campaign=active_campaign)
        assert spend.amount == amount

        # Check campaign totals were updated (even with zero)
        active_campaign.refresh_from_db()
        assert active_campaign.daily_spend == initial_daily_spend + amount
        assert active_campaign.monthly_spend == initial_monthly_spend + amount

    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_large_amount(self, active_campaign: Campaign) -> None:
        amount = Decimal("100.00")  # Much larger than daily budget of 50.00

        process_ad_spend(active_campaign, amount)

        active_campaign.refresh_from_db()
        assert active_campaign.status == Campaign.Status.PAUSED
        assert active_campaign.pause_reason == "DAILY_BUDGET_EXCEEDED"
        assert active_campaign.is_active is False
        assert active_campaign.daily_spend == amount  # Should still be updated

    @pytest.mark.parametrize(
        "amount",
        [
            Decimal("0.01"),
            Decimal("1.00"),
            Decimal("10.50"),
            Decimal("49.99"),
        ],
    )
    @freeze_time("2024-01-15 14:30:00")
    def test_process_ad_spend_various_amounts(
        self, active_campaign: Campaign, amount: Decimal
    ) -> None:
        initial_daily_spend = active_campaign.daily_spend
        initial_monthly_spend = active_campaign.monthly_spend

        process_ad_spend(active_campaign, amount)

        active_campaign.refresh_from_db()
        assert active_campaign.daily_spend == initial_daily_spend + amount
        assert active_campaign.monthly_spend == initial_monthly_spend + amount
        assert (
            active_campaign.status == Campaign.Status.ACTIVE
        )  # Should still be active
