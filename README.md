# Budget Management System

A Django + Celery-based backend system for managing advertising budgets in an Ad Agency context.

## Features
- Track and update daily and monthly ad spend for brands and campaigns
- Automatically enable/disable campaigns based on budget limits
- Reset budgets at the start of each day and month, reactivating eligible campaigns
- Enforce "dayparting" (campaigns only run during allowed time windows)
- Admin interface for managing brands, campaigns, spends, and schedules
- Periodic background jobs using Celery and Celery Beat
- Full static typing (PEP 484, MyPy)
- Comprehensive test suite with pytest

## Tech Stack
- Django (ORM, admin, business logic)
- Celery (background/periodic tasks)
- SQLite (default, can use Postgres)
- Python static typing (PEP 484, MyPy)
- pytest (testing framework)
- factory-boy (test data generation)

## Setup & Installation

### Prerequisites
- Python 3.10+
- Redis (for Celery broker & backend)
- pip

### Install dependencies
```bash
pip install -r requirements.txt
```

### Database migrations
```bash
python manage.py migrate
```

### Create superuser (for admin)
```bash
python manage.py createsuperuser
```

### Run the Django server
```bash
python manage.py runserver
```

### Start Celery worker and beat
```bash
celery -A budget_system worker --loglevel=info
celery -A budget_system beat --loglevel=info
```

## Testing

### Running Tests
The project uses pytest for comprehensive testing with fixtures and factory-boy for test data generation.

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=apps --cov-report=html --cov-report=term-missing

# Run specific test files
pytest apps/budget/test_models.py
pytest apps/budget/test_service.py
pytest apps/budget/test_tasks.py
pytest apps/budget/test_integration.py

# Run tests by markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Test Structure
- `apps/budget/conftest.py` - Pytest fixtures and factory classes
- `apps/budget/test_models.py` - Unit tests for Django models
- `apps/budget/test_service.py` - Unit tests for service layer
- `apps/budget/test_tasks.py` - Unit tests for Celery tasks
- `apps/budget/test_integration.py` - Integration tests for complete workflows

### Test Coverage
The test suite covers:
- **Models**: Brand, Campaign, Spend, DaypartingSchedule
- **Business Logic**: Budget checking, pausing/resuming, dayparting
- **Service Layer**: Ad spend processing with transaction safety
- **Celery Tasks**: All periodic background jobs
- **Integration**: Complete workflows and edge cases
- **Utilities**: Helper functions for time range checking

### Test Data Generation
Uses factory-boy for creating test data:
- `BrandFactory` - Creates test brands with realistic defaults
- `CampaignFactory` - Creates test campaigns linked to brands
- `SpendFactory` - Creates test spend records
- `DaypartingScheduleFactory` - Creates test dayparting schedules

### Fixtures
Key pytest fixtures include:
- `brand` - Single test brand
- `campaign` - Single test campaign
- `active_campaign` - Active campaign ready for testing
- `paused_campaign` - Paused campaign for reactivation tests
- `campaign_with_dayparting` - Campaign with dayparting schedule
- `multiple_campaigns` - List of campaigns for batch testing
- `campaign_near_daily_limit` - Campaign near daily budget limit
- `campaign_near_monthly_limit` - Campaign near monthly budget limit

### Testing Best Practices Used
- **Fixtures**: Reusable test data and setup
- **Parametrized Tests**: Test multiple scenarios efficiently
- **Mocking**: Isolate units under test
- **Time Freezing**: Test time-dependent logic with `freeze_time`
- **Factory Pattern**: Generate realistic test data
- **Integration Tests**: Test complete workflows
- **Edge Cases**: Test boundary conditions and error scenarios

## Data Models

### Brand
- `name`: Brand name
- `daily_budget`, `monthly_budget`: Budget limits
- `daily_spend`, `monthly_spend`: Current spend
- `is_active`: Whether the brand is active

### Campaign
- Linked to a Brand
- `status`: ACTIVE, PAUSED, COMPLETED
- `daily_budget`, `monthly_budget`, `daily_spend`, `monthly_spend`
- `start_date`, `end_date`: Campaign duration
- `pause_reason`: Reason for pausing (budget, dayparting, etc.)

### Spend
- Linked to a Campaign
- `amount`, `date`, `hour`: 
The Spend model stores raw spend logs, which are later aggregated to enforce daily/monthly budgets and used for reporting. This separation of raw data from aggregated state (on Campaign) ensures auditability and flexibility.

### DaypartingSchedule
- Linked to a Campaign
- `day_of_week`, `start_hour`, `end_hour`: Allowed time windows

## Workflow Overview

### Daily (00:00 UTC)
- Reset daily budgets for all brands and campaigns
- Reactivate eligible campaigns
- Check dayparting schedules

### Monthly (1st of month, 00:00 UTC)
- Reset monthly budgets for all brands and campaigns
- Reactivate eligible campaigns

### Hourly
- Enforce dayparting (pause/resume campaigns based on allowed hours)

### Every 5 Minutes
- Check and update ad spend for all campaigns
- Pause campaigns that exceed budget
- Resume campaigns that are under budget

## Manual Budget Reset
You can manually reset all budgets with:
```bash
python manage.py reset_budgets
```

## Assumptions & Simplifications
- Spend records are created externally (e.g., via API or integration)
- No user-facing API (admin only)
- Dayparting is enforced hourly
- Redis is used for Celery broker/backend
- SQLite is default DB, can be swapped for Postgres

## Static Typing
- All code uses Python type hints
- `mypy.ini` config included
- Run type checks with:
```bash
mypy .
```

## Extra Notes
- All periodic jobs are managed by Celery Beat (no external schedulers)
- Admin interface is enabled for all models
- Designed for extensibility and clarity
- Comprehensive test suite ensures reliability
- Factory-boy fixtures make tests maintainable and realistic 