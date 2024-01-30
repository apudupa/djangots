from rest_framework import serializers
from ..models import MemoryDump

class MemoryDumpSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryDump
        fields = ['id', 'run_identifier', 'platform', 'configuration', 'build', 'map', 'timestamp', 'summary_json']
