# Custom Addons Directory

Place all custom-developed Odoo modules here.

This directory is mapped inside the Docker container to `/mnt/extra-addons` and is automatically read by the Odoo server.

## Módulo de Ejemplo de Estructura
```
my_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── my_model.py
├── views/
│   └── my_model_views.xml
└── security/
    └── ir.model.access.csv
```
