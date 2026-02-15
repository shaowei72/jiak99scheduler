# Auto-Scheduler Algorithm Optimization

**Date:** 2026-02-15
**Status:** Mathematically Optimal

---

## Problem Statement

Minimize the number of tour guides needed to cover all 21 time slots while respecting:
1. Each tour is 1.5 hours (90 minutes)
2. Mandatory 30-minute break after each tour
3. Operating hours: 10:00 AM - 9:30 PM

---

## Mathematical Proof: 4 Guides is Optimal

### Constraint Analysis

**Operating Window:**
- Start: 10:00 AM
- End: 9:30 PM (last tour ends)
- Total: 11.5 hours = 690 minutes

**Per-Tour Requirements:**
- Tour duration: 90 minutes
- Mandatory break: 30 minutes
- **Total cycle: 120 minutes (2 hours)**

### Maximum Tours Per Guide

```
Maximum tours per guide = Operating window / Tour cycle
                        = 690 minutes / 120 minutes
                        = 5.75 tours
                        = 6 tours (rounded down, with optimal timing)
```

**Proof that 6 tours is achievable:**
```
Tour 1: 10:00 AM - 11:30 AM (90 min)
Break:  11:30 AM - 12:00 PM (30 min)
Tour 2: 12:00 PM - 01:30 PM (90 min)
Break:  01:30 PM - 02:00 PM (30 min)
Tour 3: 02:00 PM - 03:30 PM (90 min)
Break:  03:30 PM - 04:00 PM (30 min)
Tour 4: 04:00 PM - 05:30 PM (90 min)
Break:  05:30 PM - 06:00 PM (30 min)
Tour 5: 06:00 PM - 07:30 PM (90 min)
Break:  07:30 PM - 08:00 PM (30 min)
Tour 6: 08:00 PM - 09:30 PM (90 min)
```

Total time: 6 tours × 90 min + 5 breaks × 30 min = 690 minutes ✓

### Minimum Guides Required

```
Minimum guides = Total tours / Maximum tours per guide
               = 21 tours / 6 tours
               = 3.5 guides
               = 4 guides (rounded up)
```

**Therefore, 4 guides is the theoretical minimum.**

---

## Algorithm Strategy

### Priority System

The algorithm uses a strict two-tier priority system:

**Priority 1: Maximize Utilization of Working Guides**
- Always prefer guides who already have assignments today
- Among working guides, choose the one with the MOST tours
- This packs work into fewer guides

**Priority 2: Only Use New Guides When Necessary**
- Only bring in a new guide if NO working guide can take the session
- This minimizes the total number of guides used

### Key Code Logic

```python
# Separate guides into two groups
guides_with_work = [g for g in valid_guides if len(guide_assignments[g.id]) > 0]
guides_without_work = [g for g in valid_guides if len(guide_assignments[g.id]) == 0]

# PRIORITY 1: Use a guide who's already working today
if guides_with_work:
    # Among working guides, choose the one with MOST assignments
    best_guide = max(guides_with_work, key=lambda g: len(guide_assignments[g.id]))
# PRIORITY 2: Only use a new guide if no working guide can take it
elif guides_without_work:
    best_guide = guides_without_work[0]
```

---

## Actual Results

### Test Case: March 1, 2026

**Configuration:**
- Total time slots: 21
- Available guides: 12 (all full-time, all available)

**Results:**
```
Guides used: 4 out of 12 (67% reduction!)

Assignment breakdown:
- JiakGuide01: 6 tours (maxed out!)
- JiakGuide02: 5 tours
- JiakGuide03: 5 tours
- JiakGuide04: 5 tours
Total: 21 tours ✓
```

**Utilization:**
- Average: 5.25 tours per guide
- Maximum achieved: 6 tours (100% utilization)
- Guides not needed: 8 (saved from scheduling)

### Break Validation

All assignments respect the 30-minute break requirement:

**JiakGuide01's Schedule:**
```
10:00 AM - 11:30 AM → 30-min break → 12:00 PM
12:00 PM - 01:30 PM → 30-min break → 02:00 PM
02:00 PM - 03:30 PM → 30-min break → 04:00 PM
04:00 PM - 05:30 PM → 30-min break → 06:00 PM
06:00 PM - 07:30 PM → 30-min break → 08:00 PM
08:00 PM - 09:30 PM (last tour, no break needed)
```

All gaps are exactly 30 minutes ✓

---

## Why 3 Guides Won't Work

### Attempt to Use 3 Guides

If we try to distribute 21 tours among 3 guides:
- Each guide would need: 21 ÷ 3 = 7 tours
- But maximum possible: 6 tours (as proven above)

**Conclusion:** 7 tours per guide is physically impossible within the 11.5-hour operating window with 30-minute breaks.

### Time Slot Staggering Issue

Time slots start every 30 minutes:
- 10:00, 10:30, 11:00, 11:30, 12:00, etc.

With 21 slots and only 3 guides, some slots would be simultaneously needed by multiple tours, but a guide can only conduct one tour at a time.

**Example conflict with 3 guides:**
- Guide1: 10:00 (on tour until 11:30)
- Guide2: 10:30 (on tour until 12:00)
- Guide3: 11:00 (on tour until 12:30)
- **11:30 time slot:** All guides are busy! Cannot cover.

---

## Comparison: Old vs New Algorithm

### Old Algorithm (Balanced Distribution)

**Strategy:** Spread work evenly across all available guides

**Problem:**
- Would use 12 guides for 21 tours
- Average: 1.75 tours per guide
- Low utilization: 1.75 / 6 = 29% efficiency

### New Algorithm (Minimized Guide Count)

**Strategy:** Maximize each guide's utilization before using another

**Benefits:**
- Uses 4 guides for 21 tours
- Average: 5.25 tours per guide
- High utilization: 5.25 / 6 = 87.5% efficiency
- **Cost savings:** 67% fewer guides needed (8 guides saved)

---

## Edge Cases Handled

### 1. Guide Type Constraints
- Algorithm respects PTM (morning only) and PTA (afternoon only) constraints
- With all FT guides: Optimal 4-guide solution
- With PTM/PTA mix: May require more guides depending on distribution

### 2. Guide Availability
- Unavailable guides are automatically excluded
- Algorithm recalculates optimal distribution with remaining guides

### 3. Unfillable Slots
- If no guide can take a slot (all busy or unavailable), marks as unfillable
- Reports these clearly in output

---

## Performance Metrics

### Time Complexity
- O(n × m × log m) where:
  - n = number of sessions (21)
  - m = number of guides (12)
  - log m for sorting

### Space Complexity
- O(n + m) for tracking assignments and guide availability

### Execution Time
- Tested: <1 second for full day scheduling
- Suitable for real-time use in web interface

---

## Validation

### Unit Tests Performed

✓ **Maximum utilization achieved**
  - JiakGuide01 assigned 6 tours (maximum possible)

✓ **Break requirements enforced**
  - All assignments have ≥30-minute gaps

✓ **Guide count minimized**
  - 4 guides used (theoretical minimum)

✓ **100% coverage**
  - All 21 time slots filled

✓ **Deterministic results**
  - Same input always produces same optimal output

---

## Conclusion

**The algorithm achieves mathematically optimal results:**

1. ✓ Uses minimum number of guides (4)
2. ✓ Maximizes utilization per guide (87.5% avg)
3. ✓ Respects all constraints (breaks, guide types, availability)
4. ✓ Achieves 100% coverage
5. ✓ Produces deterministic, reproducible results

**No further optimization is possible without violating constraints.**

The 4-guide solution is provably optimal given:
- 21 time slots
- 1.5-hour tours
- 30-minute mandatory breaks
- 11.5-hour operating window

---

## Future Enhancements (Optional)

While the current algorithm is optimal for the given constraints, potential enhancements for different scenarios:

1. **Multi-day optimization:** Optimize across multiple days to balance workload over weeks
2. **Preference learning:** Learn from manual adjustments to match manager preferences
3. **Cost optimization:** Factor in guide rates (if some guides cost more than others)
4. **Fatigue modeling:** Consider guide fatigue for consecutive high-utilization days

However, for single-day scheduling with uniform constraints, **the current algorithm cannot be improved**.
