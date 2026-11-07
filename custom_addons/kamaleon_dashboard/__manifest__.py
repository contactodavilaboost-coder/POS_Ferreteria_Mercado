# -*- coding: utf-8 -*-
{
    'name': 'Tablero de Analítica y Gráficos POS - Ferretería Mercado',
    'version': '18.0.1.0.0',
    'summary': 'Dashboard interactivo de analítica ejecutiva del Punto de Venta (POS), Ventas, Inventario y Métodos de Cobro',
    'description': """
        Módulo Especializado de Tableros y Analítica POS para Ferretería Mercado:
        - 1. Ventas Totales y Ticket Promedio del POS
        - 2. Desglose de Ventas por Métodos de Cobro (Efectivo, Pago Móvil, Punto / Tarjeta, BioPago)
        - 3. Tendencia de Ventas Diarias / Mensuales del POS
        - 4. Top 50 Artículos de Ferretería más vendidos
        - 5. Comparativa Compras a Proveedores vs Ventas de Mostrador
        - 6. Valoración de Inventario de Ferretería (Precio Costo vs Precio Venta)
        - 7. Alerta de Stock Crítico y Productos por Agotarse
        - 8. Rendimiento de Cajas / Cajeros
        - 9. Ranking de Clientes VIP
    """,
    'author': 'Ferretería Mercado Team',
    'category': 'Point of Sale/Reporting',
    'depends': [
        'base',
        'web',
        'point_of_sale',
        'sale_management',
        'account',
        'purchase',
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
