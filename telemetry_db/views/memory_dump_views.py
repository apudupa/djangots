from rest_framework import viewsets
from ..models import MemoryDump, Map
from ..serializers import MemoryDumpSerializer
from django.http import JsonResponse
from collections import defaultdict
import re



class MemoryDumpViewSet(viewsets.ModelViewSet):
    queryset = MemoryDump.objects.all()
    serializer_class = MemoryDumpSerializer


def memdump_data(request):
    platforms = ['xboxone', 'playstation']
    maps = [map_obj.name for map_obj in Map.objects.all()]

    def process_single_build(memdump :MemoryDump):
        categories = memdump.summary_json
        data = {
            'build': memdump.test_run.build.version,
            'categories': [{
                'name': category['name'],
                'size': category['max size']['detail'],
                'count': category['max count']['detail']} for category in categories]
        }
        return data

    def fetch_data_for_platform_and_map(platform, map_name):
        last_data_no_patch = MemoryDump.objects.filter(
            test_run__platform__name=platform,
            test_run__map__name=map_name
        ).defer('allocations_json').exclude(test_run__build__version__icontains='-patch').order_by('-timestamp')[:15]

        last_data_with_patch = MemoryDump.objects.filter(
            test_run__platform__name=platform,
            test_run__map__name=map_name,
            test_run__build__version__icontains='-patch'
        ).defer('allocations_json').order_by('-timestamp')

        combined_results = list(last_data_no_patch) + list(last_data_with_patch)
        return [process_single_build(b) for b in combined_results]

    data_by_platform_and_map = {
        platform: {
            map_name: fetch_data_for_platform_and_map(platform, map_name) for map_name in maps
        } for platform in platforms
    }

    return JsonResponse(data_by_platform_and_map)


def extract_path(s):
    match = re.search(r'\\workspace\\.*?\\', s)
    return s[match.end():] if match else s


def calculate_diff(build_data_1, build_data_2, category):
    # Initialize a map for storing sum and count differences, indexed by purpose+file
    diff_map = defaultdict(lambda: {
        'purpose': None,
        'size': 0,
        'count': 0,
        'file': None,
        'category': None,
        'category 0': None,
        'category 1': None,
        'category 2': None,
    })

    # Function to update the map with values from a build_data
    def update_map(data, operation):
        for record in data:
            if record['category'] != category:
                continue
            key = f"{record['purpose']}_{extract_path(record['file'])}_{record['line']}"
            diff_map[key]['size'] += operation * record['sum']
            diff_map[key]['count'] += operation * record['count']
            diff_map[key]['purpose'] = record['purpose']
            diff_map[key]['file'] = f"{extract_path(record['file'])} ({record['line']})"
            diff_map[key]['category'] = record['category']
            diff_map[key]['category 0'] = record['category 0']
            diff_map[key]['category 1'] = record['category 1']
            diff_map[key]['category 2'] = record['category 2']

    # Update the map with values from the right build (addition operation)
    update_map(build_data_2, 1)

    # Update the map with values from the left build (subtraction operation)
    update_map(build_data_1, -1)

    return diff_map


def allocation_diff(request):
    build_list = request.GET.get('builds')
    platform = request.GET.get('platform')
    category = request.GET.get('category')

    if not build_list or not platform or not category:
        return JsonResponse({"error": "Missing builds, platform, or category parameter"}, status=400)

    builds = build_list.split(',')
    if len(builds) != 2:
        return JsonResponse({"error": "Exactly two builds are required for comparison"}, status=400)

    # Fetch allocation data for the specified builds
    allocation_data = {}
    for build in builds:
        memdump = MemoryDump.objects.filter(
            test_run__platform__name=platform,
            test_run__build__version=build
        ).first()
        allocation_data[build] = memdump.allocations_json if memdump else []
    
    build_1_data = allocation_data.get(builds[0], [])
    build_2_data = allocation_data.get(builds[1], [])

    missing_data = [build for build in builds if not allocation_data.get(build)]

    if missing_data:
        return JsonResponse({'error': f'no allocations data for {missing_data}'}, status=404)

    # Calculate the difference
    diff_result = calculate_diff(build_1_data, build_2_data, category)

    # Filter out zero-size differences
    filtered_diff_result = {k: v for k, v in diff_result.items() if v['size'] != 0}

    return JsonResponse(filtered_diff_result)
