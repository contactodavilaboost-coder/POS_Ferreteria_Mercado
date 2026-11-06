# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Find salesperson user (e.g. rodriguezraed@gmail.com)
    vendedor = env['res.users'].search([('login', '=', 'rodriguezraed@gmail.com')], limit=1)
    if not vendedor:
        partner = env['res.partner'].create({'name': 'Vendedor Zais', 'email': 'vendedor@zaisexpress.com'})
        vendedor = env['res.users'].create({
            'name': 'Vendedor Zais',
            'login': 'vendedor@zaisexpress.com',
            'email': 'vendedor@zaisexpress.com',
            'partner_id': partner.id,
            'x_is_vendedor_touch': True,
        })
    else:
        vendedor.write({'x_is_vendedor_touch': True})
        
    cr.commit()
    print(f"SUCCESS: User {vendedor.name} ({vendedor.login}) is now configured as VENDEDOR (SOLO COTIZADOR TOUCH)!")
    print(f"  Home Action: {vendedor.action_id.name} ({vendedor.action_id.id})")
    print(f"  Groups: {[g.name for g in vendedor.groups_id]}")
