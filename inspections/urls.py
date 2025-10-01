from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_restaurants, name="search_restaurants"),
]
