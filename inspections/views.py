from django.shortcuts import render
from inspections.models import RestaurantInspection

def search_restaurants(request):
    query = request.GET.get('q', '')
    results = RestaurantInspection.objects.all()

    if query:
        results = results.filter(DBA__icontains=query)  # case-insensitive search by restaurant name

    context = {
        "results": results[:100],  # limit to first 100 for speed
        "query": query
    }
    return render(request, "inspections/search.html", context)
