from django.db import models

class RestaurantInspection(models.Model):
    CAMIS = models.BigIntegerField()
    DBA = models.CharField(max_length=255, null=True, blank=True)
    BORO = models.CharField(max_length=50, null=True, blank=True)
    BUILDING = models.CharField(max_length=50, null=True, blank=True)
    STREET = models.CharField(max_length=255, null=True, blank=True)
    ZIPCODE = models.CharField(max_length=20, null=True, blank=True)
    PHONE = models.CharField(max_length=20, null=True, blank=True)
    CUISINE_DESCRIPTION = models.CharField(max_length=255, null=True, blank=True)
    INSPECTION_DATE = models.DateField(null=True, blank=True)
    ACTION = models.TextField(null=True, blank=True)
    VIOLATION_CODE = models.CharField(max_length=20, null=True, blank=True)
    VIOLATION_DESCRIPTION = models.TextField(null=True, blank=True)
    CRITICAL_FLAG = models.CharField(max_length=50, null=True, blank=True)
    SCORE = models.IntegerField(null=True, blank=True)
    GRADE = models.CharField(max_length=5, null=True, blank=True)
    GRADE_DATE = models.DateField(null=True, blank=True)
    RECORD_DATE = models.DateField(null=True, blank=True)
    INSPECTION_TYPE = models.CharField(max_length=255, null=True, blank=True)
    Latitude = models.FloatField(null=True, blank=True)
    Longitude = models.FloatField(null=True, blank=True)
    Community_Board = models.CharField(max_length=50, null=True, blank=True)
    Council_District = models.CharField(max_length=50, null=True, blank=True)
    Census_Tract = models.CharField(max_length=50, null=True, blank=True)
    BIN = models.CharField(max_length=50, null=True, blank=True)
    BBL = models.CharField(max_length=50, null=True, blank=True)
    NTA = models.CharField(max_length=50, null=True, blank=True)
    Location_Point1 = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.DBA} ({self.CAMIS})"
