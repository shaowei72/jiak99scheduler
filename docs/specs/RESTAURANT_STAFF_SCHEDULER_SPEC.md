# Restaurant Staff Scheduler - Design Specification

**Version:** 1.0.0
**Date:** 2026-02-16
**Status:** Draft

---

## 1. Overview

### Purpose
Automated scheduling system for Kitchen and Serving staff to minimize total staff needed while maintaining minimum coverage requirements throughout operating hours.

### Scope
- Kitchen Staff scheduling (separate from Serving Staff)
- Serving Staff scheduling (separate from Kitchen Staff)
- 8-hour shift assignments within 10am-9:30pm operating hours
- Manager interface for staff management and schedule viewing
- Auto-scheduler optimization

---

## 2. Requirements Summary

### Staff Structure
- **Kitchen Staff**: Separate role, minimum 2 required at all times
- **Serving Staff**: Separate role, minimum 2 required at all times
- No cross-training between roles

### Operating Hours
- **Start:** 10:00 AM
- **End:** 9:30 PM
- **Total coverage needed:** 11.5 hours
- **Peak hours:**
  - Lunch rush: 12:00 PM - 2:00 PM
  - Dinner rush: 6:00 PM - 8:00 PM

### Shift Structure
- **Duration:** 4 hours (half-day) OR 8 hours (full-day)
- **Start times:** Flexible (can start at any time within operating hours)
- **Break:** Included within shift (not specified explicitly)
- **Examples:**
  - **Full-day (8 hours):**
    - 10:00 AM - 6:00 PM
    - 11:00 AM - 7:00 PM
    - 1:30 PM - 9:30 PM
  - **Half-day (4 hours):**
    - 10:00 AM - 2:00 PM
    - 2:00 PM - 6:00 PM
    - 5:30 PM - 9:30 PM

### Constraints
- Each staff member works either **4 hours** (half-day) OR **8 hours** (full-day)
- Minimum coverage at all times:
  - **2 Kitchen staff** throughout 10am-9:30pm
  - **2 Serving staff** throughout 10am-9:30pm
- Staff cannot work split shifts (must be continuous)
- Each staff member works at most 1 shift per day

### Optimization Goal
**Minimize total number of staff assigned per day** while maintaining coverage requirements.

---

## 3. Data Model

### 3.1 Staff Model (extends/similar to Guide model)

```python
class RestaurantStaff(models.Model):
    """Kitchen or Serving staff member"""

    STAFF_TYPE_CHOICES = [
        ('kitchen', 'Kitchen Staff'),
        ('serving', 'Serving Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True)

    # Similar to Guide model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3.2 Staff Availability Model

```python
class StaffAvailability(models.Model):
    """Track which days staff are available"""

    staff = models.ForeignKey(RestaurantStaff, on_delete=models.CASCADE)
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['staff', 'date']
```

### 3.3 Daily Restaurant Schedule Model

```python
class DailyRestaurantSchedule(models.Model):
    """Container for all restaurant staff shifts on a specific date"""

    date = models.DateField(unique=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3.4 Staff Shift Model

```python
class StaffShift(models.Model):
    """Individual shift assignment (4 or 8 hours)"""

    SHIFT_DURATION_CHOICES = [
        (4, '4 hours (Half-day)'),
        (8, '8 hours (Full-day)'),
    ]

    daily_schedule = models.ForeignKey(
        DailyRestaurantSchedule,
        on_delete=models.CASCADE,
        related_name='shifts'
    )
    staff = models.ForeignKey(
        RestaurantStaff,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Shift timing
    start_time = models.TimeField()  # e.g., 10:00 AM
    end_time = models.TimeField()    # e.g., 6:00 PM (start + duration)
    duration_hours = models.IntegerField(
        choices=SHIFT_DURATION_CHOICES,
        default=8,
        help_text="Shift duration: 4 hours (half-day) or 8 hours (full-day)"
    )

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_full_day(self):
        """Returns True if 8-hour shift"""
        return self.duration_hours == 8

    @property
    def is_half_day(self):
        """Returns True if 4-hour shift"""
        return self.duration_hours == 4

    @property
    def staff_type(self):
        """Kitchen or Serving"""
        return self.staff.staff_type if self.staff else None

    def clean(self):
        """Validate shift duration matches start/end times"""
        from datetime import datetime, timedelta
        if self.start_time and self.end_time:
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            actual_hours = (end - start).total_seconds() / 3600
            if abs(actual_hours - self.duration_hours) > 0.1:
                raise ValidationError(
                    f"Duration mismatch: {actual_hours:.1f} hours between "
                    f"start and end, but duration_hours is {self.duration_hours}"
                )
```

---

## 4. Algorithm Design

### 4.1 Optimization Goal

**Minimize:** Total number of staff assigned
**Subject to:** Coverage constraints

```
Objective: MIN(kitchen_staff_count + serving_staff_count)

Constraints:
- At any time t in [10:00, 21:30]:
  - kitchen_staff_working(t) >= 2
  - serving_staff_working(t) >= 2
- Each shift is exactly 8 hours
- Each staff works at most 1 shift per day
```

### 4.2 Mathematical Analysis

**Operating hours:** 10:00 AM - 9:30 PM = 11.5 hours
**Shift duration:** 8 hours
**Coverage needed:** 11.5 hours

**Minimum staff calculation:**
- To cover 11.5 hours with 8-hour shifts:
  - 1 staff can cover 8 hours
  - Need at least 2 staff to cover 11.5 hours (8 + 8 = 16 hours > 11.5 hours)

**Per role:**
- Minimum 2 kitchen staff needed throughout
- Minimum 2 serving staff needed throughout

**Theoretical minimum:**
- Kitchen: 2 staff × 2 (minimum coverage) = **4 kitchen staff**
- Serving: 2 staff × 2 (minimum coverage) = **4 serving staff**
- **Total: 8 staff per day** (4 kitchen + 4 serving)

But with optimal shift overlap, we can achieve:
- **3 kitchen staff** (with proper staggering)
- **3 serving staff** (with proper staggering)
- **Total: 6 staff per day** (3 kitchen + 3 serving)

### 4.3 Optimal Shift Pattern

To cover 11.5 hours with minimum staff using flexible 4-hour and 8-hour shifts:

**Strategy:** Mix 4-hour and 8-hour shifts to minimize staff while maintaining coverage

**Option A: Mix of 4-hour and 8-hour shifts (Most Flexible)**

```
Staff 1: 10:00 AM - 6:00 PM   (8 hours) - Full day, covers opening + lunch + dinner prep
Staff 2: 10:00 AM - 2:00 PM   (4 hours) - Half day, covers opening + lunch rush
Staff 3: 1:30 PM - 9:30 PM    (8 hours) - Full day, covers lunch rush + dinner + closing
Staff 4: 5:30 PM - 9:30 PM    (4 hours) - Half day, covers dinner rush + closing

Coverage:
10:00-13:30: Staff 1, 2 (2 people) ✓
13:30-14:00: Staff 1, 2, 3 (3 people) ✓✓
14:00-17:30: Staff 1, 3 (2 people) ✓
17:30-18:00: Staff 1, 3, 4 (3 people) ✓✓
18:00-21:30: Staff 3, 4 (2 people) ✓

Total hours worked: 8+4+8+4 = 24 hours
Required coverage: 11.5 hours × 2 = 23 hours
Efficiency: 96% (minimal waste from overlap)
```

**Option B: All 8-hour shifts (Simpler but less flexible)**

```
Staff 1: 10:00 AM - 6:00 PM   (8 hours)
Staff 2: 10:00 AM - 6:00 PM   (8 hours)
Staff 3: 1:30 PM - 9:30 PM    (8 hours)
Staff 4: 1:30 PM - 9:30 PM    (8 hours)

Coverage:
10:00-13:30: Staff 1, 2 (2 people) ✓
13:30-18:00: Staff 1, 2, 3, 4 (4 people) ✓✓
18:00-21:30: Staff 3, 4 (2 people) ✓

Total hours worked: 32 hours
Efficiency: 72% (more overlap/waste)
```

**Optimal solution: 4 staff per role (either option)**
- **4 Kitchen staff** (mix of 4-hour and 8-hour shifts)
- **4 Serving staff** (mix of 4-hour and 8-hour shifts)
- **Total: 8 staff per day**

**Recommendation:** Use **Option A** (mixed shifts) for better efficiency and staff flexibility

### 4.4 Algorithm Steps

```python
def auto_schedule_restaurant_staff(date):
    """
    Auto-assign kitchen and serving staff for a date
    Uses optimal mix of 4-hour and 8-hour shifts
    """

    # Get available staff
    kitchen_staff = get_available_kitchen_staff(date)
    serving_staff = get_available_serving_staff(date)

    # Define optimal shift templates (Option A: mixed 4h and 8h)
    shift_templates = [
        {'start': '10:00', 'end': '18:00', 'duration': 8},  # Full day - opening
        {'start': '10:00', 'end': '14:00', 'duration': 4},  # Half day - lunch rush
        {'start': '13:30', 'end': '21:30', 'duration': 8},  # Full day - closing
        {'start': '17:30', 'end': '21:30', 'duration': 4},  # Half day - dinner rush
    ]

    # Assign kitchen staff
    for i, template in enumerate(shift_templates):
        if i < len(kitchen_staff):
            create_shift(
                staff=kitchen_staff[i],
                start_time=template['start'],
                end_time=template['end'],
                duration_hours=template['duration']
            )

    # Assign serving staff
    for i, template in enumerate(shift_templates):
        if i < len(serving_staff):
            create_shift(
                staff=serving_staff[i],
                start_time=template['start'],
                end_time=template['end'],
                duration_hours=template['duration']
            )

    return {
        'kitchen_assigned': min(len(kitchen_staff), 4),
        'serving_assigned': min(len(serving_staff), 4),
        'total_staff': min(len(kitchen_staff), 4) + min(len(serving_staff), 4),
        'pattern': 'mixed_4h_8h'  # or 'all_8h' as fallback
    }
```

**Alternative Patterns:**

The algorithm can support multiple shift patterns:

```python
# Pattern 1: Mixed 4h and 8h (most efficient)
PATTERN_MIXED = [
    {'start': '10:00', 'end': '18:00', 'duration': 8},
    {'start': '10:00', 'end': '14:00', 'duration': 4},
    {'start': '13:30', 'end': '21:30', 'duration': 8},
    {'start': '17:30', 'end': '21:30', 'duration': 4},
]

# Pattern 2: All 8-hour (simpler, but more hours)
PATTERN_ALL_8H = [
    {'start': '10:00', 'end': '18:00', 'duration': 8},
    {'start': '10:00', 'end': '18:00', 'duration': 8},
    {'start': '13:30', 'end': '21:30', 'duration': 8},
    {'start': '13:30', 'end': '21:30', 'duration': 8},
]

# Pattern 3: All 4-hour (maximum flexibility, but needs more staff)
PATTERN_ALL_4H = [
    {'start': '10:00', 'end': '14:00', 'duration': 4},
    {'start': '10:00', 'end': '14:00', 'duration': 4},
    {'start': '13:30', 'end': '17:30', 'duration': 4},
    {'start': '13:30', 'end': '17:30', 'duration': 4},
    {'start': '17:30', 'end': '21:30', 'duration': 4},
    {'start': '17:30', 'end': '21:30', 'duration': 4},
]  # Requires 6 staff per role (12 total)
```

---

## 5. User Interface Design

### 5.1 Schedule Manager View

Similar to Tour Guide Schedule Manager but adapted for shifts:

```
┌────────────────────────────────────────────────────────────┐
│  Restaurant Staff Schedule - February 16, 2026             │
├────────────────────────────────────────────────────────────┤
│  [← Feb 15]  [Today: Feb 16, 2026]  [Feb 17 →]           │
├────────────────────────────────────────────────────────────┤
│  [⚡ Auto-Assign] [📄 Export CSV] [💾 Save] [✓ Publish]   │
└────────────────────────────────────────────────────────────┘

KITCHEN STAFF (Minimum 2 at all times)
┌──────────┬──────────────────────────────────────────────┐
│ Time     │ 10  11  12  13  14  15  16  17  18  19  20  21│
├──────────┼──────────────────────────────────────────────┤
│ Alice    │ █████████████████████████                    │
│ Bob      │ █████████████████████████                    │
│ Charlie  │                      █████████████████████   │
│ Diana    │                      █████████████████████   │
└──────────┴──────────────────────────────────────────────┘
Coverage:     2   2   2   2   4   4   4   4   2   2   2   2

SERVING STAFF (Minimum 2 at all times)
┌──────────┬──────────────────────────────────────────────┐
│ Time     │ 10  11  12  13  14  15  16  17  18  19  20  21│
├──────────┼──────────────────────────────────────────────┤
│ Emma     │ █████████████████████████                    │
│ Frank    │ █████████████████████████                    │
│ Grace    │                      █████████████████████   │
│ Henry    │                      █████████████████████   │
└──────────┴──────────────────────────────────────────────┘
Coverage:     2   2   2   2   4   4   4   4   2   2   2   2

Status Panel:
├─────────────────────┐
│ Coverage            │
│ Kitchen:  100% ✓    │
│ Serving:  100% ✓    │
│                     │
│ Staff Count         │
│ Kitchen:  4         │
│ Serving:  4         │
│ Total:    8         │
│                     │
│ Issues              │
│ ✓ All good!         │
└─────────────────────┘
```

### 5.2 Key Features

1. **Timeline View**: Horizontal bars showing 8-hour shifts
2. **Coverage Display**: Show number of staff working each hour
3. **Warning Indicators**: Highlight hours below minimum coverage
4. **Click to Edit**: Click shift to modify start/end time or assign different staff
5. **Auto-Assign**: Automatically fills optimal shift pattern
6. **CSV Export**: Export schedule for payroll/reporting

---

## 6. Integration with Existing Scheduling App

### 6.1 App Structure

Integrate into existing `apps/scheduling/` as a separate module:

```
apps/scheduling/
├── models.py              # Existing: Guide, TourSession, etc.
│                         # NEW: RestaurantStaff, StaffShift, etc.
├── views.py              # Existing: schedule_manager (tours)
│                         # NEW: restaurant_schedule_manager
├── api_views.py          # Existing: tour APIs
│                         # NEW: restaurant APIs
├── services.py           # Existing: SchedulingService (tours)
│                         # NEW: RestaurantSchedulingService
├── urls.py               # Add new restaurant routes
├── templates/scheduling/
│   ├── schedule_manager.html           # Existing (tours)
│   └── restaurant_schedule_manager.html # NEW (restaurant)
└── static/scheduling/
    ├── schedule_manager.css            # Existing
    └── restaurant_schedule_manager.css # NEW
```

### 6.2 Navigation Structure

Add restaurant scheduler as separate dashboard accessible from admin:

```
Django Admin
├── Scheduling
│   ├── Tour Guides
│   ├── Tour Sessions
│   ├── Daily Schedules
│   └── 📅 Tour Schedule Manager     ← Existing
│
└── Restaurant Staffing (NEW)
    ├── Kitchen Staff
    ├── Serving Staff
    ├── Staff Shifts
    ├── Daily Restaurant Schedules
    └── 📅 Restaurant Schedule Manager ← NEW (separate dashboard)
```

### 6.3 URL Structure

```python
# apps/scheduling/urls.py

urlpatterns = [
    # Existing tour routes
    path('manager/', views.schedule_manager, name='schedule_manager'),
    path('api/assign/', api_views.assign_guide, name='api_assign_guide'),
    path('api/auto-assign/', api_views.auto_assign, name='api_auto_assign'),
    # ... other tour routes

    # NEW: Restaurant routes
    path('restaurant/', views.restaurant_schedule_manager, name='restaurant_schedule_manager'),
    path('restaurant/api/schedule/<str:date>/', api_views.get_restaurant_schedule),
    path('restaurant/api/auto-assign/', api_views.auto_assign_restaurant_staff),
    path('restaurant/api/assign-shift/', api_views.assign_shift),
    path('restaurant/api/publish/', api_views.publish_restaurant_schedule),
    path('restaurant/api/export/<str:date>/', api_views.export_restaurant_csv),
]
```

### 6.4 Separate Models (No Overlap)

**Clear separation:**
- Tour scheduling: `Guide`, `TourSession`, `TourTimeSlot`, `DailySchedule`
- Restaurant staffing: `RestaurantStaff`, `StaffShift`, `DailyRestaurantSchedule`, `StaffAvailability`

**No shared tables or data between tour guides and restaurant staff**

### 6.5 Admin Registration

```python
# apps/scheduling/admin.py

# Existing tour admin
@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    ...

@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    ...

# NEW: Restaurant admin
@admin.register(RestaurantStaff)
class RestaurantStaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'staff_type', 'is_active', 'hire_date']
    list_filter = ['staff_type', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(DailyRestaurantSchedule)
class DailyRestaurantScheduleAdmin(admin.ModelAdmin):
    list_display = ['date', 'is_published', 'published_at']
    list_filter = ['is_published', 'date']
    actions = ['open_schedule_manager']

    def open_schedule_manager(self, request, queryset):
        # Redirect to restaurant schedule manager
        if queryset.count() == 1:
            schedule = queryset.first()
            return redirect(f'/schedule/restaurant/?date={schedule.date}')
```

## 7. Implementation Plan

### Phase 1: Data Models (1 day)
- [ ] Create `RestaurantStaff` model
- [ ] Create `StaffAvailability` model
- [ ] Create `DailyRestaurantSchedule` model
- [ ] Create `StaffShift` model
- [ ] Run migrations
- [ ] Add sample data

### Phase 2: Admin Interface (1 day)
- [ ] Register models in admin
- [ ] Create staff management interface
- [ ] Add availability management
- [ ] Test CRUD operations

### Phase 3: Auto-Scheduler Algorithm (2 days)
- [ ] Implement `RestaurantSchedulingService`
- [ ] Write shift assignment logic
- [ ] Add coverage validation
- [ ] Test with various scenarios
- [ ] Optimize for minimum staff

### Phase 4: Schedule Manager UI (3 days)
- [ ] Create `restaurant_schedule_manager.html` template
- [ ] Build timeline view (horizontal shift bars)
- [ ] Add coverage indicators
- [ ] Implement click-to-edit functionality
- [ ] Add status panel

### Phase 5: API Endpoints (2 days)
- [ ] GET `/restaurant/api/schedule/<date>/` - Fetch schedule
- [ ] POST `/restaurant/api/auto-assign/` - Run auto-scheduler
- [ ] POST `/restaurant/api/assign-shift/` - Manual assignment
- [ ] POST `/restaurant/api/publish/` - Publish schedule
- [ ] GET `/restaurant/api/export/<date>/` - CSV export

### Phase 6: Testing & Polish (2 days)
- [ ] Write unit tests
- [ ] Test edge cases (insufficient staff, unavailable staff)
- [ ] Add validation messages
- [ ] Polish UI/UX
- [ ] Write documentation

**Total Estimated Time:** 11 days

---

## 7. API Endpoints

### 7.1 Get Schedule
```
GET /restaurant/api/schedule/<date>/

Response:
{
  "date": "2026-02-16",
  "is_published": false,
  "kitchen_shifts": [
    {
      "id": 1,
      "staff_id": 5,
      "staff_name": "Alice Smith",
      "start_time": "10:00",
      "end_time": "18:00"
    },
    ...
  ],
  "serving_shifts": [...],
  "coverage": {
    "10:00": {"kitchen": 2, "serving": 2},
    "11:00": {"kitchen": 2, "serving": 2},
    ...
  },
  "stats": {
    "kitchen_staff_count": 4,
    "serving_staff_count": 4,
    "total_staff": 8,
    "coverage_valid": true
  }
}
```

### 7.2 Auto-Assign
```
POST /restaurant/api/auto-assign/

Request:
{
  "date": "2026-02-16"
}

Response:
{
  "success": true,
  "kitchen_assigned": 4,
  "serving_assigned": 4,
  "total_staff": 8,
  "message": "Successfully assigned 8 staff (4 kitchen, 4 serving)"
}
```

### 7.3 Manual Shift Assignment
```
POST /restaurant/api/assign-shift/

Request:
{
  "shift_id": 123,
  "staff_id": 5,
  "start_time": "10:00",
  "end_time": "18:00"
}

Response:
{
  "success": true,
  "errors": []
}
```

---

## 8. Database Schema

```sql
-- Restaurant Staff
CREATE TABLE restaurant_staff (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    staff_type VARCHAR(20),  -- 'kitchen' or 'serving'
    is_active BOOLEAN,
    hire_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Staff Availability
CREATE TABLE staff_availability (
    id INTEGER PRIMARY KEY,
    staff_id INTEGER REFERENCES restaurant_staff(id),
    date DATE,
    is_available BOOLEAN,
    notes TEXT,
    UNIQUE(staff_id, date)
);

-- Daily Restaurant Schedule
CREATE TABLE daily_restaurant_schedule (
    id INTEGER PRIMARY KEY,
    date DATE UNIQUE,
    is_published BOOLEAN,
    published_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Staff Shifts
CREATE TABLE staff_shift (
    id INTEGER PRIMARY KEY,
    daily_schedule_id INTEGER REFERENCES daily_restaurant_schedule(id),
    staff_id INTEGER REFERENCES restaurant_staff(id),
    start_time TIME,
    end_time TIME,
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 9. Validation Rules

### 9.1 Shift Validation
- Shift must be either 4 hours OR 8 hours (no other durations)
- Start time must be within operating hours (10:00 AM - 9:30 PM)
- End time must be within operating hours (10:00 AM - 9:30 PM)
- End time must equal start time + duration (e.g., 10:00 AM + 4h = 2:00 PM)
- Staff can only have one shift per day
- Staff must be available on that date
- Staff type (kitchen/serving) must match shift requirements

### 9.2 Coverage Validation
- At all times during 10:00 AM - 9:30 PM:
  - Minimum 2 kitchen staff working
  - Minimum 2 serving staff working

### 9.3 Publishing Validation
Before publishing, check:
- [ ] All hours have minimum coverage (2 kitchen + 2 serving)
- [ ] No overlapping shifts for same staff member
- [ ] All assigned staff are available

---

## 10. Future Enhancements

### Version 2.0 (Optional)
- [ ] Flexible shift durations (6-hour, 10-hour shifts)
- [ ] Break scheduling (explicit 30-min breaks)
- [ ] Skill levels (Chef, Sous Chef, Line Cook, Server, Busser)
- [ ] Position assignments (Station 1, Station 2, Bar, Patio)
- [ ] Overtime tracking and alerts
- [ ] Labor cost optimization
- [ ] Integration with tour bookings (adjust serving staff based on tour group size)
- [ ] Staff preferences (preferred shifts, days off)
- [ ] Seniority-based assignment
- [ ] Mobile app for staff to view their schedules

---

## 11. Success Metrics

### Efficiency Metrics
- **Staff utilization**: 8 staff per day (4 kitchen + 4 serving)
- **Coverage rate**: 100% (minimum 2 per role at all times)
- **Scheduling time**: < 30 seconds to auto-assign

### Quality Metrics
- **Assignment accuracy**: 100% (all shifts meet constraints)
- **Manager satisfaction**: Reduce manual scheduling time by 80%
- **Staff satisfaction**: Fair and balanced shift distribution

---

## 12. Constraints Summary

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Operating Hours | 10:00 AM - 9:30 PM | Match restaurant hours |
| Shift Duration | 8 hours (fixed) | Standardized workday |
| Minimum Kitchen Staff | 2 at all times | Food safety & efficiency |
| Minimum Serving Staff | 2 at all times | Customer service coverage |
| Max Shifts per Staff | 1 per day | No overtime/split shifts |
| Optimization Goal | Minimize total staff | Reduce labor costs |

---

## 13. Example Schedule

**Date:** February 16, 2026

### Kitchen Staff
| Staff | Shift | Hours |
|-------|-------|-------|
| Alice | 10:00 AM - 6:00 PM | 8 |
| Bob | 10:00 AM - 6:00 PM | 8 |
| Charlie | 1:30 PM - 9:30 PM | 8 |
| Diana | 1:30 PM - 9:30 PM | 8 |

### Serving Staff
| Staff | Shift | Hours |
|-------|-------|-------|
| Emma | 10:00 AM - 6:00 PM | 8 |
| Frank | 10:00 AM - 6:00 PM | 8 |
| Grace | 1:30 PM - 9:30 PM | 8 |
| Henry | 1:30 PM - 9:30 PM | 8 |

### Coverage Analysis
```
Time     Kitchen Serving
10:00    2       2       ✓
11:00    2       2       ✓
12:00    2       2       ✓ (lunch rush starts)
13:00    2       2       ✓
13:30    4       4       ✓✓ (overlap)
14:00    4       4       ✓✓
15:00    4       4       ✓✓
16:00    4       4       ✓✓
17:00    4       4       ✓✓
18:00    2       2       ✓ (dinner rush ends)
19:00    2       2       ✓
20:00    2       2       ✓
21:00    2       2       ✓
21:30    2       2       ✓
```

**Result:** 100% coverage with 8 total staff (optimal)

---

**End of Specification**
