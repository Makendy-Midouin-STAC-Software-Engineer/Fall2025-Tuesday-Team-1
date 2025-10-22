from django.shortcuts import render
from inspections.models import RestaurantInspection, RestaurantReview, FavoriteRestaurant, FollowedRestaurant, RestaurantNotification
from collections import OrderedDict
from django.db.models import Q
from datetime import datetime, date
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def search_restaurants(request):
    query = request.GET.get('q', '').strip()
    cuisine = request.GET.get('cuisine', '').strip()
    zipcode = request.GET.get('zipcode', '').strip()
    borough = request.GET.get('borough', '').strip()
    sort_by = request.GET.get('sort_by', 'name').strip()
    page_number = request.GET.get('page', 1)

    restaurants = []
    paginator = None
    page_obj = None
    
    if query or cuisine or zipcode or borough:
        # Build search filter
        search_filter = Q()
        if query:
            search_filter &= (
                Q(DBA__icontains=query) | 
                Q(CUISINE_DESCRIPTION__icontains=query)
            )
        if cuisine and cuisine != 'All Cuisines':
            search_filter &= Q(CUISINE_DESCRIPTION__icontains=cuisine)
        if zipcode:
            try:
                zipcode_num = float(zipcode)
                search_filter &= Q(ZIPCODE=zipcode_num)
            except ValueError:
                # If zipcode is not a valid number, ignore it
                pass
        if borough and borough != 'All Boroughs':
            search_filter &= Q(BORO__iexact=borough)

        # Get unique restaurants efficiently (SQLite compatible)
        # First get all matching inspections ordered by restaurant and date
        inspections = (
            RestaurantInspection.objects
            .filter(search_filter)
            .order_by('CAMIS', '-INSPECTION_DATE')
        )
        
        # Process to get unique restaurants (first 100 for performance)
        seen_camis = set()
        limited_restaurants = []
        
        for inspection in inspections:
            if inspection.CAMIS not in seen_camis:
                seen_camis.add(inspection.CAMIS)
                limited_restaurants.append({
                    'CAMIS': inspection.CAMIS,
                    'DBA': inspection.DBA,
                    'BUILDING': inspection.BUILDING,
                    'STREET': inspection.STREET,
                    'BORO': inspection.BORO,
                    'ZIPCODE': inspection.ZIPCODE,
                    'CUISINE_DESCRIPTION': inspection.CUISINE_DESCRIPTION
                })
                
                # Limit to 100 restaurants for performance
                if len(limited_restaurants) >= 100:
                    break
        
        # Get latest inspections for all restaurants in one query (much faster)
        camis_list = [rest['CAMIS'] for rest in limited_restaurants]
        latest_inspections = {}
        
        if camis_list:
            # Get the latest inspection for each restaurant in a single query
            for inspection in RestaurantInspection.objects.filter(
                CAMIS__in=camis_list
            ).order_by('CAMIS', '-INSPECTION_DATE'):
                if inspection.CAMIS not in latest_inspections:
                    latest_inspections[inspection.CAMIS] = inspection
        
        # Create lightweight restaurant objects with minimal data
        restaurants = []
        for rest_data in limited_restaurants:
            latest_inspection = latest_inspections.get(rest_data['CAMIS'])
            
            # Simple grade-based rating (much faster than full calculation)
            if latest_inspection and latest_inspection.GRADE:
                grade = latest_inspection.GRADE
                if grade == 'A':
                    stars = 5
                    description = "Excellent"
                elif grade == 'B':
                    stars = 4
                    description = "Good"
                elif grade == 'C':
                    stars = 3
                    description = "Fair"
                else:
                    stars = 2
                    description = "Needs improvement"
            else:
                stars = 0
                grade = 'N/A'
                description = "No grade available"
            
            # Check if favorited and followed (quick lookup)
            is_favorited = is_restaurant_favorited(request, rest_data['CAMIS'])
            is_followed = is_restaurant_followed(request, rest_data['CAMIS'])
            
            restaurants.append({
                'info': type('obj', (object,), {
                    'CAMIS': rest_data['CAMIS'],
                    'DBA': rest_data['DBA'],
                    'BUILDING': rest_data['BUILDING'],
                    'STREET': rest_data['STREET'],
                    'BORO': rest_data['BORO'],
                    'ZIPCODE': rest_data['ZIPCODE'],
                    'CUISINE_DESCRIPTION': rest_data['CUISINE_DESCRIPTION']
                }),
                'rating': {
                    'stars': stars,
                    'grade': grade,
                    'description': description,
                    'inspection_count': 1,  # Simplified
                    'latest_inspection': latest_inspection.INSPECTION_DATE if latest_inspection else None
                },
                'reviews': [],  # Skip reviews for performance
                'is_favorited': is_favorited,
                'is_followed': is_followed,
                'citations': []
            })
        
        # Sort restaurants based on selected criteria
        if sort_by == 'rating_high':
            restaurants.sort(key=lambda r: r['rating']['stars'], reverse=True)
        elif sort_by == 'rating_low':
            restaurants.sort(key=lambda r: r['rating']['stars'])
        elif sort_by == 'name':
            restaurants.sort(key=lambda r: r['info'].DBA or '')
        elif sort_by == 'latest_inspection':
            restaurants.sort(key=lambda r: r['rating']['latest_inspection'] or date(1900, 1, 1), reverse=True)
        elif sort_by == 'grade':
            grade_order = {'A': 1, 'B': 2, 'C': 3, 'N': 4, 'P': 5, 'Z': 6}
            restaurants.sort(key=lambda r: grade_order.get(r['rating']['grade'], 7))

        # Implement pagination - 20 restaurants per page
        paginator = Paginator(restaurants, 20)
        
        try:
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)

    # Get all available cuisines for the filter dropdown
    all_cuisines = (
        RestaurantInspection.objects
        .values_list('CUISINE_DESCRIPTION', flat=True)
        .distinct()
        .exclude(CUISINE_DESCRIPTION__isnull=True)
        .exclude(CUISINE_DESCRIPTION__exact='')
        .order_by('CUISINE_DESCRIPTION')
    )

    # Get all available boroughs for the dropdown
    all_boroughs = (
        RestaurantInspection.objects
        .values_list('BORO', flat=True)
        .distinct()
        .exclude(BORO__isnull=True)
        .exclude(BORO__exact='')
        .order_by('BORO')
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


def add_review(request):
    """Handle adding new restaurant reviews"""
    if request.method == 'POST':
        camis = request.POST.get('camis')
        restaurant_name = request.POST.get('restaurant_name')
        reviewer_name = request.POST.get('reviewer_name', 'Anonymous')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        
        if camis and rating and review_text:
            RestaurantReview.objects.create(
                camis=camis,
                restaurant_name=restaurant_name,
                reviewer_name=reviewer_name,
                rating=int(rating),
                review_text=review_text
            )
    
    # Redirect back to search results
    return render(request, 'inspections/review_success.html', {
        'restaurant_name': restaurant_name
    })


def restaurant_detail(request, camis):
    """Display detailed information about a specific restaurant"""
    from inspections.models import RestaurantDetails
    
    # Get restaurant inspection info
    restaurant = RestaurantInspection.objects.filter(CAMIS=camis).first()
    if not restaurant:
        return render(request, 'inspections/restaurant_not_found.html')
    
    # Get all inspections for this restaurant
    all_inspections = RestaurantInspection.objects.filter(
        CAMIS=camis
    ).order_by('-INSPECTION_DATE')
    
    # Get rating information
    rating_info = RestaurantInspection.get_restaurant_rating(camis)
    
    # Get all reviews
    reviews = RestaurantReview.objects.filter(camis=camis).order_by('-review_date')
    
    # Get extended details (or create empty one if doesn't exist)
    try:
        details = RestaurantDetails.objects.get(camis=camis)
    except RestaurantDetails.DoesNotExist:
        # Create a basic details entry for this restaurant
        details = RestaurantDetails(
            camis=camis,
            restaurant_name=restaurant.DBA or 'Restaurant Name Not Available'
        )
        # Don't save it yet - just use for display
    
    # Check if restaurant is favorited by current user
    is_favorited = is_restaurant_favorited(request, camis)
    
    context = {
        'restaurant': restaurant,
        'details': details,
        'rating': rating_info,
        'reviews': reviews,
        'all_inspections': all_inspections[:10],  # Limit to recent 10 inspections
        'total_inspections': all_inspections.count(),
        'is_favorited': is_favorited,
    }
    
    return render(request, 'inspections/restaurant_detail.html', context)


@require_POST
def toggle_favorite(request):
    """Toggle favorite status for a restaurant via AJAX"""
    camis = request.POST.get('camis')
    restaurant_name = request.POST.get('restaurant_name', '')
    
    if not camis:
        return JsonResponse({'error': 'Invalid restaurant'}, status=400)
    
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        # Check if already favorited
        favorite = FavoriteRestaurant.objects.get(
            session_key=session_key,
            camis=camis
        )
        # Remove from favorites
        favorite.delete()
        is_favorited = False
        message = f"Removed {restaurant_name} from favorites"
    except FavoriteRestaurant.DoesNotExist:
        # Add to favorites
        FavoriteRestaurant.objects.create(
            session_key=session_key,
            camis=camis,
            restaurant_name=restaurant_name
        )
        is_favorited = True
        message = f"Added {restaurant_name} to favorites"
    
    return JsonResponse({
        'is_favorited': is_favorited,
        'message': message
    })


def favorites_list(request):
    """Display user's favorite restaurants"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Get user's favorites
    favorites = FavoriteRestaurant.objects.filter(session_key=session_key)
    
    # Get detailed info for each favorite restaurant
    favorite_restaurants = []
    for fav in favorites:
        # Get latest inspection info for this restaurant
        restaurant = RestaurantInspection.objects.filter(CAMIS=fav.camis).first()
        if restaurant:
            # Get rating information
            rating_info = RestaurantInspection.get_restaurant_rating(fav.camis)
            
            favorite_restaurants.append({
                'favorite': fav,
                'restaurant': restaurant,
                'rating': rating_info
            })
    
    context = {
        'favorite_restaurants': favorite_restaurants,
        'total_favorites': len(favorite_restaurants)
    }
    
    return render(request, 'inspections/favorites_list.html', context)


def is_restaurant_favorited(request, camis):
    """Helper function to check if a restaurant is favorited by current user"""
    if not request.session.session_key:
        return False
    
    return FavoriteRestaurant.objects.filter(
        session_key=request.session.session_key,
        camis=camis
    ).exists()


def is_restaurant_followed(request, camis):
    """Helper function to check if a restaurant is followed by current user"""
    if not request.session.session_key:
        return False
    
    return FollowedRestaurant.objects.filter(
        session_key=request.session.session_key,
        camis=camis
    ).exists()


@require_POST
def toggle_follow(request):
    """Toggle follow status for a restaurant via AJAX"""
    camis = request.POST.get('camis')
    restaurant_name = request.POST.get('restaurant_name', '')
    
    if not camis:
        return JsonResponse({'error': 'Invalid restaurant'}, status=400)
    
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        # Check if already followed
        followed = FollowedRestaurant.objects.get(
            session_key=session_key,
            camis=camis
        )
        # Remove from followed
        followed.delete()
        is_followed = False
        message = f"Unfollowed {restaurant_name}"
    except FollowedRestaurant.DoesNotExist:
        # Add to followed restaurants
        # First get current restaurant state for tracking changes
        latest_inspection = RestaurantInspection.objects.filter(
            CAMIS=camis
        ).order_by('-INSPECTION_DATE').first()
        
        FollowedRestaurant.objects.create(
            session_key=session_key,
            camis=camis,
            restaurant_name=restaurant_name,
            last_known_grade=latest_inspection.GRADE if latest_inspection else None,
            last_inspection_date=latest_inspection.INSPECTION_DATE if latest_inspection else None
        )
        is_followed = True
        message = f"Now following {restaurant_name} - You'll get notified of health updates!"
    
    return JsonResponse({
        'is_followed': is_followed,
        'message': message
    })


def followed_restaurants(request):
    """Display user's followed restaurants with notifications"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Get user's followed restaurants
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
            
            followed_restaurants_list.append({
                'follow': follow,
                'restaurant': restaurant,
                'rating': rating_info,
                'recent_notifications': recent_notifications
            })
    
    # Get all unread notifications for the user
    all_notifications = RestaurantNotification.objects.filter(
        followed_restaurant__session_key=session_key,
        is_read=False
    ).order_by('-created_at')[:10]
    
    context = {
        'followed_restaurants': followed_restaurants_list,
        'notifications': all_notifications,
        'total_followed': followed.count()
    }
    
    return render(request, 'inspections/followed_restaurants.html', context)


def notifications_list(request):
    """Display all notifications for followed restaurants"""
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    # Get all notifications for this user's followed restaurants
    notifications = RestaurantNotification.objects.filter(
        followed_restaurant__session_key=session_key
    ).order_by('-created_at')
    
    # Mark all notifications as read when viewed
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
        'total_notifications': notifications.count()
    }
    
    return render(request, 'inspections/notifications.html', context)


@require_POST  
def update_notification_preferences(request):
    """Update notification preferences for a followed restaurant"""
    camis = request.POST.get('camis')
    notification_type = request.POST.get('notification_type')
    enabled = request.POST.get('enabled') == 'true'
    
    if not camis or not notification_type:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        followed = FollowedRestaurant.objects.get(
            session_key=session_key,
            camis=camis
        )
        
        # Update the specific notification preference
        if notification_type == 'grade_changes':
            followed.notify_grade_changes = enabled
        elif notification_type == 'new_inspections':
            followed.notify_new_inspections = enabled
        elif notification_type == 'violations':
            followed.notify_violations = enabled
        else:
            return JsonResponse({'error': 'Invalid notification type'}, status=400)
        
        followed.save()
        
        return JsonResponse({
            'success': True,
            'message': f"Notification preference updated for {followed.restaurant_name}"
        })
        
    except FollowedRestaurant.DoesNotExist:
        return JsonResponse({'error': 'Restaurant not found in your followed list'}, status=404)


@require_POST
def update_notification_preferences(request):
    """Update notification preferences for a followed restaurant"""
    camis = request.POST.get('camis')
    notification_type = request.POST.get('notification_type')
    enabled = request.POST.get('enabled') == 'true'
    
    if not camis or not notification_type:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    try:
        followed = FollowedRestaurant.objects.get(
            session_key=session_key,
            camis=camis
        )
        
        # Update the specific preference
        if notification_type == 'grade_changes':
            followed.notify_grade_changes = enabled
        elif notification_type == 'new_inspections':
            followed.notify_new_inspections = enabled
        elif notification_type == 'violations':
            followed.notify_violations = enabled
        else:
            return JsonResponse({'error': 'Invalid notification type'}, status=400)
        
        followed.save()
        
        return JsonResponse({
            'success': True,
            'message': f"Notification preference updated for {followed.restaurant_name}"
        })
        
    except FollowedRestaurant.DoesNotExist:
        return JsonResponse({'error': 'Restaurant not found in followed list'}, status=404)
