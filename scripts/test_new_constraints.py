#!/usr/bin/env python
"""Test script to validate updated scheduling constraints."""

from apps.scheduling.models import TourSession, DailySchedule
from apps.scheduling.services import SchedulingService
from datetime import date

def test_constraints():
    schedule = DailySchedule.objects.get(date=date(2026, 4, 1))
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
    print("CONSTRAINT VALIDATION - April 1, 2026")
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

        print()

        # CONSTRAINT 1: Max 4 tours per guide
        if len(sessions) <= 4:
            print(f"  ✓ Total tours: {len(sessions)} (max: 4)")
        else:
            print(f"  ✗ VIOLATION: Total tours: {len(sessions)} (max: 4)")
            all_valid = False

        # CONSTRAINT 2: Max 2 consecutive tours
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

        # CONSTRAINT 3: 90-min gap for 3+ tours
        if len(sessions) >= 3:
            has_90min_gap = False
            for i in range(len(sessions) - 1):
                gap = service._calculate_time_gap(
                    sessions[i].time_slot.end_time,
                    sessions[i + 1].time_slot.start_time
                )
                if gap >= 90:
                    has_90min_gap = True
                    break

            if has_90min_gap:
                print(f"  ✓ Has 90-min gap: Yes (30-min buffer + 60-min break for {len(sessions)} tours)")
            else:
                print(f"  ✗ VIOLATION: No 90-min gap (required for {len(sessions)} tours)")
                all_valid = False
        else:
            print(f"  ~ 90-min gap: Not required (only {len(sessions)} tours)")

    print("\n" + "="*70)
    if all_valid:
        print("✓ ALL CONSTRAINTS SATISFIED")
    else:
        print("✗ CONSTRAINT VIOLATIONS FOUND")
    print("="*70)

    # Summary
    total_sessions = TourSession.objects.filter(daily_schedule=schedule).count()
    print(f"\nTotal guides used: {len(guide_data)}")
    print(f"Total tours assigned: {sum(len(d['sessions']) for d in guide_data.values())} out of {total_sessions}")
    print(f"Average tours per guide: {sum(len(d['sessions']) for d in guide_data.values()) / len(guide_data):.1f}")
    print(f"Max tours per guide: {max(len(d['sessions']) for d in guide_data.values())}")

    # Show time slots
    print("\n" + "="*70)
    print("TOUR START TIMES (ON THE HOUR, 10AM-8PM):")
    print("="*70)
    all_slots = TourSession.objects.filter(daily_schedule=schedule).select_related('time_slot').order_by('time_slot__start_time')
    for session in all_slots:
        slot = session.time_slot
        assigned = session.assigned_guide.user.username if session.assigned_guide else "UNASSIGNED"
        print(f"  {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')} → {assigned}")

if __name__ == '__main__':
    test_constraints()
