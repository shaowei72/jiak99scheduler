#!/usr/bin/env python
"""Test script to validate new scheduling constraints."""

from apps.scheduling.models import TourSession, DailySchedule
from apps.scheduling.services import SchedulingService
from datetime import date

def test_constraints():
    schedule = DailySchedule.objects.get(date=date(2026, 3, 1))
    service = SchedulingService()

    guide_data = {}
    for session in TourSession.objects.filter(daily_schedule=schedule, assigned_guide__isnull=False):
        guide_id = session.assigned_guide.id
        if guide_id not in guide_data:
            guide_data[guide_id] = {
                'name': session.assigned_guide.user.username,
                'sessions': []
            }
        guide_data[guide_id]['sessions'].append(session)

    print("="*70)
    print("CONSTRAINT VALIDATION - March 1, 2026")
    print("="*70)

    all_valid = True

    for guide_id, data in sorted(guide_data.items()):
        sessions = sorted(data['sessions'], key=lambda s: s.time_slot.start_time)
        print(f"\n{data['name']}: {len(sessions)} tours")
        print("-" * 70)

        # Show tour times
        for i, session in enumerate(sessions):
            slot = session.time_slot
            print(f"  Tour {i+1}: {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}")

            if i < len(sessions) - 1:
                next_session = sessions[i + 1]
                gap = service._calculate_time_gap(slot.end_time, next_session.time_slot.start_time)
                print(f"          → Gap to next tour: {gap} min")

        # Check constraints
        print()

        # Constraint 1: Check consecutive tours (max 3)
        max_consecutive = 1
        current_consecutive = 1

        for i in range(len(sessions) - 1):
            gap = service._calculate_time_gap(
                sessions[i].time_slot.end_time,
                sessions[i + 1].time_slot.start_time
            )
            if gap == 30:  # Only 30-min buffer = consecutive
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1

        if max_consecutive <= 2:
            print(f"  ✓ Max consecutive tours: {max_consecutive} (limit: 2)")
        else:
            print(f"  ✗ VIOLATION: Max consecutive tours: {max_consecutive} (limit: 2)")
            all_valid = False

        # Constraint 2: Check 1-hour break (90-min gap = 30-min buffer + 60-min break)
        if len(sessions) >= 4:
            has_1hr_break = service._has_one_hour_break(sessions)

            # Also check if there's actually a 90-min gap
            has_90min_gap = False
            for i in range(len(sessions) - 1):
                gap = service._calculate_time_gap(
                    sessions[i].time_slot.end_time,
                    sessions[i + 1].time_slot.start_time
                )
                if gap >= 90:
                    has_90min_gap = True
                    break

            if has_1hr_break and has_90min_gap:
                print(f"  ✓ Has 1-hour break: Yes - 90-min gap (30-min buffer + 60-min break)")
            elif has_90min_gap:
                print(f"  ✓ Has 90-min gap: Yes (required for {len(sessions)} tours)")
            else:
                print(f"  ✗ VIOLATION: No 90-min gap (30-min buffer + 60-min break required)")
                all_valid = False
        else:
            print(f"  ~ 1-hour break: Not required (only {len(sessions)} tours)")

    print("\n" + "="*70)
    if all_valid:
        print("✓ ALL CONSTRAINTS SATISFIED")
    else:
        print("✗ CONSTRAINT VIOLATIONS FOUND")
    print("="*70)

    # Summary
    print(f"\nTotal guides used: {len(guide_data)}")
    print(f"Total tours assigned: {sum(len(d['sessions']) for d in guide_data.values())}")
    print(f"Average tours per guide: {sum(len(d['sessions']) for d in guide_data.values()) / len(guide_data):.1f}")

if __name__ == '__main__':
    test_constraints()
