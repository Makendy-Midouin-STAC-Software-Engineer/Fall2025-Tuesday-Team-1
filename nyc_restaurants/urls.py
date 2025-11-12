from django.contrib import admin
from django.urls import path, include
from inspections import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("inspections/", include("inspections.urls")),
    path("", views.search_restaurants, name="home"),
]
