{
    'name': 'Comercializadora Venezuela',
    'version': '18.0.1.0.0',
    'summary': 'Módulo personalizado para la localización, comisiones por días de cobro y tema visual moderno para Venezuela',
    'description': """
        Módulo base y localización para comercializadoras en Venezuela:
        - Adaptación de campos fiscales (RIF con validación y tipo de contribuyente).
        - Cálculo automatizado de comisiones de ventas según días de cobro:
            * Hasta 20 días: 7%
            * De 21 a 25 días: 5%
            * Más de 25 días: 2%
        - Tema visual moderno (Emerald Green Theme) con estética glassmorphic y micro-interacciones.
    """,
    'author': 'Antigravity Consultant',
    'category': 'Custom',
    'depends': [
        'base',
        'web',
        'sale_management',
        'purchase',
        'stock',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/sale_commission_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'comercializadora_venezuela/static/src/scss/modern_theme.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
