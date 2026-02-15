# Development Setup Guide - Schedule Manager

**Project:** Tour Guide Scheduler - Schedule Manager Interface
**Start Date:** 2026-02-15
**Target:** 15-19 development days

---

## Current Environment Status

✅ **Already Installed:**
- Python 3.11.9
- Django 5.0.14
- SQLite database (db.sqlite3)
- Existing Tour Guide Scheduler application

---

## Phase 0: Initial Setup (Do This First)

### 1. Verify Environment

```bash
# Check Python version (should be 3.11+)
python --version

# Check Django version (should be 5.0+)
python -c "import django; print(django.get_version())"

# Check database exists
ls -lh db.sqlite3
```

**Expected:**
- Python 3.11.9 ✅
- Django 5.0.14 ✅
- db.sqlite3 exists ✅

### 2. Create Database Backup

**CRITICAL:** Do this before any changes!

```bash
# Create timestamped backup
cp db.sqlite3 "db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)"

# Verify backup created
ls -lh db.sqlite3.backup.*

# Also create JSON export
python manage.py dumpdata > backup_full.json
```

### 3. Check Git Status

```bash
# Current branch
git branch

# Status
git status

# Create feature branch for Schedule Manager
git checkout -b feature/schedule-manager
```

### 4. Update Requirements (Frontend Libraries)

**File:** `requirements.txt`

Current content:
```
Django>=5.0,<5.1
```

Add frontend dependencies (for later phases):
```
Django>=5.0,<5.1

# For CSV generation (already included in Python stdlib)
# No additional packages needed - we'll use Python's csv module

# Frontend assets will be loaded via CDN (see below)
```

**Note:** HTMX and Alpine.js will be loaded via CDN in templates, no pip install needed.

---

## Frontend Setup (For Phases 1-4)

### HTMX + Alpine.js via CDN

**Location:** Create/update base template for Schedule Manager

**File:** `apps/scheduling/templates/scheduling/base_schedule_manager.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Schedule Manager{% endblock %}</title>

    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'scheduling/schedule_manager.css' %}">

    {% block extra_css %}{% endblock %}
</head>
<body>
    <div id="schedule-manager-app">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.5/dist/cdn.min.js"></script>

    <!-- Custom JS -->
    <script src="{% static 'scheduling/schedule_manager.js' %}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

**CDN Versions:**
- Bootstrap 5.3.0 (CSS framework)
- HTMX 1.9.10 (AJAX interactions)
- Alpine.js 3.13.5 (Reactive state management)

**Checklist:**
- [ ] Template created (will be done in Phase 1)
- [ ] CDN links verified working
- [ ] Static files directory set up

---

## Project Structure Overview

```
Jiak99_App01/
├── apps/
│   ├── guides/           # Guide management (existing)
│   ├── scheduling/       # Scheduling logic (existing, will enhance)
│   │   ├── migrations/
│   │   ├── templates/
│   │   │   └── scheduling/
│   │   │       ├── schedule_overview.html (existing)
│   │   │       └── schedule_manager.html (NEW - Phase 1)
│   │   ├── static/
│   │   │   └── scheduling/
│   │   │       ├── schedule_manager.css (NEW - Phase 1)
│   │   │       └── schedule_manager.js (NEW - Phase 1)
│   │   ├── models.py     (UPDATE - Phase 0)
│   │   ├── views.py      (UPDATE - Phase 1)
│   │   ├── api_views.py  (NEW - Phase 2)
│   │   ├── admin.py      (UPDATE - Phase 6)
│   │   ├── services.py   (existing, reuse)
│   │   └── urls.py       (UPDATE - Phase 1)
│   └── core/             # Shared utilities (existing)
├── config/               # Django settings (existing)
├── templates/            # Global templates (existing)
├── db.sqlite3            # Database
├── db.sqlite3.backup.*   # Backups (NEW)
├── manage.py
├── requirements.txt
├── README.md
├── DESIGN.md
├── SCHEDULING_UI_SPEC.md         (NEW - Specification)
├── CSV_EXPORT_EXAMPLE.md         (NEW - CSV reference)
├── IMPLEMENTATION_SUMMARY.md     (NEW - Summary)
├── DEV_SETUP_GUIDE.md           (NEW - This file)
└── PHASE_0_CHECKLIST.md         (NEW - Task list)
```

---

## Development Workflow

### Daily Workflow

1. **Start of day:**
   ```bash
   # Activate virtual environment (if using one)
   # source venv/bin/activate  # Unix
   # venv\Scripts\activate     # Windows

   # Pull latest changes (if team)
   git pull origin feature/schedule-manager

   # Check database status
   python manage.py showmigrations
   ```

2. **During development:**
   ```bash
   # Run dev server
   python manage.py runserver

   # Open browser: http://localhost:8000/admin/
   ```

3. **After changes:**
   ```bash
   # Create migration if models changed
   python manage.py makemigrations

   # Apply migrations
   python manage.py migrate

   # Test changes
   python manage.py shell  # For model testing
   ```

4. **End of day:**
   ```bash
   # Commit progress
   git add .
   git commit -m "Phase X: [description of work done]"
   git push origin feature/schedule-manager

   # Backup database
   cp db.sqlite3 "db.sqlite3.backup.$(date +%Y%m%d)"
   ```

---

## Phase-by-Phase Setup Requirements

### Phase 0: Data Model (Current)
**What's needed:**
- ✅ Python 3.11+
- ✅ Django 5.0+
- ✅ SQLite database
- ✅ Database backup

**No additional setup required!**

### Phase 1: Core Grid View
**What's needed:**
- Template file: `schedule_manager.html`
- CSS file: `schedule_manager.css`
- View: `ScheduleManagerView` in views.py
- URL routing
- Bootstrap 5 (via CDN)

**Setup:**
```bash
# Create static directory if doesn't exist
mkdir -p apps/scheduling/static/scheduling

# Create template directory structure if doesn't exist
mkdir -p apps/scheduling/templates/scheduling
```

### Phase 2: Editing & Validation
**What's needed:**
- JavaScript file: `schedule_manager.js`
- API views: `api_views.py`
- Alpine.js (via CDN)
- HTMX (via CDN)

**Setup:**
```bash
# Create API views file
touch apps/scheduling/api_views.py

# Create JavaScript file
touch apps/scheduling/static/scheduling/schedule_manager.js
```

### Phase 3: Auto-Assignment
**What's needed:**
- Existing: `SchedulingService.auto_schedule_day()` ✅
- API endpoint for auto-assignment

**No additional setup required** (reuse existing service)

### Phase 4: CSV Export & Publishing
**What's needed:**
- Python csv module (built-in) ✅
- Export API endpoint

**No additional setup required**

### Phase 5: Polish & Testing
**What's needed:**
- Browser testing (Chrome, Firefox, Edge)
- Test user accounts

**Setup:**
```bash
# Create test users if needed
python manage.py createsuperuser  # For manager
python manage.py shell  # Create test guides
```

### Phase 6: Cleanup
**What's needed:**
- Documentation updates

**No additional setup required**

---

## Useful Django Commands

### Database Management
```bash
# Show migrations status
python manage.py showmigrations

# Show SQL for a migration
python manage.py sqlmigrate scheduling 000X

# Reverse a migration
python manage.py migrate scheduling 000X  # X = previous migration

# Reset database (DANGER - loses all data)
rm db.sqlite3
python manage.py migrate
```

### Development
```bash
# Run server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Collect static files (if needed for production)
python manage.py collectstatic
```

### Debugging
```bash
# Check for errors
python manage.py check

# Show URL patterns
python manage.py show_urls  # If django-extensions installed

# Run tests
python manage.py test apps.scheduling
```

---

## IDE Setup (Optional but Recommended)

### VS Code Extensions
- **Python** (Microsoft)
- **Django** (Baptiste Darthenay)
- **HTML CSS Support**
- **JavaScript (ES6) code snippets**
- **Prettier** (code formatter)

### VS Code Settings
**File:** `.vscode/settings.json`
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "editor.formatOnSave": true,
    "python.formatting.provider": "black",
    "files.associations": {
        "**/*.html": "html",
        "**/templates/**/*.html": "django-html",
        "**/templates/**/*": "django-txt"
    }
}
```

---

## Browser DevTools Setup

### For Testing (Phases 2-5)

**Chrome DevTools:**
1. Open DevTools (F12)
2. Go to Network tab → Monitor AJAX requests
3. Go to Console → See JavaScript errors
4. Go to Application → Check localStorage (if used)

**Useful for:**
- Debugging HTMX requests
- Inspecting Alpine.js state
- Testing responsive design

---

## Git Workflow

### Branching Strategy

```bash
# Main branches
main            # Production-ready code
master          # Current development (existing)

# Feature branch (recommended)
feature/schedule-manager  # New interface development
```

### Commit Guidelines

**Format:** `Phase X: Brief description`

**Examples:**
```bash
git commit -m "Phase 0: Add booking details fields to TourSession model"
git commit -m "Phase 1: Create schedule manager grid view"
git commit -m "Phase 2: Add inline editing with validation"
git commit -m "Phase 3: Integrate auto-assignment algorithm"
git commit -m "Phase 4: Implement CSV export functionality"
```

### Regular Commits

Commit after completing each subtask:
- Model changes → commit
- Template created → commit
- Feature working → commit
- Bug fixed → commit

**Don't wait until phase complete!**

---

## Testing Strategy

### Manual Testing Checklist

**Phase 0:**
- [ ] Migration runs without errors
- [ ] Can add booking details in admin
- [ ] Fields save correctly

**Phase 1:**
- [ ] Grid displays correctly
- [ ] Shows all guides and time slots
- [ ] Date navigation works

**Phase 2:**
- [ ] Can click cells to edit
- [ ] Dropdown shows eligible guides
- [ ] Validation errors display
- [ ] Save button works

**Phase 3:**
- [ ] Auto-assign button works
- [ ] Results modal appears
- [ ] Grid updates with assignments

**Phase 4:**
- [ ] CSV export downloads
- [ ] Excel opens file correctly
- [ ] Publish workflow functions

**Phase 5:**
- [ ] All features work together
- [ ] No console errors
- [ ] Responsive on different screens

---

## Troubleshooting

### Common Issues

**1. Server won't start**
```bash
# Check port in use
lsof -i :8000  # Unix
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python manage.py runserver 8080
```

**2. Static files not loading**
```bash
# Check STATIC_URL in settings
# Make sure DEBUG = True

# Clear browser cache
# Hard refresh: Ctrl+Shift+R
```

**3. Migration errors**
```bash
# Check for conflicts
python manage.py showmigrations

# Try fake migration
python manage.py migrate --fake scheduling 000X

# Last resort: reset migrations (DANGER)
# (Don't do this if you have production data!)
```

**4. Database locked**
```bash
# Stop all Django processes
# Close DB browser
# Restart server
```

---

## Ready to Start!

### Phase 0 Quick Start

1. **Backup database:**
   ```bash
   cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **Open checklist:**
   ```bash
   # Read PHASE_0_CHECKLIST.md
   # Follow step-by-step
   ```

3. **Update models:**
   ```bash
   # Edit apps/scheduling/models.py
   # Add booking detail fields
   ```

4. **Create migration:**
   ```bash
   python manage.py makemigrations scheduling
   ```

5. **Apply migration:**
   ```bash
   python manage.py migrate
   ```

6. **Verify:**
   ```bash
   python manage.py shell
   # Test booking fields
   ```

**Estimated time: 1 hour**

---

## Resources

### Documentation
- Django 5.0 Docs: https://docs.djangoproject.com/en/5.0/
- HTMX Docs: https://htmx.org/docs/
- Alpine.js Docs: https://alpinejs.dev/
- Bootstrap 5 Docs: https://getbootstrap.com/docs/5.3/

### Project Documentation
- `SCHEDULING_UI_SPEC.md` - Full specification
- `CSV_EXPORT_EXAMPLE.md` - CSV format reference
- `IMPLEMENTATION_SUMMARY.md` - Quick overview
- `PHASE_0_CHECKLIST.md` - Current phase tasks
- `DESIGN.md` - Original design plan
- `README.md` - User guide

### Contact
- Specification questions → Review SCHEDULING_UI_SPEC.md
- Implementation questions → Check relevant phase checklist
- Technical issues → Django/HTMX/Alpine.js docs

---

**Status:** ✅ Environment Ready - Begin Phase 0!

**Next:** Complete `PHASE_0_CHECKLIST.md`
