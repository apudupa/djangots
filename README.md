│   manage.py
│   __init__.py
│
├───telemetry_db
│   │   admin.py
│   │   apps.py
│   │   models.py
│   │   tests.py
│   │   urls.py
│   │   __init__.py
│   │
│   │
│   ├───management
│   │   └───commands
│   │       │   migrate_memory_data.py
│   │       │   migrate_mesh_data.py
│   │
│   │
│   ├───serializers
│   │       memory_dump_serializers.py
│   │       mesh_dump_serializers.py
│   │       __init__.py
│   │   
│   │   
│   ├───views
│       │   memory_dump_views.py
│       │   mesh_dump_views.py
│       │   __init__.py
│       
│       
│
└───telemetry_store
        asgi.py
        settings.py
        urls.py
        wsgi.py
        __init__.py
