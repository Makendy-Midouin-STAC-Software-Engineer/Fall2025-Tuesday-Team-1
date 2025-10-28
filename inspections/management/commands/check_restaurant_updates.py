from django.core.management.base import BaseCommand
from inspections.models import (
    FollowedRestaurant,
    RestaurantInspection,
    RestaurantNotification,
)
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "Check for restaurant updates and create notifications for followers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Number of days back to check for updates (default: 1)",
        )

    def handle(self, *args, **options):
        days_back = options["days"]
        cutoff_date = datetime.now().date() - timedelta(days=days_back)

        self.stdout.write(f"🔍 Checking for restaurant updates since {cutoff_date}...")

        notifications_created = 0
        followed_restaurants = FollowedRestaurant.objects.all()

        for followed in followed_restaurants:
            try:
                # Get the latest inspection for this restaurant
                latest_inspection = (
                    RestaurantInspection.objects.filter(
                        CAMIS=followed.camis, INSPECTION_DATE__gte=cutoff_date
                    )
                    .order_by("-INSPECTION_DATE")
                    .first()
                )

                if not latest_inspection:
                    continue

                # Check for grade changes
                if (
                    followed.notify_grade_changes
                    and followed.last_known_grade != latest_inspection.GRADE
                    and latest_inspection.GRADE
                ):
                    old_grade = followed.last_known_grade or "No grade"
                    new_grade = latest_inspection.GRADE

                    # Determine notification type
                    grade_hierarchy = {"A": 4, "B": 3, "C": 2, "N": 1, "P": 1, "Z": 1}
                    old_score = grade_hierarchy.get(followed.last_known_grade, 0)
                    new_score = grade_hierarchy.get(new_grade, 0)

                    if new_score > old_score:
                        notification_type = "score_improvement"
                        title = f"🎉 {followed.restaurant_name} improved to grade {new_grade}!"
                        message = f"Great news! {followed.restaurant_name} upgraded from grade {old_grade} to {new_grade}. Their health standards have improved!"
                    elif new_score < old_score:
                        notification_type = "score_decline"
                        title = f"⚠️ {followed.restaurant_name} grade declined to {new_grade}"
                        message = f"Notice: {followed.restaurant_name} dropped from grade {old_grade} to {new_grade}. You may want to check recent inspection details."
                    else:
                        notification_type = "grade_change"
                        title = f"📊 {followed.restaurant_name} grade changed to {new_grade}"
                        message = f"{followed.restaurant_name} received a new grade: {new_grade} (was {old_grade})."

                    RestaurantNotification.objects.create(
                        followed_restaurant=followed,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                    )
                    notifications_created += 1

                    # Update the tracked grade
                    followed.last_known_grade = new_grade
                    followed.save()

                # Check for new inspections
                if (
                    followed.notify_new_inspections
                    and latest_inspection.INSPECTION_DATE
                    > (followed.last_inspection_date or datetime.min.date())
                ):
                    RestaurantNotification.objects.create(
                        followed_restaurant=followed,
                        notification_type="new_inspection",
                        title=f"🔍 New inspection completed at {followed.restaurant_name}",
                        message=f"A new health inspection was completed on {latest_inspection.INSPECTION_DATE.strftime('%B %d, %Y')}. Grade: {latest_inspection.GRADE or 'Pending'}. Check the details to see the latest results!",
                    )
                    notifications_created += 1

                    # Update the last inspection date
                    followed.last_inspection_date = latest_inspection.INSPECTION_DATE
                    followed.save()

                # Check for violations if enabled
                if followed.notify_violations and latest_inspection.VIOLATION_CODE:
                    # Check if this is a critical violation
                    if latest_inspection.CRITICAL_FLAG == "Critical":
                        RestaurantNotification.objects.create(
                            followed_restaurant=followed,
                            notification_type="violation_added",
                            title=f"⚠️ Critical violation reported at {followed.restaurant_name}",
                            message=f"A critical health violation was reported during the recent inspection: {latest_inspection.VIOLATION_DESCRIPTION[:100]}... Review the full details for more information.",
                        )
                        notifications_created += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing {followed.restaurant_name}: {str(e)}"
                    )
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Notification check complete! Created {notifications_created} new notifications for {followed_restaurants.count()} followed restaurants."
            )
        )

        # Clean up old notifications (older than 90 days)
        old_notifications = RestaurantNotification.objects.filter(
            created_at__lt=datetime.now() - timedelta(days=90)
        )
        deleted_count = old_notifications.count()
        old_notifications.delete()

        if deleted_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"🧹 Cleaned up {deleted_count} old notifications (older than 90 days)."
                )
            )
