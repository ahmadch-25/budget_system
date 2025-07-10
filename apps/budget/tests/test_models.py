from __future__ import annotations

from decimal import Decimal


from apps.budget.models import Brand, Campaign, DaypartingSchedule, Spend


class TestBrand:
    def test_brand_creation(self, brand: Brand) -> None:
        assert brand.name.startswith("Brand")
        assert brand.daily_budget == Decimal("100.00")
        assert brand.monthly_budget == Decimal("1000.00")
        assert brand.daily_spend == Decimal("0.00")
        assert brand.monthly_spend == Decimal("0.00")
        assert brand.is_active is True

    def test_brand_str_representation(self, brand: Brand) -> None:
        assert str(brand) == brand.name

    def test_check_budget_limits_daily_exceeded(self, brand: Brand) -> None:
        brand.daily_spend = Decimal("100.00")
        brand.check_budget_limits()
        assert brand.is_active is False

    def test_check_budget_limits_monthly_exceeded(self, brand: Brand) -> None:
        brand.monthly_spend = Decimal("1000.00")
        brand.check_budget_limits()
        assert brand.is_active is False

    def test_check_budget_limits_reactivation(self, brand: Brand) -> None:
        brand.is_active = False
        brand.daily_spend = Decimal("50.00")
        brand.monthly_spend = Decimal("500.00")
        brand.check_budget_limits()
        assert brand.is_active is True

    def test_reset_daily_spend(self, brand: Brand) -> None:
        brand.daily_spend = Decimal("50.00")
        brand.reset_daily_spend()
        assert brand.daily_spend == Decimal("0.00")

    def test_reset_monthly_spend(self, brand: Brand) -> None:
        brand.monthly_spend = Decimal("500.00")
        brand.reset_monthly_spend()
        assert brand.monthly_spend == Decimal("0.00")


class TestCampaign:
    def test_campaign_creation(self, campaign: Campaign) -> None:
        assert campaign.name.startswith("Campaign")
        assert campaign.status == Campaign.Status.ACTIVE
        assert campaign.daily_budget == Decimal("50.00")
        assert campaign.monthly_budget == Decimal("500.00")
        assert campaign.daily_spend == Decimal("0.00")
        assert campaign.monthly_spend == Decimal("0.00")
        assert campaign.is_active is True
        assert campaign.pause_reason is None

    def test_campaign_str_representation(self, campaign: Campaign) -> None:
        assert str(campaign) == campaign.name

    def test_check_budget_limits_daily_exceeded(self, campaign: Campaign) -> None:
        campaign.daily_spend = Decimal("50.00")
        campaign.check_budget_limits()
        assert campaign.status == Campaign.Status.PAUSED
        assert campaign.pause_reason == "DAILY_BUDGET_EXCEEDED"

    def test_check_budget_limits_monthly_exceeded(self, campaign: Campaign) -> None:
        campaign.monthly_spend = Decimal("500.00")
        campaign.check_budget_limits()
        assert campaign.status == Campaign.Status.PAUSED
        assert campaign.pause_reason == "MONTHLY_BUDGET_EXCEEDED"

    def test_check_budget_limits_reactivation(self, paused_campaign: Campaign) -> None:
        paused_campaign.daily_spend = Decimal("25.00")
        paused_campaign.monthly_spend = Decimal("250.00")
        paused_campaign.check_budget_limits()
        assert paused_campaign.status == Campaign.Status.ACTIVE
        assert paused_campaign.pause_reason is None

    def test_can_resume_true(self, paused_campaign: Campaign) -> None:
        paused_campaign.daily_spend = Decimal("25.00")
        paused_campaign.monthly_spend = Decimal("250.00")
        assert paused_campaign.can_resume() is True

    def test_can_resume_false_daily_exceeded(self, paused_campaign: Campaign) -> None:
        paused_campaign.daily_spend = Decimal("50.00")
        paused_campaign.monthly_spend = Decimal("250.00")
        assert paused_campaign.can_resume() is False

    def test_can_resume_false_monthly_exceeded(self, paused_campaign: Campaign) -> None:
        paused_campaign.daily_spend = Decimal("25.00")
        paused_campaign.monthly_spend = Decimal("500.00")
        assert paused_campaign.can_resume() is False

    def test_reset_daily_spend(self, campaign: Campaign) -> None:
        campaign.daily_spend = Decimal("25.00")
        campaign.reset_daily_spend()
        assert campaign.daily_spend == Decimal("0.00")

    def test_reset_monthly_spend(self, campaign: Campaign) -> None:
        campaign.monthly_spend = Decimal("250.00")
        campaign.reset_monthly_spend()
        assert campaign.monthly_spend == Decimal("0.00")

    # @freeze_time("2024-01-15 14:30:00")  # Monday 2:30 PM
    # def test_is_within_dayparting_true(self, campaign_with_dayparting: Campaign) -> None:
    #     assert campaign_with_dayparting.is_within_dayparting() is True
    #
    # @freeze_time("2024-01-15 20:30:00")  # Monday 8:30 PM
    # def test_is_within_dayparting_false(self, campaign_with_dayparting: Campaign) -> None:
    #     assert campaign_with_dayparting.is_within_dayparting() is False
    #
    # @freeze_time("2024-01-16 14:30:00")  # Tuesday 2:30 PM
    # def test_is_within_dayparting_wrong_day(self, campaign_with_dayparting: Campaign) -> None:
    #     assert campaign_with_dayparting.is_within_dayparting() is False

    def test_is_within_dayparting_no_schedule(self, campaign: Campaign) -> None:
        assert campaign.is_within_dayparting() is False

    def test_campaign_brand_relationship(self, campaign: Campaign) -> None:
        assert campaign.brand is not None
        assert campaign in campaign.brand.campaigns.all()


class TestSpend:
    def test_spend_creation(self, spend_record: Spend) -> None:
        assert spend_record.campaign is not None
        assert spend_record.amount == Decimal("10.00")
        assert spend_record.hour is not None

    def test_spend_str_representation(self, spend_record: Spend) -> None:
        expected = f"{spend_record.campaign.name} - 10.00 on {spend_record.date} at {spend_record.hour}:00"
        assert str(spend_record) == expected

    def test_spend_campaign_relationship(self, spend_record: Spend) -> None:
        assert spend_record.campaign is not None
        assert spend_record in spend_record.campaign.spends.all()


class TestDaypartingSchedule:
    def test_dayparting_schedule_creation(
        self, dayparting_schedule: DaypartingSchedule
    ) -> None:
        assert dayparting_schedule.campaign is not None
        assert dayparting_schedule.day_of_week == 0
        assert dayparting_schedule.start_hour == 9
        assert dayparting_schedule.end_hour == 17
        assert dayparting_schedule.is_active is True

    def test_dayparting_schedule_str_representation(
        self, dayparting_schedule: DaypartingSchedule
    ) -> None:
        expected = f"{dayparting_schedule.campaign.name} - 0 9:00-17:00"
        assert str(dayparting_schedule) == expected

    def test_dayparting_schedule_campaign_relationship(
        self, dayparting_schedule: DaypartingSchedule
    ) -> None:
        """Test dayparting schedule-campaign relationship."""
        assert dayparting_schedule.campaign is not None
        assert (
            dayparting_schedule
            in dayparting_schedule.campaign.dayparting_schedules.all()
        )
