# Budget Management System - Pseudo-code

## Data Models

### Brand
```
Brand {
    id: UUID
    name: String
    daily_budget: Decimal
    monthly_budget: Decimal
    daily_spend: Decimal (current day)
    monthly_spend: Decimal (current month)
    is_active: Boolean
    created_at: DateTime
    updated_at: DateTime
}
```

### Campaign
```
Campaign {
    id: UUID
    brand: ForeignKey(Brand)
    name: String
    status: Enum(ACTIVE, PAUSED, COMPLETED)
    daily_budget: Decimal
    monthly_budget: Decimal
    daily_spend: Decimal (current day)
    monthly_spend: Decimal (current month)
    start_date: Date
    end_date: Date
    is_active: Boolean
    created_at: DateTime
    updated_at: DateTime
}
```

### Spend
```
Spend {
    id: UUID
    campaign: ForeignKey(Campaign)
    amount: Decimal
    date: Date
    hour: Integer (0-23)
    created_at: DateTime
}
```

### DaypartingSchedule
```
DaypartingSchedule {
    id: UUID
    campaign: ForeignKey(Campaign)
    day_of_week: Integer (0-6, Monday=0)
    start_hour: Integer (0-23)
    end_hour: Integer (0-23)
    is_active: Boolean
    created_at: DateTime
    updated_at: DateTime
}
```

## Core Logic

### 1. Tracking and Updating Daily/Monthly Spend
```
function update_spend(campaign_id, amount, date, hour):
    spend = create_spend_record(campaign_id, amount, date, hour)
    
    campaign = get_campaign(campaign_id)
    brand = campaign.brand
    
    // Update campaign spend
    if spend.date == today:
        campaign.daily_spend += amount
    if spend.date.month == current_month:
        campaign.monthly_spend += amount
    
    // Update brand spend
    if spend.date == today:
        brand.daily_spend += amount
    if spend.date.month == current_month:
        brand.monthly_spend += amount
    
    save(campaign)
    save(brand)
    
    // Check budget limits
    check_budget_limits(campaign)
    check_budget_limits(brand)
```

### 2. Budget Enforcement (Pausing/Resuming Campaigns)
```
function check_budget_limits(entity):
    if entity.daily_spend >= entity.daily_budget:
        pause_entity(entity, "DAILY_BUDGET_EXCEEDED")
    elif entity.monthly_spend >= entity.monthly_budget:
        pause_entity(entity, "MONTHLY_BUDGET_EXCEEDED")
    else:
        // Check if we can resume
        if entity.status == PAUSED and can_resume(entity):
            resume_entity(entity)

function pause_entity(entity, reason):
    entity.status = PAUSED
    entity.pause_reason = reason
    save(entity)

function resume_entity(entity):
    entity.status = ACTIVE
    entity.pause_reason = null
    save(entity)

function can_resume(entity):
    return entity.daily_spend < entity.daily_budget and 
           entity.monthly_spend < entity.monthly_budget
```

### 3. Daily/Monthly Resets
```
function reset_daily_budgets():
    brands = get_all_active_brands()
    campaigns = get_all_active_campaigns()
    
    for brand in brands:
        brand.daily_spend = 0
        save(brand)
    
    for campaign in campaigns:
        campaign.daily_spend = 0
        save(campaign)
    
    // Reactivate eligible campaigns
    reactivate_eligible_campaigns()

function reset_monthly_budgets():
    brands = get_all_active_brands()
    campaigns = get_all_active_campaigns()
    
    for brand in brands:
        brand.monthly_spend = 0
        save(brand)
    
    for campaign in campaigns:
        campaign.monthly_spend = 0
        save(campaign)
    
    // Reactivate eligible campaigns
    reactivate_eligible_campaigns()

function reactivate_eligible_campaigns():
    paused_campaigns = get_paused_campaigns()
    
    for campaign in paused_campaigns:
        if can_resume(campaign):
            resume_entity(campaign)
```

### 4. Dayparting Checks
```
function check_dayparting():
    campaigns = get_all_active_campaigns()
    current_time = now()
    current_day = current_time.weekday()
    current_hour = current_time.hour
    
    for campaign in campaigns:
        schedules = get_dayparting_schedules(campaign.id)
        
        if not schedules:
            // No dayparting restrictions
            continue
        
        is_allowed = false
        for schedule in schedules:
            if schedule.day_of_week == current_day and 
               schedule.start_hour <= current_hour <= schedule.end_hour:
                is_allowed = true
                break
        
        if not is_allowed:
            pause_entity(campaign, "OUTSIDE_DAYPARTING_HOURS")
        elif campaign.status == PAUSED and campaign.pause_reason == "OUTSIDE_DAYPARTING_HOURS":
            // Check if we can resume (budget-wise)
            if can_resume(campaign):
                resume_entity(campaign)
```

## Periodic Tasks

### Daily Tasks (run at 00:00 UTC)
1. Reset daily budgets for all brands and campaigns
2. Reactivate eligible campaigns
3. Check dayparting schedules

### Monthly Tasks (run on 1st of month at 00:00 UTC)
1. Reset monthly budgets for all brands and campaigns
2. Reactivate eligible campaigns

### Hourly Tasks (run every hour)
1. Check dayparting schedules
2. Update spend tracking (if real-time data available)

### Continuous Tasks (run every 5 minutes)
1. Check budget limits for all active campaigns
2. Pause campaigns that exceed budgets
3. Resume campaigns that are under budget 