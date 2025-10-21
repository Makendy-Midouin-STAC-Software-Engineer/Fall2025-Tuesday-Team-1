from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_restaurants, name="search_restaurants"),
    path("add_review/", views.add_review, name="add_review"),
    path("restaurant/<int:camis>/", views.restaurant_detail, name="restaurant_detail"),
    path("toggle_favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("favorites/", views.favorites_list, name="favorites_list"),
]
