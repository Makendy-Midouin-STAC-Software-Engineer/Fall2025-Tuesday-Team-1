from django.test import TestCase
from django.urls import reverse
from inspections.models import RestaurantInspection


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
