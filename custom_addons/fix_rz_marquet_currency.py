# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
    rz = env['res.company'].search([('name', 'ilike', 'RZ MARQUET')], limit=1)

    if not rz:
        print("Company RZ MARQUET not found!")
    else:
        print(f"Old Company Currency: {rz.currency_id.name} ({rz.currency_id.symbol})")
        
        # 1. Update res_company currency_id directly in SQL
        cr.execute("UPDATE res_company SET currency_id = %s WHERE id = %s;", (usd.id, rz.id))

        # 2. Update account_journal currency_id where VEF
        cr.execute("UPDATE account_journal SET currency_id = NULL WHERE company_id = %s AND currency_id IN (SELECT id FROM res_currency WHERE name = 'VEF');", (rz.id,))
        
        # 3. Update product_pricelist currency_id
        cr.execute("UPDATE product_pricelist SET currency_id = %s WHERE company_id = %s;", (usd.id, rz.id))

        # 4. Invalidate Odoo ORM cache
        env.invalidate_all()

        cr.commit()
        
        rz_updated = env['res.company'].browse(rz.id)
        pos = env['pos.config'].search([('company_id', '=', rz.id)])
        print(f"NEW Company Currency: {rz_updated.currency_id.name} ({rz_updated.currency_id.symbol})")
        for p in pos:
            print(f"POS {p.name} Currency: {p.currency_id.name} ({p.currency_id.symbol})")
        print("SUCCESS: RZ MARQUET updated to USD ($)!")
