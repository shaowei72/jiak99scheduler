# Update to New Operating Hours (10am-9:30pm, 1.5-hour tours)

**Date:** 2026-02-15
**Status:** Ready to Apply

---

## What's Changed

### Old Configuration:
- **Hours:** 8:30 AM - 10:00 PM
- **Tour Duration:** 2 hours
- **Time Slots:** 24 per day

### New Configuration:
- **Hours:** 10:00 AM - 9:30 PM
- **Tour Duration:** 1.5 hours
- **Time Slots:** 21 per day

---

## Files Updated

✅ **apps/scheduling/services.py** - Updated `generate_tour_time_slots()`
- Changed start time: 10:00 AM (was 8:30 AM)
- Changed tour duration: 90 minutes (was 120 minutes)
- Changed last tour: 8:00 PM start, 9:30 PM end (was 8:00 PM start, 10:00 PM end)

✅ **apps/scheduling/management/commands/generate_tour_slots.py** - Updated description

✅ **apps/scheduling/management/commands/regenerate_tour_slots.py** - New command to safely regenerate

✅ **README.md** - Updated all references to hours and tour counts

---

## Guide Type Constraints (Still Valid)

The guide type boundaries remain the same:
- **Full-time (FT):** Can work any slot (10:00 AM - 9:30 PM)
- **Part-time Morning (PTM):** Can work slots ending by 2:30 PM
- **Part-time Afternoon (PTA):** Can work slots starting from 2:30 PM

With 1.5-hour tours starting from 10:00 AM:
- **PTM can work:** 10:00 AM - 1:00 PM (ends at 2:30 PM)
- **PTA can work:** 2:30 PM - 8:00 PM (starts at 2:30 PM or later)
- **Both boundaries handled properly** ✅

---

## How to Apply Changes

### Step 1: Backup Database

```bash
cp db.sqlite3 "db.sqlite3.backup.before_new_hours_$(date +%Y%m%d)"
```

### Step 2: Regenerate Time Slots

```bash
# This will DELETE old time slots and create new ones
python manage.py regenerate_tour_slots --confirm
```

**Output:**
```
🔄 Starting time slot regeneration...

Found 24 existing time slots
Found X existing tour sessions
Found Y existing daily schedules

🗑️  Deleting old time slots...
✓ Old time slots deleted

🔨 Generating new time slots (10am-9:30pm, 1.5-hour tours)...
✓ Created 21 new time slots

📋 New Time Slots:
  • 10:00 AM - 11:30 AM
  • 10:30 AM - 12:00 PM
  • 11:00 AM - 12:30 PM
  • 11:30 AM - 01:00 PM
  • 12:00 PM - 01:30 PM
  ... and 16 more

✅ Successfully regenerated time slots!
```

### Step 3: Recreate Schedules

Since old sessions are deleted, recreate schedules for needed dates:

```bash
# Example: Create schedules for March 2024
python manage.py create_monthly_schedule --month 3 --year 2024
```

### Step 4: Verify in Schedule Manager

1. Open Schedule Manager: http://localhost:8000/schedule/manager/
2. **Expected:** Grid shows 21 time slots (10:00 AM to 8:00 PM starts)
3. **Verify:** Each tour duration is 1.5 hours

---

## New Time Slots (21 total)

| # | Start Time | End Time | Duration |
|---|------------|----------|----------|
| 1 | 10:00 AM | 11:30 AM | 1.5h |
| 2 | 10:30 AM | 12:00 PM | 1.5h |
| 3 | 11:00 AM | 12:30 PM | 1.5h |
| 4 | 11:30 AM | 01:00 PM | 1.5h |
| 5 | 12:00 PM | 01:30 PM | 1.5h |
| 6 | 12:30 PM | 02:00 PM | 1.5h |
| 7 | 01:00 PM | 02:30 PM | 1.5h |
| 8 | 01:30 PM | 03:00 PM | 1.5h |
| 9 | 02:00 PM | 03:30 PM | 1.5h |
| 10 | 02:30 PM | 04:00 PM | 1.5h |
| 11 | 03:00 PM | 04:30 PM | 1.5h |
| 12 | 03:30 PM | 05:00 PM | 1.5h |
| 13 | 04:00 PM | 05:30 PM | 1.5h |
| 14 | 04:30 PM | 06:00 PM | 1.5h |
| 15 | 05:00 PM | 06:30 PM | 1.5h |
| 16 | 05:30 PM | 07:00 PM | 1.5h |
| 17 | 06:00 PM | 07:30 PM | 1.5h |
| 18 | 06:30 PM | 08:00 PM | 1.5h |
| 19 | 07:00 PM | 08:30 PM | 1.5h |
| 20 | 07:30 PM | 09:00 PM | 1.5h |
| 21 | 08:00 PM | 09:30 PM | 1.5h |

---

## Auto-Scheduler Impact

The auto-scheduler algorithm automatically adapts to the new 1.5-hour tours:

✅ **Break validation:** Now enforces 30-minute minimum break between tours (reduced from 1 hour)
✅ **Guide type constraints:** PTM/PTA boundaries still work correctly
✅ **Workload balancing:** Works with any tour duration

**No algorithm changes needed!** The algorithm is duration-agnostic.

---

## Visual Grid Changes

**Before:** 24 rows (8:30 AM - 8:00 PM)
**After:** 21 rows (10:00 AM - 8:00 PM)

The Schedule Manager grid will automatically display:
- **Fewer rows** (21 instead of 24)
- **New start time** (10:00 AM)
- **New end time** (last tour starts 8:00 PM, ends 9:30 PM)

---

## Testing Checklist

After regenerating time slots:

- [ ] Schedule Manager shows 21 time slots
- [ ] First slot: 10:00 AM - 11:30 AM
- [ ] Last slot: 8:00 PM - 9:30 PM
- [ ] Can create schedules for new dates
- [ ] Auto-assign works correctly
- [ ] PTM guides can't work afternoon slots
- [ ] PTA guides can't work morning slots
- [ ] CSV export shows correct times

---

## Rollback Plan

If you need to revert:

```bash
# Restore database backup
cp db.sqlite3.backup.before_new_hours_YYYYMMDD db.sqlite3

# Restart server
python manage.py runserver
```

---

## Summary

✅ **Code updated** - All references to 8:30 AM, 10 PM, 2-hour tours updated
✅ **New command created** - `regenerate_tour_slots` for safe migration
✅ **Documentation updated** - README.md reflects new hours
✅ **Algorithm compatible** - Auto-scheduler works with 1.5-hour tours
✅ **Ready to apply** - Just run the regenerate command!

**Run now:**
```bash
python manage.py regenerate_tour_slots --confirm
```

Then test in Schedule Manager! 🎯
