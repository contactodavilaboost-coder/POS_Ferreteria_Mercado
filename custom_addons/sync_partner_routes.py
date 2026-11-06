# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    routes = env['kamaleon.sale.route'].search([('user_id', '!=', False)])
    print(f"Found {len(routes)} routes with assigned salespersons.")
    
    total_updated = 0
    for route in routes:
        # Find partners assigned to this route
        partners = env['res.partner'].search([('x_route_id', '=', route.id)])
        for p in partners:
            if p.user_id != route.user_id:
                p.write({'user_id': route.user_id.id})
                total_updated += 1
                
        # Also sync route.partner_ids
        for p in route.partner_ids:
            if p.x_route_id != route or p.user_id != route.user_id:
                p.write({'x_route_id': route.id, 'user_id': route.user_id.id})
                total_updated += 1
                
    cr.commit()
    print(f"SUCCESS: Synchronized route and salesperson on {total_updated} partner records!")
