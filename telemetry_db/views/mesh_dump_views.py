from rest_framework.views import APIView
from rest_framework.response import Response
from collections import defaultdict
from django.db.models import Sum, Max
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from ..models import Mesh, MeshDumpLocation, MeshInstance, Build, TestRun
from rest_framework import status
from ..serializers import FlatMeshInstanceSerializer
from django.shortcuts import get_object_or_404


class MeshMemoryTableView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request, build_id):
        # Retrieve unique 'dir' values for columns
        dirs = Mesh.objects.values_list('dir', flat=True).distinct()

        # Aggregate CPU and GPU sizes directly in the database
        aggregates = MeshInstance.objects.filter(
            test_run__build_id=build_id
        ).values(
            'dump_location', 'mesh__dir'
        ).annotate(
            total_cpu_size=Sum('cpu_size'),
            total_gpu_size=Sum('gpu_size')
        ).order_by('dump_location', 'mesh__dir')

        # Initialize a dictionary to hold the structured data
        structured_data = defaultdict(lambda: defaultdict(lambda: {'cpu': 0, 'gpu': 0}))

        # Process each aggregated row and add it to the structured_data
        for aggregate in aggregates:
            loc_id = aggregate['dump_location']
            dir_value = aggregate['mesh__dir']
            structured_data[loc_id][dir_value] = {
                'cpu': aggregate['total_cpu_size'] or 0,
                'gpu': aggregate['total_gpu_size'] or 0
            }

        # Convert the structured data into the final table_data format
        table_data = []
        for loc_id, dirs in structured_data.items():
            # Fetch the human-readable name of the location, if necessary
            location_name = MeshDumpLocation.objects.get(pk=loc_id).name

            row = {'location': location_name, 'location_id': loc_id}
            for dir, totals in dirs.items():
                row[dir] = totals  # This adds each dir with its CPU and GPU totals to the row
            table_data.append(row)

        return Response(table_data)


class BuildsWithMeshDataView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request):
        # Query Build objects that have related MeshInstance entries through TestRun
        builds_with_mesh_data = (
            Build.objects
            .filter(testrun__meshinstance__isnull=False)
            .distinct()
            .values('id', 'version', 'display', 'stream', 'release_date')
            .order_by('-release_date')
        )

        # Convert QuerySet to a list of dicts
        builds_list = list(builds_with_mesh_data)
        return Response(builds_list)


class MeshMemoryGrowthView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request):
        builds = Build.objects.filter(testrun__meshinstance__isnull=False).distinct().order_by('release_date')

        chart_data = []

        for build in builds:
            max_memory_per_location = (
                MeshInstance.objects.filter(test_run__build=build)
                .values('dump_location')
                .annotate(total_memory=Sum('cpu_size') + Sum('gpu_size'))
                .aggregate(max_memory=Max('total_memory'))
            )['max_memory'] or 0

            chart_data.append({
                'build': {
                    'id': build.id,
                    'version': build.version,
                    'display': build.display,
                    'stream': build.stream,
                    'release_date': build.release_date.isoformat(),
                },
                'max_memory': max_memory_per_location
            })

        return Response(chart_data)


class DirectoryMeshMemoryGrowthView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request, dir_name, location_id):
        # Filter builds by MeshInstance data with the specified directory and location
        builds = Build.objects.filter(
            testrun__meshinstance__isnull=False,
            testrun__meshinstance__mesh__dir=dir_name,
            testrun__meshinstance__dump_location_id=location_id
        ).distinct().order_by('release_date')

        chart_data = []

        for build in builds:
            max_memory_per_location = (
                MeshInstance.objects.filter(
                    test_run__build=build,
                    mesh__dir=dir_name,
                    dump_location_id=location_id
                )
                .values('dump_location')
                .annotate(total_memory=Sum('cpu_size') + Sum('gpu_size'))
                .aggregate(max_memory=Max('total_memory'))
            )['max_memory'] or 0

            chart_data.append({
                'build': {
                    'id': build.id,
                    'version': build.version,
                    'display': build.display,
                    'stream': build.stream,
                    'release_date': build.release_date.isoformat(),
                },
                'max_memory': max_memory_per_location
            })

        return Response(chart_data)


def compute_differences(queryset1, queryset2, desired_set):
    # Fetch Mesh IDs from the MeshInstance querysets
    mesh_ids_set1 = set(queryset1.values_list('mesh_id', flat=True))
    mesh_ids_set2 = set(queryset2.values_list('mesh_id', flat=True))

    # Compute added, removed, and common Mesh IDs
    added_mesh_ids = mesh_ids_set2 - mesh_ids_set1
    removed_mesh_ids = mesh_ids_set1 - mesh_ids_set2
    common_mesh_ids = mesh_ids_set1 & mesh_ids_set2

    results = []

    if desired_set == 'added':
        added_meshes = queryset2.filter(mesh_id__in=added_mesh_ids)
        added_serializer = FlatMeshInstanceSerializer(added_meshes, many=True)
        results = added_serializer.data

    if desired_set == 'removed':
        removed_meshes = queryset1.filter(mesh_id__in=removed_mesh_ids)
        removed_serializer = FlatMeshInstanceSerializer(removed_meshes, many=True)
        results = removed_serializer.data

    if desired_set in {'common', 'changed'}:
        common_meshes_qs1_dict = {mi.mesh_id: mi for mi in queryset1.filter(mesh_id__in=common_mesh_ids).select_related('mesh')}
        common_meshes_qs2 = queryset2.filter(mesh_id__in=common_mesh_ids).select_related('mesh')

        changed_meshes_with_diffs = []
        for mesh2 in common_meshes_qs2:
            mesh1 = common_meshes_qs1_dict.get(mesh2.mesh_id)

            # Check if the size has changed
            cpu_diff = mesh2.cpu_size - mesh1.cpu_size
            gpu_diff = mesh2.gpu_size - mesh1.gpu_size

            if cpu_diff != 0 or gpu_diff != 0:
                # If there's a change, prepare the data
                changed_data = FlatMeshInstanceSerializer(mesh2).data
                changed_data['cpu_size_diff'] = cpu_diff
                changed_data['gpu_size_diff'] = gpu_diff
                changed_meshes_with_diffs.append(changed_data)

        # Serialize common MeshInstances
        if desired_set == 'common':
            common_serializer = FlatMeshInstanceSerializer(common_meshes_qs2, many=True)
            results = common_serializer.data

        # Add the changed MeshInstances with diffs
        if desired_set == 'changed':
            results = changed_meshes_with_diffs

    return results


class MeshListDifferenceView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request):
        # Extract parameters from the request
        build_id_1 = request.query_params.get('build1')
        build_id_2 = request.query_params.get('build2')
        location_id = request.query_params.get('location')
        directory = request.query_params.get('dir')
        desired_set = request.query_params.get('set')

        if desired_set not in {'added', 'removed', 'common', 'changed'}:
            return Response({'error': "Parameter 'set' must be one of: 'added', 'removed', 'common', 'changed'."}, status=status.HTTP_400_BAD_REQUEST)

        if not all([build_id_1, build_id_2, location_id, directory]):
            return Response({'error': 'Missing parameters for build IDs, location, or directory.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve MeshInstances for each build
        mesh_instances_build_1 = MeshInstance.objects.filter(
            test_run__build_id=build_id_1,
            dump_location_id=location_id,
            mesh__dir=directory
        ).select_related('mesh', 'test_run', 'dump_location')

        mesh_instances_build_2 = MeshInstance.objects.filter(
            test_run__build_id=build_id_2,
            dump_location_id=location_id,
            mesh__dir=directory
        ).select_related('mesh', 'test_run', 'dump_location')

        differences = compute_differences(mesh_instances_build_1, mesh_instances_build_2, desired_set)

        return Response(differences)


def compute_counts(queryset1, queryset2):
    mesh_ids_set1 = set(queryset1.values_list('mesh_id', flat=True))
    mesh_ids_set2 = set(queryset2.values_list('mesh_id', flat=True))

    added_count = len(mesh_ids_set2 - mesh_ids_set1)
    removed_count = len(mesh_ids_set1 - mesh_ids_set2)
    common_count = len(mesh_ids_set1 & mesh_ids_set2)

    return {
        'added': added_count,
        'removed': removed_count,
        'common': common_count
    }


class MeshCountsView(APIView):
    @method_decorator(cache_page(60*60))
    def get(self, request):
        build_id_1 = request.query_params.get('build1')
        build_id_2 = request.query_params.get('build2')
        location_id = request.query_params.get('location')
        directory = request.query_params.get('dir')

        if not all([build_id_1, build_id_2, location_id, directory]):
            return Response({'error': 'Missing parameters for build IDs, location, or directory.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve MeshInstances for each build
        mesh_instances_build_1 = MeshInstance.objects.filter(
            test_run__build_id=build_id_1,
            dump_location_id=location_id,
            mesh__dir=directory
        ).select_related('mesh')

        mesh_instances_build_2 = MeshInstance.objects.filter(
            test_run__build_id=build_id_2,
            dump_location_id=location_id,
            mesh__dir=directory
        ).select_related('mesh')

        counts = compute_counts(mesh_instances_build_1, mesh_instances_build_2)

        return Response(counts)


class MeshHistoryView(APIView):
    def get(self, request, mesh_name, format=None):
        mesh = get_object_or_404(Mesh, name=mesh_name)

        # Get all test runs
        test_runs = TestRun.objects.all().order_by('build__release_date')

        mesh_history = []
        first_time_seen = None

        for test_run in test_runs:
            # Get the first mesh instance for this test run, if any
            first_instance = MeshInstance.objects.filter(
                mesh=mesh, test_run=test_run
            ).first()

            if first_instance:
                cpu_size = first_instance.cpu_size
                gpu_size = first_instance.gpu_size
                instance_count = MeshInstance.objects.filter(
                    mesh=mesh, test_run=test_run
                ).count()

                # Record the first time the mesh is seen
                if first_time_seen is None:
                    first_time_seen = test_run.build.display
            else:
                cpu_size = 0
                gpu_size = 0
                instance_count = 0

            mesh_history.append({
                'cpu_size': cpu_size,
                'gpu_size': gpu_size,
                'instances_sum': instance_count,
                'build': test_run.build.display
            })
            
        results = {
            'first_time_seen': first_time_seen,
            'history': self.process_history(mesh_history, first_time_seen)
        }

        return Response(results)

    def process_history(self, mesh_history, first_time_seen):
        processed_history = []
        previous_instance_count = 0
        previous_cpu_size = 0
        previous_gpu_size = 0

        for entry in mesh_history:
            
            entry['status'] = []
            if entry['instances_sum'] == 0 and previous_instance_count > 0:
                entry['status'] = ['disappeared']
            elif (entry['instances_sum'] > 0 and previous_instance_count == 0) and entry['build'] != first_time_seen:
                entry['status'] = ['reappeared']
            elif entry['build'] == first_time_seen:
                entry['status'] = ['first time registered']
            else:
                entry['status'] = []
                    
            if (entry['instances_sum'] > 0 and previous_instance_count > 0) and ((entry['cpu_size'] != previous_cpu_size) or (entry['gpu_size'] != previous_gpu_size)):
                entry['status'] += ['size changed']
                entry['cpu_size_diff'] = entry['cpu_size'] - previous_cpu_size
                entry['gpu_size_diff'] = entry['gpu_size'] - previous_gpu_size

            if entry['status']:
                processed_history.append(entry)

            previous_instance_count = entry['instances_sum']
            
            if entry['instances_sum']:
                previous_cpu_size = entry['cpu_size']
                previous_gpu_size = entry['gpu_size']

        return processed_history
