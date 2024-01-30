# Generated by Django 3.2.23 on 2023-12-19 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telemetry_db', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mesh',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('rpack', models.CharField(max_length=100)),
                ('path', models.TextField()),
                ('dir', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='MeshDumpLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('invoke', models.TextField()),
                ('region', models.CharField(max_length=50)),
                ('coords', models.CharField(max_length=100)),
                ('map', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telemetry_db.map')),
            ],
        ),
        migrations.CreateModel(
            name='MeshInstance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cpu_size', models.IntegerField()),
                ('gpu_size', models.IntegerField()),
                ('instance_count', models.IntegerField()),
                ('dump_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telemetry_db.meshdumplocation')),
                ('mesh', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telemetry_db.mesh')),
                ('test_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telemetry_db.testrun')),
            ],
        ),
    ]
