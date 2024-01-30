from rest_framework import serializers
from telemetry_db.models import TestRun

class TestRunSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='platform.name')
    configuration = serializers.CharField(source='configuration.name')
    build = serializers.CharField(source='build.version')
    map = serializers.CharField(source='map.name')
    
    class Meta:
        model = TestRun
        fields = ['id', 'platform', 'configuration', 'build', 'map', 'run_identifier']
