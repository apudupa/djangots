from rest_framework import serializers
from telemetry_db.models import TestRun, Build

class TestRunSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='platform.name')
    configuration = serializers.CharField(source='configuration.name')
    build = serializers.IntegerField(source='build.id')
    map = serializers.CharField(source='map.name')
    
    class Meta:
        model = TestRun
        fields = ['id', 'platform', 'configuration', 'build', 'map', 'run_identifier']


class BuildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Build
        fields = ['id', 'version', 'display', 'stream', 'release_date']