# 🚀 START HERE - Schedule Manager Implementation

**Welcome to the Schedule Manager Implementation!**

This guide will get you started in 5 minutes.

---

## ✅ What's Ready

Your environment is already set up:
- ✅ Python 3.11.9 installed
- ✅ Django 5.0.14 installed
- ✅ Tour Guide Scheduler app running
- ✅ Complete specification ready

---

## 📚 Documentation Overview

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **START_HERE.md** | Quick start (this file) | **Read first** |
| **PHASE_0_CHECKLIST.md** | Step-by-step Phase 0 tasks | **Start here after reading this** |
| **DEV_SETUP_GUIDE.md** | Development environment reference | When setting up tools |
| **SCHEDULING_UI_SPEC.md** | Complete design specification | Reference during all phases |
| **IMPLEMENTATION_SUMMARY.md** | Feature overview & timeline | Quick reference |
| **CSV_EXPORT_EXAMPLE.md** | CSV format examples | Phase 4 (CSV export) |

---

## 🎯 What We're Building

**Before (Current):**
4 separate admin sections for scheduling

**After (New):**
1 unified Schedule Manager with:
- Interactive grid (time slots × guides)
- Inline editing with booking details
- Auto-assignment button
- CSV export
- Real-time validation
- Publish workflow

**Timeline:** 15-19 development days across 6 phases

---

## 🏁 Phase 0: Quick Start (1 hour)

### Step 1: Backup Database (2 minutes)

```bash
# Navigate to project directory
cd C:\Users\P1251354\LocalDev\Jiak99_App01

# Create backup with timestamp
cp db.sqlite3 db.sqlite3.backup.20260215
```

**✅ Verify:** Check that `db.sqlite3.backup.20260215` exists

---

### Step 2: Update TourSession Model (10 minutes)

**File:** `apps\scheduling\models.py`

**Find line 107** (after `status` field, before `notes` field) and add:

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

**✅ Save the file**

---

### Step 3: Create Migration (2 minutes)

```bash
python manage.py makemigrations scheduling
```

**Expected output:**
```
Migrations for 'scheduling':
  apps\scheduling\migrations\0003_add_booking_details.py
    - Add field visitor_count to toursession
    - Add field visitor_type to toursession
    - Add field booking_channel to toursession
```

**✅ Verify:** Migration file created in `apps\scheduling\migrations\`

---

### Step 4: Run Migration (1 minute)

```bash
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  Applying scheduling.0003_add_booking_details... OK
```

**✅ Verify:** "OK" appears, no errors

---

### Step 5: Test in Django Shell (5 minutes)

```bash
python manage.py shell
```

```python
from apps.scheduling.models import TourSession

# Get first session
session = TourSession.objects.first()

# Test new fields exist
print(f"Visitor count: {session.visitor_count}")  # Should print: None
print(f"Visitor type: {session.visitor_type}")    # Should print: None
print(f"Channel: {session.booking_channel}")      # Should print: None

# Test setting values
session.visitor_count = 25
session.visitor_type = 'local'
session.booking_channel = 'online'
session.save()

print("✅ Test successful! New fields work.")

# Exit
exit()
```

**✅ Verify:** No errors, fields save correctly

---

### Step 6: Check Admin (Optional - 2 minutes)

```bash
# Start server
python manage.py runserver

# Open browser: http://localhost:8000/admin/
# Go to: Scheduling → Tour sessions
# Click any session
# Scroll down - you should see new fields:
#   - Visitor count
#   - Visitor type
#   - Booking channel
```

**✅ Verify:** New fields visible in admin form

---

## 🎉 Phase 0 Complete!

**Congratulations!** Your database now tracks booking details for each tour.

**What you've accomplished:**
- ✅ Database backed up
- ✅ TourSession model updated with 3 new fields
- ✅ Migration created and applied
- ✅ Booking details functional

**Time taken:** ~20 minutes (if followed quickly)

---

## 📋 Next Steps

### Complete Phase 0 Checklist

Open `PHASE_0_CHECKLIST.md` and complete remaining tasks:
- [ ] Add helper methods to TourSession
- [ ] Update admin inline fields
- [ ] Add test data
- [ ] Update documentation

**Estimated time:** 40 more minutes

---

### Then Move to Phase 1

**Phase 1: Core Grid View (2-3 days)**

Phase 1 will involve:
1. Creating the Schedule Manager template
2. Building the grid layout
3. Adding date navigation
4. Displaying booking details in cells
5. Integrating with Django admin

**Checklist will be created** when Phase 0 is fully complete.

---

## 📊 Overall Progress

```
Phase 0: Data Model          [████░░░░░░] 40% (quick start done)
Phase 1: Core Grid View      [░░░░░░░░░░]  0%
Phase 2: Editing             [░░░░░░░░░░]  0%
Phase 3: Auto-Assignment     [░░░░░░░░░░]  0%
Phase 4: CSV Export          [░░░░░░░░░░]  0%
Phase 5: Polish              [░░░░░░░░░░]  0%
Phase 6: Cleanup             [░░░░░░░░░░]  0%

Total Progress:              [█░░░░░░░░░]  6%
```

---

## 🆘 Need Help?

### If Migration Fails

```bash
# Check what's wrong
python manage.py check

# See migration SQL (for debugging)
python manage.py sqlmigrate scheduling 0003

# Rollback if needed
python manage.py migrate scheduling 0002
```

### If Database Issues

```bash
# Restore from backup
cp db.sqlite3.backup.20260215 db.sqlite3

# Revert migration
python manage.py migrate scheduling 0002

# Try again
```

### If Server Won't Start

```bash
# Check for errors
python manage.py check

# Try different port
python manage.py runserver 8080
```

---

## 📖 Key Documents Reference

**During Development:**
- Reference `SCHEDULING_UI_SPEC.md` for design details
- Follow phase checklists for tasks
- Check `DEV_SETUP_GUIDE.md` for commands

**For Features:**
- Section 3.3: Grid cell design
- Section 3.5: Auto-assignment flow
- Section 6.7.7: CSV export format

**For Technical:**
- Section 6.2: Technology stack
- Section 6.4: API endpoints
- Section 6.3: Data models

---

## ⚡ Quick Commands Reference

```bash
# Start development server
python manage.py runserver

# Create migration
python manage.py makemigrations scheduling

# Run migrations
python manage.py migrate

# Django shell (for testing)
python manage.py shell

# Check for issues
python manage.py check

# Backup database
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

---

## 🎯 Your Action Plan

### Today (Phase 0)
1. ✅ Quick start (20 min) - DONE if you followed above
2. ⬜ Complete Phase 0 checklist (40 min)
3. ⬜ Commit changes to git

### Tomorrow (Phase 1 Start)
1. ⬜ Create schedule manager template
2. ⬜ Build grid layout (reuse schedule_overview.html)
3. ⬜ Add CSS styling

### This Week (Phases 1-2)
1. ⬜ Complete Phase 1 (grid view)
2. ⬜ Start Phase 2 (editing)
3. ⬜ Set up HTMX + Alpine.js

### Next 2-3 Weeks (Phases 3-6)
1. ⬜ Phase 3: Auto-assignment
2. ⬜ Phase 4: CSV export & publish
3. ⬜ Phase 5: Polish & testing
4. ⬜ Phase 6: Cleanup & deploy

---

## 🎊 Motivation

**You're building something that will:**
- Save managers 50% of their scheduling time
- Reduce scheduling errors to near zero
- Make booking data visible and actionable
- Provide easy export for reporting
- Create a better experience for everyone

**Keep going! Each phase builds on the last.** 💪

---

## ✅ Current Status

```
✅ Specification complete
✅ Environment ready
✅ Phase 0 quick start done
⬜ Phase 0 checklist remaining
⬜ Ready for Phase 1
```

**Next:** Complete `PHASE_0_CHECKLIST.md`

---

## 📞 Resources

- **Specification:** `SCHEDULING_UI_SPEC.md` (comprehensive)
- **Summary:** `IMPLEMENTATION_SUMMARY.md` (overview)
- **Setup:** `DEV_SETUP_GUIDE.md` (technical reference)
- **CSV Format:** `CSV_EXPORT_EXAMPLE.md` (Phase 4)
- **Original Design:** `DESIGN.md` (Phase 1 context)
- **User Guide:** `README.md` (current app features)

---

**Ready? Let's build this! 🚀**

**Start with:** `PHASE_0_CHECKLIST.md`
