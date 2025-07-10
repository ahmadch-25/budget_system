from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
import uuid

from apps.budget.utils.helpers import is_hour_in_range

if TYPE_CHECKING:
    pass


class Brand(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name: str = models.CharField(max_length=255)
    daily_budget: Decimal = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_budget: Decimal = models.DecimalField(max_digits=15, decimal_places=2)
    daily_spend: Decimal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    monthly_spend: Decimal = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    is_active: bool = models.BooleanField(default=True)
    created_at: timezone.datetime = models.DateTimeField(auto_now_add=True)
    updated_at: timezone.datetime = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    def check_budget_limits(self) -> None:
        if self.daily_spend >= self.daily_budget:
            self.is_active = False
            self.save(update_fields=["is_active"])
        elif self.monthly_spend >= self.monthly_budget:
            self.is_active = False
            self.save(update_fields=["is_active"])
        else:
            if not self.is_active:
                self.is_active = True
                self.save(update_fields=["is_active"])

    def reset_daily_spend(self) -> None:
        self.daily_spend = Decimal("0.0")
        self.save(update_fields=["daily_spend"])

    def reset_monthly_spend(self) -> None:
        self.monthly_spend = Decimal("0.0")
        self.save(update_fields=["monthly_spend"])


class Campaign(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        PAUSED = "PAUSED"
        COMPLETED = "COMPLETED"

    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    brand: Brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="campaigns"
    )
    name: str = models.CharField(max_length=255)
    status: str = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    daily_budget: Decimal = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_budget: Decimal = models.DecimalField(max_digits=15, decimal_places=2)
    daily_spend: Decimal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    monthly_spend: Decimal = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )
    start_date: timezone.datetime = models.DateField()
    end_date: timezone.datetime = models.DateField()
    is_active: bool = models.BooleanField(default=True)
    created_at: timezone.datetime = models.DateTimeField(auto_now_add=True)
    updated_at: timezone.datetime = models.DateTimeField(auto_now=True)
    pause_reason: Optional[str] = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    def check_budget_limits(self) -> None:
        if self.daily_spend >= self.daily_budget:
            self.status = self.Status.PAUSED
            self.pause_reason = "DAILY_BUDGET_EXCEEDED"
            self.save(update_fields=["status", "pause_reason"])
        elif self.monthly_spend >= self.monthly_budget:
            self.status = self.Status.PAUSED
            self.pause_reason = "MONTHLY_BUDGET_EXCEEDED"
            self.save(update_fields=["status", "pause_reason"])
        else:
            if self.status == self.Status.PAUSED and self.can_resume():
                self.status = self.Status.ACTIVE
                self.pause_reason = None
                self.save(update_fields=["status", "pause_reason"])

    def can_resume(self) -> bool:
        return (
            self.daily_spend < self.daily_budget
            and self.monthly_spend < self.monthly_budget
        )

    def reset_daily_spend(self) -> None:
        self.daily_spend = Decimal("0.0")
        self.save(update_fields=["daily_spend"])

    def reset_monthly_spend(self) -> None:
        self.monthly_spend = Decimal("0.0")
        self.save(update_fields=["monthly_spend"])

    def is_within_dayparting(self, now: Optional[datetime] = None) -> bool:
        now = now or timezone.now()
        current_day = now.weekday()
        current_hour = now.hour

        for schedule in self.dayparting_schedules.filter(is_active=True):
            if schedule.day_of_week != current_day:
                continue
            if is_hour_in_range(schedule.start_hour, schedule.end_hour, current_hour):
                return True
        return False


class Spend(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    campaign: Campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="spends"
    )
    amount: Decimal = models.DecimalField(max_digits=12, decimal_places=2)
    date: timezone.datetime = models.DateField()
    hour: int = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    created_at: timezone.datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["campaign", "date"]),
            models.Index(fields=["campaign", "date", "hour"]),
        ]

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.amount} on {self.date} at {self.hour}:00"


class DaypartingSchedule(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    campaign: Campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="dayparting_schedules"
    )
    day_of_week: int = models.PositiveSmallIntegerField()  # 0=Monday, 6=Sunday
    start_hour: int = models.PositiveSmallIntegerField()
    end_hour: int = models.PositiveSmallIntegerField()
    is_active: bool = models.BooleanField(default=True)
    created_at: timezone.datetime = models.DateTimeField(auto_now_add=True)
    updated_at: timezone.datetime = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.day_of_week} {self.start_hour}:00-{self.end_hour}:00"
