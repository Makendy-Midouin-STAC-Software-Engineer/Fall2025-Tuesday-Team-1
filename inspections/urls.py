from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("search/", views.search_restaurants, name="search_restaurants"),
    path("", RedirectView.as_view(url="/inspections/search/", permanent=False)),
    path("add_review/", views.add_review, name="add_review"),
    path("restaurant/<int:camis>/", views.restaurant_detail, name="restaurant_detail"),
    path("toggle_favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("favorites/", views.favorites_list, name="favorites_list"),
    path("toggle_follow/", views.toggle_follow, name="toggle_follow"),
    path("followed/", views.followed_restaurants, name="followed_restaurants"),
    path("notifications/", views.notifications_list, name="notifications_list"),
    path(
        "update_notification_preferences/",
        views.update_notification_preferences,
        name="update_notification_preferences",
    ),

    # Owner auth & dashboard
    path("owner/signup/", views.owner_signup, name="owner_signup"),
    path("owner/login/", views.owner_login, name="owner_login"),
    path("owner/dashboard/", views.owner_dashboard, name="owner_dashboard"),
]
