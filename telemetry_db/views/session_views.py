from rest_framework import generics, filters
from telemetry_db.models import TestRun, Build
from telemetry_db.serializers.session_serializers import TestRunSerializer, BuildSerializer

class SessionListView(generics.ListAPIView):
    queryset = TestRun.objects.all()
    serializer_class = TestRunSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['platform__name', 'configuration__name', 'build__version', 'map__name', 'run_identifier']
    ordering_fields = '__all__'
    
    def get_queryset(self):
        """
        Optionally restricts the returned sessions to a given platform, 
        by filtering against a `platform` query parameter in the URL.
        """
        queryset = super().get_queryset()
        platform = self.request.query_params.get('platform', None)
        if platform is not None:
            queryset = queryset.filter(platform__name=platform)
        return queryset


class BuildListView(generics.ListAPIView):
    queryset = Build.objects.all()
    serializer_class = BuildSerializer