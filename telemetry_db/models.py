from django.db import models
import jsonfield
import datetime
import re


class Platform(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Configuration(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Build(models.Model):
    version = models.CharField(max_length=100)
    display = models.CharField(max_length=100, blank=True)
    stream = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Extract date and name from version
        build_date_match = self._parse_build_date(self.version)
        if build_date_match:
            year, month, day = (
                int(build_date_match[:4]),
                int(build_date_match[4:6]),
                int(build_date_match[6:8]),
            )
            self.release_date = datetime.date(year, month, day)

            formatted_date = f"{build_date_match[6:8]}.{build_date_match[4:6]}"
            build_name = self._parse_build_name(self.version)
            self.display = (
                f"{build_name} {formatted_date}" if build_name else formatted_date
            )
            self.stream = build_name

        super(Build, self).save(*args, **kwargs)

    @staticmethod
    def _parse_build_date(version):
        match = re.search(r'__(\d{8})_', version)
        return match[1] if match else None

    @staticmethod
    def _parse_build_name(version):
        match = re.search(r'__(.*?)__', version)
        return match[1].replace('_', ' ') if match else None

    def __str__(self):
        return self.display


class Map(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class TestRun(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    configuration = models.ForeignKey(Configuration, on_delete=models.CASCADE)
    build = models.ForeignKey(Build, on_delete=models.CASCADE)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    run_identifier = models.CharField(max_length=100)

    def __str__(self):
        return self.run_identifier


class MemoryDump(models.Model):
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    dump_label = models.CharField(max_length=255)
    summary_json = jsonfield.JSONField()
    allocations_json = jsonfield.JSONField()

    def __str__(self):
        return f"{self.test_run} {self.dump_label} {self.timestamp}"


class Mesh(models.Model):
    name = models.CharField(max_length=255)
    rpack = models.CharField(max_length=100)
    path = models.TextField()
    dir = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name


class MeshDumpLocation(models.Model):
    name = models.CharField(max_length=255)
    invoke = models.TextField()
    region = models.CharField(max_length=50)
    coords = models.CharField(max_length=100)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class MeshInstance(models.Model):
    mesh = models.ForeignKey(Mesh, on_delete=models.CASCADE)
    dump_location = models.ForeignKey(MeshDumpLocation, on_delete=models.CASCADE)
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    cpu_size = models.IntegerField(db_index=True)
    gpu_size = models.IntegerField(db_index=True)
    instance_count = models.IntegerField(db_index=True)

    def __str__(self):
        return f"{self.mesh.name} instances at {self.dump_location.name} during {self.test_run}"