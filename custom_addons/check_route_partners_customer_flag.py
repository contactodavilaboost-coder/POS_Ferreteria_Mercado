# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    jorge = env['res.users'].search([('login', '=', 'arevalooliveros30@gmail.com')], limit=1)
    
    routes = env['kamaleon.sale.route'].search([('user_id', '=', jorge.id)])
    for route in routes:
        all_route_partners = env['res.partner'].search([('x_route_id', '=', route.id)])
        print(f"Route '{route.name}' (ID {route.id}): Total partners = {len(all_route_partners)}")
        customers_true = env['res.partner'].search([('x_route_id', '=', route.id), ('x_is_customer', '=', True)])
        print(f"  - with x_is_customer = True: {len(customers_true)}")
