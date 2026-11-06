# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    jorge = env['res.users'].search([('login', '=', 'arevalooliveros30@gmail.com')], limit=1)
    print(f"User Jorge: ID {jorge.id}, Name: {jorge.name}")
    
    # Check routes assigned to Jorge
    routes = env['kamaleon.sale.route'].search([('user_id', '=', jorge.id)])
    print(f"Routes assigned to Jorge ({len(routes)}):")
    for r in routes:
        print(f"  - Route ID {r.id}: {r.name} (Code: {r.code}) | Partners count: {len(r.partner_ids)}")
        
    # Check partners assigned to Jorge directly via user_id
    partners_direct = env['res.partner'].search([('user_id', '=', jorge.id), ('x_is_customer', '=', True)])
    print(f"Partners with direct user_id = Jorge: {len(partners_direct)}")
    
    # Check partners with x_route_id.user_id = Jorge
    partners_route = env['res.partner'].search([('x_route_id.user_id', '=', jorge.id), ('x_is_customer', '=', True)])
    print(f"Partners with x_route_id.user_id = Jorge: {len(partners_route)}")
    
    # Total unique partners for Jorge
    all_jorge_partners = env['res.partner'].search([
        ('x_is_customer', '=', True),
        '|', ('user_id', '=', jorge.id), ('x_route_id.user_id', '=', jorge.id)
    ])
    print(f"Total unique customer partners matching Jorge (user_id OR route.user_id): {len(all_jorge_partners)}")
    for p in all_jorge_partners[:10]:
        print(f"  - Partner {p.id}: {p.name} | user_id: {p.user_id.name} | route: {p.x_route_id.name if p.x_route_id else None}")
