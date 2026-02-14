from django.core.management.base import BaseCommand, CommandError
from apps.scheduling.services import SchedulingService
from datetime import date
import calendar


class Command(BaseCommand):
    help = 'Create tour sessions for a specific month (must be at least 2 weeks in advance)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Year (e.g., 2024). Defaults to current year if month is in future, or next year if not.'
        )
        parser.add_argument(
            '--month',
            type=int,
            required=True,
            help='Month number (1-12)'
        )

    def handle(self, *args, **options):
        month = options['month']
        today = date.today()

        # Validate month
        if month < 1 or month > 12:
            raise CommandError("Month must be between 1 and 12")

        # Determine year
        if options['year']:
            year = options['year']
        else:
            # Default to current year if month is in future, otherwise next year
            if month > today.month:
                year = today.year
            else:
                year = today.year + 1

        month_name = calendar.month_name[month]

        self.stdout.write(f"Creating schedule for {month_name} {year}...")

        service = SchedulingService()

        try:
            total_sessions, schedules = service.generate_sessions_for_month(year, month)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {total_sessions} session(s) across {len(schedules)} day(s)"
                )
            )

            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Go to the Django admin interface")
            self.stdout.write("2. Navigate to 'Daily schedules'")
            self.stdout.write(f"3. Filter by date to see schedules for {month_name} {year}")
            self.stdout.write("4. Assign guides to tour sessions")
            self.stdout.write("5. Assign standby guide for each day")
            self.stdout.write("6. Publish schedules when ready")

        except ValueError as e:
            raise CommandError(str(e))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating schedules: {str(e)}")
            )
            raise
