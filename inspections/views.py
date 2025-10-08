from django.shortcuts import render
from django.db.models import Q
from inspections.models import RestaurantInspection
from collections import OrderedDict

def search_restaurants(request):
    query = request.GET.get('q', '').strip()
    cuisine = request.GET.get('cuisine', '').strip()

    # Get all available cuisines for the dropdown
    all_cuisines = (
        RestaurantInspection.objects
        .values_list('CUISINE_DESCRIPTION', flat=True)
        .distinct()
        .order_by('CUISINE_DESCRIPTION')
    )

    restaurants = []  # nothing by default

    if query or cuisine:
        # Build filter conditions
        filter_conditions = Q()
        
        if query:
            filter_conditions &= Q(DBA__icontains=query)
        
        if cuisine:
            filter_conditions &= Q(CUISINE_DESCRIPTION=cuisine)

        inspections = (
            RestaurantInspection.objects
            .filter(filter_conditions)
            .order_by('DBA', 'INSPECTION_DATE')
        )

        grouped = OrderedDict()
        for insp in inspections:
            if insp.CAMIS not in grouped:
                grouped[insp.CAMIS] = {
                    "info": insp,
                    "citations": []
                }
            grouped[insp.CAMIS]["citations"].append(insp)

        restaurants = list(grouped.values())

    context = {
        "restaurants": restaurants,
        "query": query,
        "cuisine": cuisine,
        "all_cuisines": all_cuisines,
    }
    return render(request, "inspections/search.html", context)
