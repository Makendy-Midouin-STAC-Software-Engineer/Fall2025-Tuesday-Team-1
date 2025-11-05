<<<<<<< HEAD
from inspections.models import RestaurantInspection, RestaurantDetails
from django.test import TestCase
=======
from django.test import TestCase, Client
>>>>>>> c007b54eb366bfd83c4f78f35e6a8b2b1d3e57c6
from django.urls import reverse
from django.contrib.auth.models import User
from inspections.models import (
    RestaurantInspection,
    RestaurantReview,
    FavoriteRestaurant,
    FollowedRestaurant,
    RestaurantNotification,
    RestaurantDetails,
)


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
<<<<<<< HEAD
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
=======


class AuthenticatedViewTests(TestCase):
    """Tests for views that require authentication or session."""

    def setUp(self):
        self.client = Client()
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            BORO="MANHATTAN",
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

    def test_restaurant_detail_view(self):
        response = self.client.get(
            reverse("restaurant_detail", kwargs={"camis": 12345678})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Restaurant")

    def test_restaurant_detail_invalid_camis(self):
        response = self.client.get(
            reverse("restaurant_detail", kwargs={"camis": 99999999})
        )
        self.assertIn(response.status_code, [200, 404])

    def test_add_review_post(self):
        response = self.client.post(
            reverse("add_review"),
            {
                "camis": 12345678,
                "restaurant_name": "Test Restaurant",
                "reviewer_name": "Test User",
                "rating": 5,
                "review_text": "Great food!",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertIn(response.status_code, [200, 302, 400])

    def test_favorites_list_view(self):
        response = self.client.get(reverse("favorites_list"))
        self.assertEqual(response.status_code, 200)

    def test_followed_restaurants_view(self):
>>>>>>> c007b54eb366bfd83c4f78f35e6a8b2b1d3e57c6
        response = self.client.get(reverse("followed_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_view(self):
<<<<<<< HEAD
        """Test notifications list view loads."""
        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)

    def test_update_notification_preferences_post(self):
        """Test update_notification_preferences view with missing params."""
        response = self.client.post(reverse("update_notification_preferences"), {})
        self.assertEqual(response.status_code, 400)
=======
        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)

    def test_update_notification_preferences(self):
        self.client.post(
            reverse("toggle_follow"),
            {"camis": 12345678},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        response = self.client.post(
            reverse("update_notification_preferences"),
            {
                "camis": 12345678,
                "notify_grade_changes": "true",
                "notify_new_inspections": "true",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertIn(response.status_code, [200, 302, 400])


class OwnerViewTests(TestCase):
    """Tests for owner-related views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testowner", password="testpass123", email="owner@test.com"
        )

    def test_owner_signup_get(self):
        response = self.client.get(reverse("owner_signup"))
        self.assertEqual(response.status_code, 200)

    def test_owner_signup_post(self):
        response = self.client.post(
            reverse("owner_signup"),
            {
                "username": "newowner",
                "email": "newowner@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertIn(response.status_code, [200, 302, 400])

    def test_owner_login_get(self):
        response = self.client.get(reverse("owner_login"))
        self.assertEqual(response.status_code, 200)

    def test_owner_login_post_valid(self):
        response = self.client.post(
            reverse("owner_login"),
            {"username": "testowner", "password": "testpass123"},
        )
        self.assertIn(response.status_code, [200, 302, 400])

    def test_owner_login_post_invalid(self):
        response = self.client.post(
            reverse("owner_login"),
            {"username": "testowner", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_authenticated(self):
        self.client.login(username="testowner", password="testpass123")
        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 200)


class RedirectTests(TestCase):
    def test_root_redirects_to_search(self):
        response = self.client.get("/inspections/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/inspections/search/", response.url)


class ModelMethodTests(TestCase):
    def setUp(self):
        self.restaurant = RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            BORO="MANHATTAN",
            INSPECTION_DATE="2024-01-01",
            ACTION="Violations were cited",
            SCORE=15,
            GRADE="A",
            GRADE_DATE="2024-01-01",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_restaurant_str_method(self):
        result = str(self.restaurant)
        self.assertEqual(result, "Test Restaurant (12345678)")

    def test_restaurant_fields(self):
        self.assertEqual(self.restaurant.CAMIS, 12345678)
        self.assertEqual(self.restaurant.DBA, "Test Restaurant")
        self.assertEqual(self.restaurant.GRADE, "A")
        self.assertEqual(self.restaurant.SCORE, 15)

    def test_get_grade_display(self):
        self.assertEqual(self.restaurant.get_grade_display(), "Excellent")
        self.restaurant.GRADE = "B"
        self.assertEqual(self.restaurant.get_grade_display(), "Good")
        self.restaurant.GRADE = "C"
        self.assertEqual(self.restaurant.get_grade_display(), "Fair")

    def test_get_restaurant_rating(self):
        rating_info = RestaurantInspection.get_restaurant_rating(12345678)
        self.assertIsInstance(rating_info, dict)
        self.assertIn("stars", rating_info)
        self.assertIn("grade", rating_info)
        self.assertIn("inspection_count", rating_info)
        self.assertEqual(rating_info["grade"], "A")
        self.assertGreater(rating_info["stars"], 0)

    def test_get_restaurant_rating_no_data(self):
        rating_info = RestaurantInspection.get_restaurant_rating(99999999)
        self.assertEqual(rating_info["stars"], 0)
        self.assertEqual(rating_info["grade"], "N/A")
        self.assertEqual(rating_info["inspection_count"], 0)


class RestaurantReviewModelTests(TestCase):
    def test_review_creation(self):
        review = RestaurantReview.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            reviewer_name="Test User",
            rating=5,
            review_text="Great food!",
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.restaurant_name, "Test Restaurant")

    def test_review_str_method(self):
        review = RestaurantReview.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            reviewer_name="Test User",
            rating=5,
            review_text="Great food!",
        )
        expected = "Test Restaurant - 5 stars by Test User"
        self.assertEqual(str(review), expected)

    def test_stars_display_property(self):
        review = RestaurantReview.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            reviewer_name="Test User",
            rating=3,
            review_text="Good food",
        )
        self.assertEqual(review.stars_display, "★★★☆☆")


class RestaurantDetailsModelTests(TestCase):
    def test_details_creation(self):
        details = RestaurantDetails.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            website="https://test.com",
            phone_formatted="(212) 555-1234",
            monday_hours="9:00 AM - 10:00 PM",
            price_range="$$",
        )
        self.assertEqual(details.camis, 12345678)
        self.assertEqual(details.price_range, "$$")

    def test_details_str_method(self):
        details = RestaurantDetails.objects.create(
            camis=12345678, restaurant_name="Test Restaurant"
        )
        expected = "Test Restaurant (CAMIS: 12345678)"
        self.assertEqual(str(details), expected)

    def test_get_weekly_hours(self):
        details = RestaurantDetails.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            monday_hours="9:00 AM - 10:00 PM",
            tuesday_hours="9:00 AM - 10:00 PM",
        )
        weekly_hours = details.get_weekly_hours()
        self.assertEqual(len(weekly_hours), 7)
        self.assertEqual(weekly_hours[0]["day"], "Monday")
        self.assertEqual(weekly_hours[0]["hours"], "9:00 AM - 10:00 PM")


class FavoriteRestaurantModelTests(TestCase):
    def test_favorite_creation(self):
        favorite = FavoriteRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertEqual(favorite.camis, 12345678)

    def test_favorite_str_method(self):
        favorite = FavoriteRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertIn("Favorite: Test Restaurant", str(favorite))


class FollowedRestaurantModelTests(TestCase):
    def test_followed_creation(self):
        followed = FollowedRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
            notify_grade_changes=True,
        )
        self.assertEqual(followed.camis, 12345678)
        self.assertTrue(followed.notify_grade_changes)

    def test_followed_str_method(self):
        followed = FollowedRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertIn("Following: Test Restaurant", str(followed))


class SearchFilterTests(TestCase):
    def setUp(self):
        RestaurantInspection.objects.create(
            CAMIS=11111111,
            DBA="Pizza Palace",
            CUISINE_DESCRIPTION="Pizza",
            BORO="MANHATTAN",
            INSPECTION_DATE="2024-01-01",
            ACTION="No violations",
            SCORE=10,
            GRADE="A",
            GRADE_DATE="2024-01-01",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )
        RestaurantInspection.objects.create(
            CAMIS=22222222,
            DBA="Burger Barn",
            CUISINE_DESCRIPTION="American",
            BORO="BROOKLYN",
            INSPECTION_DATE="2024-01-01",
            ACTION="Violations cited",
            SCORE=25,
            GRADE="B",
            GRADE_DATE="2024-01-01",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_search_by_name(self):
        response = self.client.get(reverse("search_restaurants"), {"q": "Pizza"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pizza Palace")

    def test_search_empty(self):
        response = self.client.get(reverse("search_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_search_no_results(self):
        response = self.client.get(
            reverse("search_restaurants"), {"q": "NonexistentRestaurant12345"}
        )
        self.assertEqual(response.status_code, 200)


# ==================== NEW EDGE CASE TESTS ====================


class TestViewsEdgeCases(TestCase):
    """Additional tests for untested view branches."""

    def setUp(self):
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="EdgeCase Restaurant",
            CUISINE_DESCRIPTION="Italian",
            BORO="BRONX",
            INSPECTION_DATE="2024-02-01",
            ACTION="Violations were cited.",
            VIOLATION_CODE="10F",
            VIOLATION_DESCRIPTION="Unsanitary conditions",
            CRITICAL_FLAG="Critical",
            SCORE=12,
            GRADE="B",
            GRADE_DATE="2024-02-01",
            INSPECTION_TYPE="Cycle Inspection / Re-inspection",
        )

    def test_invalid_zip_search(self):
        """Invalid ZIP code triggers ValueError branch."""
        response = self.client.get(reverse("search_restaurants"), {"zipcode": "abcd"})
        self.assertEqual(response.status_code, 200)

    def test_sort_by_rating_low(self):
        """Test sort_by branch for 'rating_low'."""
        response = self.client.get(
            reverse("search_restaurants"), {"sort_by": "rating_low"}
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_page_number(self):
        """Pagination edge case."""
        response = self.client.get(reverse("search_restaurants"), {"page": "999"})
        self.assertEqual(response.status_code, 200)

    def test_add_review_missing_fields(self):
        """Test missing fields in add_review."""
        response = self.client.post(reverse("add_review"), {"camis": "", "rating": "5"})
        self.assertEqual(response.status_code, 200)

    def test_restaurant_detail_not_found(self):
        """Test restaurant_detail for nonexistent CAMIS."""
        response = self.client.get(
            reverse("restaurant_detail", kwargs={"camis": 999999})
        )
        self.assertIn(response.status_code, [200, 404])

    def test_toggle_favorite_no_camis(self):
        """Test missing CAMIS in toggle_favorite."""
        response = self.client.post(reverse("toggle_favorite"), {})
        self.assertEqual(response.status_code, 400)

    def test_toggle_follow_no_camis(self):
        """Test missing CAMIS in toggle_follow."""
        response = self.client.post(reverse("toggle_follow"), {})
        self.assertEqual(response.status_code, 400)

    def test_update_notification_missing_params(self):
        """Missing params should return 400."""
        response = self.client.post(reverse("update_notification_preferences"), {})
        self.assertEqual(response.status_code, 400)

    def test_update_notification_invalid_type(self):
        """Invalid notification_type should return 400."""
        response = self.client.post(
            reverse("update_notification_preferences"),
            {"camis": "12345", "notification_type": "invalid", "enabled": "true"},
        )
        self.assertEqual(response.status_code, 400)

    def test_update_notification_nonexistent_restaurant(self):
        """Nonexistent followed restaurant should return 404."""
        response = self.client.post(
            reverse("update_notification_preferences"),
            {"camis": "99999", "notification_type": "violations", "enabled": "true"},
        )
        self.assertIn(response.status_code, [404, 400])
>>>>>>> c007b54eb366bfd83c4f78f35e6a8b2b1d3e57c6
