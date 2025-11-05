from inspections.models import RestaurantInspection, RestaurantDetails
from django.test import TestCase
from django.urls import reverse
from inspections.models import RestaurantInspection


class InspectionsTestCase(TestCase):

    def test_restaurantinspection_str(self):
        restaurant = RestaurantInspection.objects.get(CAMIS=12345678)
        self.assertIn("Test Restaurant", str(restaurant))

    def test_get_restaurant_rating_no_inspections(self):
        # Should return default dict if no inspections exist for CAMIS
        rating = RestaurantInspection.get_restaurant_rating(99999999)
        self.assertEqual(rating["stars"], 0)
        self.assertEqual(rating["grade"], "N/A")
        self.assertEqual(rating["inspection_count"], 0)

    def test_get_grade_display_edge_cases(self):
        r = RestaurantInspection.objects.get(CAMIS=12345678)
        r.GRADE = "B"
        self.assertEqual(r.get_grade_display(), "Good")
        r.GRADE = "C"
        self.assertEqual(r.get_grade_display(), "Fair")
        r.GRADE = "N"
        self.assertEqual(r.get_grade_display(), "Not Yet Graded")
        r.GRADE = "P"
        self.assertEqual(r.get_grade_display(), "Pending")
        r.GRADE = "Z"
        self.assertEqual(r.get_grade_display(), "Grade Pending")
        r.GRADE = "X"
        self.assertEqual(r.get_grade_display(), "Unknown")

    def test_add_review_view_get(self):
        response = self.client.get(reverse("add_review"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review")

    def test_add_review_view_post_invalid(self):
        response = self.client.post(reverse("add_review"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review")

    def test_restaurant_detail_invalid_camis(self):
        response = self.client.get(reverse("restaurant_detail", args=[999999]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restaurant Not Found", status_code=200)

    def test_toggle_favorite_missing_camis(self):
        response = self.client.post(reverse("toggle_favorite"), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)

    def test_toggle_follow_missing_camis(self):
        response = self.client.post(reverse("toggle_follow"), {}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)

    def test_update_notification_preferences_invalid_type(self):
        # Add a followed restaurant for this session
        from inspections.models import FollowedRestaurant
        session_key = self.client.session.session_key or self.client.session.create()
        FollowedRestaurant.objects.create(session_key=self.client.session.session_key, camis=12345678, restaurant_name="Test Restaurant")
        response = self.client.post(reverse("update_notification_preferences"), {"camis": "12345678", "notification_type": "badtype", "enabled": "true"})
        self.assertEqual(response.status_code, 400)

    def test_update_notification_preferences_not_followed(self):
        response = self.client.post(reverse("update_notification_preferences"), {"camis": "99999999", "notification_type": "grade_changes", "enabled": "true"})
        self.assertEqual(response.status_code, 404)

    def test_restaurant_details_properties(self):
        """Test RestaurantDetails model properties and methods."""
        details = RestaurantDetails.objects.create(
            camis=99999999,
            restaurant_name="Details Test",
            monday_hours="9:00 AM - 5:00 PM",
            tuesday_hours="Closed",
        )
        # Test __str__
        self.assertIn("Details Test", str(details))
        # Test hours_today (should be string)
        self.assertIsInstance(details.hours_today, str)
        # Test is_open_now (should be bool)
        self.assertIsInstance(details.is_open_now, bool)
        # Test get_weekly_hours (should be list of 7)
        weekly = details.get_weekly_hours()
        self.assertEqual(len(weekly), 7)
        self.assertIn("day", weekly[0])
        self.assertIn("hours", weekly[0]) 
    """Basic test suite for the inspections app."""

    def setUp(self):
        """Set up test data."""
        # Create a sample restaurant inspection for testing
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            INSPECTION_DATE="2024-01-01",
            ACTION="Violations were cited in the following area(s).",
            VIOLATION_CODE="04L",
            VIOLATION_DESCRIPTION="Test violation",
            CRITICAL_FLAG="Critical",
            SCORE=15,
            GRADE="A",
            GRADE_DATE="2024-01-01",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_search_view_loads(self):
        """Test that the search view loads successfully."""
        response = self.client.get(reverse("search_restaurants"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restaurant Search")

    def test_search_functionality(self):
        """Test basic search functionality."""
        response = self.client.get(reverse("search_restaurants"), {"q": "Test"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Restaurant")


    def test_restaurant_model(self):
        """Test the restaurant inspection model and rating methods."""
        restaurant = RestaurantInspection.objects.get(CAMIS=12345678)
        self.assertEqual(restaurant.DBA, "Test Restaurant")
        self.assertEqual(restaurant.GRADE, "A")
        # Test get_restaurant_rating
        rating = RestaurantInspection.get_restaurant_rating(12345678)
        self.assertIn("stars", rating)
        self.assertIn("grade", rating)
        self.assertIn("inspection_count", rating)
        self.assertGreaterEqual(rating["stars"], 0)
        # Test get_grade_display
        self.assertEqual(restaurant.get_grade_display(), "Excellent")

    def test_favorites_functionality(self):
        """Test favorites toggle functionality."""
        response = self.client.post(
            reverse("toggle_favorite"),
            {"camis": "12345678"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)


    def test_owner_signup_view(self):
        """Test owner signup view GET and POST."""
        # GET request
        response = self.client.get(reverse("owner_signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign Up")
        # POST request with invalid data
        response = self.client.post(reverse("owner_signup"), {})
        self.assertEqual(response.status_code, 200)

    def test_owner_login_view(self):
        """Test owner login view GET and POST."""
        # GET request
        response = self.client.get(reverse("owner_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")
        # POST request with invalid data
        response = self.client.post(reverse("owner_login"), {})
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_view_requires_login(self):
        """Test owner dashboard redirects if not logged in."""
        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_favorites_list_view(self):
        """Test favorites list view loads."""
        response = self.client.get(reverse("favorites_list"))
        self.assertEqual(response.status_code, 200)

    def test_is_restaurant_favorited_helper(self):
        """Test is_restaurant_favorited helper function."""
        from inspections.views import is_restaurant_favorited
        request = self.client.request().wsgi_request
        request.session = self.client.session
        # Should be False for new session
        self.assertFalse(is_restaurant_favorited(request, "12345678"))

    def test_is_restaurant_followed_helper(self):
        """Test is_restaurant_followed helper function."""
        from inspections.views import is_restaurant_followed
        request = self.client.request().wsgi_request
        request.session = self.client.session
        # Should be False for new session
        self.assertFalse(is_restaurant_followed(request, "12345678"))

    def test_followed_restaurants_view(self):
        """Test followed restaurants view loads."""
        response = self.client.get(reverse("followed_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_view(self):
        """Test notifications list view loads."""
        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)

    def test_update_notification_preferences_post(self):
        """Test update_notification_preferences view with missing params."""
        response = self.client.post(reverse("update_notification_preferences"), {})
        self.assertEqual(response.status_code, 400)
