from django.core.management.base import BaseCommand
from apps.scheduling.services import SchedulingService


class Command(BaseCommand):
    help = 'Generate all tour time slots (10:00am-9:30pm, every 30 minutes, 1.5-hour tours)'

    def handle(self, *args, **options):
        service = SchedulingService()

        self.stdout.write("Generating tour time slots...")

        try:
            slots_created = service.generate_tour_time_slots()

            if slots_created > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created {slots_created} new time slot(s)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("No new slots created (all slots already exist)")
                )

            from apps.scheduling.models import TourTimeSlot
            total_slots = TourTimeSlot.objects.count()
            self.stdout.write(f"Total time slots in system: {total_slots}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error generating time slots: {str(e)}")
            )
            raise
