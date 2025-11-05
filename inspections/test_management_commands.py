from django.core.management import call_command
from django.test import TestCase
from inspections.models import RestaurantInspection, FollowedRestaurant
from io import StringIO

class ManagementCommandsTestCase(TestCase):

    def test_check_restaurant_updates_days_argument(self):
        out = StringIO()
        call_command("check_restaurant_updates", "--days", "10", stdout=out)
        self.assertIn("Notification check complete", out.getvalue())

    def test_check_restaurant_updates_no_followed(self):
        # Remove all followed restaurants
        from inspections.models import FollowedRestaurant
        FollowedRestaurant.objects.all().delete()
        out = StringIO()
        call_command("check_restaurant_updates", stdout=out)
        self.assertIn("Notification check complete", out.getvalue())

    def test_check_restaurant_updates_no_new_inspections(self):
        # Set last_inspection_date to today so no new inspections
        from inspections.models import FollowedRestaurant
        import datetime
        fr = FollowedRestaurant.objects.first()
        fr.last_inspection_date = datetime.date.today()
        fr.save()
        out = StringIO()
        call_command("check_restaurant_updates", stdout=out)
        self.assertIn("Notification check complete", out.getvalue())

    def setUp(self):
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            INSPECTION_DATE="2024-01-01",
            GRADE="A",
            VIOLATION_CODE="04L",
            VIOLATION_DESCRIPTION="Test violation",
            CRITICAL_FLAG="Critical",
        )
        FollowedRestaurant.objects.create(
            session_key="abc123",
            camis=12345678,
            restaurant_name="Test Restaurant",
            last_known_grade="B",
            last_inspection_date="2023-01-01",
            notify_grade_changes=True,
            notify_new_inspections=True,
            notify_violations=True,
        )

    def test_check_restaurant_updates_command(self):
        out = StringIO()
        call_command("check_restaurant_updates", stdout=out)
        self.assertIn("Notification check complete", out.getvalue())

    def test_load_inspections_command_truncate(self):
        # Just test the command parses arguments and runs (no real file loaded)
        out = StringIO()
        try:
            call_command("load_inspections", "fake.csv", "--truncate", stdout=out)
        except Exception as e:
            self.assertIn("fake.csv", str(e))  # Should error on missing file
