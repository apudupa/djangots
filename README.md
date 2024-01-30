│   manage.py<br>
│   __init__.py<br>
│<br>
├───telemetry_db<br>
│   │   admin.py<br>
│   │   apps.py<br>
│   │   models.py<br>
│   │   tests.py<br>
│   │   urls.py<br>
│   │   __init__.py<br>
│   │<br>
│   │<br>
│   ├───management<br>
│   │   └───commands<br>
│   │       │   migrate_memory_data.py<br>
│   │       │   migrate_mesh_data.py<br>
│   │<br>
│   │<br>
│   ├───serializers<br>
│   │       memory_dump_serializers.py<br>
│   │       mesh_dump_serializers.py<br>
│   │       __init__.py<br>
│   │   <br>
│   │   <br>
│   ├───views<br>
│       │   memory_dump_views.py<br>
│       │   mesh_dump_views.py<br>
│       │   __init__.py<br>
│       <br>
│       <br>
│<br>
└───telemetry_store<br>
        asgi.py<br>
        settings.py<br>
        urls.py<br>
        wsgi.py<br>
        __init__.py<br>
