# Jiak99 Planner

A comprehensive manager dashboard for scheduling tour guides and restaurant staff at an F&B attraction. Built with Django 5.0 and SQLite.

**Current Status:** v0.8 - Pre-user-testing release (70-80% complete)

## Overview

Jiak99 Planner is a **manager-only** scheduling tool that provides:
- Tour guide scheduling (11 tours/day, 10am-8pm)
- Restaurant staff scheduling (kitchen & serving, 10am-9:30pm)
- Auto-scheduling with intelligent algorithms
- Multiple view formats (timeline, grid, overview)
- Constraint validation and coverage checking

> **Note:** This is the manager tool. A separate application will be built for guides and staff to view their schedules.

## Features

### Tour Guide Scheduling
- **Guide Types**: Full-time, Part-time Morning, Part-time Afternoon
- **Operating Hours**: 10:00 AM - 8:00 PM (11 daily tours)
- **Tour Duration**: 1.5 hours per tour
- **Auto-Scheduling**: Intelligent algorithm with workload balancing
- **Validation**: Guide type compatibility, 30-min break requirements, availability checks
- **Multiple Views**: Timeline manager, Grid view, Read-only overview

### Restaurant Staff Scheduling
- **Staff Types**: Kitchen Staff, Serving Staff
- **Operating Hours**: 10:00 AM - 9:30 PM
- **Shift Patterns**: Mixed (4h + 8h shifts) or All 8h shifts
- **Coverage Requirements**: Minimum 2 kitchen + 2 serving staff at all times
- **Auto-Scheduling**: Optimal shift pattern generation
- **Multiple Views**: Timeline manager, Grid view

### Management Features
- Unified schedule dashboard
- Date navigation and filtering
- Auto-assign functionality for both schedulers
- Publish/unpublish schedules
- CSV export capabilities
- Date range availability management
- Role conflict validation

## Quick Start

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete installation instructions.

```bash
# Clone repository
git clone <repository-url>
cd Jiak99_App01

# Install dependencies
pip install -r requirements.txt

# Initialize database
python manage.py migrate
python manage.py generate_tour_slots

# Create admin account
python manage.py createsuperuser

# Run server
python manage.py runserver
```

Access at: **http://localhost:8000**

## Application Structure

```
/main/                              → Main landing page
/schedule/                          → Schedule management dashboard
├── /schedule/guide/                → Tour guide schedule manager
├── /schedule/guide/overview/       → Tour guide grid view
├── /schedule/restaurant/           → Restaurant staff timeline view
└── /schedule/restaurant/grid/      → Restaurant staff grid view
/admin/                             → Django admin panel
```

## User Roles

### Manager (Staff User)
- Access to all scheduling features
- Can create and manage schedules
- Can publish schedules
- Full admin panel access

### Guide/Staff (Future Separate App)
- View personal schedule
- Mark availability
- View standby assignments

## Guide Types & Constraints

### Full-time (FT)
- Can work any time slot (10:00 AM - 8:00 PM)
- No time restrictions

### Part-time Morning (PTM)
- Can only work slots ending by 2:30 PM
- Ideal for morning shifts

### Part-time Afternoon (PTA)
- Can only work slots starting from 2:30 PM onwards
- Ideal for afternoon/evening shifts

### Scheduling Rules
1. **30-minute break**: Required between tours
2. **Max 2 consecutive tours**: Prevents guide fatigue
3. **Max 4 tours/day**: Daily limit per guide
4. **1-hour break for 3+ tours**: Extended break requirement
5. **Guide type compatibility**: Auto-validated

## Restaurant Staff Scheduling

### Shift Patterns

**Pattern A: Mixed (Recommended)**
- 2 full-day shifts (8h): 10am-6pm, 1:30pm-9:30pm
- 2 half-day shifts (4h): 10am-2pm, 5:30pm-9:30pm
- Total: 24 hours coverage with 4 staff

**Pattern B: All 8-hour**
- 4 full-day shifts (8h)
- Total: 32 hours coverage with 4 staff
- Less efficient but simpler

### Coverage Requirements
- **Minimum**: 2 kitchen staff + 2 serving staff at all times
- **Validation**: System checks coverage for every 30-minute period
- **Auto-fix**: Auto-scheduler ensures requirements are met

## Management Commands

### Generate Tour Time Slots
Creates 11 tour time slots (10am-8pm, 1.5h tours).
```bash
python manage.py generate_tour_slots
```

### Auto-Schedule Restaurant Staff
Automatically assign staff to shifts.
```bash
python manage.py auto_schedule_restaurant --date 2026-02-17
```

## Technology Stack

- **Backend**: Django 5.0
- **Database**: SQLite (for single-user deployment)
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Python**: 3.11+

## Multi-Manager Deployment

⚠️ **Important:** The current SQLite setup is designed for **single-manager** use.

For multiple managers accessing the same schedules, you'll need:
1. Centralized web server deployment
2. PostgreSQL or MySQL database
3. Network/internet access for all managers

See [DEPLOYMENT.md](DEPLOYMENT.md) for multi-manager setup options.

## Data Backup

The database file `db.sqlite3` contains all schedule data.

**Backup:**
```bash
# Copy database file
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3

# Or export as JSON
python manage.py dumpdata > backups/backup_$(date +%Y%m%d).json
```

**Restore:**
```bash
# From database file
cp backups/db_20260217.sqlite3 db.sqlite3

# From JSON
python manage.py loaddata backups/backup_20260217.json
```

## Project Structure

```
Jiak99_App01/
├── manage.py
├── requirements.txt
├── README.md
├── DEPLOYMENT.md
├── db.sqlite3                      # Database (created after migrations)
├── config/                         # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── views.py                    # Main landing page view
├── apps/
│   ├── guides/                     # Tour guide management
│   │   ├── models.py               # Guide, GuideAvailability
│   │   ├── admin.py
│   │   ├── views.py                # (Hidden - for future app)
│   │   └── urls.py
│   ├── scheduling/                 # Core scheduling logic
│   │   ├── models.py               # TourSession, DailySchedule, RestaurantStaff, StaffShift
│   │   ├── views.py                # Schedule managers and grid views
│   │   ├── api_views.py            # AJAX API endpoints
│   │   ├── services.py             # Business logic and algorithms
│   │   ├── admin.py
│   │   ├── urls.py
│   │   ├── templates/
│   │   └── templatetags/           # Custom filters
│   ├── restaurant_staff/           # Restaurant staff admin organization
│   │   ├── models.py               # Proxy models
│   │   └── admin.py
│   └── core/                       # Shared utilities
└── templates/                      # Global templates
    ├── base.html                   # Base template with navigation
    └── main_landing.html           # Landing page
```

## Known Limitations

1. **Single-user database**: SQLite not suitable for concurrent access
2. **No real-time updates**: Manual page refresh required
3. **Basic auth**: Uses Django's built-in authentication
4. **Local deployment only**: No production server setup included

## Roadmap

### Completed (v0.8)
- ✅ Manager dashboard and navigation
- ✅ Tour guide scheduling (10am-8pm, 11 tours)
- ✅ Restaurant staff scheduling
- ✅ Auto-scheduling algorithms
- ✅ Multiple view formats
- ✅ Date range availability
- ✅ Role conflict validation

### Planned (v1.0)
- User testing feedback implementation
- Bug fixes and UX improvements
- Production deployment guide
- Performance optimizations

### Future
- Separate guide/staff mobile app
- Real-time notifications
- Advanced reporting and analytics
- Multi-manager concurrent access
- API for third-party integrations

## Support

For issues, questions, or deployment assistance:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for setup instructions
- Review this README for feature documentation
- Contact your system administrator

## License

Proprietary - Internal use only
