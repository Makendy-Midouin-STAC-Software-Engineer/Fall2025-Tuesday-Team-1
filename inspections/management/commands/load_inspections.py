import pandas as pd
from django.core.management.base import BaseCommand
from inspections.models import RestaurantInspection


class Command(BaseCommand):
    help = "Load NYC restaurant inspection CSV data"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file")
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete all existing records before loading",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        if options["truncate"]:
            self.stdout.write("Deleting all existing RestaurantInspection records...")
            RestaurantInspection.objects.all().delete()

        self.stdout.write(f"Loading CSV from {csv_file} in chunks...")

        chunksize = 5000
        total_inserted = 0
        total_rows = sum(1 for _ in open(csv_file, encoding="utf-8")) - 1
        self.stdout.write(f"Total rows in file: {total_rows}")

        for chunk in pd.read_csv(csv_file, chunksize=chunksize, encoding="utf-8"):
            inspections = []

            for _, row in chunk.iterrows():

                def parse_date(date_val):
                    if pd.isna(date_val):
                        return None
                    try:
                        return pd.to_datetime(date_val).date()
                    except (ValueError, TypeError):
                        return None

                inspections.append(
                    RestaurantInspection(
                        CAMIS=row.get("CAMIS"),
                        DBA=row.get("DBA"),
                        BORO=row.get("BORO"),
                        BUILDING=row.get("BUILDING"),
                        STREET=row.get("STREET"),
                        ZIPCODE=str(row.get("ZIPCODE"))
                        if pd.notnull(row.get("ZIPCODE"))
                        else None,
                        PHONE=row.get("PHONE"),
                        CUISINE_DESCRIPTION=row.get("CUISINE DESCRIPTION"),
                        INSPECTION_DATE=parse_date(row.get("INSPECTION DATE")),
                        ACTION=row.get("ACTION"),
                        VIOLATION_CODE=row.get("VIOLATION CODE"),
                        VIOLATION_DESCRIPTION=row.get("VIOLATION DESCRIPTION"),
                        CRITICAL_FLAG=row.get("CRITICAL FLAG"),
                        SCORE=row.get("SCORE")
                        if pd.notnull(row.get("SCORE"))
                        else None,
                        GRADE=row.get("GRADE"),
                        GRADE_DATE=parse_date(row.get("GRADE DATE")),
                        RECORD_DATE=parse_date(row.get("RECORD DATE")),
                        INSPECTION_TYPE=row.get("INSPECTION TYPE"),
                        Latitude=row.get("Latitude")
                        if pd.notnull(row.get("Latitude"))
                        else None,
                        Longitude=row.get("Longitude")
                        if pd.notnull(row.get("Longitude"))
                        else None,
                        Community_Board=row.get("Community Board"),
                        Council_District=row.get("Council District"),
                        Census_Tract=row.get("Census Tract"),
                        BIN=row.get("BIN"),
                        BBL=row.get("BBL"),
                        NTA=row.get("NTA"),
                        Location_Point1=row.get("Location Point1"),
                    )
                )

            RestaurantInspection.objects.bulk_create(inspections)
            total_inserted += len(inspections)
            pct = (total_inserted / total_rows) * 100
            self.stdout.write(
                f"Inserted {total_inserted}/{total_rows} rows ({pct:.2f}%)"
            )

        self.stdout.write(self.style.SUCCESS("Data loaded successfully!"))
