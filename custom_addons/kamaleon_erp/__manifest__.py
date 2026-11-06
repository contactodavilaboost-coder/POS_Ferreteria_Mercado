# -*- coding: utf-8 -*-
{
    'name': 'Ferretería Mercado ERP & POS',
    'version': '18.0.1.0.1',
    'summary': 'Sistema POS y ERP Especializado para Ferretería Mercado - Punto de Venta Bimonetario, Inventario, Compras y Facturación',
    'description': """
        Ferretería Mercado ERP & POS
        ====================================================
        Módulo principal personalizado para Ferretería Mercado:
        - Punto de Venta (POS) bimonetario ($ / Bs.) con tasa del día editable.
        - Calculadora rápida de pago en billete de dólares con vuelto exacto en Bolívares.
        - Atajos de teclado completos (F1 a F10, D, E, T, M, Z, B) para operación sin mouse.
        - Impresión de boleta térmica optimizada 100% en Bolívares.
        - Módulos comerciales: Ventas, Facturación, Compras e Inventario de stock.
        - Tema profesional Slate / Gris Neutro de alto contraste.
    """,
    'author': 'Ferretería Mercado Team',
    'category': 'Sales/Accounting',
    'depends': [
        'base',
        'web',
        'contacts',
        'sale_management',
        'account',
        'purchase',
        'stock',
        'hr',
        'point_of_sale',
        'web_responsive',
    ],
    'data': [
        'security/kamaleon_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'views/sale_route_views.xml',
        'views/res_partner_views.xml',
        'views/sale_commission_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/account_payment_views.xml',
        'views/kamaleon_branding_views.xml',
        'views/touch_sales_views.xml',
        'views/res_users_views.xml',
        'views/product_template_views.xml',
        'views/stock_quant_views.xml',
        'views/report_invoice_zais_express.xml',
        'views/pos_config_views.xml',
        'views/ves_rate_wizard_views.xml',
        'views/report_product_label_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kamaleon_erp/static/lib/chart.js',
            'kamaleon_erp/static/src/scss/kamaleon_theme.scss',
            'kamaleon_erp/static/src/js/kamaleon_title.js',
            'kamaleon_erp/static/src/scss/touch_sales.scss',
            'kamaleon_erp/static/src/js/touch_sales.js',
            'kamaleon_erp/static/src/xml/touch_sales.xml',
        ],
        'web.report_assets_common': [
            'kamaleon_erp/static/src/scss/report_watermark_removal.scss',
        ],
        'point_of_sale._assets_pos': [
            'kamaleon_erp/static/src/scss/kamaleon_theme.scss',
            'kamaleon_erp/static/src/js/kamaleon_pos_pago_movil.js',
            'kamaleon_erp/static/src/js/kamaleon_pos_dual_currency.js',
            'kamaleon_erp/static/src/js/kamaleon_pos_keyboard_shortcuts.js',
            'kamaleon_erp/static/src/xml/kamaleon_pos_dual_currency.xml',
            'kamaleon_erp/static/src/xml/kamaleon_pos_keyboard_shortcuts.xml',
        ],
    },
    'post_migrate': 'kamaleon_erp.hooks',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
