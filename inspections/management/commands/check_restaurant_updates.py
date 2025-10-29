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
                        title = f"🎉 {followed.restaurant_name} grade improved!"
                        message = (
                            f"{followed.restaurant_name} improved from grade {old_grade} to {new_grade}. "
                            f"This means the restaurant's health standards have gotten better. "
                            f"Previous grade: {old_grade}. New grade: {new_grade}."
                        )
                    elif new_score < old_score:
                        notification_type = "score_decline"
                        title = f"⚠️ {followed.restaurant_name} grade declined."
                        message = (
                            f"{followed.restaurant_name} declined from grade {old_grade} to {new_grade}. "
                            f"This may indicate a drop in health standards. "
                            f"Previous grade: {old_grade}. New grade: {new_grade}."
                        )
                    else:
                        notification_type = "grade_change"
                        title = f"📊 {followed.restaurant_name} grade changed."
                        message = (
                            f"{followed.restaurant_name} received a new grade: {new_grade} (previously {old_grade}). "
                            f"Check the inspection details for more information."
                        )

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
                    inspection_date_str = latest_inspection.INSPECTION_DATE.strftime('%B %d, %Y') if latest_inspection.INSPECTION_DATE else 'Unknown date'
                    grade_str = latest_inspection.GRADE or 'Pending'
                    violations = latest_inspection.VIOLATION_DESCRIPTION or 'No violations reported.'
                    message = (
                        f"A new health inspection was completed on {inspection_date_str}. "
                        f"Grade received: {grade_str}. "
                        f"Violations noted: {violations[:120]}... "
                        f"See the inspection details for the full report."
                    )
                    RestaurantNotification.objects.create(
                        followed_restaurant=followed,
                        notification_type="new_inspection",
                        title=f"🔍 New inspection at {followed.restaurant_name}",
                        message=message,
                    )
                    notifications_created += 1

                    # Update the last inspection date
                    followed.last_inspection_date = latest_inspection.INSPECTION_DATE
                    followed.save()

                # Check for violations if enabled
                if followed.notify_violations and latest_inspection.VIOLATION_CODE:
                    # Check if this is a critical violation
                    if latest_inspection.CRITICAL_FLAG == "Critical":
                        violation_code = latest_inspection.VIOLATION_CODE or 'N/A'
                        violation_desc = latest_inspection.VIOLATION_DESCRIPTION or 'No description.'
                        message = (
                            f"A critical health violation was reported: [Code: {violation_code}] "
                            f"{violation_desc[:120]}... "
                            f"This violation is considered critical and may impact health safety."
                        )
                        RestaurantNotification.objects.create(
                            followed_restaurant=followed,
                            notification_type="violation_added",
                            title=f"⚠️ Critical violation at {followed.restaurant_name}",
                            message=message,
                        )
                        notifications_created += 1

                    # Check for health outbreak keywords in violation description
                    outbreak_keywords = [
                        "outbreak",
                        "norovirus",
                        "salmonella",
                        "hepatitis",
                        "shigella",
                        "e. coli",
                        "listeria",
                        "foodborne illness",
                        "contagious disease",
                        "infectious disease",
                        "health outbreak",
                        "disease outbreak",
                        "illness outbreak",
                        "public health hazard",
                        "unsafe food",
                        "contaminated food",
                        "epidemic",
                        "pandemic",
                    ]
                    violation_desc = (latest_inspection.VIOLATION_DESCRIPTION or "").lower()
                    if any(keyword in violation_desc for keyword in outbreak_keywords):
                        message = (
                            f"A potential health outbreak or serious foodborne illness was reported: "
                            f"{latest_inspection.VIOLATION_DESCRIPTION[:120]}... "
                            f"This may indicate a public health risk. Please review the inspection details for more information."
                        )
                        RestaurantNotification.objects.create(
                            followed_restaurant=followed,
                            notification_type="health_outbreak",
                            title=f"🚨 Health outbreak alert at {followed.restaurant_name}",
                            message=message,
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
