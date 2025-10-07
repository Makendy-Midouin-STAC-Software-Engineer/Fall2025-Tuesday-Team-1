from django.shortcuts import render
from inspections.models import RestaurantInspection
from collections import OrderedDict

def search_restaurants(request):
    query = request.GET.get('q', '').strip()

    restaurants = []  # nothing by default

    if query:
        inspections = (
            RestaurantInspection.objects
            .filter(DBA__icontains=query)
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
    }
    return render(request, "inspections/search.html", context)
