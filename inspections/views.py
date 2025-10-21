from django.shortcuts import render
from inspections.models import RestaurantInspection, RestaurantReview, FavoriteRestaurant
from collections import OrderedDict
from django.db.models import Q
from datetime import datetime, date
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def search_restaurants(request):
    query = request.GET.get('q', '').strip()
    cuisine = request.GET.get('cuisine', '').strip()
    zipcode = request.GET.get('zipcode', '').strip()
    borough = request.GET.get('borough', '').strip()
    sort_by = request.GET.get('sort_by', 'name').strip()

    restaurants = []  # nothing by default

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

        inspections = (
            RestaurantInspection.objects
            .filter(search_filter)
            .order_by('DBA', '-INSPECTION_DATE')
        )

        grouped = OrderedDict()
        processed_count = 0
        max_restaurants = 50  # Limit to 50 restaurants for performance
        
        for insp in inspections:
            if insp.CAMIS not in grouped:
                # Stop processing if we've reached our limit
                if processed_count >= max_restaurants:
                    break
                    
                processed_count += 1
                
                # Get rating information for this restaurant
                rating_info = RestaurantInspection.get_restaurant_rating(insp.CAMIS)
                
                # Get recent user reviews
                recent_reviews = RestaurantReview.objects.filter(
                    camis=insp.CAMIS
                ).order_by('-review_date')[:3]  # Get 3 most recent reviews
                
                # Check if restaurant is favorited by current user
                is_favorited = is_restaurant_favorited(request, insp.CAMIS)
                
                grouped[insp.CAMIS] = {
                    "info": insp,
                    "citations": [],
                    "rating": rating_info,
                    "reviews": list(recent_reviews),
                    "is_favorited": is_favorited
                }
            grouped[insp.CAMIS]["citations"].append(insp)

        restaurants = list(grouped.values())
        
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
            # Sort by grade (A first, then B, C, etc.)
            grade_order = {'A': 1, 'B': 2, 'C': 3, 'N': 4, 'P': 5, 'Z': 6}
            restaurants.sort(key=lambda r: grade_order.get(r['rating']['grade'], 7))

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
        "restaurants": restaurants,
        "query": query,
        "cuisine": cuisine,
        "zipcode": zipcode,
        "borough": borough,
        "sort_by": sort_by,
        "all_cuisines": all_cuisines,
        "all_boroughs": all_boroughs,
        "results_limited": len(restaurants) >= 50,  # Show message if results were limited
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
