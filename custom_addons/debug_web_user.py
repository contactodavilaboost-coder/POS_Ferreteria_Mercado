# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    # Test for all non-admin users
    users = env = api.Environment(cr, 1, {})['res.users'].search([('id', '!=', 1), ('id', '!=', 2)])
    for u in users:
        u_env = api.Environment(cr, u.id, {})
        u_user = u_env.user
        routes = u_env['kamaleon.sale.route'].sudo().search([('user_id', '=', u_user.id)])
        
        domain_1 = [
            ('active', '=', True),
            ('x_is_customer', '=', True),
            ('parent_id', '=', False),
            '|', '|',
            ('user_id', '=', u_user.id),
            ('x_route_id.user_id', '=', u_user.id),
            ('x_route_id', 'in', routes.ids)
        ]
        
        partners = u_env['res.partner'].sudo().search_read(
            domain_1,
            ['id', 'name'],
            order='name asc'
        )
        print(f"User {u.id} - {u.name} ({u.login}):")
        print(f"  - x_is_vendedor_touch: {u.x_is_vendedor_touch}")
        print(f"  - Routes count: {len(routes)} -> {[r.name for r in routes]}")
        print(f"  - Filtered Partners count: {len(partners)}")
