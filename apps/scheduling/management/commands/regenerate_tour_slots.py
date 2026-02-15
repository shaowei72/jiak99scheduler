from django.core.management.base import BaseCommand
from django.db import transaction
from apps.scheduling.models import TourTimeSlot, TourSession, DailySchedule
from apps.scheduling.services import SchedulingService


class Command(BaseCommand):
    help = 'Regenerate tour time slots with new timing (10am-9:30pm, 1.5-hour tours)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of old time slots and associated sessions'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    "\nWARNING: This will DELETE all existing time slots and tour sessions!\n"
                    "\nThis action cannot be undone.\n"
                    "\nTo proceed, run:\n"
                    "  python manage.py regenerate_tour_slots --confirm\n"
                )
            )
            return

        self.stdout.write(self.style.WARNING("\nStarting time slot regeneration...\n"))

        try:
            with transaction.atomic():
                # Count existing data
                old_slots = TourTimeSlot.objects.count()
                old_sessions = TourSession.objects.count()
                old_schedules = DailySchedule.objects.count()

                self.stdout.write(f"Found {old_slots} existing time slots")
                self.stdout.write(f"Found {old_sessions} existing tour sessions")
                self.stdout.write(f"Found {old_schedules} existing daily schedules")

                # Delete tour sessions first (they reference time slots)
                self.stdout.write("\nDeleting tour sessions...")
                TourSession.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("+ Tour sessions deleted"))

                # Now delete time slots
                self.stdout.write("Deleting old time slots...")
                TourTimeSlot.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("+ Old time slots deleted"))

                # Generate new time slots
                self.stdout.write("\nGenerating new time slots (10am-9:30pm, 1.5-hour tours)...")
                service = SchedulingService()
                slots_created = service.generate_tour_time_slots()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"+ Created {slots_created} new time slots"
                    )
                )

                # Show what was created
                new_slots = TourTimeSlot.objects.all().order_by('start_time')

                self.stdout.write("\nNew Time Slots:")
                for slot in new_slots[:5]:
                    self.stdout.write(f"  - {slot}")
                if new_slots.count() > 5:
                    self.stdout.write(f"  ... and {new_slots.count() - 5} more")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n>>> Successfully regenerated time slots!"
                        f"\n\nSummary:"
                        f"\n  Old slots: {old_slots}"
                        f"\n  New slots: {slots_created}"
                        f"\n\nNote: You'll need to recreate schedules for any dates."
                        f"\n  Use: python manage.py create_monthly_schedule --month <month>"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\nError: {str(e)}")
            )
            raise
