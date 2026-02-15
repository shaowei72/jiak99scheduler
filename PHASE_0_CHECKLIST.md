# Phase 0: Data Model Migration - Implementation Checklist

**Goal:** Add booking details fields to TourSession model
**Duration:** 1 day
**Status:** Not Started

---

## Prerequisites

- [x] Specification approved ✅
- [ ] Development environment set up
- [ ] Database backup created
- [ ] Virtual environment activated

---

## Task List

### 1. Backup Current Database
**Priority:** CRITICAL - Do this first!

```bash
# Backup SQLite database
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Or export as JSON
python manage.py dumpdata > backup_before_migration.json
```

**Verification:**
- [ ] Backup file created
- [ ] Backup file size > 0 KB
- [ ] Backup file readable

---

### 2. Update TourSession Model

**File:** `apps/scheduling/models.py`

**Add these fields to TourSession class (after line 109, before `created_at`):**

```python
# Booking details (NEW - Phase 0)
visitor_count = models.PositiveIntegerField(
    null=True,
    blank=True,
    help_text="Number of visitors for this tour"
)

VISITOR_TYPE_CHOICES = [
    ('local', 'Local'),
    ('international', 'International'),
]
visitor_type = models.CharField(
    max_length=20,
    choices=VISITOR_TYPE_CHOICES,
    null=True,
    blank=True,
    help_text="Type of visitors (Local or International)"
)

BOOKING_CHANNEL_CHOICES = [
    ('online', 'Online Platform'),
    ('walkin', 'Walk-in'),
    ('direct', 'Direct Sales'),
]
booking_channel = models.CharField(
    max_length=20,
    choices=BOOKING_CHANNEL_CHOICES,
    null=True,
    blank=True,
    help_text="How the tour was booked"
)
```

**Checklist:**
- [ ] Code added to models.py
- [ ] Indentation correct (4 spaces)
- [ ] Placed before `created_at` field
- [ ] Choices defined before fields
- [ ] help_text included

---

### 3. Add Helper Methods to TourSession

**Add these methods at the end of TourSession class (after line 131):**

```python
def get_booking_summary(self):
    """Get a one-line summary of booking details."""
    if not self.visitor_count:
        return "No booking details"

    parts = [f"{self.visitor_count} visitors"]
    if self.visitor_type:
        parts.append(self.get_visitor_type_display())
    if self.booking_channel:
        parts.append(f"via {self.get_booking_channel_display()}")

    return ", ".join(parts)

def has_booking_details(self):
    """Check if any booking details are filled."""
    return bool(
        self.visitor_count or
        self.visitor_type or
        self.booking_channel
    )
```

**Checklist:**
- [ ] Methods added
- [ ] Proper indentation
- [ ] Test methods work (after migration)

---

### 4. Create Migration

```bash
python manage.py makemigrations scheduling
```

**Expected output:**
```
Migrations for 'scheduling':
  apps\scheduling\migrations\000X_add_booking_details.py
    - Add field visitor_count to toursession
    - Add field visitor_type to toursession
    - Add field booking_channel to toursession
```

**Checklist:**
- [ ] Migration file created
- [ ] Migration number noted (000X)
- [ ] No errors in output

---

### 5. Review Migration File

**File:** `apps/scheduling/migrations/000X_add_booking_details.py`

**Verify it contains:**
```python
operations = [
    migrations.AddField(
        model_name='toursession',
        name='visitor_count',
        field=models.PositiveIntegerField(null=True, blank=True, ...),
    ),
    migrations.AddField(
        model_name='toursession',
        name='visitor_type',
        field=models.CharField(max_length=20, choices=[...], null=True, blank=True, ...),
    ),
    migrations.AddField(
        model_name='toursession',
        name='booking_channel',
        field=models.CharField(max_length=20, choices=[...], null=True, blank=True, ...),
    ),
]
```

**Checklist:**
- [ ] Migration file reviewed
- [ ] All 3 fields present
- [ ] null=True and blank=True set
- [ ] Choices included

---

### 6. Run Migration

```bash
python manage.py migrate scheduling
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: scheduling
Running migrations:
  Applying scheduling.000X_add_booking_details... OK
```

**Checklist:**
- [ ] Migration applied successfully
- [ ] No errors in output
- [ ] Database file size increased slightly

---

### 7. Verify Migration in Database

**Option A: Django shell**
```bash
python manage.py shell
```

```python
from apps.scheduling.models import TourSession

# Check model has new fields
session = TourSession.objects.first()
print(f"Visitor count: {session.visitor_count}")
print(f"Visitor type: {session.visitor_type}")
print(f"Booking channel: {session.booking_channel}")

# Should print: None, None, None (expected for existing data)

# Test setting values
session.visitor_count = 25
session.visitor_type = 'local'
session.booking_channel = 'online'
session.save()

print(f"Booking summary: {session.get_booking_summary()}")
# Should print: "25 visitors, Local, via Online Platform"

exit()
```

**Option B: Admin panel**
```bash
python manage.py runserver
# Visit http://localhost:8000/admin/scheduling/toursession/
# Click on any session
# Verify new fields visible in form
```

**Checklist:**
- [ ] New fields visible in Django shell
- [ ] Can set and save values
- [ ] Helper methods work
- [ ] New fields visible in admin (if tested)

---

### 8. Update Admin Interface (Optional for Phase 0)

**File:** `apps/scheduling/admin.py`

**Find TourSessionInline class (line 15) and update fields:**

```python
class TourSessionInline(admin.TabularInline):
    model = TourSession
    extra = 0
    fields = [
        'time_slot',
        'assigned_guide',
        'status',
        'visitor_count',        # NEW
        'visitor_type',         # NEW
        'booking_channel',      # NEW
        'validation_status',
        'notes'
    ]
    readonly_fields = ['validation_status']
    autocomplete_fields = ['assigned_guide']
```

**Find TourSessionAdmin fieldsets (line 58) and update:**

```python
fieldsets = [
    (None, {
        'fields': ['daily_schedule', 'time_slot', 'assigned_guide', 'status']
    }),
    ('Booking Details', {     # NEW section
        'fields': ['visitor_count', 'visitor_type', 'booking_channel'],
    }),
    ('Validation', {
        'fields': ['validation_status_display'],
    }),
    ('Additional Info', {
        'fields': ['notes'],
    }),
    ('Timestamps', {
        'fields': ['created_at', 'updated_at'],
        'classes': ['collapse']
    }),
]
```

**Checklist:**
- [ ] Inline fields updated
- [ ] Fieldsets updated with new section
- [ ] Admin loads without errors

---

### 9. Test with Sample Data

**Create a test session with booking details:**

```bash
python manage.py shell
```

```python
from apps.scheduling.models import TourSession, DailySchedule
from datetime import date

# Get or create a schedule
schedule, _ = DailySchedule.objects.get_or_create(date=date.today())

# Get first session
session = schedule.sessions.first()

if session:
    # Add booking details
    session.visitor_count = 30
    session.visitor_type = 'international'
    session.booking_channel = 'online'
    session.notes = "Test booking details"
    session.save()

    print("✅ Test data created successfully!")
    print(f"Booking summary: {session.get_booking_summary()}")
else:
    print("⚠️ No sessions found. Create a schedule first.")

exit()
```

**Checklist:**
- [ ] Test data created
- [ ] No errors
- [ ] Booking summary displays correctly

---

### 10. Update Tests (if any exist)

**Check for test files:**
```bash
ls apps/scheduling/tests.py
# or
ls apps/scheduling/tests/
```

**If tests exist, update to include new fields:**
- [ ] Tests updated or noted for later
- [ ] All tests pass: `python manage.py test apps.scheduling`

---

### 11. Documentation Update

**Update README.md** to mention new booking details feature:

Find the "Features" section and add:
```markdown
- **Booking Details**: Track visitor count, visitor type (Local/International), and booking channel (Online/Walk-in/Direct) for each tour
```

**Checklist:**
- [ ] README.md updated
- [ ] DESIGN.md reviewed (already has booking details in spec)

---

## Verification Checklist

### Final Verification Steps

- [ ] **Database:** New fields exist in TourSession table
- [ ] **Admin:** Booking fields visible and editable
- [ ] **Shell:** Can create/update booking details
- [ ] **Migration:** Reversible (test with `python manage.py migrate scheduling 000X` where X is previous migration)
- [ ] **No errors:** Server runs without errors
- [ ] **Backup:** Database backup safely stored

### Rollback Plan (if needed)

If something goes wrong:
```bash
# Stop server
Ctrl+C

# Restore database backup
cp db.sqlite3.backup.YYYYMMDD_HHMMSS db.sqlite3

# Or reverse migration
python manage.py migrate scheduling 000X  # Previous migration number

# Restore models.py from git
git checkout apps/scheduling/models.py
```

---

## Phase 0 Complete! ✅

Once all checkboxes are checked, Phase 0 is complete.

**Next:** Proceed to Phase 1 (Core Grid View)

---

## Time Tracking

| Task | Estimated | Actual | Notes |
|------|-----------|--------|-------|
| Backup database | 5 min | | |
| Update model | 15 min | | |
| Create migration | 5 min | | |
| Run migration | 5 min | | |
| Verify in shell | 10 min | | |
| Update admin | 15 min | | |
| Test with data | 10 min | | |
| Documentation | 10 min | | |
| **Total** | **~75 min** | | |

---

## Common Issues & Solutions

### Issue 1: Migration conflicts
**Error:** "Conflicting migrations detected"
**Solution:**
```bash
python manage.py makemigrations --merge
```

### Issue 2: Database locked
**Error:** "database is locked"
**Solution:**
- Stop all running Django processes
- Close any DB browsers
- Try again

### Issue 3: Migration already applied
**Error:** "No migrations to apply"
**Solution:**
- Check migration status: `python manage.py showmigrations scheduling`
- If already applied, that's fine!

### Issue 4: Import errors after model change
**Error:** "cannot import name..."
**Solution:**
- Restart Django server
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`

---

## Contact / Questions

If you encounter issues:
1. Check this checklist first
2. Review error messages carefully
3. Check Django documentation: https://docs.djangoproject.com/en/5.0/topics/migrations/
4. Ask for help with specific error messages

---

**Phase 0 Status:** ⬜ Not Started → 🟡 In Progress → ✅ Complete
