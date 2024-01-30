from django.core.management.base import BaseCommand
from django.db import connection
from telemetry_db.models import MemoryDump, Build, Platform, Map, Configuration, TestRun
import json

class Command(BaseCommand):
    help = 'Migrates data from the old labeled_table to the new Django models'

    def handle(self, *args, **kwargs):
        self.migrate_data()

    def migrate_data(self):
        legacy_label = "Legacy memdump location"

        # Connect to the database and execute the raw SQL query
        with connection.cursor() as cursor:
            print("Reading summaries")
            cursor.execute("SELECT `build`, `json` FROM labeled_table WHERE `directory`='memory_xboxone' AND `label`='full' ORDER BY `date` DESC LIMIT 20")
            full_rows = cursor.fetchall()

            print("Reading allocations")
            cursor.execute("SELECT `build`, `json` FROM labeled_table WHERE `directory`='memory_xboxone' AND `label`='allocations' ORDER BY `date` DESC LIMIT 20")
            allocations_rows = cursor.fetchall()

        # Process and migrate data
        for row in full_rows:
            build_version, summary_json = row
            # Find the corresponding allocations row
            allocations_json = next((r[1] for r in allocations_rows if r[0] == build_version), None)
            
            if not allocations_json:
                print(f"No allocations for {build_version}")
                continue

            # Create or get Build, Platform, Map, Configuration, and TestRun instances
            build, _ = Build.objects.get_or_create(version=build_version)
            platform, _ = Platform.objects.get_or_create(name='xboxone')
            map_obj, _ = Map.objects.get_or_create(name='city')
            config, _ = Configuration.objects.get_or_create(name='memdump')
            test_run, _ = TestRun.objects.get_or_create(
                platform=platform,
                configuration=config,
                build=build,
                map=map_obj,
                run_identifier=legacy_label
            )

            print(f"Creating data for: {build_version}..")
            # Create MemoryDump instance
            MemoryDump.objects.create(
                test_run=test_run,
                dump_label=legacy_label,
                summary_json=json.loads(summary_json),
                allocations_json=json.loads(allocations_json) if allocations_json else None
            )
