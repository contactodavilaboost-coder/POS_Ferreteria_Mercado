# -*- coding: utf-8 -*-
{
    'name': 'Tablero de Analítica y Gráficos - Zais Express',
    'version': '18.0.1.0.0',
    'summary': 'Dashboard interactivo de analítica con 6 gráficos principales de Ventas, Cobranzas y Productos',
    'description': """
        Módulo Independiente de Tableros y Analítica para Zais Express C.A:
        - 1. Resumen de Ventas del Mes
        - 2. Top 50 Productos más vendidos
        - 3. Cobranza Exitosa del Mes (Facturado vs Cobrado)
        - 4. Resumen de Ventas por Rutas
        - 5. Resumen de Ventas por Vendedor
        - 6. Fill Rate (Pedido vs Entregado)
    """,
    'author': 'Zais Express C.A Team',
    'category': 'Reporting',
    'depends': [
        'base',
        'web',
        'sale_management',
        'account',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kamaleon_dashboard/static/lib/chart.js',
            'kamaleon_dashboard/static/src/scss/sales_dashboard.scss',
            'kamaleon_dashboard/static/src/js/sales_dashboard.js',
            'kamaleon_dashboard/static/src/xml/sales_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
