from rest_framework import serializers
from ..models import MeshInstance, Mesh


class MeshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesh
        fields = '__all__' 


class FlatMeshInstanceSerializer(serializers.ModelSerializer):
    mesh_name = serializers.CharField(source='mesh.name')
    mesh_rpack = serializers.CharField(source='mesh.rpack')
    mesh_path = serializers.CharField(source='mesh.path')
    mesh_dir = serializers.CharField(source='mesh.dir')
    cpu_size_diff = serializers.IntegerField(read_only=True, required=False)
    gpu_size_diff = serializers.IntegerField(read_only=True, required=False)


    class Meta:
        model = MeshInstance
        fields = ['mesh_name', 'mesh_rpack', 'mesh_path', 'mesh_dir', 'cpu_size_diff', 'gpu_size_diff', 'cpu_size', 'gpu_size', 'instance_count']