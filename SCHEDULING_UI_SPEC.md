# Unified Scheduling Interface Specification

**Version:** 1.0
**Date:** 2026-02-15
**Status:** Draft for Discussion

---

## Executive Summary

This specification proposes a redesign of the Tour Guide Scheduler's administration interface to consolidate the four separate "Scheduling" section items into a single, unified calendar-based scheduling interface. The new interface will serve as the primary tool for managers to view, create, edit, and validate tour guide schedules.

---

## 1. Current State Analysis

### 1.1 Existing Structure

The current admin interface has **4 separate items** under "Scheduling":
1. **Daily schedules** - Manage daily schedules with inline session editing
2. **Shift swap requests** - Handle guide swap requests
3. **Tour sessions** - Individual session management
4. **Tour time slots** - Time slot definitions (8:30am-10pm)

### 1.2 Current Workflow

Manager workflow requires navigating between multiple screens:
- Select a Daily schedule record → Opens detail page with inline TourSession editor
- Or go to Tour sessions list → Filter by date → Edit individual sessions
- Validation feedback appears in list columns or detail pages
- Auto-scheduling triggered via admin action or command line

### 1.3 Existing Assets

The application already has:
- **Schedule Overview view** (apps/scheduling/views.py:10-132)
  - Grid layout: Time slots (rows) × Guides (columns)
  - Read-only calendar visualization
  - Feasibility indicators (green/yellow/red)
  - Navigation between dates
- **Auto-scheduling algorithm** (services.py:289-408)
  - Constraint-satisfaction greedy algorithm
  - Workload balancing
- **Validation engine** (services.py:94-287)
  - Real-time constraint checking
  - Guide type compatibility
  - Break requirements
  - Availability checks

### 1.4 Pain Points

Current issues with the existing interface:
- **Context switching**: Managers must navigate between multiple admin pages
- **Limited overview**: Can't see the full day's schedule at a glance in edit mode
- **Separate validation**: Validation happens after assignments, not inline
- **Manual navigation**: Must use command line or remember to click admin actions
- **No quick undo**: Can't easily revert to auto-assigned schedule

---

## 2. Proposed Solution

### 2.1 Design Vision

**Single Primary Interface**: Replace the 4 admin items with 1 unified "**Schedule Manager**" that combines:
- Calendar grid visualization (time slots × guides)
- Inline editing capabilities
- Real-time validation feedback
- Integrated auto-scheduling controls
- Status panel with actionable insights

### 2.2 Interface Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ TOUR GUIDE SCHEDULER - SCHEDULE MANAGER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  [< Feb 14] ▼ Feb 15, 2026 (Friday) [Feb 16 >]   [Today]                     │
│                                                                                 │
│  Standby: [John Doe ▼]  Status: [Draft ▼]  [Auto-Assign] [Export CSV] [Save] [Publish] │
│                                                                                 │
├───────────────────────────────────────────────────┬─────────────────────────────┤
│                                                   │  STATUS PANEL               │
│  SCHEDULE GRID                                    │                             │
│  (Time slots × Guides)                            │  Coverage: 18/24 (75%)     │
│                                                   │                             │
│  [Interactive Calendar View]                      │  Booking Stats:             │
│                                                   │  • Total: 425 visitors      │
│                                                   │  • Local: 280 (66%)         │
│                                                   │  • Intl: 145 (34%)          │
│                                                   │                             │
│                                                   │  ⚠ Issues:                  │
│                                                   │  • 6 unassigned slots       │
│                                                   │  • 2 constraint errors      │
│                                                   │  • 3 missing booking info   │
│                                                   │                             │
│                                                   │  [View Details]             │
│                                                   │                             │
│                                                   │  Quick Actions:             │
│                                                   │  [Clear All]                │
│                                                   │  [Revert Changes]           │
│                                                   │                             │
└───────────────────────────────────────────────────┴─────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 Navigation Bar

**Location**: Top of the interface

**Components**:
- **Date selector**:
  - Previous day button: `[<]`
  - Date dropdown or picker: Shows "February 15, 2026 (Friday)"
  - Next day button: `[>]`
  - "Today" quick-jump button
- **Quick filters** (optional for future):
  - Week view toggle
  - Month view toggle

**Behavior**:
- Clicking prev/next loads adjacent date's schedule
- Date picker allows jumping to any date (with 2-week-ahead validation)
- "Today" button returns to current date
- URL updates with date parameter (?date=2026-02-15)

---

### 3.2 Control Bar

**Location**: Below navigation, above grid

**Components**:

1. **Standby Guide Selector**
   - Label: "Standby:"
   - Dropdown: Shows all active guides
   - Required field (red border if empty)
   - Auto-saves on change

2. **Status Indicator**
   - Display: Badge showing "Draft" (yellow) or "Published" (green)
   - Or: Dropdown to change status if permissions allow

3. **Auto-Assign Button**
   - Label: "Auto-Assign" or "Run Auto-Schedule"
   - Icon: 🤖 or ⚡
   - Behavior:
     - Triggers auto-scheduling algorithm for current date
     - Shows loading indicator during processing
     - Displays results in modal or status panel
     - Option: "Auto-assign only unassigned slots" checkbox

4. **Export CSV Button** *(NEW - MVP Requirement)*
   - Label: "Export CSV"
   - Icon: 📄 or ⬇
   - Behavior:
     - Downloads CSV file: `schedule_YYYY-MM-DD.csv`
     - Includes all time slots with guide assignments and booking details
     - Compatible with Excel/Google Sheets
     - One-way export (no import for MVP)

5. **Publish Button**
   - Label: "Publish Schedule"
   - Icon: ✓
   - Enabled only when:
     - All slots assigned
     - Standby guide assigned
     - No validation errors
   - Confirmation dialog before publishing

6. **Additional Actions** (dropdown menu):
   - "Clear All Assignments" - Unassign all guides
   - "Duplicate from Previous Day" - Copy assignments
   - "View as Guide" - Preview guide's schedule
   - Future: "Export to PDF", "Import CSV"

---

### 3.3 Schedule Grid (Main Calendar)

**Layout**: Matrix with sticky headers

#### 3.3.1 Structure

**Columns** (Left to Right):
1. **Status Column** (30px): Feasibility indicator per slot
   - ✓ Green: Slot filled
   - ⚠ Yellow: Not assigned but fillable
   - ✗ Red: Cannot fill (no eligible guides)
   - Gray: Unknown/no schedule

2. **Time Slot Column** (150px): Time range display
   - Format: "8:30 AM - 10:30 AM"
   - Sticky left position

3. **Guide Columns** (100px each): One column per active guide
   - Header: Guide name + guide type badge
   - Example: "John Doe [FT]"

**Rows** (Top to Bottom):
- Header row: Guide names (sticky on scroll)
- Data rows: 24 rows (one per time slot, 8:30am-10pm)

#### 3.3.2 Cell Types

**Cell States**:

1. **Assigned Cell** (Guide is working)
   - Background: Light green (#d1e7dd)
   - Display format (compact):
     ```
     ✓ JD
     25👥 Local
     Online
     ```
     Or minimal: `✓ JD • 25👥` (if space constrained)
   - **Editable**: Click to change guide, booking details, or unassign
   - Border: 2px solid green if valid, red if constraint violation
   - Tooltip: Full details on hover

2. **Available Cell** (Guide not assigned but can work)
   - Background: White or light gray
   - Text: "-" or blank
   - **Editable**: Click to assign guide
   - Hover: Shows "Click to assign"

3. **Incompatible Cell** (Guide type mismatch)
   - Background: Medium gray (#e2e3e5)
   - Text: "N/A" or "⊘"
   - **Non-editable**: Disabled/dimmed
   - Tooltip: "PTM guide cannot work afternoon slots"

4. **Validation Error Cell** (Assigned but violates constraint)
   - Background: Light red (#f8d7da)
   - Icon: ✗
   - Border: 2px solid red
   - **Editable**: Shows error on hover
   - Tooltip: "Less than 1-hour break between tours"

#### 3.3.3 Editing Behavior

**Click Interaction**:
- **On empty/available cell**: Opens assignment popover
  - Guide selector dropdown (shows only eligible guides, filtered by constraints)
  - Sorted by: Fewest assignments first (workload balancing)
  - **NEW: Booking details fields** (optional):
    - Visitor count: [____] (number input)
    - Visitor type: [ Local ▼ ] (dropdown: Local/International)
    - Channel: [ Online ▼ ] (dropdown: Online/Walk-in/Direct)
  - Buttons: "Assign" | "Cancel"

- **On assigned cell**: Opens edit popover
  - Current guide shown with "Change guide" dropdown (filtered list)
  - **NEW: Booking details** (editable):
    - Visitor count: [25]
    - Visitor type: [Local ▼]
    - Channel: [Online ▼]
  - Validation status display
  - Buttons: "Save Changes" | "Unassign" | "Cancel"

**Drag-and-drop** (Future enhancement):
- Drag guide name from header to cells
- Drag between cells to swap

**Keyboard shortcuts** (Future enhancement):
- Tab: Navigate between cells
- Enter: Open editor
- Esc: Cancel edit
- Ctrl+Z: Undo last change

#### 3.3.4 Visual Indicators

**Row-level indicators**:
- Highlight current time (if viewing today)
- Zebra striping for readability
- Bold time slots that are unfillable

**Column-level indicators**:
- Show total assignments per guide in header
- Example: "John Doe [FT] (6)" = 6 assignments today
- Color-code workload: Green (<6), Yellow (6-8), Red (>8)

---

### 3.4 Status Panel (Side Panel)

**Location**: Right side of screen (300px width, collapsible)

**Sections**:

#### 3.4.1 Coverage Summary
```
┌─────────────────────────┐
│ COVERAGE                │
│                         │
│ 18 / 24 slots filled    │
│ ████████░░  75%         │
│                         │
└─────────────────────────┘
```
- Progress bar showing completion %
- Count: Assigned / Total slots
- Color: Green (100%), Yellow (50-99%), Red (<50%)

#### 3.4.2 Issues & Warnings

**Unassigned Slots** (if any):
```
⚠ 6 Unassigned Slots:
  • 8:30 AM - 10:30 AM
  • 9:00 AM - 11:00 AM
  • 10:00 AM - 12:00 PM
  ...
[Auto-Assign These]
```

**Constraint Violations** (if any):
```
✗ 2 Constraint Errors:
  • 2:30 PM - 4:30 PM
    John Doe: No 1-hour break
  • 8:00 PM - 10:00 PM
    Jane Smith: Marked unavailable
[View Details] [Fix Now]
```

**Feasibility Issues** (if any):
```
⚠ 3 Unfillable Slots:
  • 12:00 PM - 2:00 PM
    No eligible guides available
[Adjust Availability]
```

#### 3.4.3 Schedule Metadata

```
Standby Guide: John Doe ✓
Published: No
Created: Feb 10, 2026
Last Modified: Feb 15, 2026 10:23 AM
```

#### 3.4.4 Quick Stats

```
Guide Workload:
  • John Doe: 8 sessions
  • Jane Smith: 6 sessions
  • Bob Wilson: 5 sessions
  ...
[Balance Workload]
```

#### 3.4.5 Action Buttons

- **[View Details]**: Opens modal with full validation report
- **[Clear All]**: Unassigns all guides (with confirmation)
- **[Revert Changes]**: Undo all unsaved edits (if autosave disabled)
- **[Run Validation]**: Force re-check all constraints

---

### 3.5 Auto-Assignment Flow

**Trigger**: User clicks "Auto-Assign" button

**Process**:
1. **Confirmation Dialog** (if assignments already exist):
   ```
   ┌─────────────────────────────────────────┐
   │ Auto-Assign Guides?                     │
   ├─────────────────────────────────────────┤
   │                                         │
   │ This will automatically assign guides   │
   │ to unassigned slots.                    │
   │                                         │
   │ [ ] Overwrite existing assignments      │
   │ [✓] Only fill empty slots               │
   │ [✓] Assign standby guide                │
   │                                         │
   │       [Cancel]  [Auto-Assign]           │
   └─────────────────────────────────────────┘
   ```

2. **Processing**:
   - Show loading overlay on grid
   - Call `SchedulingService.auto_schedule_day()`
   - Update cells in real-time as assignments are made (optional)

3. **Results Modal**:
   ```
   ┌─────────────────────────────────────────┐
   │ Auto-Assignment Complete                │
   ├─────────────────────────────────────────┤
   │                                         │
   │ ✓ Assigned: 18 sessions                 │
   │ ✗ Could not fill: 6 sessions            │
   │                                         │
   │ Unfillable Sessions:                    │
   │  • 8:30 AM - 10:30 AM (no guides)       │
   │  • 9:00 AM - 11:00 AM (no guides)       │
   │  ...                                    │
   │                                         │
   │ Standby: John Doe (auto-assigned)       │
   │                                         │
   │       [View Schedule]  [Close]          │
   └─────────────────────────────────────────┘
   ```

4. **Grid Update**:
   - Cells update to show new assignments
   - Status panel refreshes with new stats
   - Unsaved changes indicator appears (if not auto-saving)

---

### 3.6 Revert Functionality

**Trigger**: User clicks "Revert" or "Undo" button

**Options**:

1. **Revert to Last Saved**:
   - Restores schedule to last published/saved state
   - Discards all unsaved changes in current session

2. **Revert to Auto-Assigned**:
   - Re-runs auto-assignment algorithm
   - Discards all manual edits
   - Useful when manual changes created problems

3. **Undo Last Action**:
   - Simple undo stack for last N changes
   - Ctrl+Z keyboard shortcut

**Confirmation Dialog**:
```
┌─────────────────────────────────────────┐
│ Revert Changes?                         │
├─────────────────────────────────────────┤
│                                         │
│ This will discard all unsaved changes   │
│ since the last save.                    │
│                                         │
│ Are you sure?                           │
│                                         │
│       [Cancel]  [Yes, Revert]           │
└─────────────────────────────────────────┘
```

---

## 4. Functional Requirements

### 4.1 Core Features

| Feature | Priority | Description |
|---------|----------|-------------|
| Grid visualization | P0 (Must-have) | Display time slots × guides matrix |
| Inline editing | P0 | Click-to-edit cell assignments |
| Auto-assignment | P0 | One-click automatic scheduling |
| Real-time validation | P0 | Instant constraint checking |
| Status panel | P0 | Show unassigned & errors |
| Date navigation | P0 | Browse different dates |
| Standby selection | P0 | Assign standby guide |
| Publish workflow | P0 | Publish schedules to guides |
| Revert changes | P1 (Should-have) | Undo manual edits |
| Workload balancing UI | P1 | Visual workload indicators |
| Keyboard shortcuts | P2 (Nice-to-have) | Power user efficiency |
| Drag-and-drop | P2 | Intuitive guide assignment |
| Export PDF | P3 (Future) | Print-friendly schedules |

### 4.2 Validation Rules (Enforced in UI)

The interface must enforce these constraints in real-time:

1. **Guide Type Compatibility**:
   - Full-time (FT): Can work any slot
   - Part-time Morning (PTM): Only slots ending by 2:30 PM
   - Part-time Afternoon (PTA): Only slots starting from 2:30 PM
   - UI: Disable incompatible cells, show "N/A"

2. **Break Requirement**:
   - Guides must have ≥1 hour continuous break between tours
   - UI: Show error border if violated, block assignment in dropdown

3. **Availability Check**:
   - Guides must be marked available for the date
   - UI: Filter unavailable guides from dropdown, show warning if assigned

4. **Standby Requirement**:
   - Each day must have 1 standby guide before publishing
   - UI: Red border on standby dropdown if empty, disable Publish button

5. **Complete Coverage** (for publishing):
   - All 24 sessions must be assigned
   - UI: Disable Publish button if unassigned slots exist

### 4.3 Data Persistence

**Manual Save Strategy** (APPROVED):
- ✓ **Manual save with session state** (Option B selected)
  - Changes stored in browser/component state
  - "Save" button required to persist to database
  - "Cancel" / "Revert" discards unsaved changes
  - Unsaved changes indicator (e.g., "*" or warning badge)
  - Confirmation dialog if navigating away with unsaved changes
  - Pros: User control, batch updates, fewer server requests, easy to cancel
  - Cons: Risk of data loss if not saved (mitigated by warnings)

**Implementation Details:**
- Client-side state management: Alpine.js reactive data
- Save button triggers AJAX POST to save all changes
- Visual indicators: "Save" button highlighted when changes exist
- Browser beforeunload warning: "You have unsaved changes"
- Auto-save disabled; user has full control

### 4.4 Performance Considerations

**Data Loading**:
- Load schedule data via AJAX (don't reload page on date change)
- Cache guide list (doesn't change often)
- Prefetch adjacent dates for faster navigation

**Rendering**:
- 24 rows × ~10 guides = ~240 cells (manageable in browser)
- Use virtual scrolling if guide count exceeds 20
- Lazy-load feasibility calculations for cells outside viewport

**Validation**:
- Run validation on client-side first (instant feedback)
- Confirm with server-side validation on save
- Debounce validation for rapid changes

---

## 5. User Workflows

### 5.1 Daily Scheduling (Manager)

**Scenario**: Manager needs to schedule guides for March 1st

1. Open "Schedule Manager" from admin nav
2. Select date: March 1, 2026
3. If no schedule exists: Click "Create Schedule" → generates 24 empty sessions
4. Click "Auto-Assign" → algorithm fills most slots
5. Review status panel: "22/24 filled, 2 unfillable"
6. Manually review unfillable slots:
   - Check why (no guides available)
   - Adjust guide availability if needed
   - Or leave unfilled and document
7. Assign standby guide from dropdown
8. Check status panel: "✓ No validation errors"
9. Click "Publish" → Schedule visible to guides

**Time estimate**: 2-5 minutes per day

### 5.2 Manual Adjustment (Manager)

**Scenario**: Manager needs to swap two guides

1. Navigate to schedule date
2. Click on assigned cell (Guide A, 2:30 PM slot)
3. Popover opens → Select "Change guide"
4. Choose Guide B from dropdown
5. Cell updates, validation runs
6. If error (e.g., Guide B violates break rule):
   - Red border appears
   - Tooltip shows error
   - Manager reverts or adjusts further
7. Continue adjustments until validation passes
8. Re-publish if schedule was already published

**Time estimate**: 30 seconds per swap

### 5.3 Constraint Violation Fix (Manager)

**Scenario**: Status panel shows "2 constraint errors"

1. Click "View Details" in status panel
2. Modal lists violations:
   - "2:30 PM slot: John Doe has no 1-hour break"
   - "8:00 PM slot: Jane Smith marked unavailable"
3. Click on first error → Grid scrolls to 2:30 PM row, highlights John Doe's column
4. Manager sees adjacent assignments causing conflict
5. Unassign one conflicting slot or reassign to different guide
6. Validation re-runs, error clears
7. Repeat for second error
8. Status panel updates: "✓ No validation errors"

**Time estimate**: 1-3 minutes per error

### 5.4 Revert After Mistake (Manager)

**Scenario**: Manager made several manual changes that broke the schedule

1. Status panel shows multiple errors
2. Manager clicks "Revert Changes" dropdown
3. Selects "Revert to Auto-Assigned"
4. Confirmation dialog: "This will discard all manual changes"
5. Clicks "Yes, Revert"
6. Grid reloads with auto-assigned state
7. All validation errors cleared

**Time estimate**: 5 seconds

---

## 6. Technical Implementation

### 6.1 Architecture

**Approach**: Custom Django Admin View (not ModelAdmin)

**Rationale**:
- Django admin's `ModelAdmin` is optimized for list/detail forms
- Schedule grid requires custom layout and interaction
- Better to create a custom admin view with full control

**Integration Point**:
- Register custom view in admin site
- Add to admin navigation under "Scheduling"
- Replace existing 4 admin models (hide or relocate)

### 6.2 Technology Stack

**Backend**:
- Django view: `ScheduleManagerView` (class-based view)
- API endpoints: AJAX for cell updates, auto-assign, validation
- Service layer: Reuse existing `SchedulingService`

**Frontend**:
- Template: Custom HTML template extending `admin/base_site.html`
- CSS: Bootstrap 5 + custom grid styles (can reuse from schedule_overview.html)
- JavaScript:
  - Vanilla JS or jQuery (already in Django admin)
  - Or: Alpine.js / HTMX for reactivity (lightweight)
  - Or: Vue.js / React component (heavier, more powerful)

**Recommendation**: **HTMX + Alpine.js** for reactive UI without heavy JS framework overhead.

### 6.3 Data Models (UPDATED with Booking Details)

**Existing models to reuse:**
- `DailySchedule`: Date, standby_guide, is_published
- `TourTimeSlot`: start_time, end_time
- `Guide`: user, guide_type, is_active

**Modified model:**
- `TourSession`: **REQUIRES NEW FIELDS**
  - Existing: daily_schedule, time_slot, assigned_guide, status, notes
  - **NEW FIELDS** (for booking details):
    - `visitor_count`: IntegerField (nullable, default=None)
    - `visitor_type`: CharField choices: 'local' | 'international' (nullable)
    - `booking_channel`: CharField choices: 'online' | 'walkin' | 'direct' (nullable)
  - Migration required

**New model** (optional):
- `ScheduleSnapshot`: Store schedule history for revert functionality
  - Fields: daily_schedule, snapshot_type ('auto'|'manual'|'published'), data (JSON), created_at

### 6.4 API Endpoints

**RESTful endpoints** for AJAX operations:

1. **GET /admin/scheduling/manager/api/schedule/<date>/**
   - Returns: Grid data (guides, sessions, feasibility)
   - Format: JSON

2. **POST /admin/scheduling/manager/api/session/<id>/assign/**
   - Body: `{guide_id: 123}` or `{guide_id: null}` to unassign
   - Returns: Validation result, updated session
   - Side effect: Saves to database (auto-save)

3. **POST /admin/scheduling/manager/api/schedule/<date>/auto-assign/**
   - Body: `{overwrite: false, assign_standby: true}`
   - Returns: Auto-assignment results (assigned, unfillable)
   - Side effect: Updates all sessions

4. **POST /admin/scheduling/manager/api/schedule/<date>/publish/**
   - Returns: Validation result, success/failure
   - Side effect: Sets is_published=True

5. **POST /admin/scheduling/manager/api/schedule/<date>/revert/**
   - Body: `{revert_type: 'auto'|'last_saved'}`
   - Returns: Reverted schedule data
   - Side effect: Reloads assignments from snapshot

6. **GET /admin/scheduling/manager/api/schedule/<date>/validate/**
   - Returns: Detailed validation report (for status panel)

7. **GET /admin/scheduling/manager/api/schedule/<date>/export/** *(NEW - MVP)*
   - Returns: CSV file download
   - Headers: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="schedule_YYYY-MM-DD.csv"`
   - Format: Flat list with columns (Date, Time Slot, Guide, Booking Details, Validation Status)

### 6.5 File Structure

```
apps/scheduling/
├── views.py
│   └── ScheduleManagerView (new)
├── api_views.py (new)
│   └── schedule_api_* functions
├── templates/scheduling/
│   └── schedule_manager.html (new)
├── static/scheduling/
│   ├── schedule_manager.css (new)
│   └── schedule_manager.js (new)
├── admin.py
│   └── Register custom admin view (modified)
└── services.py (existing, reused)
```

### 6.6 Admin Integration

**Option 1: Custom Admin View** (Recommended)
```python
# admin.py
from django.contrib import admin
from django.urls import path
from .views import ScheduleManagerView

class SchedulingAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('scheduling/manager/',
                 self.admin_view(ScheduleManagerView.as_view()),
                 name='scheduling_manager'),
        ]
        return custom_urls + urls

# Register in admin navigation
admin.site.register_view(
    'scheduling/manager/',
    view=ScheduleManagerView.as_view(),
    name='Schedule Manager',
    urlname='scheduling_manager'
)
```

**Option 2: Replace DailySchedule admin**
```python
@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        # Redirect to schedule manager instead of list view
        return ScheduleManagerView.as_view()(request)
```

---

## 6.7 Booking Details: Impact Analysis

### 6.7.1 Data Model Changes

**Required migration:**
```python
# Migration: Add booking details to TourSession
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='toursession',
            name='visitor_count',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='toursession',
            name='visitor_type',
            field=models.CharField(
                max_length=20,
                choices=[('local', 'Local'), ('international', 'International')],
                null=True,
                blank=True
            ),
        ),
        migrations.AddField(
            model_name='toursession',
            name='booking_channel',
            field=models.CharField(
                max_length=20,
                choices=[('online', 'Online Platform'), ('walkin', 'Walk-in'), ('direct', 'Direct Sales')],
                null=True,
                blank=True
            ),
        ),
    ]
```

### 6.7.2 UI Changes

**Grid cell display options:**

**Option A: Compact (Recommended)**
```
┌──────────────┐
│ ✓ JD         │  ← Guide initials
│ 25👥 Local   │  ← Visitor count + type
│ Online       │  ← Channel
└──────────────┘
```
Cell width: ~120px

**Option B: Minimal (if space constrained)**
```
┌──────────────┐
│ ✓ JD • 25👥  │  ← All in one line
└──────────────┘
```
Cell width: ~100px (hover for full details)

**Option C: Icon-based**
```
┌──────────────┐
│ ✓ JD         │
│ 👥25 🌍 💻   │  ← Icons for visual scanning
└──────────────┘
```
Legend: 👥=visitors, 🌍=international, 💻=online

### 6.7.3 Edit Popover Design

**Expanded edit form:**
```
┌─────────────────────────────────────┐
│ Edit Tour Session                   │
├─────────────────────────────────────┤
│                                     │
│ Guide:  [John Doe        ▼]         │
│         [Change...] [Unassign]      │
│                                     │
│ --- Booking Details ---             │
│                                     │
│ Visitors: [_____] people            │
│                                     │
│ Type:     ( ) Local                 │
│           (•) International         │
│                                     │
│ Channel:  [ ] Online Platform       │
│           [ ] Walk-in               │
│           [✓] Direct Sales          │
│                                     │
│         [Save Changes]  [Cancel]    │
└─────────────────────────────────────┘
```

### 6.7.4 Status Panel Enhancement

**Add booking statistics:**
```
┌─────────────────────────┐
│ COVERAGE                │
│ 18 / 24 slots filled    │
│ ████████░░  75%         │
└─────────────────────────┘

┌─────────────────────────┐
│ BOOKING STATS (NEW)     │
│                         │
│ Total Visitors: 425     │
│ - Local: 280 (66%)      │
│ - International: 145    │
│                         │
│ Channels:               │
│ - Online: 12 tours      │
│ - Walk-in: 4 tours      │
│ - Direct: 2 tours       │
│                         │
│ Missing Details: 3      │
└─────────────────────────┘
```

### 6.7.5 Auto-Assignment Impact

**Algorithm changes:**
- Auto-assignment only assigns guides (existing logic)
- Booking details remain empty after auto-assignment
- Manager must manually fill in booking details for each tour
- Alternative: Separate "bulk edit booking details" feature

**Recommendation:** Keep auto-assignment focused on guide assignment only.

### 6.7.6 Guide Portal Impact

**Current guide dashboard shows:**
- "You have 6 tours today"

**Enhanced with booking details:**
```
┌───────────────────────────────────────┐
│ Today's Tours (6)                     │
├───────────────────────────────────────┤
│ 8:30 AM - 10:30 AM                    │
│ • 25 visitors (Local)                 │
│ • Channel: Online                     │
├───────────────────────────────────────┤
│ 11:00 AM - 1:00 PM                    │
│ • 30 visitors (International)         │
│ • Channel: Direct Sales               │
├───────────────────────────────────────┤
│ ...                                   │
│                                       │
│ Total today: 150 visitors             │
└───────────────────────────────────────┘
```

**Benefit:** Guides can prepare better with advance visitor info.

### 6.7.7 CSV Export Feature (MVP Requirement)

**Purpose:** Allow managers to export daily schedule to CSV for offline viewing/editing in Excel.

**CSV Format (APPROVED - Grid Layout with Multi-line Cells):**

The export matches the visual grid layout: time slots as rows, guides as columns.

**Structure:**
- **Header row**: `Time Slot, [Guide 1 Name] ([Type]), [Guide 2 Name] ([Type]), ...`
- **Data rows**: One row per time slot (24 rows total)
- **Cell content**: For assigned sessions, semicolon-separated fields with line breaks:
  ```
  [Guide Type];
  [Visitor Count];
  [Visitor Type];
  [Booking Channel];
  [Notes]
  ```

**Example CSV Output:**

```csv
Time Slot,John Doe (FT),Jane Smith (PTM),Bob Wilson (PTA),Alice Brown (FT)
08:30 AM - 10:30 AM,"FT;25;Local;Online;","","N/A",""
09:00 AM - 11:00 AM,"FT;30;International;Direct;","PTM;20;Local;Walk-in;","N/A",""
09:30 AM - 11:30 AM,"","PTM;15;Local;Online;","N/A","FT;40;International;Direct;"
10:00 AM - 12:00 PM,"","","N/A","FT;25;Local;Walk-in;"
...
```

**When opened in Excel, each cell displays:**
```
┌─────────────────────┐
│ FT                  │
│ 25                  │
│ Local               │
│ Online              │
│                     │
└─────────────────────┘
```
(Excel shows line breaks within cell; double-click to edit)

**Cell States:**
- **Assigned**: Multi-line content with all booking details
- **Unassigned**: Empty string `""`
- **Incompatible**: `"N/A"` (e.g., PTM guide in afternoon slots)

**Key Features:**
- Grid layout matches the UI (easy visual correlation)
- All booking details preserved
- Excel-friendly format with quoted cells
- Sortable/filterable by guide columns
- Can apply Excel formulas (e.g., sum visitor counts)

**Button Location:**
```
Control Bar:
[Standby: John Doe ▼]  [Draft ▼]  [Auto-Assign]  [Export CSV]  [Save]  [Publish]
                                                   ^^^^^^^^^^^^
```

**Export Workflow:**
1. User clicks "Export CSV" button
2. Browser downloads file: `schedule_2026-02-15.csv`
3. Manager opens in Excel
4. Grid layout matches UI for easy reference
5. Can analyze, print, or share offline
6. **For MVP: Export only** (no re-import)

**Technical Implementation:**

**Python code snippet:**
```python
import csv
from io import StringIO

def export_schedule_csv(daily_schedule):
    output = StringIO()
    writer = csv.writer(output)

    # Header row: Time Slot + Guide names
    guides = Guide.objects.filter(is_active=True).order_by('user__first_name')
    header = ['Time Slot'] + [f"{g.user.get_full_name()} ({g.get_guide_type_display()})"
                                for g in guides]
    writer.writerow(header)

    # Data rows: One per time slot
    time_slots = TourTimeSlot.objects.all().order_by('start_time')
    for time_slot in time_slots:
        row = [f"{time_slot.start_time.strftime('%I:%M %p')} - {time_slot.end_time.strftime('%I:%M %p')}"]

        for guide in guides:
            # Check if guide can work this slot
            if not guide.can_work_timeslot(time_slot):
                row.append("N/A")
                continue

            # Find session for this time slot and guide
            session = TourSession.objects.filter(
                daily_schedule=daily_schedule,
                time_slot=time_slot,
                assigned_guide=guide
            ).first()

            if session:
                # Build multi-line cell content
                cell_lines = [
                    guide.get_guide_type_display(),
                    str(session.visitor_count) if session.visitor_count else "",
                    session.get_visitor_type_display() if session.visitor_type else "",
                    session.get_booking_channel_display() if session.booking_channel else "",
                    session.notes if session.notes else ""
                ]
                # Join with semicolons and newlines
                cell_content = ";\n".join(cell_lines)
                row.append(cell_content)
            else:
                # Unassigned
                row.append("")

        writer.writerow(row)

    return output.getvalue()
```

**Django view endpoint:**
- URL: `/admin/scheduling/manager/api/schedule/<date>/export/`
- Returns CSV file with headers:
  - `Content-Type: text/csv; charset=utf-8`
  - `Content-Disposition: attachment; filename="schedule_YYYY-MM-DD.csv"`
- Include UTF-8 BOM for Excel compatibility: `'\ufeff'`

**Excel Behavior:**
- Cells with newlines display as multi-line (Alt+Enter in Excel)
- Grid can be formatted (borders, colors) by manager
- Can be printed as-is for distribution
- Can copy-paste into emails or reports

**Future Enhancement (Post-MVP):**
- Import CSV: Allow editing in Excel and re-importing
- Validation on import: Check constraints before applying changes
- Additional export formats: PDF, Excel (.xlsx) with formatting
- Include standby guide info in header or footer
- Include daily statistics summary row

### 6.7.8 Additional Features to Consider (Post-MVP)

1. **Booking capacity validation:**
   - Set max visitors per tour (e.g., 50)
   - Show warning if exceeded

2. **Quick fill booking details:**
   - Bulk edit modal: "Apply to all unassigned bookings"
   - Template system: "Copy booking details from last week"

3. **Reporting enhancements:**
   - Daily/weekly visitor reports
   - Channel performance analytics
   - Local vs international trends

4. **CSV Import (two-way sync):**
   - Import edited CSV back into system
   - Validate assignments before applying
   - Conflict resolution UI

5. **PDF Export:**
   - Print-friendly schedule with booking details
   - Guide-specific schedules for distribution

## 7. Implementation Phases

### Phase 0: Data Model Update (1 day)
- [ ] Add booking detail fields to TourSession model
- [ ] Create and run migration
- [ ] Update model methods/properties
- [ ] Add choices for visitor_type and booking_channel
- [ ] Test migration on development database

**Deliverable**: Database ready for booking details

### Phase 1: Core Grid View (2-3 days)
- [ ] Create `ScheduleManagerView` with read-only grid
- [ ] Reuse grid layout from `schedule_overview.html`
- [ ] **NEW: Display booking details in cells** (compact format)
- [ ] Add date navigation
- [ ] Integrate into admin navigation
- [ ] Basic status panel (coverage only)

**Deliverable**: Managers can view schedules with booking details (read-only)

### Phase 2: Editing & Validation (4-5 days)
- [ ] Implement cell click → edit popover
- [ ] Guide selector dropdown (filtered by eligibility)
- [ ] **NEW: Booking details form fields in popover**
- [ ] Manual save (not auto-save) with "Save" button
- [ ] Real-time validation feedback (borders, tooltips)
- [ ] Status panel: Show unassigned slots & errors
- [ ] **NEW: Show booking statistics in status panel**

**Deliverable**: Managers can manually assign guides and enter booking details

### Phase 3: Auto-Assignment Integration (2 days)
- [ ] "Auto-Assign" button
- [ ] AJAX call to auto-schedule API
- [ ] Results modal
- [ ] Grid refresh after auto-assignment
- [ ] Options: overwrite vs. fill-only
- [ ] Note: Auto-assign only handles guide assignment, not booking details

**Deliverable**: Managers can auto-assign guides via UI

### Phase 4: Publishing, Export & Revert (2-3 days)
- [ ] Standby guide selector
- [ ] **NEW: "Export CSV" button and endpoint**
- [ ] **NEW: CSV generation with all booking details**
- [ ] "Save" button functionality (manual save)
- [ ] "Publish" button with validation gate
- [ ] "Revert" functionality with manual save integration
- [ ] Confirmation dialogs
- [ ] Success/error messaging
- [ ] Unsaved changes warning

**Deliverable**: Complete scheduling workflow with CSV export

### Phase 5: Polish & Testing (2-3 days)
- [ ] Responsive design (desktop-first, basic mobile)
- [ ] Loading states and spinners
- [ ] Error handling (network failures, etc.)
- [ ] User testing with manager
- [ ] Bug fixes and refinements
- [ ] Documentation update
- [ ] **NEW: Test booking details workflow thoroughly**

**Deliverable**: Production-ready interface

### Phase 6: Admin Cleanup (1 day)
- [ ] Keep old interfaces accessible (Option B decision)
- [ ] Keep "Tour time slots" as-is (editable per decision)
- [ ] Remove "Shift swap requests" (future feature)
- [ ] Update README with new workflow
- [ ] Add documentation for booking details

**Deliverable**: Simplified admin navigation with legacy fallback

### Phase 7 (Optional): Enhanced Features (3-5 days)
- [ ] Guide portal: Show booking details in tour list
- [ ] Booking capacity validation
- [ ] Bulk edit booking details
- [ ] Booking statistics reports
- [ ] Export with booking details

**Deliverable**: Enhanced booking management features

**Total Estimated Time**: 15-19 development days (+ 3-5 days for Phase 7 if desired)

**MVP Scope Summary:**
- Data model with booking details ✓
- Interactive schedule grid ✓
- Manual assignment with validation ✓
- Auto-assignment (guides only) ✓
- Booking details entry ✓
- CSV export ✓
- Publish workflow ✓
- Manual save with revert ✓

---

## 8. Design Decisions (APPROVED)

### 8.1 Scope Questions

1. **Should we keep the old admin interfaces as fallback?**
   - ✓ **DECISION: Option B** - Keep old interfaces accessible during transition period

2. **What happens to "Shift Swap Requests"?**
   - ✓ **DECISION: Remove from MVP** - Not required, consider as future feature

3. **Should "Tour Time Slots" remain editable?**
   - ✓ **DECISION: Make EDITABLE with booking details**
   - **NEW REQUIREMENT**: Each tour session needs these fields:
     - Number of visitors (integer)
     - Visitor type: Local / International
     - Channel: Online Platform / Walk-in / Direct Sales
   - **Impact**: Affects data model and grid display (see Section 8.5)

### 8.2 UX Questions

4. **Auto-save vs. Manual save?**
   - ✓ **DECISION: Manual save** with "Save" and "Cancel" buttons

5. **Side panel: Fixed or collapsible?**
   - ✓ **DECISION: Fixed** (always visible)

6. **Grid scrolling: Which direction is priority?**
   - ✓ **DECISION: Vertical priority** with sticky headers for both

7. **Color scheme for cell states?**
   - ✓ **DECISION: Green (working), Gray (resting), White (otherwise)**

### 8.3 Technical Questions

8. **JavaScript framework choice?**
   - ✓ **DECISION: HTMX + Alpine.js**

9. **Real-time collaboration support?**
   - ✓ **DECISION: Phase 2+ feature** (not MVP)

10. **Mobile/tablet support priority?**
    - ✓ **DECISION: Desktop-first**, basic mobile in Phase 5

### 8.4 Feature Prioritization (APPROVED)

11. **Must-have features for MVP?**
    - ✓ **DECISION: Agreed on MVP scope**
      - Phase 0-4: Core scheduling + booking details
      - Manual guide assignment
      - Basic booking details entry
      - Auto-assignment (guides only)
      - Publish workflow
      - **NEW: CSV export of daily schedule**

12. **Future enhancements to consider?**
    - Week/month view toggle
    - Guide preference weighting
    - Copy schedule from template
    - Shift notes/comments
    - **Which are most valuable?** → PENDING DISCUSSION

### 8.5 NEW: Booking Details Design Questions

**Based on Decision #3 above, we need to clarify:**

13. **How should booking details display in grid cells?**
    - Option A: Show only in hover tooltip
    - Option B: Show compact summary in cell (e.g., "JD • 25👥 • Local")
    - Option C: Expand cell height to show all details
    - **Recommendation: Option B** (compact summary)

14. **Can one guide handle multiple tours simultaneously?**
    - Current assumption: No (1 guide per time slot)
    - New: Same logic applies even with booking details?
    - **Assumed: Yes** (no change to assignment logic)

15. **Are booking details required before publishing?**
    - Option A: Optional (can publish with guide assigned but no booking details)
    - Option B: Required (must fill in visitor count, type, channel)
    - **Recommendation: Option A** (optional for MVP, can add validation later)

16. **Should booking details be visible to guides?**
    - In guide portal, show "You have 6 tours today"?
    - Or show "You have 6 tours, 150 visitors total (80 local, 70 intl)"?
    - **Recommendation: Enhanced view** (show summary stats)

17. **Validation rules for booking details?**
    - Max visitors per tour? (e.g., capacity limit)
    - Required fields vs optional?
    - **Needs discussion** - what are the business rules?

### 8.6 NEW: CSV Export Questions (APPROVED)

**Based on MVP requirement for CSV export:**

18. **CSV export format - which layout?**
    - ✓ **DECISION: Option A** - Time-slot rows × Guide columns (matches grid view)

19. **CSV import - should managers be able to import edited CSV back?**
    - ✓ **DECISION: Option A** - Export only (one-way, no import for MVP)

20. **What should CSV export include?**
    - ✓ **DECISION: Grid layout with detailed cell content**
    - Format: Time slots as rows, guides as columns
    - Each cell contains semicolon-separated fields with CR/newline:
      - Guide Type
      - Visitor Count
      - Visitor Type
      - Booking Channel
      - Notes (if any)
    - Empty cells for unassigned slots
    - "N/A" for incompatible slots (e.g., PTM guide in afternoon)

21. **Export button location?**
    - ✓ **DECISION: Option A** - Control bar (next to Publish button)

---

## 9. Success Metrics

### 9.1 Efficiency Metrics

- **Time to schedule one day**: < 5 minutes (current: ~10-15 min with multiple pages)
- **Clicks to assign one guide**: 2 clicks (cell → select guide)
- **Time to fix validation error**: < 2 minutes (current: ~5 min with navigation)

### 9.2 Quality Metrics

- **Validation errors caught before publish**: 100% (enforced by UI)
- **Schedule publish success rate**: > 95% (validation gates)
- **Manager satisfaction**: Qualitative feedback

### 9.3 Adoption Metrics

- **Manager usage of new interface**: > 90% of scheduling tasks
- **Reduced admin navigation**: < 10% of managers use old interfaces
- **Support requests**: Decreased by 50% (clearer UX)

---

## 10. Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Managers prefer old interface | High | Low | Keep old interface accessible, training |
| Performance issues with large grids | Medium | Medium | Virtual scrolling, pagination, caching |
| Browser compatibility issues | Medium | Low | Test on Chrome, Firefox, Safari, Edge |
| Auto-save causes data conflicts | High | Low | Optimistic locking, conflict detection |
| Complex validation slows UI | Medium | Medium | Client-side validation, debouncing |
| Scope creep delays launch | High | Medium | Strict phase gates, MVP focus |

---

## 11. Next Steps

### Immediate Actions

1. **Review this specification** with stakeholders (you!)
2. **Answer open questions** (Section 8)
3. **Prioritize features** for MVP
4. **Approve design** direction

### After Approval

1. **Create detailed wireframes** (if needed)
2. **Set up development environment**
3. **Begin Phase 1 implementation**
4. **Weekly progress reviews**

---

## 12. Appendix

### A. Wireframe Reference

See existing **Schedule Overview** view:
- File: `apps/scheduling/templates/scheduling/schedule_overview.html`
- URL: `/guides/schedule-overview/`
- Current features:
  - Grid layout ✓
  - Feasibility indicators ✓
  - Date navigation ✓
- Missing features:
  - Editing ✗
  - Auto-assign button ✗
  - Status panel ✗

**Plan**: Enhance existing view into editable manager interface.

### B. Related Documentation

- `DESIGN.md` - Original implementation plan
- `README.md` - User guide
- `apps/scheduling/services.py` - Business logic
- `apps/scheduling/admin.py` - Current admin interfaces

### C. Alternative Considered: Full SPA

**Why not build as separate React/Vue app?**
- **Pros**: Modern UX, real-time updates, rich interactions
- **Cons**:
  - Higher complexity
  - Separate deployment
  - Breaks Django admin integration
  - Longer development time (4-6 weeks)
- **Decision**: Stay within Django admin for consistency and faster delivery

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-15 | Claude | Initial draft for discussion |
| 1.1 | 2026-02-15 | Claude | Updated with approved decisions (Q1-21) |

---

## Appendix D: Decision Summary

### All Approved Decisions (Ready for Implementation)

**Scope & Features:**
- ✅ Keep old admin interfaces as fallback
- ✅ Remove shift swap requests (future feature)
- ✅ Make tour time slots editable with booking details
- ✅ Manual save (not auto-save)
- ✅ CSV export - grid format with multi-line cells
- ✅ Export only (no import for MVP)

**UX Design:**
- ✅ Fixed side panel (always visible)
- ✅ Vertical scroll priority with sticky headers
- ✅ Color scheme: Green (working), Gray (resting), White (other)
- ✅ Export button in control bar (next to Publish)

**Technical:**
- ✅ HTMX + Alpine.js for frontend
- ✅ Desktop-first, basic mobile in Phase 5
- ✅ No real-time collaboration (Phase 2+ feature)

**Data Model:**
- ✅ Add to TourSession: visitor_count, visitor_type, booking_channel

**MVP Features (Must-Have):**
- ✅ Core scheduling grid (Phases 0-1)
- ✅ Manual assignment & validation (Phase 2)
- ✅ Auto-assignment for guides (Phase 3)
- ✅ Booking details entry (Phase 2)
- ✅ CSV export - grid format (Phase 4)
- ✅ Publish workflow (Phase 4)
- ✅ Manual save with revert (Phase 4)

**Deferred to Post-MVP:**
- ⏸️ CSV import
- ⏸️ Bulk edit booking details
- ⏸️ Booking capacity validation
- ⏸️ PDF export
- ⏸️ Week/month view toggle
- ⏸️ Guide preference weighting
- ⏸️ Real-time collaboration

### Outstanding Questions (For Future Discussion)

**From Section 8.5 (Booking Details):**
- Q13: Cell display format preference? (Compact, minimal, or icon-based)
- Q14: Can guides handle multiple tours simultaneously? (Assumed: No)
- Q15: Are booking details required before publishing? (Assumed: No for MVP)
- Q16: Show booking details to guides in portal? (Recommendation: Yes, enhanced view)
- Q17: Validation rules for booking details? (Needs business rules)

**From Section 8.4 (Future Enhancements):**
- Q12: Which future features are most valuable?
  - Week/month view toggle
  - Guide preference weighting
  - Copy schedule from template
  - Shift notes/comments
  - Booking capacity limits
  - CSV import (two-way sync)
  - Visitor statistics dashboard
  - Channel performance reports

### Implementation Ready

**Status:** ✅ Specification is complete and ready for implementation

**Next Steps:**
1. Begin Phase 0: Data model migration
2. Set up development environment (HTMX + Alpine.js)
3. Create project board/task tracking
4. Estimated completion: 15-19 development days

---

**END OF SPECIFICATION**
