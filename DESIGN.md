# Tour Guide Scheduler - Implementation Plan

## Context

Building a web-based scheduler application for an F&B attraction to help managers schedule tour guides. The system needs to handle:
- 10 tour guides (full-time and part-time)
- 2-hour tours every 30 minutes (8:30am-8:00pm last tour)
- Complex constraints (1-hour breaks, guide type restrictions, availability tracking)
- Manager-focused interface with simple guide portal

This is Phase 1 focusing on basic scheduling without notifications or historical tracking.

## Technology Stack

- **Backend**: Django 5.0 with built-in admin panel
- **Database**: SQLite (single-file, no external dependencies)
- **Frontend**: Django templates with Bootstrap for styling
- **Deployment**: Local machine (`python manage.py runserver`)

**Rationale**: Django admin provides a powerful manager interface out-of-the-box, SQLite requires zero configuration, and the entire stack runs on a single machine with just Python installed.

## Architecture

### Project Structure
```
tour_scheduler/
├── manage.py
├── requirements.txt
├── README.md                  # Quick start guide
├── DESIGN.md                  # This implementation plan
├── db.sqlite3                 # Database (created after migrations)
├── config/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── guides/               # Guide management & availability
│   │   ├── models.py         # Guide, GuideAvailability
│   │   ├── admin.py
│   │   ├── views.py          # Dashboard, availability form
│   │   ├── forms.py
│   │   ├── urls.py
│   │   └── templates/
│   ├── scheduling/           # Core scheduling logic
│   │   ├── models.py         # TourTimeSlot, TourSession, DailySchedule
│   │   ├── admin.py          # Manager interface with custom actions
│   │   ├── services.py       # Business logic & validation
│   │   └── management/commands/
│   │       ├── generate_tour_slots.py
│   │       └── create_monthly_schedule.py
│   └── core/                 # Shared utilities
└── templates/                # Global templates
```

### Database Models

**guides/models.py**:
- `Guide`: User profile with guide_type (FT/PTM/PTA), phone, is_active
  - Guide types: Full-time, Part-time Morning (8:30am-2:30pm), Part-time Afternoon (2:30pm-10pm)
- `GuideAvailability`: Per-date availability (guide, date, is_available, notes)
  - Constraint: Can only mark availability up to 3 months ahead

**scheduling/models.py**:
- `TourTimeSlot`: Predefined tour times (start_time, end_time, duration_minutes)
  - Generated: 8:30am-10:30am, 9:00am-11:00am, ..., 8:00pm-10:00pm
- `TourSession`: Specific tour instance (date, time_slot, assigned_guide, status)
  - One guide per session
- `DailySchedule`: Daily metadata (date, standby_guide, is_published)
  - Must have 1 standby guide per day
- `ShiftSwapRequest`: Track swap requests requiring manager approval

### Business Logic (scheduling/services.py)

Key validation rules in `SchedulingService`:
1. **Guide type compatibility**: Check if guide can work time slot
   - Full-time: All slots
   - Part-time Morning: Slots ending by 2:30pm
   - Part-time Afternoon: Slots starting from 2:30pm

2. **Break requirement**: Validate 1-hour continuous break between assigned sessions

3. **Availability check**: Ensure guide marked available for that date

4. **Daily schedule validation**: All sessions assigned + standby guide present

Methods:
- `generate_tour_time_slots()`: Create all 30-min interval slots
- `generate_sessions_for_date(date)`: Create sessions for a date
- `generate_sessions_for_month(year, month)`: Bulk create for month
- `validate_session_assignment(session)`: Check all constraints
- `validate_daily_schedule(schedule)`: Validate entire day
- `get_available_guides_for_session(session)`: List eligible guides

## Implementation Steps

### Step 1: Project Setup
1. Copy this plan document to project as `DESIGN.md`
2. Create Django project: `django-admin startproject config .`
3. Create apps: `python manage.py startapp guides`, `python manage.py startapp scheduling`, `python manage.py startapp core`
4. Move apps to `apps/` directory
5. Update `config/settings.py`:
   - Add apps to INSTALLED_APPS
   - Set TIME_ZONE to local timezone
   - Configure STATIC files
   - Set LOGIN_REDIRECT_URL
6. Create requirements.txt: Django>=5.0,<5.1
7. Create README.md with quick start instructions

### Step 2: Database Models
1. Implement `guides/models.py`:
   - Guide model with GuideType choices
   - GuideAvailability with date validation
2. Implement `scheduling/models.py`:
   - TourTimeSlot with time validation
   - TourSession with guide assignment
   - DailySchedule with standby tracking
   - ShiftSwapRequest for future use
3. Run migrations: `python manage.py makemigrations && python manage.py migrate`

### Step 3: Business Logic
1. Implement `scheduling/services.py`:
   - SchedulingService class with all validation methods
   - Time slot generation logic
   - Session generation for dates/months
   - Constraint validation (breaks, availability, guide type)
2. Add validators in `scheduling/validators.py`:
   - Availability date range validation
   - Schedule creation timing validation

### Step 4: Manager Interface (Django Admin)
1. Configure `guides/admin.py`:
   - GuideAdmin: List display, filters, search
   - GuideAvailabilityAdmin: Date hierarchy, filters
2. Configure `scheduling/admin.py`:
   - TourTimeSlotAdmin: Simple list view
   - TourSessionAdmin:
     - Add validation_status column (shows ✓/✗ with errors)
     - Actions: validate_sessions, unassign_guides
   - DailyScheduleAdmin:
     - Inline TourSession editing
     - Add coverage_status column (shows assigned/total percentage)
     - Actions: publish_schedules, generate_sessions
   - ShiftSwapRequestAdmin: approve_swaps, reject_swaps actions

### Step 5: Management Commands
1. Create `scheduling/management/commands/generate_tour_slots.py`:
   - Calls SchedulingService.generate_tour_time_slots()
   - Creates all 30-min interval time slots
2. Create `scheduling/management/commands/create_monthly_schedule.py`:
   - Takes --year and --month arguments
   - Calls SchedulingService.generate_sessions_for_month()
   - Validates 2-week advance creation

### Step 6: Guide Interface
1. Create `guides/views.py`:
   - `guide_dashboard`: Show upcoming shifts and standby days
   - `mark_availability`: Form to set availability for date ranges
   - `my_schedule`: View assigned shifts (published schedules only)
2. Create `guides/forms.py`:
   - AvailabilityForm: start_date, end_date, is_available, notes
   - Validation: date range within 3 months, start < end
3. Create templates:
   - `templates/base.html`: Base layout with navigation
   - `guides/dashboard.html`: Overview of upcoming shifts
   - `guides/availability_form.html`: Calendar-style availability marking
   - `guides/my_schedule.html`: Weekly schedule view
4. Configure `guides/urls.py` and include in `config/urls.py`

### Step 7: Configuration & URLs
1. Update `config/urls.py`:
   - Admin at /admin/
   - Guide views at /guides/
   - Root redirects to dashboard
   - Customize admin site header/title
2. Create `templates/base.html` with basic Bootstrap styling

### Step 8: Initial Setup & Testing
1. Run `python manage.py generate_tour_slots`
2. Create superuser: `python manage.py createsuperuser`
3. Test admin interface:
   - Create test guides (FT, PTM, PTA)
   - Mark availability
   - Generate monthly schedule
   - Assign guides to sessions
   - Validate constraints
   - Publish schedules
4. Test guide interface:
   - Login as guide
   - View dashboard
   - Mark availability
   - View published schedule

## Critical Files

1. **apps/scheduling/services.py**: All business logic and validation
2. **apps/scheduling/models.py**: Core scheduling data models
3. **apps/guides/models.py**: Guide and availability models
4. **apps/scheduling/admin.py**: Manager interface with custom actions
5. **apps/scheduling/management/commands/create_monthly_schedule.py**: Operational workflow

## Verification Steps

### End-to-end Test Scenario
1. **Setup**:
   - Run `python manage.py generate_tour_slots` (creates 24 time slots)
   - Create 10 test guides via admin (mix of FT/PTM/PTA types)
   - Mark availability for guides for next 30 days

2. **Schedule Creation**:
   - Run `python manage.py create_monthly_schedule --month [next_month]`
   - Verify DailySchedule and TourSession records created
   - Check session count per day (should be 24 sessions/day)

3. **Manager Workflow**:
   - Login to admin as manager
   - Open DailySchedule for a date
   - Assign guides to TourSessions via inline editing
   - Verify validation:
     - PTM guide can't work 8pm tour (should show error)
     - Guide with back-to-back tours shows break error
   - Assign standby guide
   - Publish schedule

4. **Guide Workflow**:
   - Login as guide
   - View dashboard (shows upcoming assigned shifts)
   - Mark availability for next 2 weeks
   - View schedule (shows published shifts only)

5. **Constraint Validation**:
   - Assign guide to two tours with <1hr gap (should fail validation)
   - Assign PTM guide to afternoon slot (should fail)
   - Assign guide marked unavailable (should fail)
   - Try to publish without standby (should fail)

## Future Extensibility

Prepared for Phase 2:
- **Notifications**: Add `apps.notifications` app, hook into DailySchedule.publish()
- **Historical tracking**: All models have timestamps, add `apps.reports` for analytics
- **Multiple tour types**: Add TourType model, FK from TourSession
- **Automated scheduling**: Add algorithm in services.py to auto-assign guides

## Deployment Notes

**Local Deployment**:
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Generate time slots: `python manage.py generate_tour_slots`
7. Create superuser: `python manage.py createsuperuser`
8. Run server: `python manage.py runserver`
9. Access at http://localhost:8000/admin/

**Backup Strategy**:
- Copy `db.sqlite3` file regularly (entire database in one file)
- Export data: `python manage.py dumpdata > backup.json`

**Upgrade Path**:
- To PostgreSQL: Change DATABASE settings, re-run migrations (data migrates automatically)
- To production: Use gunicorn + nginx, update ALLOWED_HOSTS, set DEBUG=False
