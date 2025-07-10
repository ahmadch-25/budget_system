from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
import os
import django
from typing import TYPE_CHECKING

import factory
import pytest
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.budget.models import Brand, Campaign, DaypartingSchedule, Spend

if TYPE_CHECKING:
    from typing import Any

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_system.settings")
django.setup()


class BrandFactory(DjangoModelFactory[Brand]):
    class Meta:
        model = Brand

    name = factory.Sequence(lambda n: f"Brand {n}")
    daily_budget = Decimal("100.00")
    monthly_budget = Decimal("1000.00")
    daily_spend = Decimal("0.00")
    monthly_spend = Decimal("0.00")
    is_active = True


class CampaignFactory(DjangoModelFactory):
    class Meta:
        model = Campaign

    brand = factory.SubFactory(BrandFactory)
    name = factory.Sequence(lambda n: f"Campaign {n}")
    status = Campaign.Status.ACTIVE
    daily_budget = Decimal("50.00")
    monthly_budget = Decimal("500.00")
    daily_spend = Decimal("0.00")
    monthly_spend = Decimal("0.00")
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(
        lambda: (timezone.now() + timedelta(days=30)).date()
    )
    is_active = True
    pause_reason = None


class SpendFactory(DjangoModelFactory):
    class Meta:
        model = Spend

    campaign = factory.SubFactory(CampaignFactory)
    amount = Decimal("10.00")
    date = factory.LazyFunction(lambda: timezone.now().date())
    hour = factory.LazyFunction(lambda: timezone.now().hour)


class DaypartingScheduleFactory(DjangoModelFactory):
    class Meta:
        model = DaypartingSchedule

    campaign = factory.SubFactory(CampaignFactory)
    day_of_week = 0  # Monday
    start_hour = 9
    end_hour = 17
    is_active = True


@pytest.fixture
def brand() -> Brand:
    return BrandFactory()  # type: ignore[return-value]


@pytest.fixture
def campaign(brand: Brand) -> Campaign:
    return CampaignFactory(brand=brand)  # type: ignore[return-value]


@pytest.fixture
def active_campaign(brand: Brand) -> Campaign:
    return CampaignFactory(  # type: ignore[return-value]
        brand=brand,
        status=Campaign.Status.ACTIVE,
        daily_spend=Decimal("0.00"),
        monthly_spend=Decimal("0.00"),
    )


@pytest.fixture
def paused_campaign(brand: Brand) -> Campaign:
    return CampaignFactory(  # type: ignore[return-value]
        brand=brand, status=Campaign.Status.PAUSED, pause_reason="DAILY_BUDGET_EXCEEDED"
    )


@pytest.fixture
def campaign_with_dayparting(campaign: Campaign) -> Campaign:
    DaypartingScheduleFactory(campaign=campaign)
    return campaign


@pytest.fixture
def campaign_near_daily_limit(campaign: Campaign) -> Campaign:
    campaign.daily_spend = Decimal("45.00")
    campaign.save()
    return campaign


@pytest.fixture
def campaign_near_monthly_limit(campaign: Campaign) -> Campaign:
    campaign.monthly_spend = Decimal("495.00")
    campaign.save()
    return campaign


@pytest.fixture
def brand_near_daily_limit() -> Brand:
    brand = BrandFactory(daily_spend=Decimal("95.00"))
    return brand


@pytest.fixture
def brand_near_monthly_limit() -> Brand:
    brand = BrandFactory(monthly_spend=Decimal("995.00"))
    return brand


@pytest.fixture
def multiple_campaigns(brand: Brand) -> list[Campaign]:
    return [CampaignFactory(brand=brand, name=f"Campaign {i}") for i in range(3)]


@pytest.fixture
def multiple_brands() -> list[Brand]:
    return [BrandFactory(name=f"Brand {i}") for i in range(3)]


@pytest.fixture
def dayparting_schedule(campaign: Campaign) -> DaypartingSchedule:
    return DaypartingScheduleFactory(campaign=campaign)


@pytest.fixture
def spend_record(campaign: Campaign) -> Spend:
    return SpendFactory(campaign=campaign)
