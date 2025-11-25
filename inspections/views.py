def owner_logout(request):
    """Log out an owner and redirect to owner login."""
    logout(request)
    return redirect("owner_login")


# --- Add Review ---
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def add_review(request):
    """Allow users to add a review for a restaurant."""
    if request.method == "POST":
        camis = request.POST.get("camis")
        restaurant_name = request.POST.get("restaurant_name")
        reviewer_name = request.POST.get("reviewer_name", "Anonymous")
        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text")
        if camis and rating and review_text:
            RestaurantReview.objects.create(
                camis=camis,
                restaurant_name=restaurant_name,
                reviewer_name=reviewer_name,
                rating=int(rating),
                review_text=review_text,
            )
            return render(
                request,
                "inspections/review_success.html",
                {"restaurant_name": restaurant_name},
            )
        # If missing data, fall through to re-render form with error
    # For GET or invalid POST, show the form
    restaurant_name = request.GET.get("restaurant_name", "")
    return render(
        request, "inspections/add_review.html", {"restaurant_name": restaurant_name}
    )


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.contrib.auth import login, logout
from django.db.models import Q
from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import (
    RestaurantInspection,
    RestaurantReview,
    FavoriteRestaurant,
    FollowedRestaurant,
    RestaurantNotification,
    RestaurantDetails,
    OwnerRestaurant,
)
from .forms import OwnerSignUpForm


# Helper to check if a restaurant is favorited by the current user/session
def is_restaurant_favorited(request, camis):
    if request.user.is_authenticated:
        return FavoriteRestaurant.objects.filter(
            user=request.user, camis=camis
        ).exists()
    else:
        session_key = request.session.session_key
        if not session_key:
            return False
        return FavoriteRestaurant.objects.filter(
            session_key=session_key, camis=camis
        ).exists()


# --- Authentication and session sync ---
def customer_welcome(request):
    return render(request, "inspections/customer_welcome.html")


def customer_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Ensure session is created before accessing session_key
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            if session_key:
                try:
                    FavoriteRestaurant.objects.filter(
                        session_key=session_key, user__isnull=True
                    ).update(user=user)
                    FollowedRestaurant.objects.filter(
                        session_key=session_key, user__isnull=True
                    ).update(user=user)
                except Exception as e:
                    # Log error but don't fail signup
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error syncing session data: {e}")
            return redirect("search_restaurants")
    else:
        form = UserCreationForm()
    return render(request, "inspections/customer_signup.html", {"form": form})


def customer_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            session_key = request.session.session_key
            if session_key:
                FavoriteRestaurant.objects.filter(
                    session_key=session_key, user__isnull=True
                ).update(user=user)
                FollowedRestaurant.objects.filter(
                    session_key=session_key, user__isnull=True
                ).update(user=user)
            return redirect("search_restaurants")
    else:
        form = AuthenticationForm()
    return render(request, "inspections/customer_login.html", {"form": form})


@login_required
def customer_dashboard(request):
    favorites = FavoriteRestaurant.objects.filter(user=request.user)
    followed = FollowedRestaurant.objects.filter(user=request.user)
    return render(
        request,
        "inspections/customer_dashboard.html",
        {"favorites": favorites, "followed": followed},
    )


# --- Search and listing ---
def search_restaurants(request):
    query = request.GET.get("q", "").strip()
    cuisine = request.GET.get("cuisine", "").strip()
    zipcode = request.GET.get("zipcode", "").strip()
    borough = request.GET.get("borough", "").strip()
    sort_by = request.GET.get("sort_by", "name").strip()
    page_number = request.GET.get("page", 1)

    restaurants = []
    paginator = None
    page_obj = None

    if query or cuisine or zipcode or borough:
        search_filter = Q()
        if query:
            search_filter &= Q(DBA__icontains=query) | Q(
                CUISINE_DESCRIPTION__icontains=query
            )
        if cuisine and cuisine != "All Cuisines":
            search_filter &= Q(CUISINE_DESCRIPTION__icontains=cuisine)
        if zipcode:
            try:
                zipcode_num = float(zipcode)
                search_filter &= Q(ZIPCODE=zipcode_num)
            except ValueError:
                pass
        if borough and borough != "All Boroughs":
            search_filter &= Q(BORO__iexact=borough)

        inspections = RestaurantInspection.objects.filter(search_filter).order_by(
            "CAMIS", "-INSPECTION_DATE"
        )
        seen_camis = set()
        limited_restaurants = []
        for inspection in inspections:
            if inspection.CAMIS not in seen_camis:
                seen_camis.add(inspection.CAMIS)
                limited_restaurants.append(
                    {
                        "CAMIS": inspection.CAMIS,
                        "DBA": inspection.DBA,
                        "BUILDING": inspection.BUILDING,
                        "STREET": inspection.STREET,
                        "BORO": inspection.BORO,
                        "ZIPCODE": inspection.ZIPCODE,
                        "CUISINE_DESCRIPTION": inspection.CUISINE_DESCRIPTION,
                    }
                )
        camis_list = [rest["CAMIS"] for rest in limited_restaurants]
        latest_inspections = {}
        if camis_list:
            for inspection in RestaurantInspection.objects.filter(
                CAMIS__in=camis_list
            ).order_by("CAMIS", "-INSPECTION_DATE"):
                if inspection.CAMIS not in latest_inspections:
                    latest_inspections[inspection.CAMIS] = inspection
        restaurants = []
        for rest_data in limited_restaurants:
            latest_inspection = latest_inspections.get(rest_data["CAMIS"])
            if latest_inspection and latest_inspection.GRADE:
                grade = latest_inspection.GRADE
                if grade == "A":
                    stars = 5
                    description = "Excellent"
                elif grade == "B":
                    stars = 4
                    description = "Good"
                elif grade == "C":
                    stars = 3
                    description = "Fair"
                else:
                    stars = 2
                    description = "Needs improvement"
            else:
                stars = 0
                grade = "N/A"
                description = "No grade available"
            restaurants.append(
                {
                    "info": type(
                        "obj",
                        (object,),
                        {
                            "CAMIS": rest_data["CAMIS"],
                            "DBA": rest_data["DBA"],
                            "BUILDING": rest_data["BUILDING"],
                            "STREET": rest_data["STREET"],
                            "BORO": rest_data["BORO"],
                            "ZIPCODE": rest_data["ZIPCODE"],
                            "CUISINE_DESCRIPTION": rest_data["CUISINE_DESCRIPTION"],
                        },
                    ),
                    "rating": {
                        "stars": stars,
                        "grade": grade,
                        "description": description,
                        "inspection_count": 1,
                        "latest_inspection": (
                            latest_inspection.INSPECTION_DATE
                            if latest_inspection
                            else None
                        ),
                    },
                    "reviews": [],
                    "citations": [],
                }
            )
        if sort_by == "rating_high":
            restaurants.sort(key=lambda r: r["rating"]["stars"], reverse=True)
        elif sort_by == "rating_low":
            restaurants.sort(key=lambda r: r["rating"]["stars"])
        elif sort_by == "name":
            restaurants.sort(key=lambda r: r["info"].DBA or "")
        elif sort_by == "latest_inspection":
            restaurants.sort(
                key=lambda r: r["rating"]["latest_inspection"] or date(1900, 1, 1),
                reverse=True,
            )
        elif sort_by == "grade":
            grade_order = {"A": 1, "B": 2, "C": 3, "N": 4, "P": 5, "Z": 6}
            restaurants.sort(key=lambda r: grade_order.get(r["rating"]["grade"], 7))
        paginator = Paginator(restaurants, 20)
        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)
    all_cuisines = (
        RestaurantInspection.objects.values_list("CUISINE_DESCRIPTION", flat=True)
        .distinct()
        .exclude(CUISINE_DESCRIPTION__isnull=True)
        .exclude(CUISINE_DESCRIPTION__exact="")
        .order_by("CUISINE_DESCRIPTION")
    )
    all_boroughs = (
        RestaurantInspection.objects.values_list("BORO", flat=True)
        .distinct()
        .exclude(BORO__isnull=True)
        .exclude(BORO__exact="")
        .order_by("BORO")
    )
    context = {
        "restaurants": page_obj.object_list if page_obj else restaurants,
        "page_obj": page_obj,
        "paginator": paginator,
        "query": query,
        "cuisine": cuisine,
        "zipcode": zipcode,
        "borough": borough,
        "sort_by": sort_by,
        "all_cuisines": all_cuisines,
        "all_boroughs": all_boroughs,
        "total_results": len(restaurants) if restaurants else 0,
        "results_limited": len(restaurants) >= 200,
    }
    return render(request, "inspections/search.html", context)


# --- Notifications ---
def notifications_list(request):
    """Display all notifications for followed restaurants (customer view). Always returns an HttpResponse."""
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    if request.user.is_authenticated:
        notifications = RestaurantNotification.objects.filter(
            followed_restaurant__user=request.user
        ).order_by("-created_at")
    else:
        notifications = RestaurantNotification.objects.filter(
            followed_restaurant__session_key=session_key
        ).order_by("-created_at")
    notifications.filter(is_read=False).update(is_read=True)
    context = {
        "notifications": notifications,
        "total_notifications": notifications.count(),
    }
    return render(request, "inspections/notifications.html", context)


def restaurant_detail(request, camis):
    """Display detailed information about a specific restaurant"""
    from inspections.models import RestaurantDetails

    # Get restaurant inspection info
    restaurant = RestaurantInspection.objects.filter(CAMIS=camis).first()
    if not restaurant:
        return render(request, "inspections/restaurant_not_found.html")

    # Get all inspections for this restaurant
    all_inspections = RestaurantInspection.objects.filter(CAMIS=camis).order_by(
        "-INSPECTION_DATE"
    )

    # Get rating information
    rating_info = RestaurantInspection.get_restaurant_rating(camis)

    # Get all reviews
    reviews = RestaurantReview.objects.filter(camis=camis).order_by("-review_date")

    # Get extended details (or create empty one if doesn't exist)
    try:
        details = RestaurantDetails.objects.get(camis=camis)
    except RestaurantDetails.DoesNotExist:
        # Create a basic details entry for this restaurant
        details = RestaurantDetails(
            camis=camis,
            restaurant_name=restaurant.DBA or "Restaurant Name Not Available",
        )
        # Don't save it yet - just use for display

    # Check if restaurant is favorited by current user
    is_favorited = is_restaurant_favorited(request, camis)

    context = {
        "restaurant": restaurant,
        "details": details,
        "rating": rating_info,
        "reviews": reviews,
        "all_inspections": all_inspections[:10],  # Limit to recent 10 inspections
        "total_inspections": all_inspections.count(),
        "is_favorited": is_favorited,
    }

    return render(request, "inspections/restaurant_detail.html", context)


# === Owner Auth & Dashboard ===


def owner_signup(request):
    if request.method == "POST":
        form = OwnerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("owner_dashboard")
    else:
        form = OwnerSignUpForm()
    return render(request, "inspections/owner_signup.html", {"form": form})


def owner_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("owner_dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "inspections/owner_login.html", {"form": form})


@login_required
def owner_dashboard(request):
    # Build dashboard data for the logged-in owner
    owned = OwnerRestaurant.objects.filter(user=request.user).select_related(
        "restaurant"
    )

    dashboard_data = []
    for owner_rel in owned:
        rest_inspection = owner_rel.restaurant
        camis = rest_inspection.CAMIS
        rating = RestaurantInspection.get_restaurant_rating(camis)

        # Determine if an alert should be shown for low ratings (C or lower)
        rating_alert = None
        try:
            grade = rating.get("grade")
            if grade and grade in ["C"]:
                rating_alert = f"Low rating: {grade}"
        except Exception:
            rating_alert = None

        dashboard_data.append(
            {
                "owner_relationship": owner_rel,
                "restaurant": rest_inspection,
                "rating": rating,
                "rating_alert": rating_alert,
            }
        )

    return render(
        request,
        "inspections/owner_dashboard.html",
        {"dashboard_data": dashboard_data},
    )


@require_POST
def toggle_favorite(request):
    camis = request.POST.get("camis")
    if not camis:
        return JsonResponse({"error": "Missing camis"}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        fav, created = FavoriteRestaurant.objects.get_or_create(
            user=request.user, camis=camis
        )
    else:
        fav, created = FavoriteRestaurant.objects.get_or_create(
            session_key=session_key, camis=camis
        )

    if not created:
        fav.delete()
        return JsonResponse({"is_favorited": False})

    return JsonResponse({"is_favorited": True})


@require_POST
def toggle_follow(request):
    camis = request.POST.get("camis")
    restaurant_name = request.POST.get("restaurant_name", "")
    if not camis:
        return JsonResponse({"error": "Missing camis"}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        follow, created = FollowedRestaurant.objects.get_or_create(
            user=request.user,
            camis=camis,
            defaults={"restaurant_name": restaurant_name},
        )
    else:
        follow, created = FollowedRestaurant.objects.get_or_create(
            session_key=session_key,
            camis=camis,
            defaults={"restaurant_name": restaurant_name},
        )

    # If newly created, populate last_known_grade and last_inspection_date from latest inspection
    if created:
        latest_inspection = (
            RestaurantInspection.objects.filter(CAMIS=camis)
            .order_by("-INSPECTION_DATE")
            .first()
        )
        if latest_inspection:
            follow.last_known_grade = latest_inspection.GRADE
            follow.last_inspection_date = latest_inspection.INSPECTION_DATE
            follow.save()

    is_followed = created
    message = ""
    if created:
        message = (
            f"Now following {restaurant_name} - You'll get notified of health updates!"
        )
    else:
        follow.delete()
        message = f"Stopped following {restaurant_name}"
        is_followed = False

    return JsonResponse({"is_followed": is_followed, "message": message})


def favorites_list(request):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        favorites = FavoriteRestaurant.objects.filter(user=request.user)
    else:
        favorites = FavoriteRestaurant.objects.filter(session_key=session_key)

    # Build structure expected by template: a list of dicts with favorite, restaurant, rating
    favorite_restaurants = []
    for fav in favorites:
        restaurant = RestaurantInspection.objects.filter(CAMIS=fav.camis).first()
        rating = (
            RestaurantInspection.get_restaurant_rating(fav.camis)
            if restaurant
            else {"stars": 0, "grade": "N/A", "inspection_count": 0}
        )
        favorite_restaurants.append(
            {
                "favorite": fav,
                "restaurant": (
                    restaurant
                    if restaurant
                    else type(
                        "obj",
                        (object,),
                        {"CAMIS": fav.camis, "DBA": fav.restaurant_name},
                    )
                ),
                "rating": rating,
            }
        )

    context = {
        "favorite_restaurants": favorite_restaurants,
        "total_favorites": favorites.count(),
    }
    return render(request, "inspections/favorites_list.html", context)


def followed_restaurants(request):
    """Display user's followed restaurants with notifications"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    if request.user.is_authenticated:
        followed = FollowedRestaurant.objects.filter(user=request.user)
    else:
        followed = FollowedRestaurant.objects.filter(session_key=session_key)

    # Get detailed info for each followed restaurant
    followed_restaurants_list = []
    for follow in followed:
        # Get latest inspection info for this restaurant
        restaurant = RestaurantInspection.objects.filter(CAMIS=follow.camis).first()
        if restaurant:
            # Get rating information
            rating_info = RestaurantInspection.get_restaurant_rating(follow.camis)

            # Get recent notifications for this restaurant
            recent_notifications = RestaurantNotification.objects.filter(
                followed_restaurant=follow
            )[:3]

            # Get full notification history for dropdown
            notification_history = RestaurantNotification.objects.filter(
                followed_restaurant=follow
            ).order_by("-created_at")

            followed_restaurants_list.append(
                {
                    "follow": follow,
                    "restaurant": restaurant,
                    "rating": rating_info,
                    "recent_notifications": recent_notifications,
                    "notification_history": notification_history,
                }
            )

    # Get all unread notifications for the user
    if request.user.is_authenticated:
        all_notifications = RestaurantNotification.objects.filter(
            followed_restaurant__user=request.user, is_read=False
        ).order_by("-created_at")[:10]
    else:
        all_notifications = RestaurantNotification.objects.filter(
            followed_restaurant__session_key=session_key, is_read=False
        ).order_by("-created_at")[:10]

    context = {
        "followed_restaurants": followed_restaurants_list,
        "notifications": all_notifications,
        "total_followed": followed.count(),
    }
    return render(request, "inspections/followed_restaurants.html", context)


def notifications_list(request):
    """Display all notifications for followed restaurants"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    if request.user.is_authenticated:
        notifications = RestaurantNotification.objects.filter(
            followed_restaurant__user=request.user
        ).order_by("-created_at")
    else:
        notifications = RestaurantNotification.objects.filter(
            followed_restaurant__session_key=session_key
        ).order_by("-created_at")
    # Mark all notifications as read when viewed
    notifications.filter(is_read=False).update(is_read=True)
    context = {
        "notifications": notifications,
        "total_notifications": notifications.count(),
    }
    return render(request, "inspections/notifications.html", context)


def customer_logout(request):
    logout(request)
    return redirect("search_restaurants")


@require_POST
def update_notification_preferences(request):
    """Update notification preferences for a followed restaurant"""
    camis = request.POST.get("camis")
    notification_type = request.POST.get("notification_type")
    enabled = request.POST.get("enabled") == "true"

    if not camis or not notification_type:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    # Validate notification_type BEFORE database lookup
    valid_types = ["grade_changes", "new_inspections", "violations"]
    if notification_type not in valid_types:
        return JsonResponse({"error": "Invalid notification type"}, status=400)

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    try:
        followed = FollowedRestaurant.objects.get(session_key=session_key, camis=camis)

        # Update the specific notification preference
        if notification_type == "grade_changes":
            followed.notify_grade_changes = enabled
        elif notification_type == "new_inspections":
            followed.notify_new_inspections = enabled
        elif notification_type == "violations":
            followed.notify_violations = enabled

        followed.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Notification preference updated for {followed.restaurant_name}",
            }
        )

    except FollowedRestaurant.DoesNotExist:
        return JsonResponse(
            {"error": "Restaurant not found in your followed list"}, status=404
        )
