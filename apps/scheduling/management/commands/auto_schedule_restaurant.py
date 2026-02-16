"""
Management command to auto-assign restaurant staff for a specific date.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.scheduling.models import DailyRestaurantSchedule
from apps.scheduling.services import RestaurantSchedulingService
from datetime import datetime, date


class Command(BaseCommand):
    help = 'Auto-assign restaurant staff shifts for a specific date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date in YYYY-MM-DD format (e.g., 2026-02-17)'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            default='mixed',
            choices=['mixed', 'all_8h'],
            help='Shift pattern: mixed (default, 4h+8h) or all_8h'
        )

    def handle(self, *args, **options):
        date_str = options['date']
        pattern = options['pattern']

        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise CommandError(f'Invalid date format: {date_str}. Use YYYY-MM-DD')

        self.stdout.write(f'Auto-scheduling restaurant staff for {target_date}...\n')

        # Create service
        service = RestaurantSchedulingService()

        # Get or create daily schedule
        daily_schedule, created = DailyRestaurantSchedule.objects.get_or_create(
            date=target_date
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new schedule for {target_date}'))
        else:
            self.stdout.write(f'Using existing schedule for {target_date}')

        # Run auto-scheduler
        self.stdout.write(f'\nRunning auto-scheduler (pattern: {pattern})...')
        results = service.auto_schedule_day(daily_schedule, pattern=pattern)

        # Display results
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('AUTO-SCHEDULING RESULTS')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Kitchen staff assigned: {results["kitchen_assigned"]}')
        self.stdout.write(f'Serving staff assigned: {results["serving_assigned"]}')
        self.stdout.write(f'Total staff assigned:   {results["total_staff"]}')
        self.stdout.write(f'Unfillable shifts:      {results["unfillable_count"]}')

        if results['errors']:
            self.stdout.write('\n' + self.style.WARNING('Errors:'))
            for error in results['errors']:
                self.stdout.write(f'  - {error}')

        # Get summary
        summary = service.get_schedule_summary(daily_schedule)

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('SCHEDULE SUMMARY')
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total shifts:     {summary["total_shifts"]}')
        self.stdout.write(f'Assigned:         {summary["assigned_shifts"]}')
        self.stdout.write(f'Kitchen staff:    {summary["kitchen_staff"]}')
        self.stdout.write(f'Serving staff:    {summary["serving_staff"]}')
        self.stdout.write(f'Total staff used: {summary["total_staff"]}')
        self.stdout.write(f'Full-day (8h):    {summary["full_day_shifts"]}')
        self.stdout.write(f'Half-day (4h):    {summary["half_day_shifts"]}')
        self.stdout.write(f'Total hours:      {summary["total_hours"]}h')
        self.stdout.write(f'Coverage valid:   {"Yes" if summary["coverage_valid"] else "No"}')

        # Validate coverage
        validation = service.validate_coverage(daily_schedule)

        if validation['is_valid']:
            self.stdout.write('\n' + self.style.SUCCESS('[OK] All coverage requirements met!'))
        else:
            self.stdout.write('\n' + self.style.ERROR('[FAIL] Coverage issues found:'))
            for gap in validation['gaps']:
                self.stdout.write(
                    f'  {gap["time"]}: Kitchen {gap["kitchen"]}/2, Serving {gap["serving"]}/2'
                )

        # Check publish readiness
        can_publish, errors = service.can_publish_schedule(daily_schedule)

        self.stdout.write('\n' + '=' * 60)
        if can_publish:
            self.stdout.write(self.style.SUCCESS('[OK] Schedule is ready to publish!'))
        else:
            self.stdout.write(self.style.ERROR('[FAIL] Cannot publish - issues found:'))
            for error in errors:
                self.stdout.write(f'  - {error}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            f'Coverage: {summary["total_shifts"]}/{summary["total_shifts"]} shifts '
            f'({100 if summary["assigned_shifts"] == summary["total_shifts"] else 0}%)'
        )
        self.stdout.write('=' * 60)

        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Review schedule in admin or Schedule Manager UI')
        self.stdout.write('2. Make manual adjustments if needed')
        self.stdout.write('3. Publish schedule when ready')
