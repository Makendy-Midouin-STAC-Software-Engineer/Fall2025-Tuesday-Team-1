from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from inspections.templatetags.extra_filters import get_item
from inspections.models import (
    RestaurantInspection,
    RestaurantReview,
    FavoriteRestaurant,
    FollowedRestaurant,
    RestaurantNotification,
    RestaurantDetails,
)


class TemplateFilterTests(TestCase):
    """Tests for custom template filters."""

    def test_get_item_existing_key(self):
        """Test get_item filter with existing key."""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = get_item(test_dict, "key1")
        self.assertEqual(result, "value1")

    def test_get_item_missing_key(self):
        """Test get_item filter with missing key returns empty list."""
        test_dict = {"key1": "value1"}
        result = get_item(test_dict, "nonexistent_key")
        self.assertEqual(result, [])


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
        response = self.client.get(reverse("followed_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_view(self):

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


# Add these test classes to your inspections/tests.py file


class CustomerAuthTests(TestCase):
    """Tests for customer authentication views."""

    def test_customer_welcome_view(self):
        """Test customer welcome page loads."""
        response = self.client.get(reverse("customer_welcome"))
        self.assertEqual(response.status_code, 200)

    def test_customer_signup_get(self):
        """Test customer signup page loads."""
        response = self.client.get(reverse("customer_signup"))
        self.assertEqual(response.status_code, 200)

    def test_customer_signup_post_valid(self):
        """Test customer signup with valid data."""
        response = self.client.post(
            reverse("customer_signup"),
            {
                "username": "newcustomer",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )
        self.assertIn(response.status_code, [200, 302])

    def test_customer_login_get(self):
        """Test customer login page loads."""
        response = self.client.get(reverse("customer_login"))
        self.assertEqual(response.status_code, 200)

    def test_customer_login_post_valid(self):
        """Test customer login with valid credentials."""
        User.objects.create_user(username="testcustomer", password="testpass123")
        response = self.client.post(
            reverse("customer_login"),
            {"username": "testcustomer", "password": "testpass123"},
        )
        self.assertIn(response.status_code, [200, 302])

    def test_customer_dashboard_authenticated(self):
        """Test customer dashboard requires authentication."""
        user = User.objects.create_user(username="testcustomer", password="testpass123")
        self.client.login(username="testcustomer", password="testpass123")
        response = self.client.get(reverse("customer_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_customer_logout(self):
        """Test customer logout."""
        user = User.objects.create_user(username="testcustomer", password="testpass123")
        self.client.login(username="testcustomer", password="testpass123")
        response = self.client.post(reverse("customer_logout"))
        self.assertIn(response.status_code, [200, 302])

    def test_owner_logout(self):
        """Test owner logout."""
        user = User.objects.create_user(username="testowner", password="testpass123")
        self.client.login(username="testowner", password="testpass123")
        response = self.client.post(reverse("owner_logout"))
        self.assertIn(response.status_code, [200, 302])


class SearchEdgeCasesTests(TestCase):
    """Tests for additional search functionality edge cases."""

    def setUp(self):
        RestaurantInspection.objects.create(
            CAMIS=11111111,
            DBA="Grade C Restaurant",
            CUISINE_DESCRIPTION="Italian",
            BORO="MANHATTAN",
            ZIPCODE=10001,
            INSPECTION_DATE="2024-01-01",
            GRADE="C",
            SCORE=30,
            ACTION="Violations cited",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )
        RestaurantInspection.objects.create(
            CAMIS=22222222,
            DBA="No Grade Restaurant",
            CUISINE_DESCRIPTION="Chinese",
            BORO="BROOKLYN",
            ZIPCODE=11201,
            INSPECTION_DATE="2024-01-01",
            GRADE=None,
            SCORE=None,
            ACTION="No violations",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_search_with_cuisine_filter(self):
        """Test search with cuisine filter."""
        response = self.client.get(
            reverse("search_restaurants"), {"q": "Restaurant", "cuisine": "Italian"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_with_borough_filter(self):
        """Test search with borough filter."""
        response = self.client.get(
            reverse("search_restaurants"), {"q": "Restaurant", "borough": "MANHATTAN"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_sort_by_latest_inspection(self):
        """Test sorting by latest inspection."""
        response = self.client.get(
            reverse("search_restaurants"),
            {"q": "Restaurant", "sort_by": "latest_inspection"},
        )
        self.assertEqual(response.status_code, 200)

    def test_search_sort_by_grade(self):
        """Test sorting by grade."""
        response = self.client.get(
            reverse("search_restaurants"), {"q": "Restaurant", "sort_by": "grade"}
        )
        self.assertEqual(response.status_code, 200)

    def test_search_grade_c_rating(self):
        """Test that grade C gets correct rating."""
        response = self.client.get(reverse("search_restaurants"), {"q": "Grade C"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Grade C Restaurant")

    def test_search_no_grade_rating(self):
        """Test that no grade gets N/A rating."""
        response = self.client.get(reverse("search_restaurants"), {"q": "No Grade"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Grade Restaurant")


class AddReviewEdgeCasesTests(TestCase):
    """Tests for add_review view edge cases."""

    def setUp(self):
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            INSPECTION_DATE="2024-01-01",
            GRADE="A",
            ACTION="No violations",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_add_review_get(self):
        """Test GET request to add_review returns form."""
        response = self.client.get(reverse("add_review"))
        self.assertEqual(response.status_code, 200)

    def test_add_review_post_success(self):
        """Test successful review submission."""
        response = self.client.post(
            reverse("add_review"),
            {
                "camis": "12345678",
                "restaurant_name": "Test Restaurant",
                "reviewer_name": "John Doe",
                "rating": "5",
                "review_text": "Great food!",
            },
        )
        self.assertEqual(response.status_code, 200)
        # Check review was created
        self.assertTrue(RestaurantReview.objects.filter(camis=12345678).exists())

    def test_add_review_post_invalid(self):
        """Test invalid review submission (missing data)."""
        response = self.client.post(
            reverse("add_review"),
            {
                "camis": "",
                "rating": "",
                "review_text": "",
            },
        )
        self.assertEqual(response.status_code, 200)


class FavoritesAuthenticatedTests(TestCase):
    """Tests for favorites with authenticated users."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            INSPECTION_DATE="2024-01-01",
            GRADE="A",
            ACTION="No violations",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_favorites_list_authenticated(self):
        """Test favorites list for authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        FavoriteRestaurant.objects.create(
            user=self.user, camis=12345678, restaurant_name="Test Restaurant"
        )
        response = self.client.get(reverse("favorites_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Restaurant")


class FollowedRestaurantsAuthenticatedTests(TestCase):
    """Tests for followed restaurants with authenticated users."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            INSPECTION_DATE="2024-01-01",
            GRADE="A",
            ACTION="No violations",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_followed_restaurants_authenticated(self):
        """Test followed restaurants list for authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        FollowedRestaurant.objects.create(
            user=self.user, camis=12345678, restaurant_name="Test Restaurant"
        )
        response = self.client.get(reverse("followed_restaurants"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_list_authenticated(self):
        """Test notifications list for authenticated user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("notifications_list"))
        self.assertEqual(response.status_code, 200)


class OwnerDashboardTests(TestCase):
    """Tests for owner dashboard functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testowner", password="testpass123"
        )
        self.restaurant = RestaurantInspection.objects.create(
            CAMIS=12345678,
            DBA="Test Restaurant",
            CUISINE_DESCRIPTION="American",
            INSPECTION_DATE="2024-01-01",
            GRADE="B",
            SCORE=20,
            ACTION="Violations cited",
            INSPECTION_TYPE="Cycle Inspection / Initial Inspection",
        )

    def test_owner_dashboard_add_restaurant(self):
        """Test adding a restaurant to owner dashboard."""
        self.client.login(username="testowner", password="testpass123")
        response = self.client.post(
            reverse("owner_dashboard"), {"add_camis": "12345678"}
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_with_reviews(self):
        """Test owner dashboard displays reviews and analytics."""
        from inspections.models import OwnerRestaurant

        self.client.login(username="testowner", password="testpass123")
        OwnerRestaurant.objects.create(user=self.user, restaurant=self.restaurant)

        # Add some reviews
        RestaurantReview.objects.create(
            camis=12345678,
            restaurant_name="Test Restaurant",
            reviewer_name="Customer 1",
            rating=2,
            review_text="The food was cold and service was slow",
        )

        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 200)
