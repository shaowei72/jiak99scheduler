from apps.scheduling.models import StaffShift, DailyRestaurantSchedule
from datetime import date

d = date(2026, 2, 17)

try:
    schedule = DailyRestaurantSchedule.objects.get(date=d)
    shifts = StaffShift.objects.filter(daily_schedule=schedule)

    print(f'Total shifts: {shifts.count()}')

    assigned = shifts.filter(staff__isnull=False)
    print(f'Assigned shifts: {assigned.count()}')

    unassigned = shifts.filter(staff__isnull=True)
    print(f'Unassigned shifts: {unassigned.count()}')

    print(f'\nFirst 10 shifts:')
    for shift in shifts[:10]:
        staff_name = shift.staff.user.get_full_name() if shift.staff else "UNASSIGNED"
        staff_type = shift.staff.get_staff_type_display() if shift.staff else "N/A"
        print(f'  {shift.start_time}-{shift.end_time} ({shift.duration_hours}h): {staff_name} ({staff_type})')

except DailyRestaurantSchedule.DoesNotExist:
    print(f'No schedule found for {d}')
except Exception as e:
    print(f'Error: {e}')
