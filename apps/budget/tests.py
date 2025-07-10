# Create your tests here.

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from apps.budget.models import Brand, Campaign, Spend, DaypartingSchedule
from apps.budget.utils.helpers import is_hour_in_range


class BrandModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
        )

    def test_brand_creation(self) -> None:
        """Test brand creation with default values."""
        self.assertEqual(self.brand.name, "Test Brand")
        self.assertEqual(self.brand.daily_budget, Decimal("100.00"))
        self.assertEqual(self.brand.monthly_budget, Decimal("1000.00"))
        self.assertEqual(self.brand.daily_spend, Decimal("0.00"))
        self.assertEqual(self.brand.monthly_spend, Decimal("0.00"))
        self.assertTrue(self.brand.is_active)

    def test_brand_str_representation(self) -> None:
        """Test string representation of brand."""
        self.assertEqual(str(self.brand), "Test Brand")

    def test_check_budget_limits_daily_exceeded(self) -> None:
        """Test brand deactivation when daily budget is exceeded."""
        self.brand.daily_spend = Decimal("100.00")
        self.brand.check_budget_limits()
        self.assertFalse(self.brand.is_active)

    def test_check_budget_limits_monthly_exceeded(self) -> None:
        """Test brand deactivation when monthly budget is exceeded."""
        self.brand.monthly_spend = Decimal("1000.00")
        self.brand.check_budget_limits()
        self.assertFalse(self.brand.is_active)

    def test_check_budget_limits_reactivation(self) -> None:
        """Test brand reactivation when under budget."""
        self.brand.is_active = False
        self.brand.daily_spend = Decimal("50.00")
        self.brand.monthly_spend = Decimal("500.00")
        self.brand.check_budget_limits()
        self.assertTrue(self.brand.is_active)

    def test_reset_daily_spend(self) -> None:
        """Test daily spend reset."""
        self.brand.daily_spend = Decimal("50.00")
        self.brand.reset_daily_spend()
        self.assertEqual(self.brand.daily_spend, Decimal("0.00"))

    def test_reset_monthly_spend(self) -> None:
        """Test monthly spend reset."""
        self.brand.monthly_spend = Decimal("500.00")
        self.brand.reset_monthly_spend()
        self.assertEqual(self.brand.monthly_spend, Decimal("0.00"))


class CampaignModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
        )

    def test_campaign_creation(self) -> None:
        """Test campaign creation with default values."""
        self.assertEqual(self.campaign.name, "Test Campaign")
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)
        self.assertEqual(self.campaign.daily_budget, Decimal("50.00"))
        self.assertEqual(self.campaign.monthly_budget, Decimal("500.00"))
        self.assertEqual(self.campaign.daily_spend, Decimal("0.00"))
        self.assertEqual(self.campaign.monthly_spend, Decimal("0.00"))
        self.assertTrue(self.campaign.is_active)
        self.assertIsNone(self.campaign.pause_reason)

    def test_campaign_str_representation(self) -> None:
        """Test string representation of campaign."""
        self.assertEqual(str(self.campaign), "Test Campaign")

    def test_check_budget_limits_daily_exceeded(self) -> None:
        """Test campaign pausing when daily budget is exceeded."""
        self.campaign.daily_spend = Decimal("50.00")
        self.campaign.check_budget_limits()
        self.assertEqual(self.campaign.status, Campaign.Status.PAUSED)
        self.assertEqual(self.campaign.pause_reason, "DAILY_BUDGET_EXCEEDED")

    def test_check_budget_limits_monthly_exceeded(self) -> None:
        """Test campaign pausing when monthly budget is exceeded."""
        self.campaign.monthly_spend = Decimal("500.00")
        self.campaign.check_budget_limits()
        self.assertEqual(self.campaign.status, Campaign.Status.PAUSED)
        self.assertEqual(self.campaign.pause_reason, "MONTHLY_BUDGET_EXCEEDED")

    def test_check_budget_limits_reactivation(self) -> None:
        """Test campaign reactivation when under budget."""
        self.campaign.status = Campaign.Status.PAUSED
        self.campaign.pause_reason = "DAILY_BUDGET_EXCEEDED"
        self.campaign.daily_spend = Decimal("25.00")
        self.campaign.monthly_spend = Decimal("250.00")
        self.campaign.check_budget_limits()
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)
        self.assertIsNone(self.campaign.pause_reason)

    def test_can_resume_true(self) -> None:
        """Test can_resume returns True when under budget."""
        self.campaign.daily_spend = Decimal("25.00")
        self.campaign.monthly_spend = Decimal("250.00")
        self.assertTrue(self.campaign.can_resume())

    def test_can_resume_false_daily_exceeded(self) -> None:
        """Test can_resume returns False when daily budget exceeded."""
        self.campaign.daily_spend = Decimal("50.00")
        self.campaign.monthly_spend = Decimal("250.00")
        self.assertFalse(self.campaign.can_resume())

    def test_can_resume_false_monthly_exceeded(self) -> None:
        """Test can_resume returns False when monthly budget exceeded."""
        self.campaign.daily_spend = Decimal("25.00")
        self.campaign.monthly_spend = Decimal("500.00")
        self.assertFalse(self.campaign.can_resume())

    def test_reset_daily_spend(self) -> None:
        """Test daily spend reset."""
        self.campaign.daily_spend = Decimal("25.00")
        self.campaign.reset_daily_spend()
        self.assertEqual(self.campaign.daily_spend, Decimal("0.00"))

    def test_reset_monthly_spend(self) -> None:
        """Test monthly spend reset."""
        self.campaign.monthly_spend = Decimal("250.00")
        self.campaign.reset_monthly_spend()
        self.assertEqual(self.campaign.monthly_spend, Decimal("0.00"))

    @freeze_time("2024-01-15 14:30:00")  # Monday 2:30 PM
    def test_is_within_dayparting_true(self) -> None:
        """Test dayparting check when within allowed hours."""
        DaypartingSchedule.objects.create(
            campaign=self.campaign,
            day_of_week=0,  # Monday
            start_hour=9,
            end_hour=17,
        )
        self.assertTrue(self.campaign.is_within_dayparting())

    @freeze_time("2024-01-15 20:30:00")  # Monday 8:30 PM
    def test_is_within_dayparting_false(self) -> None:
        """Test dayparting check when outside allowed hours."""
        DaypartingSchedule.objects.create(
            campaign=self.campaign,
            day_of_week=0,  # Monday
            start_hour=9,
            end_hour=17,
        )
        self.assertFalse(self.campaign.is_within_dayparting())

    @freeze_time("2024-01-16 14:30:00")  # Tuesday 2:30 PM
    def test_is_within_dayparting_wrong_day(self) -> None:
        """Test dayparting check on wrong day of week."""
        DaypartingSchedule.objects.create(
            campaign=self.campaign,
            day_of_week=0,  # Monday only
            start_hour=9,
            end_hour=17,
        )
        self.assertFalse(self.campaign.is_within_dayparting())

    def test_is_within_dayparting_no_schedule(self) -> None:
        """Test dayparting check when no schedule exists."""
        self.assertFalse(self.campaign.is_within_dayparting())


class SpendModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
        )

    def test_spend_creation(self) -> None:
        """Test spend creation."""
        spend = Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal("10.00"),
            date=timezone.now().date(),
            hour=14,
        )
        self.assertEqual(spend.campaign, self.campaign)
        self.assertEqual(spend.amount, Decimal("10.00"))
        self.assertEqual(spend.hour, 14)

    def test_spend_str_representation(self) -> None:
        """Test string representation of spend."""
        spend = Spend.objects.create(
            campaign=self.campaign,
            amount=Decimal("10.00"),
            date=timezone.now().date(),
            hour=14,
        )
        expected = f"{self.campaign.name} - 10.00 on {timezone.now().date()} at 14:00"
        self.assertEqual(str(spend), expected)


class DaypartingScheduleModelTest(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
        )

    def test_dayparting_schedule_creation(self) -> None:
        """Test dayparting schedule creation."""
        schedule = DaypartingSchedule.objects.create(
            campaign=self.campaign,
            day_of_week=0,  # Monday
            start_hour=9,
            end_hour=17,
        )
        self.assertEqual(schedule.campaign, self.campaign)
        self.assertEqual(schedule.day_of_week, 0)
        self.assertEqual(schedule.start_hour, 9)
        self.assertEqual(schedule.end_hour, 17)
        self.assertTrue(schedule.is_active)

    def test_dayparting_schedule_str_representation(self) -> None:
        """Test string representation of dayparting schedule."""
        schedule = DaypartingSchedule.objects.create(
            campaign=self.campaign, day_of_week=0, start_hour=9, end_hour=17
        )
        expected = f"{self.campaign.name} - 0 9:00-17:00"
        self.assertEqual(str(schedule), expected)


class HelpersTest(TestCase):
    def test_is_hour_in_range_normal(self) -> None:
        """Test hour range check for normal ranges."""
        self.assertTrue(is_hour_in_range(9, 17, 14))  # 2 PM within 9 AM - 5 PM
        self.assertFalse(is_hour_in_range(9, 17, 20))  # 8 PM outside 9 AM - 5 PM
        self.assertTrue(is_hour_in_range(9, 17, 9))  # 9 AM at start
        self.assertFalse(is_hour_in_range(9, 17, 17))  # 5 PM at end (exclusive)

    def test_is_hour_in_range_wraparound(self) -> None:
        """Test hour range check for wraparound ranges (e.g., 10 PM - 2 AM)."""
        self.assertTrue(is_hour_in_range(22, 2, 23))  # 11 PM within 10 PM - 2 AM
        self.assertTrue(is_hour_in_range(22, 2, 1))  # 1 AM within 10 PM - 2 AM
        self.assertFalse(is_hour_in_range(22, 2, 14))  # 2 PM outside 10 PM - 2 AM
        self.assertTrue(is_hour_in_range(22, 2, 22))  # 10 PM at start
        self.assertFalse(is_hour_in_range(22, 2, 2))  # 2 AM at end (exclusive)
