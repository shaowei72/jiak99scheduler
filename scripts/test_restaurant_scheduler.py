#!/usr/bin/env python
"""Test script for restaurant staff auto-scheduler."""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jiak99_app.settings')
django.setup()

from django.contrib.auth.models import User
from apps.scheduling.models import RestaurantStaff, DailyRestaurantSchedule, StaffShift
from apps.scheduling.services import RestaurantSchedulingService
from datetime import date


def create_test_staff():
    """Create test staff members (4 kitchen + 4 serving)."""
    print("Creating test staff...")

    staff_data = [
        # Kitchen staff
        ('kitchen_alice', 'Alice', 'Chen', 'kitchen'),
        ('kitchen_bob', 'Bob', 'Martinez', 'kitchen'),
        ('kitchen_charlie', 'Charlie', 'Wong', 'kitchen'),
        ('kitchen_diana', 'Diana', 'Lee', 'kitchen'),
        # Serving staff
        ('serving_emma', 'Emma', 'Davis', 'serving'),
        ('serving_frank', 'Frank', 'Johnson', 'serving'),
        ('serving_grace', 'Grace', 'Kim', 'serving'),
        ('serving_henry', 'Henry', 'Park', 'serving'),
    ]

    created_staff = []

    for username, first_name, last_name, staff_type in staff_data:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': f'{username}@example.com'
            }
        )

        staff, created = RestaurantStaff.objects.get_or_create(
            user=user,
            defaults={
                'staff_type': staff_type,
                'is_active': True,
                'hire_date': date(2024, 1, 1)
            }
        )

        created_staff.append(staff)
        status = "Created" if created else "Exists"
        print(f"  {status}: {staff}")

    return created_staff


def test_auto_scheduler():
    """Test the auto-scheduler algorithm."""
    print("\n" + "=" * 70)
    print("RESTAURANT STAFF AUTO-SCHEDULER TEST")
    print("=" * 70)

    # Create test staff
    staff = create_test_staff()

    # Test date
    test_date = date(2026, 2, 17)

    print(f"\n\nTesting auto-scheduler for {test_date}...")
    print("-" * 70)

    # Clear any existing schedule for this date
    DailyRestaurantSchedule.objects.filter(date=test_date).delete()

    # Create service
    service = RestaurantSchedulingService()

    # Create daily schedule
    daily_schedule = DailyRestaurantSchedule.objects.create(
        date=test_date,
        is_published=False
    )

    # Run auto-scheduler
    print("\nRunning auto-scheduler...")
    results = service.auto_schedule_day(daily_schedule, pattern='mixed')

    # Display results
    print("\n" + "=" * 70)
    print("AUTO-SCHEDULER RESULTS")
    print("=" * 70)
    print(f"Kitchen staff assigned: {results['kitchen_assigned']}")
    print(f"Serving staff assigned: {results['serving_assigned']}")
    print(f"Total staff assigned:   {results['total_staff']}")
    print(f"Unfillable shifts:      {results['unfillable_count']}")

    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")

    # Get schedule summary
    print("\n" + "=" * 70)
    print("SCHEDULE SUMMARY")
    print("=" * 70)
    summary = service.get_schedule_summary(daily_schedule)
    print(f"Total shifts:     {summary['total_shifts']}")
    print(f"Assigned shifts:  {summary['assigned_shifts']}")
    print(f"Unassigned:       {summary['unassigned_shifts']}")
    print(f"Kitchen staff:    {summary['kitchen_staff']}")
    print(f"Serving staff:    {summary['serving_staff']}")
    print(f"Total staff used: {summary['total_staff']}")
    print(f"Full-day (8h):    {summary['full_day_shifts']}")
    print(f"Half-day (4h):    {summary['half_day_shifts']}")
    print(f"Total hours:      {summary['total_hours']}h")
    print(f"Coverage valid:   {'✓ Yes' if summary['coverage_valid'] else '✗ No'}")
    if summary['coverage_gaps'] > 0:
        print(f"Coverage gaps:    {summary['coverage_gaps']}")

    # Validate coverage
    print("\n" + "=" * 70)
    print("COVERAGE VALIDATION")
    print("=" * 70)
    validation = service.validate_coverage(daily_schedule)

    if validation['is_valid']:
        print("✓ All coverage requirements met!")
    else:
        print("✗ Coverage issues found:")
        for gap in validation['gaps']:
            print(f"  {gap['time']}: Kitchen: {gap['kitchen']}/2, Serving: {gap['serving']}/2")

    # Display schedule by staff
    print("\n" + "=" * 70)
    print("SCHEDULE BY STAFF")
    print("=" * 70)

    shifts = StaffShift.objects.filter(
        daily_schedule=daily_schedule,
        staff__isnull=False
    ).select_related('staff__user').order_by('staff__staff_type', 'start_time')

    print("\nKitchen Staff:")
    for shift in shifts.filter(staff__staff_type='kitchen'):
        duration_label = "Full-day" if shift.is_full_day else "Half-day"
        print(f"  {shift.staff.user.get_full_name():20} "
              f"{shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')} "
              f"({shift.duration_hours}h {duration_label})")

    print("\nServing Staff:")
    for shift in shifts.filter(staff__staff_type='serving'):
        duration_label = "Full-day" if shift.is_full_day else "Half-day"
        print(f"  {shift.staff.user.get_full_name():20} "
              f"{shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')} "
              f"({shift.duration_hours}h {duration_label})")

    # Display coverage by hour
    print("\n" + "=" * 70)
    print("COVERAGE BY TIME")
    print("=" * 70)
    print("Time     Kitchen  Serving  Status")
    print("-" * 40)

    for time_key, coverage in sorted(validation['coverage_by_hour'].items()):
        kitchen = coverage['kitchen']
        serving = coverage['serving']
        status = "✓" if kitchen >= 2 and serving >= 2 else "✗"
        print(f"{time_key}    {kitchen}        {serving}        {status}")

    # Check if can publish
    print("\n" + "=" * 70)
    print("PUBLISH VALIDATION")
    print("=" * 70)
    can_publish, errors = service.can_publish_schedule(daily_schedule)

    if can_publish:
        print("✓ Schedule is ready to publish!")
    else:
        print("✗ Cannot publish - issues found:")
        for error in errors:
            print(f"  - {error}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return {
        'results': results,
        'summary': summary,
        'validation': validation,
        'can_publish': can_publish
    }


if __name__ == '__main__':
    try:
        test_auto_scheduler()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
