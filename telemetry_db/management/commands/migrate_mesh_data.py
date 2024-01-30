import json
from django.core.management.base import BaseCommand
from django.db import connection
from telemetry_db.models import Mesh, MeshDumpLocation, MeshInstance, TestRun, Build, Platform, Map, Configuration
from django.db import transaction

class Command(BaseCommand):
    help = 'Migrates mesh dump data from the old labeled_table to the new Django models'

    def handle(self, *args, **kwargs):
        self.migrate_mesh_data()

    def migrate_mesh_data(self):
        with connection.cursor() as cursor:
            print("Reading the 15 latest mesh dump data entries")
            cursor.execute("""
                SELECT `build`, `json` FROM labeled_table 
                WHERE `directory`='mesh_dump' AND `label`='raw_data'
                ORDER BY `date` DESC 
                LIMIT 15
            """)
            mesh_dump_rows = cursor.fetchall()

        default_platform, _ = Platform.objects.get_or_create(name='pc')
        default_map, _ = Map.objects.get_or_create(name='city')
        default_config, _ = Configuration.objects.get_or_create(name='rd')

        mesh_cache = {}

        # Wrap the process in a single transaction
        with transaction.atomic():
            for row in mesh_dump_rows:
                build_version, mesh_dump_json = row
                
                if Build.objects.filter(version=build_version).exists():
                    print(f'Skipping {build_version} - already added')
                    continue
                
                mesh_dump_data = json.loads(mesh_dump_json)

                print(f"Processing {build_version}")

                build, _ = Build.objects.get_or_create(version=build_version)
                test_run, _ = TestRun.objects.get_or_create(
                    platform=default_platform,
                    configuration=default_config,
                    build=build,
                    map=default_map,
                    run_identifier=f"Mesh dump @ {build.display}"
                )

                # List to hold MeshInstance objects for bulk creation
                mesh_instances_to_create = []

                for location_data in mesh_dump_data:
                    print(f"Processing {location_data['name']}")
                    location, _ = MeshDumpLocation.objects.get_or_create(
                        name=location_data['name'],
                        invoke=location_data['invoke'],
                        region=location_data['region'],
                        coords=location_data['coords'],
                        map=default_map
                    )

                    for mesh_data in location_data['dump']:
                        mesh_name = mesh_data['name']
                        if mesh_name in mesh_cache:
                            mesh = mesh_cache[mesh_name]
                        else:
                            mesh, created = Mesh.objects.get_or_create(
                                name=mesh_name,
                                defaults={
                                    'rpack': mesh_data['rpack'],
                                    'path': mesh_data['path'],
                                    'dir': mesh_data['dir'],
                                }
                            )
                            if not created:
                                mesh.rpack = mesh_data['rpack']
                                mesh.path = mesh_data['path']
                                mesh.dir = mesh_data['dir']
                                mesh.save()

                            # Store in cache
                            mesh_cache[mesh_name] = mesh

                        # Prepare MeshInstance object and add it to the list
                        mesh_instance = MeshInstance(
                            mesh=mesh,
                            dump_location=location,
                            test_run=test_run,
                            cpu_size=mesh_data['cpu_size'],
                            gpu_size=mesh_data['gpu_size'],
                            instance_count=mesh_data['refs']  # Assuming 'refs' means the instance count
                        )
                        mesh_instances_to_create.append(mesh_instance)

                # Bulk create MeshInstance objects
                MeshInstance.objects.bulk_create(mesh_instances_to_create)
                print(f"Data migrated for build: {build_version}")
