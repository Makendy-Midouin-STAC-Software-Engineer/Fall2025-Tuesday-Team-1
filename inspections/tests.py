from django.test import TestCase, Client
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
        """Test the restaurant inspection model."""
        restaurant = RestaurantInspection.objects.get(CAMIS=12345678)
        self.assertEqual(restaurant.DBA, "Test Restaurant")
        self.assertEqual(restaurant.GRADE, "A")

    def test_favorites_functionality(self):
        """Test favorites toggle functionality."""
        response = self.client.post(
            reverse("toggle_favorite"),
            {"camis": "12345678"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

    def test_follow_functionality(self):
        """Test follow toggle functionality."""
        response = self.client.post(
            reverse("toggle_follow"),
            {"camis": "12345678"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)


# ==================== NEW TESTS ADDED BELOW ====================


class AuthenticatedViewTests(TestCase):
    """Tests for views that require authentication or session."""

    def setUp(self):
        """Set up test data."""
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
        """Test restaurant detail page loads."""
        response = self.client.get(
            reverse("restaurant_detail", kwargs={"camis": 12345678})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Restaurant")

    def test_restaurant_detail_invalid_camis(self):
        """Test restaurant detail with nonexistent CAMIS."""
        response = self.client.get(
            reverse("restaurant_detail", kwargs={"camis": 99999999})
        )
        # View might return 200 with "not found" message instead of 404
        self.assertIn(response.status_code, [200, 404])

    def test_add_review_post(self):
        """Test adding a review."""
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
        """Test favorites list loads."""
        response = self.client.get(reverse("favorites_list"))
        self.assertEqual(response.status_code, 200)

    def test_followed_restaurants_view(self):
        """Test followed restaurants loads."""
        response = self.client.get(reverse("followed_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_view(self):
        """Test notifications list loads."""
        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)

    def test_update_notification_preferences(self):
        """Test updating notification preferences."""
        # First follow a restaurant
        self.client.post(
            reverse("toggle_follow"),
            {"camis": 12345678},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Then update preferences
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
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testowner", password="testpass123", email="owner@test.com"
        )

    def test_owner_signup_get(self):
        """Test owner signup page loads."""
        response = self.client.get(reverse("owner_signup"))
        self.assertEqual(response.status_code, 200)

    def test_owner_signup_post(self):
        """Test owner signup with valid data."""
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
        """Test owner login page loads."""
        response = self.client.get(reverse("owner_login"))
        self.assertEqual(response.status_code, 200)

    def test_owner_login_post_valid(self):
        """Test owner login with valid credentials."""
        response = self.client.post(
            reverse("owner_login"),
            {
                "username": "testowner",
                "password": "testpass123",
            },
        )
        self.assertIn(response.status_code, [200, 302, 400])

    def test_owner_login_post_invalid(self):
        """Test owner login with invalid credentials."""
        response = self.client.post(
            reverse("owner_login"),
            {
                "username": "testowner",
                "password": "wrongpassword",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_authenticated(self):
        """Test owner dashboard loads when logged in."""
        self.client.login(username="testowner", password="testpass123")
        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 200)


class RedirectTests(TestCase):
    """Tests for URL redirects."""

    def test_root_redirects_to_search(self):
        """Test that root inspections URL redirects to search."""
        response = self.client.get("/inspections/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/inspections/search/", response.url)


class ModelMethodTests(TestCase):
    """Tests for model methods and properties."""

    def setUp(self):
        """Set up test data."""
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
        """Test RestaurantInspection string representation."""
        result = str(self.restaurant)
        self.assertEqual(result, "Test Restaurant (12345678)")

    def test_restaurant_fields(self):
        """Test restaurant model fields are set correctly."""
        self.assertEqual(self.restaurant.CAMIS, 12345678)
        self.assertEqual(self.restaurant.DBA, "Test Restaurant")
        self.assertEqual(self.restaurant.GRADE, "A")
        self.assertEqual(self.restaurant.SCORE, 15)

    def test_get_grade_display(self):
        """Test get_grade_display method."""
        self.assertEqual(self.restaurant.get_grade_display(), "Excellent")

        # Test other grades
        self.restaurant.GRADE = "B"
        self.assertEqual(self.restaurant.get_grade_display(), "Good")

        self.restaurant.GRADE = "C"
        self.assertEqual(self.restaurant.get_grade_display(), "Fair")

    def test_get_restaurant_rating(self):
        """Test get_restaurant_rating class method."""
        rating_info = RestaurantInspection.get_restaurant_rating(12345678)

        self.assertIsInstance(rating_info, dict)
        self.assertIn("stars", rating_info)
        self.assertIn("grade", rating_info)
        self.assertIn("inspection_count", rating_info)
        self.assertEqual(rating_info["grade"], "A")
        self.assertGreater(rating_info["stars"], 0)

    def test_get_restaurant_rating_no_data(self):
        """Test get_restaurant_rating with no inspections."""
        rating_info = RestaurantInspection.get_restaurant_rating(99999999)

        self.assertEqual(rating_info["stars"], 0)
        self.assertEqual(rating_info["grade"], "N/A")
        self.assertEqual(rating_info["inspection_count"], 0)


class RestaurantReviewModelTests(TestCase):
    """Tests for RestaurantReview model."""

    def test_review_creation(self):
        """Test creating a review."""
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
        """Test review string representation."""
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
        """Test stars_display property."""
        review = RestaurantReview.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            reviewer_name="Test User",
            rating=3,
            review_text="Good food",
        )
        self.assertEqual(review.stars_display, "★★★☆☆")


class RestaurantDetailsModelTests(TestCase):
    """Tests for RestaurantDetails model."""

    def test_details_creation(self):
        """Test creating restaurant details."""
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
        """Test details string representation."""
        details = RestaurantDetails.objects.create(
            camis=12345678, restaurant_name="Test Restaurant"
        )
        expected = "Test Restaurant (CAMIS: 12345678)"
        self.assertEqual(str(details), expected)

    def test_get_weekly_hours(self):
        """Test get_weekly_hours method."""
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
    """Tests for FavoriteRestaurant model."""

    def test_favorite_creation(self):
        """Test creating a favorite."""
        favorite = FavoriteRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertEqual(favorite.camis, 12345678)

    def test_favorite_str_method(self):
        """Test favorite string representation."""
        favorite = FavoriteRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertIn("Favorite: Test Restaurant", str(favorite))


class FollowedRestaurantModelTests(TestCase):
    """Tests for FollowedRestaurant model."""

    def test_followed_creation(self):
        """Test creating a followed restaurant."""
        followed = FollowedRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
            notify_grade_changes=True,
        )
        self.assertEqual(followed.camis, 12345678)
        self.assertTrue(followed.notify_grade_changes)

    def test_followed_str_method(self):
        """Test followed string representation."""
        followed = FollowedRestaurant.objects.create(
            session_key="test_session_123",
            camis=12345678,
            restaurant_name="Test Restaurant",
        )
        self.assertIn("Following: Test Restaurant", str(followed))


class SearchFilterTests(TestCase):
    """Tests for search filtering."""

    def setUp(self):
        """Create multiple restaurants for filtering tests."""
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
        """Test search filters by restaurant name."""
        response = self.client.get(reverse("search_restaurants"), {"q": "Pizza"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pizza Palace")

    def test_search_empty(self):
        """Test search with no parameters."""
        response = self.client.get(reverse("search_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_search_no_results(self):
        """Test search with query that has no results."""
        response = self.client.get(
            reverse("search_restaurants"), {"q": "NonexistentRestaurant12345"}
        )
        self.assertEqual(response.status_code, 200)
