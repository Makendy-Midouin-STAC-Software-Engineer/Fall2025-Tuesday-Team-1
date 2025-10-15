from django.shortcuts import render
from django.db.models import Q
from inspections.models import RestaurantInspection
from collections import OrderedDict

def search_restaurants(request):
    query = request.GET.get('q', '').strip()
    selected_cuisine = request.GET.get('cuisine', '').strip()
    selected_borough = request.GET.get('borough', '').strip()
    zipcode = request.GET.get('zipcode', '').strip()

    cuisines = (
        RestaurantInspection.objects
        .exclude(CUISINE_DESCRIPTION__isnull=True)
        .exclude(CUISINE_DESCRIPTION__exact='')
        .values_list('CUISINE_DESCRIPTION', flat=True)
        .distinct()
        .order_by('CUISINE_DESCRIPTION')
    )

    boroughs = (
        RestaurantInspection.objects
        .exclude(BORO__isnull=True)
        .exclude(BORO__exact=0)
        .values_list('BORO', flat=True)
        .distinct()
        .order_by('BORO')
    )

    restaurants = []  # nothing by default

    # Build filter conditions
    filter_conditions = Q()
        
    if query:
        filter_conditions &= Q(DBA__icontains=query)

    if selected_cuisine:
        filter_conditions &= Q(CUISINE_DESCRIPTION__iexact=selected_cuisine)

    if selected_borough:
        filter_conditions &= Q(BORO__iexact=selected_borough)

    if zipcode:
        filter_conditions &= Q(ZIPCODE__icontains=zipcode)

    if filter_conditions:
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
        "cuisines": cuisines,
        "boroughs": boroughs,
        "selected_cuisine": selected_cuisine,
        "selected_borough": selected_borough,
        "zipcode": zipcode,
    }
    return render(request, "inspections/search.html", context)
