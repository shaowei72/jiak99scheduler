# Tour Guide Scheduler

A web-based scheduler application for managing tour guides at an F&B attraction. Built with Django 5.0 and SQLite.

## Features

- **Guide Management**: Support for full-time, part-time morning, and part-time afternoon guides
- **Schedule Creation**: Generate monthly schedules with 21 tour sessions per day (1.5-hour tours every 30 minutes from 10:00am-9:30pm)
- **Constraint Validation**: Automatic validation of guide type compatibility, break requirements, and availability
- **Manager Interface**: Powerful Django admin panel with custom actions for schedule management
- **Guide Portal**: Simple interface for guides to view schedules and mark availability
- **Standby System**: Assign standby guides for each day

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### Installation

1. Clone or download this repository

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Unix/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   python manage.py migrate
   ```

5. Generate tour time slots (creates 21 slots from 10:00am-9:30pm):
   ```bash
   python manage.py generate_tour_slots
   ```

6. Create a superuser account:
   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the application:
   - Admin interface: http://localhost:8000/admin/
   - Guide dashboard: http://localhost:8000/guides/dashboard/

## Usage

### For Managers

1. **Create Guide Profiles**:
   - Login to admin panel
   - Go to "Users" and create user accounts
   - Add guide profiles with guide type (FT/PTM/PTA) and phone number

2. **Generate Monthly Schedule**:
   ```bash
   python manage.py create_monthly_schedule --month 3 --year 2024
   ```
   This creates tour sessions for all days in the specified month (must be at least 2 weeks in advance).

3. **View Schedule Overview** (Recommended):
   - Click "Schedule Overview" in the navigation menu
   - Visual calendar showing all guides and time slots
   - Color-coded feasibility indicators:
     - **Green (✓)**: Slot is filled
     - **Yellow (⚠)**: Slot not yet assigned but can be filled
     - **Red (✗)**: Slot cannot be filled (no eligible guides)
   - Navigate between dates to view different days

4. **Auto-Assign Guides** (Optional but Recommended):
   - Use command: `python manage.py auto_schedule --date YYYY-MM-DD`
   - Or use "Auto-schedule guides" action in admin on Daily schedules
   - Algorithm automatically assigns guides optimally
   - Manual adjustments can be made afterwards if needed

5. **Manual Assignment** (Alternative to Auto-Assign):
   - Go to "Daily schedules" in admin
   - Select a date
   - Assign guides to tour sessions using inline editing
   - System automatically validates assignments (guide type, breaks, availability)

6. **Assign Standby Guide**:
   - For each daily schedule, assign one standby guide
   - Required before publishing
   - Auto-schedule command can do this automatically

7. **Publish Schedule**:
   - Select schedules in the list
   - Use "Publish selected schedules" action
   - Only published schedules are visible to guides

### For Guides

1. **View Dashboard**:
   - Login and view upcoming shifts and standby days
   - See shifts for the next 30 days

2. **Mark Availability**:
   - Click "Mark Availability"
   - Select date range (up to 3 months ahead)
   - Mark as available or unavailable
   - Add optional notes

3. **View Schedule**:
   - Click "My Schedule"
   - See weekly view of assigned tours
   - Navigate between weeks
   - Only published schedules are shown

## Guide Types

- **Full-time (FT)**: Can work any time slot (10:00am-9:30pm)
- **Part-time Morning (PTM)**: Can only work slots ending by 2:30pm
- **Part-time Afternoon (PTA)**: Can only work slots starting from 2:30pm onwards

## Validation Rules

The system enforces these constraints automatically:

1. **Guide Type Compatibility**: Guides can only be assigned to time slots compatible with their guide type
2. **30-Minute Break Requirement**: Guides must have at least 30 minutes break between tours
3. **Availability Check**: Guides must be marked as available for the date
4. **Standby Assignment**: Each day must have one standby guide before publishing

## Management Commands

### generate_tour_slots
Creates all tour time slots (10:00am-9:30pm, every 30 minutes, 1.5-hour tours).

```bash
python manage.py generate_tour_slots
```

Run this once during initial setup. Creates 21 time slots.

### create_monthly_schedule
Generates tour sessions for all days in a specified month.

```bash
# Generate for March 2024
python manage.py create_monthly_schedule --month 3 --year 2024

# Year is optional (defaults to current/next year based on month)
python manage.py create_monthly_schedule --month 3
```

Must be run at least 2 weeks in advance. Creates 21 sessions per day.

### auto_schedule
Automatically assigns guides to tour sessions for a specific date using an intelligent algorithm.

```bash
# Auto-schedule for today
python manage.py auto_schedule

# Auto-schedule for a specific date
python manage.py auto_schedule --date 2024-03-15

# Auto-schedule without assigning standby guide
python manage.py auto_schedule --date 2024-03-15 --no-assign-standby
```

The algorithm:
- Prioritizes filling the most constrained time slots first (slots with fewer eligible guides)
- Respects all validation rules (guide type, breaks, availability)
- Balances workload across guides
- Identifies slots that cannot be filled (shown in red in Schedule Overview)
- Optionally assigns a standby guide

**Note**: You can also trigger auto-scheduling from the admin panel using the "Auto-schedule guides for selected days" action on Daily schedules.

## Project Structure

```
tour_scheduler/
├── manage.py
├── requirements.txt
├── README.md
├── DESIGN.md                  # Implementation plan
├── db.sqlite3                 # Database (created after migrations)
├── config/                    # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── guides/               # Guide management
│   │   ├── models.py         # Guide, GuideAvailability
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── templates/
│   ├── scheduling/           # Scheduling logic
│   │   ├── models.py         # TourTimeSlot, TourSession, DailySchedule
│   │   ├── admin.py
│   │   ├── services.py       # Business logic
│   │   └── management/commands/
│   └── core/                 # Shared utilities
└── templates/                # Global templates
```

## Database Backup

The entire database is stored in a single file: `db.sqlite3`

To backup:
```bash
# Copy the database file
cp db.sqlite3 backup_YYYYMMDD.sqlite3

# Or export as JSON
python manage.py dumpdata > backup_YYYYMMDD.json
```

To restore from JSON backup:
```bash
python manage.py loaddata backup_YYYYMMDD.json
```

## Troubleshooting

### "No guide assigned" error when accessing guide dashboard
- Make sure your user account has a Guide profile
- Admin users can create Guide profiles in the admin panel

### Cannot create schedules for past months
- Schedules must be created at least 2 weeks in advance
- Use a future month that's at least 14 days away

### Validation errors when assigning guides
- Check guide type compatibility (PTM can't work afternoon, PTA can't work morning)
- Ensure guide has 1-hour break between tours
- Verify guide is marked as available for that date

### Cannot publish schedule
- All sessions must have assigned guides
- Standby guide must be assigned
- All validations must pass

## Development

This is Phase 1 of the Tour Guide Scheduler. The system is ready for local deployment and basic scheduling operations.

For deployment notes and upgrade paths, see [DESIGN.md](DESIGN.md).

## License

Proprietary - Internal use only
