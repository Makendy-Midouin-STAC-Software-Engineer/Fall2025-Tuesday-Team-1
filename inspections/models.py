from django.db import models
class OwnerRestaurant(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    restaurant = models.ForeignKey('RestaurantInspection', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'restaurant')
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.user.username} - {self.restaurant.DBA}"
from django.db import models
from django.db.models import Avg
from datetime import datetime, timedelta

class RestaurantMonthlySales(models.Model):
    camis = models.BigIntegerField()  # Link to RestaurantInspection
    month = models.DateField()  # Use first day of month
    sales = models.FloatField()  # Monthly sales amount

    class Meta:
        unique_together = ("camis", "month")
        ordering = ["-month"]

    def __str__(self):
        return f"{self.camis} - {self.month.strftime('%Y-%m')}: ${self.sales:,.2f}"
        
from django.db import models
from django.db.models import Avg
from datetime import datetime, timedelta


class RestaurantInspection(models.Model):
    CAMIS = models.BigIntegerField()
    DBA = models.CharField(max_length=255, null=True, blank=True)
    BORO = models.CharField(max_length=50, null=True, blank=True)
    BUILDING = models.CharField(max_length=50, null=True, blank=True)
    STREET = models.CharField(max_length=255, null=True, blank=True)
    ZIPCODE = models.FloatField(
        null=True, blank=True
    )  # Changed to match database structure
    PHONE = models.CharField(max_length=20, null=True, blank=True)
    CUISINE_DESCRIPTION = models.CharField(max_length=255, null=True, blank=True)
    INSPECTION_DATE = models.DateField(null=True, blank=True)
    ACTION = models.TextField(null=True, blank=True)
    VIOLATION_CODE = models.CharField(max_length=20, null=True, blank=True)
    VIOLATION_DESCRIPTION = models.TextField(null=True, blank=True)
    CRITICAL_FLAG = models.CharField(max_length=50, null=True, blank=True)
    SCORE = models.FloatField(
        null=True, blank=True
    )  # Changed to match database structure
    GRADE = models.CharField(max_length=5, null=True, blank=True)
    GRADE_DATE = models.DateField(null=True, blank=True)
    INSPECTION_TYPE = models.CharField(max_length=255, null=True, blank=True)
    Community_Board = models.FloatField(
        null=True, blank=True
    )  # Changed to match database structure
    Council_District = models.FloatField(
        null=True, blank=True
    )  # Changed to match database structure
    Census_Tract = models.FloatField(
        null=True, blank=True
    )  # Changed to match database structure

    def __str__(self):
        return f"{self.DBA} ({self.CAMIS})"

    @classmethod
    def get_restaurant_rating(cls, camis):
        """
        Calculate overall restaurant rating based on recent inspections.
        Returns a dictionary with rating info.
        """
        # Get recent inspections for this restaurant (within last 3 years)
        cutoff_date = datetime.now().date() - timedelta(days=1095)
        recent_inspections = cls.objects.filter(
            CAMIS=camis, GRADE__in=["A", "B", "C"], INSPECTION_DATE__gte=cutoff_date
        ).exclude(
            INSPECTION_DATE__year=1900
        )  # Exclude invalid dates

        if not recent_inspections.exists():
            # Fallback to all inspections if no recent ones
            recent_inspections = cls.objects.filter(
                CAMIS=camis, GRADE__in=["A", "B", "C"]
            ).exclude(INSPECTION_DATE__year=1900)

        if not recent_inspections.exists():
            return {
                "stars": 0,
                "grade": "N/A",
                "inspection_count": 0,
                "latest_inspection": None,
                "description": "No graded inspections available",
            }

        # Calculate average grade (A=5, B=4, C=3)
        grade_values = {"A": 5, "B": 4, "C": 3}

        grades = recent_inspections.values_list("GRADE", flat=True)
        total_points = sum(grade_values.get(grade, 0) for grade in grades)
        avg_rating = total_points / len(grades) if grades else 0

        # Get the most common grade
        grade_counts = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        most_common_grade = (
            max(grade_counts, key=grade_counts.get) if grade_counts else "N/A"
        )

        # Get latest inspection info
        latest = recent_inspections.order_by("-INSPECTION_DATE").first()

        # Create description
        inspection_count = recent_inspections.count()
        if avg_rating >= 4.5:
            description = f"Excellent (mostly A grades, {inspection_count} inspections)"
        elif avg_rating >= 3.5:
            description = f"Good (mostly A-B grades, {inspection_count} inspections)"
        elif avg_rating >= 2.5:
            description = f"Fair (mixed grades, {inspection_count} inspections)"
        else:
            description = f"Needs improvement ({inspection_count} inspections)"

        return {
            "stars": round(avg_rating, 1),
            "grade": most_common_grade,
            "inspection_count": inspection_count,
            "latest_inspection": latest.INSPECTION_DATE if latest else None,
            "description": description,
            "avg_score": recent_inspections.aggregate(avg=Avg("SCORE"))["avg"] or 0,
        }

    def get_grade_display(self):
        """Get a human-readable grade description"""
        grade_descriptions = {
            "A": "Excellent",
            "B": "Good",
            "C": "Fair",
            "N": "Not Yet Graded",
            "P": "Pending",
            "Z": "Grade Pending",
        }
        return grade_descriptions.get(self.GRADE, "Unknown")


class RestaurantReview(models.Model):
    """User-submitted reviews for restaurants"""

    camis = models.BigIntegerField()  # Link to restaurant
    restaurant_name = models.CharField(max_length=255)
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review_text = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)  # For future verification system

    class Meta:
        ordering = ["-review_date"]

    def __str__(self):
        return f"{self.restaurant_name} - {self.rating} stars by {self.reviewer_name}"

    @property
    def stars_display(self):
        """Return star rating as string of stars"""
        return "★" * self.rating + "☆" * (5 - self.rating)


class RestaurantDetails(models.Model):
    """Extended restaurant information including hours, menu, contact details"""

    camis = models.BigIntegerField(unique=True)  # Link to restaurant inspections
    restaurant_name = models.CharField(max_length=255)

    # Contact Information
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_formatted = models.CharField(
        max_length=20, blank=True, null=True
    )  # Better formatted phone

    # Hours of Operation
    monday_hours = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., '9:00 AM - 10:00 PM' or 'Closed'",
    )
    tuesday_hours = models.CharField(max_length=50, blank=True, null=True)
    wednesday_hours = models.CharField(max_length=50, blank=True, null=True)
    thursday_hours = models.CharField(max_length=50, blank=True, null=True)
    friday_hours = models.CharField(max_length=50, blank=True, null=True)
    saturday_hours = models.CharField(max_length=50, blank=True, null=True)
    sunday_hours = models.CharField(max_length=50, blank=True, null=True)

    # Menu and Service Information
    menu_highlights = models.TextField(
        blank=True, null=True, help_text="Popular dishes, specialties"
    )
    price_range = models.CharField(
        max_length=20, blank=True, null=True, help_text="e.g., '$', '$$', '$$$', '$$$$'"
    )
    delivery_available = models.BooleanField(default=False)
    takeout_available = models.BooleanField(default=True)
    reservations_accepted = models.BooleanField(default=False)

    # Additional Details
    description = models.TextField(
        blank=True, null=True, help_text="Restaurant description/about"
    )
    special_features = models.TextField(
        blank=True, null=True, help_text="Outdoor seating, live music, etc."
    )
    parking_info = models.CharField(max_length=200, blank=True, null=True)

    # Management fields
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(
        default=False
    )  # For verified business information

    def __str__(self):
        return f"{self.restaurant_name} (CAMIS: {self.camis})"

    @property
    def hours_today(self):
        """Get today's hours, always returns a string."""
        import datetime
        today = datetime.datetime.now().strftime("%A").lower()
        hours_field = f"{today}_hours"
        hours = getattr(self, hours_field, None)
        if not hours:
            return "Hours not available"
        return hours

    @property
    def is_open_now(self):
        """Check if restaurant is currently open (simplified logic)"""
        hours = self.hours_today
        if not hours or hours.lower() in ["closed", "hours not available"]:
            return False
        # This is a simplified check - real implementation would parse hours
        return "closed" not in hours.lower()

    def get_weekly_hours(self):
        """Return all weekly hours as a list"""
        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        weekly_hours = []
        for day in days:
            hours = getattr(self, f"{day}_hours", None)
            weekly_hours.append(
                {"day": day.capitalize(), "hours": hours or "Hours not available"}
            )
        return weekly_hours


class FavoriteRestaurant(models.Model):
    """Track user's favorite restaurants using session ID for anonymous users"""

    session_key = models.CharField(max_length=40)  # Django session key
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    camis = models.BigIntegerField()  # Restaurant identifier
    restaurant_name = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session_key", "camis")  # Prevent duplicate favorites
        ordering = ["-date_added"]

    def __str__(self):
        return f"Favorite: {self.restaurant_name} (Session: {self.session_key[:8]}...)"


class FollowedRestaurant(models.Model):
    """Track restaurants users are following for health and rating updates"""

    session_key = models.CharField(max_length=40)  # Django session key
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    camis = models.BigIntegerField()  # Restaurant identifier
    restaurant_name = models.CharField(max_length=255)
    date_followed = models.DateTimeField(auto_now_add=True)

    # Notification preferences
    notify_grade_changes = models.BooleanField(default=True)
    notify_new_inspections = models.BooleanField(default=True)
    notify_violations = models.BooleanField(default=True)

    # Track last known state to detect changes
    last_known_grade = models.CharField(max_length=5, null=True, blank=True)
    last_inspection_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("session_key", "camis")  # Prevent duplicate follows
        ordering = ["-date_followed"]

    def __str__(self):
        return f"Following: {self.restaurant_name} (Session: {self.session_key[:8]}...)"


class RestaurantNotification(models.Model):
    """Store notifications for followed restaurant updates"""

    NOTIFICATION_TYPES = [
        ("grade_change", "Grade Change"),
        ("new_inspection", "New Inspection"),
        ("violation_added", "Violation Added"),
        ("score_improvement", "Score Improvement"),
        ("score_decline", "Score Decline"),
        ("health_outbreak", "Health Outbreak"),
    ]

    followed_restaurant = models.ForeignKey(
        FollowedRestaurant, on_delete=models.CASCADE
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.followed_restaurant.restaurant_name}"
