from django.contrib import admin
from .models import RestaurantInspection


@admin.register(RestaurantInspection)
class RestaurantInspectionAdmin(admin.ModelAdmin):
    list_display = ("DBA", "BORO", "CUISINE_DESCRIPTION", "GRADE", "SCORE")
    search_fields = ("DBA", "CUISINE_DESCRIPTION", "BORO")
