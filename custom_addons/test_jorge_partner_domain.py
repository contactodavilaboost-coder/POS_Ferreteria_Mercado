# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 12, {})
    user = env.user
    
    routes = env['kamaleon.sale.route'].sudo().search([('user_id', '=', user.id)])
    
    domain = [
        ('active', '=', True),
        ('x_is_customer', '=', True),
        ('parent_id', '=', False),
    ]
    
    if user.sudo().x_is_vendedor_touch or not env.is_admin():
        domain.extend([
            '|', '|',
            ('user_id', '=', user.id),
            ('x_route_id.user_id', '=', user.id),
            ('x_route_id', 'in', routes.ids)
        ])
        
    partners = env['res.partner'].sudo().search_read(
        domain,
        ['id', 'name', 'vat', 'email', 'phone', 'x_route_id', 'user_id'],
        order='name asc'
    )
    
    print(f"Testing domain for user {user.name}:")
    print(f"  Assigned routes count: {len(routes)}")
    print(f"  Matching customer partners found: {len(partners)}")
    for p in partners[:10]:
        print(f"    - {p['id']}: {p['name']} | Route: {p.get('x_route_id')}")
