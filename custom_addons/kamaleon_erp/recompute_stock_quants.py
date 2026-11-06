# -*- coding: utf-8 -*-
import odoo
from odoo import api

registry = odoo.modules.registry.Registry('said_express')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    quants = env['stock.quant'].sudo().search([])
    print(f'Recomputing sale valuation for {len(quants)} stock quants...')
    for q in quants:
        if q.product_id:
            q.total_sale_value = q.quantity * q.product_id.lst_price
    cr.commit()
    print('SUCCESSFULLY RECOMPUTED STOCK QUANTS SALE VALUATION!')
