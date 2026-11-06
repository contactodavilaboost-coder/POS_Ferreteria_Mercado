# -*- coding: utf-8 -*-
import odoo
from odoo import api, SUPERUSER_ID

db_names = odoo.service.db.list_dbs()
print(f'FOUND DATABASES IN POSTGRES: {db_names}')

for db_name in db_names:
    print(f'UPGRADING/INSTALLING MODULES ON DATABASE: {db_name}...')
    try:
        registry = odoo.modules.registry.Registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            mods = env['ir.module.module'].search([('name', 'in', ['kamaleon_dashboard', 'kamaleon_erp'])])
            for m in mods:
                print(f'Module {m.name} state: {m.state}')
                if m.state != 'installed':
                    m.button_immediate_install()
                else:
                    m.button_immediate_upgrade()
            cr.commit()

            quants = env['stock.quant'].sudo().search([])
            for q in quants:
                if q.product_id:
                    q.total_sale_value = q.quantity * q.product_id.lst_price
            cr.commit()
            print(f'SUCCESSFULLY UPDATED {db_name}!')
    except Exception as e:
        print(f'Error updating {db_name}: {e}')
