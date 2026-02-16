# Restaurant Staff Scheduler - Quick Summary

## Overview

**Goal:** Minimize total staff while maintaining 2 kitchen + 2 serving staff at all times during 10am-9:30pm

---

## Staff Structure

```
Kitchen Staff (Separate)     Serving Staff (Separate)
- Minimum 2 at all times     - Minimum 2 at all times
- 8-hour shifts              - 8-hour shifts
- No cross-training          - No cross-training
```

---

## Optimal Shift Pattern (8 staff total)

### Option A: Mixed 4-hour & 8-hour shifts (RECOMMENDED - Most Efficient)

**Kitchen Staff (4 people):**
```
Staff 1: 10:00 AM ─────────────────────── 6:00 PM  (8 hours full-day)
Staff 2: 10:00 AM ──────── 2:00 PM                  (4 hours half-day)
Staff 3:              1:30 PM ─────────────────────── 9:30 PM  (8 hours full-day)
Staff 4:                                5:30 PM ──── 9:30 PM  (4 hours half-day)

Timeline (coverage count):
10:00  11  12  13  14  15  16  17  18  19  20  21  22
│  2   2   2   2   2   2   2   2   3   2   2   2  │
└─ Opening ──┴── Lunch ──┴── Prep ──┴─ Dinner ──┴─ Close

Total hours: 8+4+8+4 = 24 hours (96% efficiency)
```

**Serving Staff (4 people):**
```
Same pattern as Kitchen Staff
```

### Option B: All 8-hour shifts (Simpler but less efficient)

**Kitchen Staff (4 people):**
```
Staff 1: 10:00 AM ──────────────────── 6:00 PM  (8 hours)
Staff 2: 10:00 AM ──────────────────── 6:00 PM  (8 hours)
Staff 3:              1:30 PM ──────────────────── 9:30 PM  (8 hours)
Staff 4:              1:30 PM ──────────────────── 9:30 PM  (8 hours)

Timeline:
10:00  11  12  13  14  15  16  17  18  19  20  21  22
│  2   2   2   2   4   4   4   4   2   2   2   2  │

Total hours: 32 hours (72% efficiency - more overlap)
```

---

## Coverage Verification

| Time | Kitchen | Serving | Status |
|------|---------|---------|--------|
| 10:00-13:30 | 2 | 2 | ✓ Minimum met |
| 13:30-18:00 | 4 | 4 | ✓✓ Overlap (peak) |
| 18:00-21:30 | 2 | 2 | ✓ Minimum met |

**Result:** 100% coverage with 8 staff (4 kitchen + 4 serving)

---

## Key Differences from Tour Guide Scheduler

| Aspect | Tour Guide | Restaurant Staff |
|--------|------------|------------------|
| **Work unit** | 1.5-hour tours | 4 or 8-hour shifts |
| **Optimization** | Minimize guides | Minimize staff |
| **Flexibility** | Variable assignments | Half-day or full-day |
| **Coverage** | 1 guide per tour | 2 minimum per role |
| **Complexity** | High (breaks, consecutive limits) | Medium (shift coverage) |
| **Roles** | Single (Guide) | Dual (Kitchen/Serving) |
| **Shift types** | Fixed duration | Flexible (4h or 8h) |

---

## Database Models

```
RestaurantStaff (like Guide)
├── staff_type: kitchen or serving
└── is_active

StaffAvailability (like GuideAvailability)
├── date
└── is_available

DailyRestaurantSchedule (like DailySchedule)
├── date
└── is_published

StaffShift (like TourSession)
├── staff
├── start_time (e.g., 10:00)
└── end_time (e.g., 18:00)
```

---

## Implementation Phases

### Phase 1: Models (1 day)
Create 4 models + migrations

### Phase 2: Admin (1 day)
Staff management interface

### Phase 3: Algorithm (2 days)
Auto-scheduler with optimal shift pattern

### Phase 4: UI (3 days)
Schedule manager with timeline view

### Phase 5: API (2 days)
REST endpoints for CRUD operations

### Phase 6: Testing (2 days)
Validation + edge cases

**Total:** ~11 days

---

## Auto-Scheduler Logic

```python
Algorithm:
1. Get available kitchen staff (minimum 4 needed)
2. Get available serving staff (minimum 4 needed)
3. Assign shift pattern:
   - 2 early shifts: 10:00 AM - 6:00 PM
   - 2 late shifts: 1:30 PM - 9:30 PM
4. Validate coverage (2 minimum at all times)
5. Return result

Optimization: Uses exactly 8 staff (minimum possible)
```

---

## UI Design

**Timeline View** (similar to tour schedule but with shift bars):

```
KITCHEN STAFF
┌──────────┬─────────────────────────────────────────┐
│ Alice    │ ████████████████████████                │ 10am-6pm
│ Bob      │ ████████████████████████                │ 10am-6pm
│ Charlie  │                     ████████████████    │ 1:30pm-9:30pm
│ Diana    │                     ████████████████    │ 1:30pm-9:30pm
└──────────┴─────────────────────────────────────────┘
Coverage:     2  2  2  2  4  4  4  4  2  2  2  2

SERVING STAFF
[Same layout]
```

---

## Next Steps

1. **Review this specification**
2. **Confirm design decisions**
3. **Start Phase 1: Create models**
4. **Iterate and refine**

---

## Confirmed Requirements ✓

Based on your input:

1. ✅ **Shift flexibility:** 4 hours (half-day) OR 8 hours (full-day)
2. ✅ **Minimum coverage:** Always 2 kitchen + 2 serving at all times
3. ✅ **Separate roles:** Kitchen and Serving are completely separate (no cross-training)
4. ✅ **Optimization:** Minimize total staff count
5. ✅ **Integration:** Extend existing `apps/scheduling/` app but as **separate dashboard**
6. ✅ **Simplicity:** Keep simple for now (no breaks, specializations, overtime tracking)

---

## Integration Approach

```
apps/scheduling/
├── Tour Guide Scheduler (existing)
│   ├── URL: /schedule/manager/
│   ├── Models: Guide, TourSession, DailySchedule
│   └── Dashboard: Tour Schedule Manager
│
└── Restaurant Scheduler (NEW)
    ├── URL: /schedule/restaurant/
    ├── Models: RestaurantStaff, StaffShift, DailyRestaurantSchedule
    └── Dashboard: Restaurant Schedule Manager (separate)
```

**Navigation:**
- Both accessible from Django admin
- Separate dashboards (no overlap)
- Similar UI/UX patterns
- Independent data models

---

## Ready to Start! 🚀

The design is complete and requirements are confirmed. We can begin implementation with:

**Phase 1: Create Data Models**
- Add 4 new models to `apps/scheduling/models.py`
- Create migrations
- Test in Django shell
