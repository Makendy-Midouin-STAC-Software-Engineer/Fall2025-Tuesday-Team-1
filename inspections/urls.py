from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("search/", views.search_restaurants, name="search_restaurants"),
    path("", RedirectView.as_view(url="/inspections/search/", permanent=False)),
]
