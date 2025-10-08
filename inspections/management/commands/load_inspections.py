import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from inspections.models import RestaurantInspection

class Command(BaseCommand):
    help = "Load NYC restaurant inspection CSV data"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file", type=str, help="Path to the CSV file"
        )
        parser.add_argument(
            "--truncate", action="store_true", help="Delete all existing records before loading"
        )
        parser.add_argument(
            "--chunksize", type=int, default=10000, help="Number of rows to process per chunk"
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        chunksize = options["chunksize"]

        if options["truncate"]:
            self.stdout.write("Deleting all existing RestaurantInspection records...")
            RestaurantInspection.objects.all().delete()

        self.stdout.write(f"Loading CSV from {csv_file} in chunks of {chunksize}...")

        total_inserted = 0
        total_rows = sum(1 for _ in open(csv_file, encoding="utf-8")) - 1
        self.stdout.write(f"Total rows in file: {total_rows}")

        # Parse dates when reading CSV for better performance
        date_columns = ['INSPECTION DATE', 'GRADE DATE']
        
        for chunk in pd.read_csv(
            csv_file, 
            chunksize=chunksize, 
            encoding="utf-8",
            parse_dates=date_columns
        ):
            inspections = []

            # Use vectorized operations instead of iterrows
            for idx in range(len(chunk)):
                row = chunk.iloc[idx]
                
                # Helper to extract date from datetime
                def get_date(val):
                    if pd.isna(val):
                        return None
                    return val.date() if hasattr(val, 'date') else None
                
                # Helper to get value or None
                def get_val(key):
                    val = row.get(key)
                    return None if pd.isna(val) else val

                inspections.append(
                    RestaurantInspection(
                        CAMIS=get_val("CAMIS"),
                        DBA=get_val("DBA"),
                        BORO=get_val("BORO"),
                        BUILDING=get_val("BUILDING"),
                        STREET=get_val("STREET"),
                        ZIPCODE=get_val("ZIPCODE"),
                        PHONE=get_val("PHONE"),
                        CUISINE_DESCRIPTION=get_val("CUISINE DESCRIPTION"),
                        INSPECTION_DATE=get_date(row.get("INSPECTION DATE")),
                        ACTION=get_val("ACTION"),
                        VIOLATION_CODE=get_val("VIOLATION CODE"),
                        VIOLATION_DESCRIPTION=get_val("VIOLATION DESCRIPTION"),
                        CRITICAL_FLAG=get_val("CRITICAL FLAG"),
                        SCORE=get_val("SCORE"),
                        GRADE=get_val("GRADE"),
                        GRADE_DATE=get_date(row.get("GRADE DATE")),
                        INSPECTION_TYPE=get_val("INSPECTION TYPE"),
                        Community_Board=get_val("Community Board"),
                        Council_District=get_val("Council District"),
                        Census_Tract=get_val("Census Tract"),
                    )
                )

            # Use bulk_create with ignore_conflicts and batch_size
            with transaction.atomic():
                RestaurantInspection.objects.bulk_create(
                    inspections, 
                    batch_size=1000,
                    ignore_conflicts=False
                )
            
            total_inserted += len(inspections)
            pct = (total_inserted / total_rows) * 100
            self.stdout.write(f"Inserted {total_inserted}/{total_rows} rows ({pct:.2f}%)")

        self.stdout.write(self.style.SUCCESS(f"Data loaded successfully! Total records: {total_inserted}"))