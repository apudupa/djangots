from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessionListView, BuildListView, MemoryDumpViewSet, memdump_data, allocation_diff
from .views import MeshMemoryTableView, BuildsWithMeshDataView, MeshMemoryGrowthView, MeshListDifferenceView
from .views import DirectoryMeshMemoryGrowthView, MeshCountsView, MeshHistoryView

router = DefaultRouter()
router.register(r'memorydumps', MemoryDumpViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('memdump_data', memdump_data, name='memdump_data'),
    path('allocation_diff', allocation_diff, name='allocation_diff'),
    path('meshtable/<int:build_id>/', MeshMemoryTableView.as_view(), name='mesh-table'),
    path('buildswithmeshdata/', BuildsWithMeshDataView.as_view(), name='builds-with-mesh-data'),
    path('mesh-memory-growth/', MeshMemoryGrowthView.as_view(), name='mesh-memory-growth'),
    path('mesh-list-diff/', MeshListDifferenceView.as_view(), name='mesh-list-diff'),
    path('mesh-counts/', MeshCountsView.as_view(), name='mesh-counts'),
    path('directory-mesh-memory-growth/<str:dir_name>/<int:location_id>/', DirectoryMeshMemoryGrowthView.as_view(), name='directory-mesh-memory-growth'),
    path('mesh/<str:mesh_name>/history/', MeshHistoryView.as_view(), name='mesh-history'),
    path('sessions/', SessionListView.as_view(), name='session-list'),
    path('builds/', BuildListView.as_view(), name='build-list'),
]
