from django.shortcuts import render
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

    inspections = RestaurantInspection.objects.all()

    if selected_cuisine:
        inspections = inspections.filter(CUISINE_DESCRIPTION__iexact=selected_cuisine)

    if selected_borough:
        inspections = inspections.filter(BORO__iexact=selected_borough)

    if query:
        inspections = inspections.filter(DBA__icontains=query)

    if zipcode:
        inspections = inspections.filter(ZIPCODE__icontains=zipcode)

    if selected_cuisine or query or selected_borough or zipcode:
        inspections = inspections.order_by('DBA', 'INSPECTION_DATE')
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
